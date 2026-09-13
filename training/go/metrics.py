"""Exact whole-document spans and mask-aware diagnostics, separated by stream."""
from __future__ import annotations

from collections import Counter
import time

import torch

from encoding import IGNORE
from inference import decode, document_logits
from lexical_inference import constrained_decode, scan_documents
from model import GoSemanticTransformer, ModelOutput
from progress import validation_line
from trainer_data import WindowSplit


def prf(tp: int, fp: int, fn: int) -> dict:
    return {"precision": tp / (tp + fp) if tp + fp else 0.0,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
            "tp": tp, "fp": fp, "fn": fn, "support": tp + fn}


class SpanMetrics:
    def __init__(self, schema: dict) -> None:
        self.schema = schema
        self.counts = {role: Counter(tp=0, fp=0, fn=0) for role in schema["tokenTypes"]}
        self.with_modifiers = Counter(tp=0, fp=0, fn=0)
        self.documents = self.exact_documents = 0

    def add(self, gold: dict, predicted: dict) -> None:
        def key(item: dict, modifiers: bool = False) -> tuple:
            base = (item["start"], item["end"], item["tokenType"])
            return base + (tuple(sorted(item.get("modifiers", []))),) if modifiers else base
        true, pred = {key(s) for s in gold["spans"]}, {key(s) for s in predicted["spans"]}
        for status, values in (("tp", true & pred), ("fp", pred - true), ("fn", true - pred)):
            for value in values:
                self.counts[value[2]][status] += 1
        true_m = {key(s, True) for s in gold["spans"]}
        pred_m = {key(s, True) for s in predicted["spans"]}
        self.with_modifiers.update(tp=len(true_m & pred_m), fp=len(pred_m - true_m), fn=len(true_m - pred_m))
        self.documents += 1
        self.exact_documents += true_m == pred_m

    def report(self) -> dict:
        total = Counter(tp=0, fp=0, fn=0)
        roles = {}
        for role, counts in self.counts.items():
            total.update(counts)
            roles[role] = prf(**counts)
        represented = [value["f1"] for value in roles.values() if value["tp"] + value["fp"] + value["fn"]]
        return {"documents": self.documents, "exactDocumentsIncludingModifiers": self.exact_documents,
                "exactSpan": prf(**total), "exactSpanMacroF1": sum(represented) / len(represented) if represented else 0.0,
                "exactSpanIncludingModifiers": prf(**self.with_modifiers), "byTokenType": roles}


class Diagnostics:
    def __init__(self, schema: dict) -> None:
        self.boundary = torch.zeros(3, 3, dtype=torch.long)
        n = len(schema["tokenTypes"])
        self.token = torch.zeros(n, n, dtype=torch.long)
        self.modifiers = torch.zeros(len(schema["modifiers"]), 3, dtype=torch.long)

    def add(self, out: ModelOutput, batch: dict, row: int, length: int, threshold: float) -> None:
        for logits, labels, matrix in ((out.boundary[row, :length], batch["boundary_labels"][row, :length], self.boundary),
                                        (out.token_type[row, :length], batch["token_type_labels"][row, :length], self.token)):
            labels = labels.cpu()
            valid = labels != IGNORE
            n = matrix.shape[0]
            flat = labels[valid] * n + logits.argmax(-1).cpu()[valid]
            matrix += torch.bincount(flat, minlength=n * n).reshape(n, n)
        valid = batch["boundary_labels"][row, :length].cpu() == 1
        true = batch["modifier_targets"][row, :length].cpu()[valid].bool()
        predicted = out.modifier[row, :length].cpu()[valid].sigmoid() >= threshold
        self.modifiers[:, 0] += (true & predicted).sum(0)
        self.modifiers[:, 1] += (~true & predicted).sum(0)
        self.modifiers[:, 2] += (true & ~predicted).sum(0)

    @staticmethod
    def confusion(matrix: torch.Tensor) -> dict:
        tp = matrix.diag()
        fp, fn = matrix.sum(0) - tp, matrix.sum(1) - tp
        included = tp + fp + fn > 0
        scores = 2 * tp.float() / (2 * tp + fp + fn).clamp_min(1)
        return {"accuracy": float(tp.sum() / matrix.sum().clamp_min(1)),
                "macroF1": float(scores[included].mean()) if bool(included.any()) else 0.0,
                "confusion": matrix.tolist()}

    def report(self, schema: dict) -> dict:
        return {"boundary": self.confusion(self.boundary), "tokenTypeAtGoldPositions": self.confusion(self.token),
                "modifiersAtGoldBeginnings": {name: prf(*row) for name, row in zip(schema["modifiers"], self.modifiers.tolist())}}


def evaluation_indices(split: WindowSplit, max_windows_per_stream: int = 0) -> list[int]:
    """A smoke cap selects complete documents, never clipped validation fragments."""
    if not max_windows_per_stream:
        return list(range(len(split.refs)))
    selected, used = [], Counter()
    for indices in split.document_indices.values():
        kind = split.refs[indices[0]]["stream"]
        if used[kind] + len(indices) <= max_windows_per_stream:
            selected.extend(indices)
            used[kind] += len(indices)
    if any(not used[kind] for kind in split.streams if split.streams[kind]):
        raise ValueError("Smoke validation cap cannot fit a complete document; increase --smoke-eval-windows")
    return selected


@torch.inference_mode()
def evaluate_fixed(model: GoSemanticTransformer, split: WindowSplit, device: torch.device,
                   *, batch_size: int = 32, threshold: float = .60,
                   max_windows_per_stream: int = 0, log_every: int = 25,
                   decoder: str = "neural") -> dict:
    """Batch fixed windows, reassemble all logits, and score whole documents.

    Cut-crossing spans are decoded only after reassembly. No Gold boundary
    guides prediction, no edge fragment is treated as an independent span.
    This is NOT the adaptive runtime benchmark; evaluate_adaptive supplies that.
    """
    started = time.monotonic()
    model.eval()
    schema = split.snapshot.schema
    docs = split.documents()
    if decoder not in {"neural", "lexical"}:
        raise ValueError("Unknown fixed-window decoder")
    if decoder == "lexical" and max_windows_per_stream:
        raise ValueError("Lexical validation requires complete documents")
    lexical = scan_documents(docs) if decoder == "lexical" else None
    indices = evaluation_indices(split, max_windows_per_stream)
    spans = {kind: SpanMetrics(schema) for kind in split.streams}
    diagnostics = {kind: Diagnostics(schema) for kind in split.streams}
    features: dict[str, SpanMetrics] = {}
    count_windows = Counter()
    pending_id, pending, pending_bytes = None, [], []

    def finish() -> None:
        if pending_id is None:
            return
        doc = docs[pending_id]
        source = b"".join(pending_bytes).decode("utf-8")
        if source != doc["source"]:
            raise ValueError("Prepared bytes do not match document source")
        output = ModelOutput(torch.cat([p.boundary for p in pending]), torch.cat([p.token_type for p in pending]),
                             torch.cat([p.modifier for p in pending]))
        predicted = (
            constrained_decode(source, output, lexical[pending_id], schema, modifier_threshold=threshold)
            if lexical is not None else decode(source, output, schema, threshold=threshold)
        )
        spans[doc["stream"]].add(doc["result"], predicted)
        if doc["stream"] == "focus":
            for feature in doc.get("features", []):
                features.setdefault(feature, SpanMetrics(schema)).add(doc["result"], predicted)

    batches = (len(indices) + batch_size - 1) // batch_size
    for step, start in enumerate(range(0, len(indices), batch_size), 1):
        chosen = indices[start:start + batch_size]
        batch = split.batch(chosen, device)
        gpu = model(batch["input_ids"], batch["attention_mask"])
        output = ModelOutput(gpu.boundary.cpu(), gpu.token_type.cpu(), gpu.modifier.cpu())
        for row, index in enumerate(chosen):
            ref = split.refs[index]
            name, length, kind = ref["documentId"], ref["length"], ref["stream"]
            if pending_id != name:
                finish()
                pending_id, pending, pending_bytes = name, [], []
            # Clone row slices so the pending document does not retain every
            # full batch allocation while it spans multiple windows.
            pending.append(ModelOutput(output.boundary[row, :length].clone(), output.token_type[row, :length].clone(),
                                       output.modifier[row, :length].clone()))
            pending_bytes.append(bytes(batch["input_ids"][row, :length].cpu().tolist()))
            diagnostics[kind].add(output, batch, row, length, threshold)
            count_windows[kind] += 1
        if log_every and step != batches and (step == 1 or step % log_every == 0):
            print(validation_line(split.split, step, batches, sum(count_windows.values()), time.monotonic() - started), flush=True)
    finish()
    if log_every:
        print(validation_line(split.split, batches, batches, sum(count_windows.values()), time.monotonic() - started), flush=True)
    inference_name = ("fixed-window-neural-logits-with-go-lexical-scaffold" if lexical is not None
                      else "fixed-window-logits-reassembled-before-document-decoding")
    return {"split": split.split, "inference": inference_name,
            "limitedSmokeEvaluation": bool(max_windows_per_stream), "seconds": time.monotonic() - started,
            "streams": {kind: {**spans[kind].report(), "windows": count_windows[kind],
                               "diagnostics": diagnostics[kind].report(schema)} for kind in spans},
            "focusFeatures": {name: value.report() for name, value in features.items()}}


@torch.inference_mode()
def evaluate_adaptive(model: GoSemanticTransformer, split: WindowSplit, device: torch.device,
                      *, threshold: float = .60) -> dict:
    docs, schema = split.documents(), split.snapshot.schema
    metrics = {kind: SpanMetrics(schema) for kind in split.streams}
    features: dict[str, SpanMetrics] = {}
    started = time.monotonic()
    for index, doc in enumerate(docs.values(), 1):
        output = document_logits(model, doc["source"], device)
        result = decode(doc["source"], output, schema, threshold=threshold)
        metrics[doc["stream"]].add(doc["result"], result)
        if doc["stream"] == "focus":
            for feature in doc.get("features", []):
                features.setdefault(feature, SpanMetrics(schema)).add(doc["result"], result)
        if index == 1 or index % 10 == 0 or index == len(docs):
            print(f"  adaptive {split.split}: document {index}/{len(docs)}, elapsed {time.monotonic() - started:.1f}s", flush=True)
    return {"split": split.split, "inference": "predicted-adaptive-cursor", "seconds": time.monotonic() - started,
            "streams": {kind: value.report() for kind, value in metrics.items()},
            "focusFeatures": {name: value.report() for name, value in features.items()}}
