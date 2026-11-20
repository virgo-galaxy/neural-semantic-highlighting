"""Portable release metadata; training checkpoints may retain local working paths."""
from __future__ import annotations

import copy
from pathlib import Path
import re

REPOSITORY = Path(__file__).resolve().parents[1]


def portable_text(value: str, *, repository: Path = REPOSITORY, home: Path | None = None) -> str:
    """Keep repository references relative and home references user-independent."""
    root = str(repository.resolve())
    home_path = str(home or Path.home())
    value = value.replace(root + "/", "")
    if value == root:
        value = "."
    value = re.sub(re.escape(home_path) + r"(?=/|$|[\s\"'])", "~", value)
    # macOS temporary directory identities are local, even outside the home path.
    return re.sub(r"/(?:private/)?var/folders/[^/\s]+/[^/\s]+/[A-Za-z0-9_]+", "<temp>", value)


def portable_data(value, **paths):
    """Copy metadata recursively, preserving tensors and mapping attributes."""
    if isinstance(value, str):
        return portable_text(value, **paths)
    if isinstance(value, dict):
        result = copy.copy(value)
        result.clear()
        result.update((portable_data(key, **paths), portable_data(item, **paths))
                      for key, item in value.items())
        if hasattr(value, "_metadata"):
            result._metadata = portable_data(value._metadata, **paths)
        return result
    if isinstance(value, list):
        return [portable_data(item, **paths) for item in value]
    if isinstance(value, tuple):
        items = [portable_data(item, **paths) for item in value]
        return type(value)(*items) if hasattr(value, "_fields") else tuple(items)
    return value


def strip_onnx_debug(message, *, all_metadata: bool = False) -> None:
    """Drop exporter debug annotations, recursively, without touching computation."""
    if "doc_string" in message.DESCRIPTOR.fields_by_name:
        message.ClearField("doc_string")
    if "metadata_props" in message.DESCRIPTOR.fields_by_name:
        kept = []
        for item in message.metadata_props:
            if all_metadata or item.key == "namespace" or item.key.startswith("pkg.torch."):
                continue
            entry = copy.deepcopy(item)
            entry.value = portable_text(entry.value)
            kept.append(entry)
        del message.metadata_props[:]
        message.metadata_props.extend(kept)
    for field, value in message.ListFields():
        if field.message_type is not None:
            if field.is_repeated:
                for item in value:
                    strip_onnx_debug(item, all_metadata=all_metadata)
            else:
                strip_onnx_debug(value, all_metadata=all_metadata)


def computation_bytes(model) -> bytes:
    """Fingerprint every non-annotation protobuf field, including all tensors."""
    clean = copy.deepcopy(model)
    strip_onnx_debug(clean, all_metadata=True)
    return clean.SerializeToString(deterministic=True)
