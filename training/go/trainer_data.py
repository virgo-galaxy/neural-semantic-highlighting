"""Validated immutable snapshots and a tensor bridge over the existing mmap reader."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import random

import torch

from dataset import GoWindowDataset
from encoding import COLUMNS, IGNORE, PAD, Schema

REPOSITORY = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def default_prepared() -> Path:
    parent = Path(os.environ.get("NSH_DATASET_ROOT", "~/Datasets/neural-semantic-highlighting")).expanduser()
    return parent / "go/prepared"


def resolve_snapshot(path: Path | None) -> Path:
    path = (path or default_prepared() / "current.json").expanduser().resolve()
    if path.is_file():
        pointer = json.loads(path.read_text(encoding="utf-8"))
        name = pointer.get("snapshotDirectory")
        if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."}:
            raise ValueError("Invalid snapshot pointer")
        path = path.parent / name
    if not (path / "manifest.json").is_file():
        raise ValueError(f"Prepared snapshot not found: {path}. Run make dataset-go-prepare first.")
    return path.resolve()


@dataclass(frozen=True)
class Snapshot:
    path: Path
    manifest: dict
    manifest_hash: str

    @classmethod
    def open(cls, path: Path | None = None) -> Snapshot:
        folder = resolve_snapshot(path)
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("format") != "nsh-go-byte-dataset-v1":
            raise ValueError("Unsupported prepared Go dataset format")
        if manifest.get("contextBytes") != 512:
            raise ValueError("This baseline requires the existing 512-byte prepared snapshot")
        schema = Schema.load(REPOSITORY / "packs/go/schema.json")
        if manifest.get("schema") != {"tokenTypes": list(schema.token_types), "modifiers": list(schema.modifiers)}:
            raise ValueError("Snapshot schema differs from packs/go/schema.json; do not relabel ids silently")
        labels = manifest.get("labels", {})
        if (labels.get("padByteId") != PAD or labels.get("ignoreId") != IGNORE
                or labels.get("boundaryClasses") != ["outside", "begin", "inside"]
                or labels.get("modifierSupervision") != "span-beginnings"
                or labels.get("continuationBytes") != "ignored"):
            raise ValueError("Unsupported prepared label masks or encoding")
        if manifest.get("policy", {}).get("evaluationWindowing") != "character-safe-fixed-cursor":
            raise ValueError("Evaluation must use fixed character-safe cuts, not Gold-adaptive cuts")
        gate = manifest.get("qualityGates", {}).get("naturalSplitBalance", {})
        if not gate.get("applicable") or not gate.get("passed"):
            raise ValueError("Prepared natural split balance has not passed its quality gate")
        if manifest.get("policy", {}).get("split") != "size-balanced-source-groups-before-windowing":
            raise ValueError("Use an audited size-balanced snapshot, not the earlier hash-only allocation")
        return cls(folder, manifest, sha256_file(folder / "manifest.json"))

    @property
    def schema(self) -> dict:
        return self.manifest["schema"]

    def identity(self) -> dict:
        return {"snapshot": self.manifest["snapshot"], "manifestHash": self.manifest_hash}

    def verify_split(self, split: str) -> None:
        if split not in {"train", "validation", "test"}:
            raise ValueError("Unknown split")
        names = [name + ".bin" for name in COLUMNS] + ["windows.jsonl", "documents.jsonl"]
        for name in names:
            relative = f"{split}/{name}"
            expected = self.manifest.get("checksums", {}).get(relative)
            if not expected or sha256_file(self.path / relative) != expected:
                raise ValueError(f"Snapshot checksum mismatch: {relative}. Do not train from changed data.")


class WindowSplit:
    def __init__(self, snapshot: Snapshot, split: str) -> None:
        self.snapshot, self.split = snapshot, split
        snapshot.verify_split(split)
        self.rows = GoWindowDataset(snapshot.path, split)
        self.refs: list[dict] = []
        self.streams: dict[str, list[int]] = {"natural": [], "focus": []}
        self.document_indices: dict[str, list[int]] = {}
        try:
            with (snapshot.path / split / "windows.jsonl").open(encoding="utf-8") as stream:
                last_document, previous_end, seen = None, 0, set()
                for index, line in enumerate(stream):
                    ref = json.loads(line)
                    document, kind = ref["documentId"], ref["stream"]
                    if kind not in self.streams:
                        raise ValueError("Unknown sampling stream")
                    if document != last_document:
                        if document in seen:
                            raise ValueError("Noncontiguous document windows")
                        seen.add(document)
                        last_document, previous_end = document, 0
                    if (ref["startByte"] != previous_end or ref["endByte"] - ref["startByte"] != ref["length"]
                            or not 0 < ref["length"] <= self.rows.size):
                        raise ValueError("Invalid document window coordinates")
                    previous_end = ref["endByte"]
                    self.refs.append(ref)
                    self.streams[kind].append(index)
                    self.document_indices.setdefault(document, []).append(index)
            if len(self.refs) != len(self.rows):
                raise ValueError("Window metadata/column count mismatch")
            counts = snapshot.manifest["splits"][split]
            for kind in self.streams:
                if len(self.streams[kind]) != counts[kind + "Windows"]:
                    raise ValueError("Stream count does not match manifest")
        except Exception:
            self.close()
            raise

    def batch(self, indices: list[int], device: torch.device) -> dict[str, torch.Tensor]:
        rows = [self.rows[index] for index in indices]
        length = max(self.refs[index]["length"] for index in indices)
        # Convert only this batch; no full corpus tensor and no DataLoader workers
        # carrying inherited mmap handles on macOS.
        result = {name: torch.tensor([list(row[name][:length]) for row in rows], dtype=torch.long, device=device)
                  for name in COLUMNS}
        result["attention_mask"] = result["input_ids"] != PAD
        count = len(self.snapshot.schema["modifiers"])
        result["modifier_targets"] = torch.stack(
            [(result["modifier_bits"] & (1 << bit)) != 0 for bit in range(count)], dim=-1
        ).float()
        return result

    def documents(self) -> dict[str, dict]:
        with (self.snapshot.path / self.split / "documents.jsonl").open(encoding="utf-8") as stream:
            docs = {record["id"]: record for record in map(json.loads, stream)}
        if set(docs) != set(self.document_indices):
            raise ValueError("Document metadata/window identities do not match")
        for name, doc in docs.items():
            refs = [self.refs[i] for i in self.document_indices[name]]
            if (refs[-1]["endByte"] != len(doc["source"].encode("utf-8"))
                    or any(ref["stream"] != doc["stream"] for ref in refs)):
                raise ValueError("Document source length or stream mismatch")
        return docs

    def close(self) -> None:
        self.rows.close()


def epoch_batches(split: WindowSplit, *, batch_size: int, focus_batch_size: int,
                  focus_every: int, seed: int, epoch: int, max_main_batches: int = 0) -> list[tuple[str, list[int]]]:
    if min(batch_size, focus_batch_size, focus_every) < 1 or max_main_batches < 0:
        raise ValueError("Invalid batch or sampling settings")
    rng = random.Random(seed + epoch * 1000003)
    natural, focus = list(split.streams["natural"]), list(split.streams["focus"])
    if not natural or not focus:
        raise ValueError("Baseline training needs both natural and focused training streams")
    rng.shuffle(natural)
    main = [natural[i:i + batch_size] for i in range(0, len(natural), batch_size)]
    if max_main_batches:
        main = main[:max_main_batches]
    result, focus_cursor, focus_order = [], 0, []
    for index, batch in enumerate(main, 1):
        result.append(("natural", batch))
        if index % focus_every == 0 or index == len(main):
            batch = []
            while len(batch) < focus_batch_size:
                if focus_cursor == len(focus_order):
                    focus_order = focus[:]
                    rng.shuffle(focus_order)
                    focus_cursor = 0
                take = min(focus_batch_size - len(batch), len(focus_order) - focus_cursor)
                batch.extend(focus_order[focus_cursor:focus_cursor + take])
                focus_cursor += take
            result.append(("focus", batch))
    return result


def training_weights(split: WindowSplit) -> dict[str, torch.Tensor]:
    """Compute class weights from training rows only, counting each row once."""
    if split.split != "train":
        raise ValueError("Loss weights must not use held-out labels")
    counts_b = torch.zeros(3, dtype=torch.long)
    counts_t = torch.zeros(len(split.snapshot.schema["tokenTypes"]), dtype=torch.long)
    positives = torch.zeros(len(split.snapshot.schema["modifiers"]), dtype=torch.long)
    begins = 0
    for start in range(0, len(split.refs), 128):
        batch = split.batch(list(range(start, min(start + 128, len(split.refs)))), torch.device("cpu"))
        boundary, token = batch["boundary_labels"], batch["token_type_labels"]
        counts_b += torch.bincount(boundary[boundary != IGNORE], minlength=3)
        counts_t += torch.bincount(token[token != IGNORE], minlength=len(counts_t))
        mask = boundary == 1
        begins += int(mask.sum())
        positives += batch["modifier_targets"][mask].sum(0).long()
        end = min(start + 128, len(split.refs))
        if start == 0 or end % 8192 == 0 or end == len(split.refs):
            print(f"  training label counts: {end}/{len(split.refs)} windows", flush=True)
    def inverse(counts: torch.Tensor, lo: float, hi: float) -> torch.Tensor:
        present = counts > 0
        weights = torch.zeros(len(counts), dtype=torch.float32)
        weights[present] = counts[present].float().rsqrt()
        weights[present] = (weights[present] / weights[present].mean()).clamp(lo, hi)
        return weights
    modifier = ((begins - positives).float() / positives.clamp_min(1)).sqrt().clamp(1, 4)
    modifier[positives == 0] = 1
    return {"boundary": inverse(counts_b, .5, 2), "token_type": inverse(counts_t, .25, 4),
            "modifier": modifier, "boundary_counts": counts_b, "token_type_counts": counts_t,
            "modifier_positives": positives, "span_beginnings": torch.tensor(begins)}
