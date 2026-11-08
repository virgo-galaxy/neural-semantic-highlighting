"""Atomic local checkpoints with explicit schema, snapshot, optimizer, and RNG state."""
from __future__ import annotations

import os
from pathlib import Path
import random
import tempfile

import torch

from training.css.io import atomic_json, training_lock
from training.css.model import CssSemanticTransformer, ModelConfig

FORMAT = "nsh-css-checkpoint-v1"
MODEL_FORMAT = "nsh-css-model-v1"


def select_device(name: str = "auto") -> torch.device:
    if name == "auto":
        if torch.backends.mps.is_available():
            name = "mps"
        elif torch.cuda.is_available():
            name = "cuda"
        else:
            name = "cpu"
    if name not in {"cpu", "mps", "cuda"}:
        raise ValueError("Device must be auto, cpu, mps, or cuda")
    if name == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS is not available in this Python/PyTorch environment; no fallback was installed")
    if name == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA is not available in this Python/PyTorch environment")
    return torch.device(name)


def seed_all(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)


def capture_rng(device: torch.device) -> dict:
    result = {"python": random.getstate(), "cpu": torch.get_rng_state(), "device": device.type}
    if device.type == "cuda":
        result["accelerator"] = torch.cuda.get_rng_state_all()
    elif device.type == "mps":
        result["accelerator"] = torch.mps.get_rng_state()
    return result


def restore_rng(state: dict, device: torch.device) -> None:
    random.setstate(state["python"])
    torch.set_rng_state(state["cpu"])
    if state["device"] != device.type:
        print("Device changed on resume; exact numerical replay across backends is not promised.", flush=True)
    elif device.type == "cuda":
        torch.cuda.set_rng_state_all(state["accelerator"])
    elif device.type == "mps":
        torch.mps.set_rng_state(state["accelerator"])


def cpu_copy(value):
    if torch.is_tensor(value):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: cpu_copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [cpu_copy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(cpu_copy(item) for item in value)
    return value


def save_checkpoint(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name + "-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            torch.save(cpu_copy(payload), stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def load_checkpoint(path: Path) -> dict:
    payload = torch.load(path.expanduser(), map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or payload.get("format") != FORMAT:
        raise ValueError("Not a compatible CSS checkpoint; TypeScript checkpoints cannot be loaded here")
    required = {"model", "modelConfig", "schema", "dataset", "trainingConfig", "epoch", "rng", "trainingState", "optimizer", "lossWeights", "documentKinds"}
    if not required.issubset(payload):
        raise ValueError("Incomplete CSS checkpoint")
    return payload


def load_model_artifact(path: Path) -> dict:
    """Load either a selected inference artifact or a full training checkpoint."""
    payload = torch.load(path.expanduser(), map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or payload.get("format") not in {FORMAT, MODEL_FORMAT}:
        raise ValueError("Not a compatible CSS model artifact")
    required = {"model", "modelConfig", "schema", "dataset", "trainingConfig", "epoch"}
    if not required.issubset(payload):
        raise ValueError("Incomplete CSS model artifact")
    return payload


def model_from_checkpoint(payload: dict, device: torch.device) -> CssSemanticTransformer:
    schema = payload["schema"]
    if (not schema.get("tokenTypes") or len(set(schema["tokenTypes"])) != len(schema["tokenTypes"])
            or not schema.get("modifiers") or len(set(schema["modifiers"])) != len(schema["modifiers"])):
        raise ValueError("Invalid checkpoint schema")
    model = CssSemanticTransformer(ModelConfig(**payload["modelConfig"]), len(schema["tokenTypes"]), len(schema["modifiers"]))
    model.load_state_dict(payload["model"], strict=True)
    return model.to(device)

