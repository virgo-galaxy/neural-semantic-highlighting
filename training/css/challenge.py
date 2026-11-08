"""Inspect neural predictions against independent Golden cases, including the product example.

These small, visible development probes are not an independent corpus test score.
No parser or Gold boundaries participate in inference.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from packs.css.runtime.local import CssLocalPack
from training.css.checkpoints import atomic_json
from training.css.metrics import SpanMetrics
from training.css.prepare import REPOSITORY, file_hash

CASES = REPOSITORY / "packs/css/fixtures/golden.json"


def unmark(marked: str) -> dict:
    source, spans, cursor, units = "", [], 0, 0
    for match in re.finditer(r"⟦([^|]+)\|([\s\S]*?)⟧", marked):
        gap = marked[cursor:match.start()]
        if gap.strip():
            raise ValueError("Golden source has an unmarked source gap")
        source += gap
        units += len(gap.encode("utf-16-le")) // 2
        role, *modifiers = match[1].split("+")
        start = units
        source += match[2]
        units += len(match[2].encode("utf-16-le")) // 2
        span = {"start": start, "end": units, "tokenType": role}
        if modifiers:
            span["modifiers"] = modifiers
        spans.append(span)
        cursor = match.end()
    if marked[cursor:].strip():
        raise ValueError("Golden source has an unmarked source tail")
    return {"source": source + marked[cursor:], "spans": spans}


def inspect(pack: CssLocalPack) -> dict:
    metrics = {kind: SpanMetrics(pack.checkpoint["schema"]) for kind in ("css", "scss", "less")}
    results = []
    for case in json.loads(CASES.read_text()):
        gold = unmark(case["markedSource"])
        result = pack.highlight(source=gold["source"], document_kind=case["documentKind"])
        metrics[case["documentKind"]].add(gold, result)
        def key(span):
            return span["start"], span["end"], span["tokenType"], tuple(span.get("modifiers", []))
        expected = {key(span) for span in gold["spans"]}
        actual = {key(span) for span in result["spans"]}
        raw = gold["source"].encode("utf-16-le")
        def describe(values):
            return [{"start": a, "end": b, "text": raw[a*2:b*2].decode("utf-16-le"),
                     "tokenType": role, "modifiers": list(modifiers)} for a, b, role, modifiers in sorted(values)]
        results.append({"id": case["id"], "documentKind": case["documentKind"], "source": gold["source"],
                        "exactIncludingModifiers": expected == actual,
                        "missing": describe(expected - actual), "unexpected": describe(actual - expected)})
    return {"inference": "predicted-adaptive-cursor", "purpose": "visible development probes, not held-out corpus test",
            "fixtureHash": file_hash(CASES), "cases": results,
            "documentKinds": {kind: metric.report() for kind, metric in metrics.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "mps", "cuda"], default="auto")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checkpoint_hash = file_hash(args.checkpoint)
    pack = CssLocalPack(checkpoint_path=args.checkpoint, device_name=args.device)
    if file_hash(args.checkpoint) != checkpoint_hash:
        raise ValueError("Checkpoint changed while loading; inspect a frozen checkpoint")
    report = inspect(pack)
    report.update(checkpointHash=checkpoint_hash, checkpointEpoch=pack.checkpoint["epoch"], device=pack.device.type)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    output = args.output or args.checkpoint.parent / ("golden-" + stamp + ".json")
    atomic_json(output, report)
    for case in report["cases"]:
        print(case["id"], "exact" if case["exactIncludingModifiers"] else
              f"missing={len(case['missing'])} unexpected={len(case['unexpected'])}")
    print("Report:", output)


if __name__ == "__main__":
    main()
