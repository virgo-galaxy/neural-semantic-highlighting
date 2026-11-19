"""Explicit weights-only initialization from a compatible full training checkpoint."""
from __future__ import annotations

from training.shared.spec import current, PackSpec, REPOSITORY

import hashlib
import io
from pathlib import Path

import torch

from training.shared.model import SemanticTransformer, ModelConfig


def initialize_from_checkpoint(model: SemanticTransformer, path: Path) -> dict:
    raw = path.expanduser().read_bytes()
    source = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
    required = {"model", "modelConfig", "schema", "epoch", "dataset", "trainingConfig",
                "optimizer", "rng", "trainingState"}
    allowed={"nsh-css-checkpoint-v1", "nsh-go-checkpoint-v1", "nsh-html-checkpoint-v1", "nsh-vue-checkpoint-v1"}
    allowed.update(PackSpec.open(path.parent.name).checkpoint_format for path in (REPOSITORY/'packs').glob('*/pack.json'))
    if (not isinstance(source, dict) or source.get("format") not in allowed
            or not required.issubset(source) or source["trainingConfig"].get("smoke")):
        raise ValueError("Initialization requires a full, non-smoke compatible training checkpoint from artifacts")
    source_config = ModelConfig(**source["modelConfig"])
    target_dimensions = model.config.to_dict()
    source_dimensions = source_config.to_dict()
    target_kernel = target_dimensions.pop("local_kernel")
    source_kernel = source_dimensions.pop("local_kernel")
    target_relative = target_dimensions.pop('relative_attention')
    source_relative = source_dimensions.pop('relative_attention')
    if source_relative and not target_relative:
        raise ValueError('Transfer must preserve learned relative attention')
    if source_dimensions != target_dimensions or source_kernel not in (1, target_kernel):
        raise ValueError("Initialization requires identical model dimensions")
    schema = source["schema"]
    for name in ("tokenTypes", "modifiers"):
        if not schema.get(name) or len(schema[name]) != len(set(schema[name])):
            raise ValueError("Invalid initialization checkpoint schema")
    from training.shared.encoding import Schema
    target_schema = Schema.load(current().schema_path)
    labels = {"token_head": (list(target_schema.token_types), schema["tokenTypes"]),
              "modifier_head": (list(target_schema.modifiers), schema["modifiers"])}
    target_state, original = model.state_dict(), source["model"]
    fresh_local = {name for name in target_state if name.startswith("local_context.") and source_kernel == 1}
    if target_relative and not source_relative:fresh_local.add('relative_bias')
    if set(target_state) - fresh_local != set(original):
        raise ValueError("Incompatible initialization checkpoint tensor names")
    for name, tensor in target_state.items():
        if name in fresh_local:
            if bool(tensor.any()):
                raise ValueError("New residual and attention parameters must start at zero")
            continue
        head = name.split(".")[0]
        shape = ((len(labels[head][1]), *tensor.shape[1:]) if head in labels else tensor.shape)
        if original[name].shape != shape or original[name].dtype != tensor.dtype:
            raise ValueError("Incompatible initialization checkpoint tensor: " + name)
    with torch.no_grad():
        for name, tensor in target_state.items():
            if name in fresh_local:
                continue
            head = name.split(".")[0]
            if head in labels:
                target_labels, source_labels = labels[head]
                for index, label in enumerate(target_labels):
                    if label in source_labels:
                        tensor[index].copy_(original[name][source_labels.index(label)])
            else:
                tensor.copy_(original[name])
    return {"mode": source["format"].removeprefix("nsh-").removesuffix("-checkpoint-v1") + "-weights-only-transfer", "checkpoint": str(path.expanduser().resolve()),
            "checkpointHash": hashlib.sha256(raw).hexdigest(), "sourceEpoch": source["epoch"],
            "sourceDataset": source["dataset"],
            "copiedTokenTypes": [name for name in target_schema.token_types if name in schema["tokenTypes"]],
            "newTokenTypes": [name for name in target_schema.token_types if name not in schema["tokenTypes"]],
            "newTensors": sorted(fresh_local),
            "copiedModifiers": [name for name in target_schema.modifiers if name in schema["modifiers"]],
            "optimizerAndTrainingState": "fresh pack run"}
