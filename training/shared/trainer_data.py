"""Verified snapshot identities and batch-local tensor conversion."""
from __future__ import annotations

from training.shared.spec import current

from dataclasses import dataclass
import json
from pathlib import Path

import torch

from training.shared.dataset import WindowDataset
from training.shared.encoding import COLUMNS, IGNORE, PAD, Schema
from training.shared.prepare import REPOSITORY, dataset_root, file_hash


sha256_file = file_hash


def resolve_snapshot(path: Path | None) -> Path:
    path = (path or dataset_root() / "prepared/current.json").expanduser().resolve()
    if path.is_file():
        pointer = json.loads(path.read_text())
        name = pointer.get("snapshotDirectory")
        if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."}:
            raise ValueError("Invalid prepared snapshot pointer")
        path = path.parent / name
    if not (path / "manifest.json").is_file():
        raise ValueError("pack snapshot not found; run make dataset-vue first")
    return path


@dataclass(frozen=True)
class Snapshot:
    path: Path
    manifest: dict
    manifest_hash: str

    @classmethod
    def open(cls, path: Path | None = None) -> Snapshot:
        folder = resolve_snapshot(path)
        manifest = json.loads((folder / "manifest.json").read_text())
        if manifest.get("format") != current().dataset_format or manifest.get("contextBytes") != 512:
            raise ValueError("Incompatible pack byte dataset")
        schema = Schema.load(current().schema_path)
        if manifest.get("schema") != {"tokenTypes": list(schema.token_types), "modifiers": list(schema.modifiers)}:
            raise ValueError("pack snapshot/schema mismatch")
        if manifest["identity"].get("semanticContractHash") != file_hash(current().semantics_path):
            raise ValueError("pack snapshot/semantic contract mismatch")
        current().verify_config(manifest['identity'])
        expected = {"padByteId": PAD, "ignoreId": IGNORE, "boundaryClasses": ["outside", "begin", "inside"],
                    "modifierSupervision": "span-beginnings", "continuationBytes": "ignored"}
        if manifest.get("labels") != expected:
            raise ValueError("pack label mask/encoding mismatch")
        policy = manifest.get("policy", {})
        if (policy.get("evaluationWindowing") != "character-safe-fixed-cursor"
                or policy.get("split") != "intact-source-directories-before-windowing"):
            raise ValueError("pack evaluation must use grouped holdouts and non-Gold cuts")
        for split in ("train", "validation", "test"):
            for kind in current().document_kinds:
                if manifest["splits"][split]["documentKinds"][kind]["documents"] < 1:
                    raise ValueError(f"Missing {kind} coverage in {split}")
        return cls(folder, manifest, file_hash(folder / "manifest.json"))

    @property
    def schema(self) -> dict:
        return self.manifest["schema"]

    def identity(self) -> dict:
        return {"snapshot": self.manifest["snapshot"], "manifestHash": self.manifest_hash}

    def verify_split(self, split: str) -> None:
        if split not in {"train", "validation", "test"}:
            raise ValueError("Invalid split")
        for name in [column + ".bin" for column in COLUMNS] + ["documents.jsonl", "windows.jsonl"]:
            relative = split + "/" + name
            if file_hash(self.path / relative) != self.manifest["checksums"].get(relative):
                raise ValueError("Prepared pack checksum mismatch: " + relative)


class WindowSplit:
    def __init__(self, snapshot: Snapshot, split: str) -> None:
        self.snapshot, self.split = snapshot, split
        snapshot.verify_split(split)
        self.rows = WindowDataset(snapshot.path, split)
        self.refs = [json.loads(line) for line in (snapshot.path / split / "windows.jsonl").read_text().splitlines()]
        self.streams: dict[str, list[int]] = {"natural": [], "focus": []}
        self.document_indices: dict[str, list[int]] = {}
        try:
            previous, end, seen = None, 0, set()
            for index, ref in enumerate(self.refs):
                name = ref["documentId"]
                if ref["documentKind"] not in set(current().document_kinds) or ref["stream"] not in self.streams:
                    raise ValueError("Unknown document kind or sampling stream")
                if previous != name:
                    if name in seen:
                        raise ValueError("Noncontiguous pack document windows")
                    seen.add(name)
                    previous, end = name, 0
                if ref["startByte"] != end or not 0 < ref["length"] <= 512 or ref["endByte"] - end != ref["length"]:
                    raise ValueError("Invalid prepared pack window coordinates")
                end = ref["endByte"]
                self.streams[ref["stream"]].append(index)
                self.document_indices.setdefault(name, []).append(index)
            if len(self.rows) != len(self.refs):
                raise ValueError("pack window/column count mismatch")
        except Exception:
            self.close()
            raise

    def batch(self, indices: list[int], device: torch.device) -> dict:
        if not indices:
            raise ValueError("Empty batch")
        rows = [self.rows[index] for index in indices]
        length = max(self.refs[index]["length"] for index in indices)
        result = {name: torch.tensor([list(row[name][:length]) for row in rows], dtype=torch.long, device=device)
                  for name in COLUMNS}
        result["attention_mask"] = result["input_ids"] != PAD
        result["modifier_targets"] = torch.stack(
            [(result["modifier_bits"] & (1 << bit)) != 0 for bit in range(len(self.snapshot.schema["modifiers"]))],
            dim=-1).float()
        return result

    def documents(self) -> dict[str, dict]:
        docs = {record["id"]: record for record in map(json.loads,
            (self.snapshot.path / self.split / "documents.jsonl").read_text().splitlines())}
        if set(docs) != set(self.document_indices):
            raise ValueError("pack document/window identity mismatch")
        for name, record in docs.items():
            refs = [self.refs[index] for index in self.document_indices[name]]
            if (refs[-1]["endByte"] != len(record["source"].encode("utf-8"))
                    or any(ref["documentKind"] != record["documentKind"] for ref in refs)):
                raise ValueError("pack source length/kind mismatch")
        return docs

    def close(self) -> None:
        self.rows.close()


def training_weights(split: WindowSplit, *, stream: str = 'all') -> dict[str, torch.Tensor]:
    if stream not in {'all', 'natural'}:
        raise ValueError('Loss weights require all or natural training windows')
    boundary = torch.zeros(3)
    token = torch.zeros(len(split.snapshot.schema["tokenTypes"]))
    positive = torch.zeros(len(split.snapshot.schema["modifiers"]))
    beginnings = 0
    selected = 0
    for index in range(len(split.rows)):
        if stream == 'natural' and split.refs[index].get('stream', 'natural') != 'natural':
            continue
        selected += 1
        row = split.rows[index]
        for values, counts in ((row["boundary_labels"], boundary), (row["token_type_labels"], token)):
            valid = torch.tensor([value for value in values if value != IGNORE], dtype=torch.long)
            counts += torch.bincount(valid, minlength=len(counts))
        for label, bits in zip(row["boundary_labels"], row["modifier_bits"]):
            if label == 1:
                beginnings += 1
                for bit in range(len(positive)):
                    positive[bit] += bool(bits & (1 << bit))
    if not selected:
        raise ValueError('No selected training windows for loss weights')
    def weights(counts):
        active = counts > 0
        result = torch.ones_like(counts)
        result[active] = (counts[active].mean() / counts[active]).sqrt().clamp(.25, 8.)
        return result
    return {"boundary": weights(boundary), "token_type": weights(token),
            "modifier": ((beginnings - positive) / positive.clamp_min(1)).clamp(1., 16.)}
