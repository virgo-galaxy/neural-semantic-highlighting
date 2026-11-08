"""Explicit weights-only initialization from a compatible full training checkpoint."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path

import torch

from training.html.model import HtmlSemanticTransformer


def initialize_from_checkpoint(model: HtmlSemanticTransformer, path: Path) -> dict:
    raw = path.expanduser().read_bytes()
    source = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
    required = {"model", "modelConfig", "schema", "epoch", "dataset", "trainingConfig",
                "optimizer", "rng", "trainingState"}
    if (not isinstance(source, dict) or source.get("format") not in {"nsh-css-checkpoint-v1", "nsh-go-checkpoint-v1", "nsh-html-checkpoint-v1"}
            or not required.issubset(source) or source["trainingConfig"].get("smoke")):
        raise ValueError("Initialization requires a full, non-smoke compatible training checkpoint from artifacts")
    if source["modelConfig"] != model.config.to_dict():
        raise ValueError("Initialization requires identical model dimensions")
    schema = source["schema"]
    for name in ("tokenTypes", "modifiers"):
        if not schema.get(name) or len(schema[name]) != len(set(schema[name])):
            raise ValueError("Invalid initialization checkpoint schema")
    from training.html.encoding import Schema
    from training.html.prepare import REPOSITORY
    target_schema = Schema.load(REPOSITORY / "packs/html/model-schema.json")
    labels = {"token_head": (list(target_schema.token_types), schema["tokenTypes"]),
              "modifier_head": (list(target_schema.modifiers), schema["modifiers"])}
    current, original = model.state_dict(), source["model"]
    if set(current) != set(original):
        raise ValueError("Incompatible initialization checkpoint tensor names")
    for name, tensor in current.items():
        head = name.split(".")[0]
        shape = ((len(labels[head][1]), *tensor.shape[1:]) if head in labels else tensor.shape)
        if original[name].shape != shape or original[name].dtype != tensor.dtype:
            raise ValueError("Incompatible initialization checkpoint tensor: " + name)
    with torch.no_grad():
        for name, tensor in current.items():
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
            "copiedModifiers": [name for name in target_schema.modifiers if name in schema["modifiers"]],
            "optimizerAndTrainingState": "fresh HTML run"}
