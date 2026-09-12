"""Diagnose held-out Go function-range method errors without training or opening the test split."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

import torch

from checkpoints import atomic_json, load_checkpoint, model_from_checkpoint, select_device
from inference import decode, document_logits
from model import ModelOutput
from trainer_data import Snapshot, WindowSplit, sha256_file

FEATURE = "function-range"
ROLE = "method"


def utf16_slice(source: str, start: int, end: int) -> str:
    if start < 0 or end < start:
        raise ValueError("Invalid UTF-16 range")
    units = 0
    begin_index = end_index = None
    for index, char in enumerate(source):
        if units == start and begin_index is None:
            begin_index = index
        if units == end:
            end_index = index
            break
        units += 2 if ord(char) > 0xFFFF else 1
    if units == start and begin_index is None:
        begin_index = len(source)
    if units == end and end_index is None:
        end_index = len(source)
    if begin_index is None or end_index is None:
        raise ValueError("Range is not aligned to UTF-16 character boundaries")
    return source[begin_index:end_index]


def overlaps(left: dict, right: dict) -> bool:
    return max(left["start"], right["start"]) < min(left["end"], right["end"])


def span_view(source: str, span: dict) -> dict:
    return {
        "start": span["start"],
        "end": span["end"],
        "tokenType": span["tokenType"],
        "modifiers": span.get("modifiers", []),
        "text": utf16_slice(source, span["start"], span["end"]),
    }


def classify_gold_method(source: str, gold: dict, predicted: list[dict]) -> dict:
    same_range = [
        item
        for item in predicted
        if item["start"] == gold["start"] and item["end"] == gold["end"]
    ]
    exact = next((item for item in same_range if item["tokenType"] == ROLE), None)
    touching = [item for item in predicted if overlaps(gold, item)]
    same_role = [item for item in touching if item["tokenType"] == ROLE]

    if exact is not None:
        kind = "exact"
    elif same_range:
        kind = "wrong-role"
    elif not touching:
        kind = "missing"
    elif not same_role:
        kind = "role-mismatch"
    elif len(same_role) > 1:
        kind = "split"
    else:
        item = same_role[0]
        if item["start"] <= gold["start"] and item["end"] >= gold["end"]:
            kind = "overextended"
        elif item["start"] >= gold["start"] and item["end"] <= gold["end"]:
            kind = "truncated"
        else:
            kind = "shifted"

    return {
        "kind": kind,
        "gold": span_view(source, gold),
        "sameRangePredictions": [span_view(source, item) for item in same_range],
        "overlappingPredictions": [span_view(source, item) for item in touching],
    }


def analyze_document(doc: dict, predicted: dict) -> dict:
    source = doc["source"]
    gold_methods = [span for span in doc["result"]["spans"] if span["tokenType"] == ROLE]
    predicted_spans = predicted["spans"]
    cases = [classify_gold_method(source, span, predicted_spans) for span in gold_methods]
    gold_ranges = {(span["start"], span["end"]) for span in gold_methods}
    extras = [
        span_view(source, span)
        for span in predicted_spans
        if span["tokenType"] == ROLE and (span["start"], span["end"]) not in gold_ranges
    ]
    return {
        "id": doc["id"],
        "family": doc.get("family"),
        "features": doc.get("features", []),
        "variant": doc.get("variant"),
        "source": source,
        "goldMethodCount": len(gold_methods),
        "exactMethodCount": sum(case["kind"] == "exact" for case in cases),
        "cases": cases,
        "extraPredictedMethods": extras,
    }


@torch.inference_mode()
def fixed_prediction(model, split: WindowSplit, document_id: str, device: torch.device, threshold: float) -> dict:
    pieces: list[ModelOutput] = []
    raw = bytearray()
    for start in range(0, len(split.document_indices[document_id]), 32):
        chosen = split.document_indices[document_id][start : start + 32]
        batch = split.batch(chosen, device)
        gpu = model(batch["input_ids"], batch["attention_mask"])
        output = ModelOutput(gpu.boundary.cpu(), gpu.token_type.cpu(), gpu.modifier.cpu())
        for row, index in enumerate(chosen):
            length = split.refs[index]["length"]
            pieces.append(
                ModelOutput(
                    output.boundary[row, :length].clone(),
                    output.token_type[row, :length].clone(),
                    output.modifier[row, :length].clone(),
                )
            )
            raw.extend(batch["input_ids"][row, :length].cpu().tolist())
    source = raw.decode("utf-8")
    logits = ModelOutput(
        torch.cat([piece.boundary for piece in pieces]),
        torch.cat([piece.token_type for piece in pieces]),
        torch.cat([piece.modifier for piece in pieces]),
    )
    return decode(source, logits, split.snapshot.schema, threshold=threshold)


def aggregate(documents: list[dict]) -> dict:
    kinds = Counter(case["kind"] for document in documents for case in document["cases"])
    wrong_roles = Counter()
    families: dict[str, Counter] = defaultdict(Counter)
    for document in documents:
        family = document.get("family") or "unknown"
        for case in document["cases"]:
            families[family][case["kind"]] += 1
            if case["kind"] == "wrong-role":
                for predicted in case["sameRangePredictions"]:
                    wrong_roles[predicted["tokenType"]] += 1
            elif case["kind"] == "role-mismatch":
                for predicted in case["overlappingPredictions"]:
                    wrong_roles[predicted["tokenType"]] += 1
    return {
        "goldMethods": sum(document["goldMethodCount"] for document in documents),
        "exactMethods": sum(document["exactMethodCount"] for document in documents),
        "errorKinds": dict(sorted(kinds.items())),
        "wrongRolePredictions": dict(sorted(wrong_roles.items())),
        "families": {name: dict(sorted(counts.items())) for name, counts in sorted(families.items())},
        "extraPredictedMethods": sum(len(document["extraPredictedMethods"]) for document in documents),
    }


def markdown(report: dict) -> str:
    lines = [
        "# Go Function-Range Method Diagnostic",
        "",
        f"- Checkpoint epoch: {report['checkpointEpoch']}",
        f"- Inference: {report['inference']}",
        f"- Documents: {report['summary']['documents']}",
        f"- Gold method spans: {report['summary']['goldMethods']}",
        f"- Exact method spans: {report['summary']['exactMethods']}",
        f"- Extra predicted method spans: {report['summary']['extraPredictedMethods']}",
        "",
        "## Error kinds",
        "",
    ]
    for name, count in report["summary"]["errorKinds"].items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Wrong-role predictions", ""])
    if report["summary"]["wrongRolePredictions"]:
        for name, count in report["summary"]["wrongRolePredictions"].items():
            lines.append(f"- `{name}`: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Families", ""])
    for family, counts in report["summary"]["families"].items():
        rendered = ", ".join(f"{name}={count}" for name, count in counts.items())
        lines.append(f"- `{family}`: {rendered}")
    lines.extend(["", "## Documents", ""])
    for document in report["documents"]:
        lines.extend(
            [
                f"### {document.get('family') or document['id']} / variant {document.get('variant')}",
                "",
                "```go",
                document["source"].rstrip(),
                "```",
                "",
            ]
        )
        for case in document["cases"]:
            gold = case["gold"]
            lines.append(f"- **{case['kind']}** Gold `{gold['text']}` [{gold['start']}, {gold['end']})")
            if case["sameRangePredictions"]:
                for predicted in case["sameRangePredictions"]:
                    lines.append(
                        f"  - same-range `{predicted['tokenType']}` `{predicted['text']}` "
                        f"[{predicted['start']}, {predicted['end']})"
                    )
            else:
                for predicted in case["overlappingPredictions"]:
                    lines.append(
                        f"  - overlapping `{predicted['tokenType']}` `{predicted['text']}` "
                        f"[{predicted['start']}, {predicted['end']})"
                    )
        if document["extraPredictedMethods"]:
            lines.append("- Extra predicted methods:")
            for predicted in document["extraPredictedMethods"]:
                lines.append(f"  - `{predicted['text']}` [{predicted['start']}, {predicted['end']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    parser.add_argument("--inference", choices=["fixed", "adaptive"], default="fixed")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    split = None
    try:
        checkpoint = load_checkpoint(args.checkpoint)
        snapshot = Snapshot.open(args.snapshot or Path(checkpoint["snapshotPath"]))
        if snapshot.identity() != checkpoint["dataset"] or snapshot.schema != checkpoint["schema"]:
            raise ValueError("Diagnostic snapshot or schema does not match checkpoint")
        device = select_device(args.device)
        if device.type == "cpu":
            torch.set_num_threads(min(8, torch.get_num_threads()))
        split = WindowSplit(snapshot, "validation")
        docs = split.documents()
        selected = [
            doc for doc in docs.values() if doc["stream"] == "focus" and FEATURE in doc.get("features", [])
        ]
        if not selected:
            raise ValueError("No held-out function-range validation documents were found")
        model = model_from_checkpoint(checkpoint, device)
        model.eval()
        threshold = checkpoint["trainingConfig"]["modifier_threshold"]
        analyzed = []
        for index, doc in enumerate(selected, 1):
            if args.inference == "adaptive":
                prediction = decode(
                    doc["source"],
                    document_logits(model, doc["source"], device),
                    snapshot.schema,
                    threshold=threshold,
                )
            else:
                prediction = fixed_prediction(model, split, doc["id"], device, threshold)
            analyzed.append(analyze_document(doc, prediction))
            print(f"function-range validation: {index}/{len(selected)} documents", flush=True)
        summary = aggregate(analyzed)
        summary["documents"] = len(analyzed)
        report = {
            "format": "nsh-go-function-range-diagnostic-v1",
            "split": "validation",
            "feature": FEATURE,
            "role": ROLE,
            "inference": args.inference,
            "summary": summary,
            "documents": analyzed,
            "dataset": snapshot.identity(),
            "checkpointHash": sha256_file(args.checkpoint),
            "checkpointEpoch": checkpoint["epoch"],
        }
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        output_dir = (args.output_dir or args.checkpoint.parent / f"function-range-diagnostic-{stamp}").resolve()
        output_dir.mkdir(parents=True, exist_ok=False)
        atomic_json(output_dir / "report.json", report)
        (output_dir / "REPORT.md").write_text(markdown(report), encoding="utf-8")
        print("\nGo Function-Range Method Diagnostic")
        print("-----------------------------------")
        print(f"Documents: {summary['documents']}")
        print(f"Gold methods: {summary['goldMethods']}")
        print(f"Exact methods: {summary['exactMethods']}")
        print(f"Extra predicted methods: {summary['extraPredictedMethods']}")
        print("Error kinds: " + ", ".join(f"{name}={count}" for name, count in summary["errorKinds"].items()))
        if summary["wrongRolePredictions"]:
            print(
                "Wrong roles: "
                + ", ".join(f"{name}={count}" for name, count in summary["wrongRolePredictions"].items())
            )
        archive_base = Path.home() / "Downloads" / f"nsh-go-function-range-diagnostic-{stamp}"
        archive = Path(shutil.make_archive(str(archive_base), "zip", root_dir=output_dir))
        print(f"Report directory: {output_dir}")
        print("No training was performed and the test split was not opened.")
        print(f"Send this ZIP: {archive}")
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        print(f"Go function-range diagnostic failed: {error}", file=sys.stderr)
        return 1
    finally:
        if split is not None:
            split.close()


if __name__ == "__main__":
    raise SystemExit(main())
