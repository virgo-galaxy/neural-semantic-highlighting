"""Post-open diagnostic for Go sealed-v1 failures.

This tool is intentionally diagnostic-only. It requires the sealed-v1 marker to
already exist, never writes or changes that marker, and refuses a checkpoint
whose hash differs from the checkpoint that originally opened the seal.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any
import zipfile

import torch

from checkpoints import atomic_json, load_checkpoint, model_from_checkpoint, select_device
from encoding import Schema
from inference import decode, document_logits
from metrics import SpanMetrics
from quality import TARGETED_ROLES
from sealed_eval import dataset_root, load_sealed_data, load_json, sha256_file, utf16_slice, SCHEMA_PATH


def span_key(span: dict) -> tuple[int, int, str]:
    return int(span["start"]), int(span["end"]), str(span["tokenType"])


def boundary_key(span: dict) -> tuple[int, int]:
    return int(span["start"]), int(span["end"])


def overlaps(a: dict, b: dict) -> bool:
    return int(a["start"]) < int(b["end"]) and int(b["start"]) < int(a["end"])


def family_of(record: dict) -> str:
    path = str(record.get("path", ""))
    parts = path.split("/")
    return "/".join(parts[:-1]) if len(parts) > 1 else path


def string_kind(text: str) -> str:
    if text.startswith("`"):
        return "raw-multiline" if "\n" in text else "raw-singleline"
    if text.startswith('"'):
        return "interpreted-multiline" if "\n" in text else "interpreted-singleline"
    return "other"


def length_bucket(text: str) -> str:
    length = len(text.encode("utf-8"))
    if length <= 32:
        return "<=32B"
    if length <= 64:
        return "33-64B"
    if length <= 128:
        return "65-128B"
    if length <= 256:
        return "129-256B"
    if length <= 512:
        return "257-512B"
    return ">512B"


def short(text: str, limit: int = 180) -> str:
    value = text.replace("\n", "\\n")
    return value if len(value) <= limit else value[: limit - 3] + "..."


def classify_gold_span(gold: dict, predicted: list[dict], source: str) -> dict[str, Any]:
    exact_same = [span for span in predicted if span_key(span) == span_key(gold)]
    if exact_same:
        return {"status": "exact"}
    same_bounds = [span for span in predicted if boundary_key(span) == boundary_key(gold)]
    overlapping = [span for span in predicted if overlaps(gold, span)]
    overlapping_strings = [span for span in overlapping if span.get("tokenType") == "string"]
    if same_bounds:
        return {
            "status": "retyped",
            "predictedTypes": sorted({str(span.get("tokenType")) for span in same_bounds}),
        }
    if len(overlapping_strings) >= 2:
        return {
            "status": "split-string",
            "parts": [short(utf16_slice(source, int(s["start"]), int(s["end"]))) for s in overlapping_strings],
        }
    if len(overlapping_strings) == 1:
        s = overlapping_strings[0]
        return {
            "status": "partial-string",
            "part": short(utf16_slice(source, int(s["start"]), int(s["end"]))),
        }
    if overlapping:
        return {
            "status": "overlap-other",
            "predictedTypes": sorted({str(span.get("tokenType")) for span in overlapping}),
        }
    return {"status": "missed"}


def add_target_confusions(counter: Counter, record: dict, predicted: dict, role: str) -> None:
    pred_by_bounds: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for span in predicted["spans"]:
        pred_by_bounds[boundary_key(span)].append(span)
    for gold in record["result"]["spans"]:
        if gold.get("tokenType") != role:
            continue
        options = pred_by_bounds.get(boundary_key(gold), [])
        if any(span.get("tokenType") == role for span in options):
            counter[(role, role)] += 1
        elif options:
            for predicted_span in options:
                counter[(role, str(predicted_span.get("tokenType")))] += 1
        else:
            counter[(role, "<missing>")] += 1


@torch.inference_mode()
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    args = parser.parse_args()

    root = dataset_root()
    marker_path = root / "sealed" / "opened-v1.json"
    if not marker_path.is_file():
        raise SystemExit("sealed-v1 is still sealed; run the official one-time acceptance before diagnostics")
    marker = load_json(marker_path)
    checkpoint_path = args.checkpoint.expanduser().resolve()
    checkpoint_hash = sha256_file(checkpoint_path)
    if checkpoint_hash != marker.get("checkpointHash"):
        raise SystemExit(
            "diagnostic checkpoint differs from the checkpoint that opened sealed-v1; "
            "use the original acceptance checkpoint"
        )

    checkpoint = load_checkpoint(checkpoint_path)
    file_schema = Schema.load(SCHEMA_PATH)
    schema = checkpoint["schema"]
    natural, focus, seal_identity = load_sealed_data(root, file_schema)
    if seal_identity.get("sealHash") != marker.get("sealHash"):
        raise SystemExit("sealed-v1 artifacts changed after opening; refusing diagnostic")

    device = select_device(args.device)
    if device.type == "cpu":
        torch.set_num_threads(min(8, torch.get_num_threads()))
    model = model_from_checkpoint(checkpoint, device)
    threshold = float(checkpoint["trainingConfig"]["modifier_threshold"])

    natural_string = {
        "support": 0,
        "exact": 0,
        "bySource": defaultdict(lambda: Counter()),
        "byKind": defaultdict(lambda: Counter()),
        "byLength": defaultdict(lambda: Counter()),
        "failureExamples": [],
    }
    focus_family_metrics: dict[str, SpanMetrics] = {}
    focus_confusions: dict[str, Counter] = defaultdict(Counter)
    focus_target_failures: list[dict] = []

    documents = [("natural", r) for r in natural] + [("focus", r) for r in focus]
    for index, (stream, record) in enumerate(documents, 1):
        output = document_logits(model, record["source"], device, adaptive=True)
        predicted = decode(record["source"], output, schema, threshold=threshold)

        if stream == "natural":
            for gold in record["result"]["spans"]:
                if gold.get("tokenType") != "string":
                    continue
                text = utf16_slice(record["source"], int(gold["start"]), int(gold["end"]))
                outcome = classify_gold_span(gold, predicted["spans"], record["source"])
                status = outcome["status"]
                source_id = str(record.get("_sealedSource", "unknown"))
                kind = string_kind(text)
                bucket = length_bucket(text)
                natural_string["support"] += 1
                natural_string["bySource"][source_id][status] += 1
                natural_string["byKind"][kind][status] += 1
                natural_string["byLength"][bucket][status] += 1
                if status == "exact":
                    natural_string["exact"] += 1
                elif len(natural_string["failureExamples"]) < 80:
                    natural_string["failureExamples"].append({
                        "source": source_id,
                        "package": record.get("package"),
                        "path": record.get("path"),
                        "kind": kind,
                        "length": len(text.encode("utf-8")),
                        "text": short(text),
                        **outcome,
                    })
        else:
            feature = (record.get("features") or [None])[0]
            if feature not in {"function-range", "struct-tags"}:
                continue
            family = family_of(record)
            focus_family_metrics.setdefault(family, SpanMetrics(schema)).add(record["result"], predicted)
            role = TARGETED_ROLES[feature]
            add_target_confusions(focus_confusions[family], record, predicted, role)
            for gold in record["result"]["spans"]:
                if gold.get("tokenType") != role:
                    continue
                outcome = classify_gold_span(gold, predicted["spans"], record["source"])
                if outcome["status"] != "exact" and len(focus_target_failures) < 120:
                    text = utf16_slice(record["source"], int(gold["start"]), int(gold["end"]))
                    focus_target_failures.append({
                        "feature": feature,
                        "family": family,
                        "path": record.get("path"),
                        "role": role,
                        "text": short(text),
                        **outcome,
                    })

        if index == 1 or index % 50 == 0 or index == len(documents):
            print(f"diagnostic {index}/{len(documents)} documents", flush=True)

    def serialize_counter_map(mapping: dict[str, Counter]) -> dict[str, dict[str, int]]:
        return {key: dict(sorted(counter.items())) for key, counter in sorted(mapping.items())}

    families = {}
    for family, metrics in sorted(focus_family_metrics.items()):
        feature = family.split("/", 1)[0]
        role = TARGETED_ROLES[feature]
        report = metrics.report()
        families[family] = {
            "feature": feature,
            "targetRole": role,
            "target": report["byTokenType"][role],
            "exactSpan": report["exactSpan"],
            "confusions": [
                {"gold": gold, "predicted": pred, "count": count}
                for (gold, pred), count in sorted(focus_confusions[family].items())
            ],
        }

    result = {
        "format": "nsh-go-sealed-v1-diagnostic-v1",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sealHash": marker.get("sealHash"),
        "checkpointHash": checkpoint_hash,
        "naturalString": {
            "support": natural_string["support"],
            "exact": natural_string["exact"],
            "exactRate": natural_string["exact"] / natural_string["support"] if natural_string["support"] else 0.0,
            "bySource": serialize_counter_map(natural_string["bySource"]),
            "byKind": serialize_counter_map(natural_string["byKind"]),
            "byLength": serialize_counter_map(natural_string["byLength"]),
            "failureExamples": natural_string["failureExamples"],
        },
        "focusFamilies": families,
        "focusTargetFailures": focus_target_failures,
    }

    lines = [
        "# Go sealed-v1 failure diagnostic",
        "",
        f"Seal: `{str(marker.get('sealHash', ''))[:20]}`",
        f"Checkpoint: `{checkpoint_path}`",
        "",
        "## Natural string exact-span breakdown",
        "",
        f"Gold string spans: {natural_string['support']}; exact: {natural_string['exact']} "
        f"({result['naturalString']['exactRate']:.4f})",
        "",
        "### By source",
        "",
    ]
    for source_id, counts in result["naturalString"]["bySource"].items():
        total = sum(counts.values())
        exact = counts.get("exact", 0)
        failures = ", ".join(f"{key}={value}" for key, value in counts.items() if key != "exact") or "none"
        lines.append(f"- `{source_id}`: exact {exact}/{total}; failures: {failures}")
    lines += ["", "### By literal kind", ""]
    for kind, counts in result["naturalString"]["byKind"].items():
        total = sum(counts.values())
        exact = counts.get("exact", 0)
        failures = ", ".join(f"{key}={value}" for key, value in counts.items() if key != "exact") or "none"
        lines.append(f"- `{kind}`: exact {exact}/{total}; failures: {failures}")
    lines += ["", "### By UTF-8 length", ""]
    for bucket, counts in result["naturalString"]["byLength"].items():
        total = sum(counts.values())
        exact = counts.get("exact", 0)
        failures = ", ".join(f"{key}={value}" for key, value in counts.items() if key != "exact") or "none"
        lines.append(f"- `{bucket}`: exact {exact}/{total}; failures: {failures}")

    lines += ["", "## Focused failed-feature families", ""]
    for family, family_report in families.items():
        target = family_report["target"]
        lines.append(
            f"- `{family}` — {family_report['targetRole']} F1={target['f1']:.4f} "
            f"precision={target['precision']:.4f} recall={target['recall']:.4f} support={target['support']}"
        )
        for row in family_report["confusions"]:
            if row["gold"] != row["predicted"]:
                lines.append(f"  - {row['gold']} -> {row['predicted']}: {row['count']}")

    lines += ["", "## Representative target failures", ""]
    for row in focus_target_failures[:40]:
        detail = row.get("predictedTypes") or row.get("parts") or row.get("part") or ""
        lines.append(
            f"- `{row['family']}` `{row['path']}` `{row['text']}`: {row['status']} {detail}"
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    folder = downloads / f"nsh-go-sealed-v1-diagnostic-{stamp}"
    folder.mkdir(parents=True, exist_ok=False)
    atomic_json(folder / "diagnostic.json", result)
    (folder / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    zip_path = downloads / f"{folder.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(folder / "diagnostic.json", "diagnostic.json")
        archive.write(folder / "REPORT.md", "REPORT.md")
    shutil.rmtree(folder)

    print("\n" + "\n".join(lines[: min(len(lines), 80)]))
    print(f"\nSend this ZIP: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
