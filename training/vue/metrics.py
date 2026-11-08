"""Exact whole-document spans and mask-aware diagnostics, separated by stream."""
from __future__ import annotations

from collections import Counter
import time

import torch

from training.vue.encoding import IGNORE
from training.vue.inference import decode, document_logits
from training.vue.model import VueSemanticTransformer, ModelOutput
from training.vue.progress import validation_line
from training.vue.trainer_data import WindowSplit


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


class RegionMetrics:
    """Score neural body detection separately from markup or child-language semantics."""
    def __init__(self):
        self.roles = tuple("embedded-" + role for role in ("javascript", "typescript", "jsx", "tsx", "css", "scss", "less", "data", "expression"))
        self.exact = SpanMetrics({"tokenTypes": self.roles})
        self.coverage = {role: Counter(tp=0, fp=0, fn=0) for role in self.roles}

    def add(self, gold: dict, predicted: dict):
        true = [s for s in gold["spans"] if s["tokenType"] in self.roles]
        pred = [s for s in predicted["spans"] if s["tokenType"] in self.roles]
        self.exact.add({"spans": true}, {"spans": pred})
        for role in self.roles:
            a = [s for s in true if s["tokenType"] == role]
            b = [s for s in pred if s["tokenType"] == role]
            i = j = overlap = 0
            while i < len(a) and j < len(b):
                overlap += max(0, min(a[i]["end"], b[j]["end"]) - max(a[i]["start"], b[j]["start"]))
                if a[i]["end"] <= b[j]["end"]: i += 1
                else: j += 1
            self.coverage[role].update(tp=overlap,
                fp=sum(s["end"] - s["start"] for s in b) - overlap,
                fn=sum(s["end"] - s["start"] for s in a) - overlap)

    def report(self):
        return {"scope": "body region recognition only; child JS/CSS semantics not evaluated",
                "exactRegions": self.exact.report(),
                "utf16CoverageByRole": {role: prf(**counts) for role, counts in self.coverage.items()}}


def evaluation_indices(split: WindowSplit, max_windows_per_stream: int = 0) -> list[int]:
    """A smoke cap selects complete documents per kind, never clipped fragments."""
    if not max_windows_per_stream:
        return list(range(len(split.refs)))
    selected, used = [], Counter()
    documents = split.documents()
    for document_id, indices in split.document_indices.items():
        record = documents[document_id]
        kind = (record["profile"], record["stream"])
        if used[kind] + len(indices) <= max_windows_per_stream:
            selected.extend(indices)
            used[kind] += len(indices)
    if any(not used[(profile, "natural")] for profile in ("vue2", "vue3", "vue3.2")):
        raise ValueError("Smoke validation cap cannot fit a complete document; increase --smoke-eval-windows")
    return selected


@torch.inference_mode()
def evaluate_fixed(model: VueSemanticTransformer, split: WindowSplit, device: torch.device,
                   *, batch_size: int = 32, threshold: float = .60,
                   max_windows_per_stream: int = 0, log_every: int = 25) -> dict:
    """Batch fixed windows, reassemble all logits, and score whole documents.

    Cut-crossing spans are decoded only after reassembly. No Gold boundary
    guides prediction, no edge fragment is treated as an independent span.
    This is NOT the adaptive runtime benchmark; evaluate_adaptive supplies that.
    """
    started = time.monotonic()
    model.eval()
    schema = split.snapshot.schema
    docs = split.documents()
    indices = evaluation_indices(split, max_windows_per_stream)
    spans = {kind: SpanMetrics(schema) for kind in split.streams}
    document_kinds = {kind: SpanMetrics(schema) for kind in ("vue",)}
    diagnostics = {kind: Diagnostics(schema) for kind in split.streams}
    features: dict[str, SpanMetrics] = {}
    profiles = {p: {stream: SpanMetrics(schema) for stream in split.streams} for p in ("vue2", "vue3", "vue3.2")}
    regions = RegionMetrics()
    stream_regions = {stream: RegionMetrics() for stream in split.streams}
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
        predicted = decode(source, output, schema, threshold=threshold)
        spans[doc["stream"]].add(doc["result"], predicted)
        profiles[doc["profile"]][doc["stream"]].add(doc["result"], predicted)
        document_kinds[doc["documentKind"]].add(doc["result"], predicted)
        regions.add(doc["result"], predicted)
        stream_regions[doc["stream"]].add(doc["result"], predicted)
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
    return {"split": split.split, "inference": "fixed-window-logits-reassembled-before-document-decoding",
            "limitedSmokeEvaluation": bool(max_windows_per_stream), "seconds": time.monotonic() - started,
            "streams": {kind: {**spans[kind].report(), "windows": count_windows[kind],
                               "diagnostics": diagnostics[kind].report(schema)} for kind in spans},
            "documentKinds": {kind: value.report() for kind, value in document_kinds.items()},
            "features": {name: value.report() for name, value in features.items()}, "bodyRegions": regions.report(),
            "profiles": {p: {stream: metric.report() for stream, metric in values.items()} for p, values in profiles.items()},
            "bodyRegionsByStream": {name: value.report() for name, value in stream_regions.items()},
            "scope": "base-vue-markup-and-neural-regions"}


@torch.inference_mode()
def evaluate_adaptive(model: VueSemanticTransformer, split: WindowSplit, device: torch.device,
                      *, threshold: float = .60) -> dict:
    docs, schema = split.documents(), split.snapshot.schema
    metrics = {kind: SpanMetrics(schema) for kind in split.streams}
    document_kinds = {kind: SpanMetrics(schema) for kind in ("vue",)}
    features: dict[str, SpanMetrics] = {}
    profiles = {p: {stream: SpanMetrics(schema) for stream in split.streams} for p in ("vue2", "vue3", "vue3.2")}
    regions = RegionMetrics()
    stream_regions = {stream: RegionMetrics() for stream in split.streams}
    started = time.monotonic()
    for index, doc in enumerate(docs.values(), 1):
        output = document_logits(model, doc["source"], device)
        result = decode(doc["source"], output, schema, threshold=threshold)
        metrics[doc["stream"]].add(doc["result"], result)
        profiles[doc["profile"]][doc["stream"]].add(doc["result"], result)
        document_kinds[doc["documentKind"]].add(doc["result"], result)
        regions.add(doc["result"], result)
        stream_regions[doc["stream"]].add(doc["result"], result)
        for feature in doc.get("features", []):
            features.setdefault(feature, SpanMetrics(schema)).add(doc["result"], result)
        if index == 1 or index % 10 == 0 or index == len(docs):
            print(f"  adaptive {split.split}: document {index}/{len(docs)}, elapsed {time.monotonic() - started:.1f}s", flush=True)
    return {"split": split.split, "inference": "predicted-adaptive-cursor", "seconds": time.monotonic() - started,
            "streams": {kind: value.report() for kind, value in metrics.items()},
            "documentKinds": {kind: value.report() for kind, value in document_kinds.items()},
            "features": {name: value.report() for name, value in features.items()}, "bodyRegions": regions.report(),
            "profiles": {p: {stream: metric.report() for stream, metric in values.items()} for p, values in profiles.items()},
            "bodyRegionsByStream": {name: value.report() for name, value in stream_regions.items()},
            "scope": "base-vue-markup-and-neural-regions"}
