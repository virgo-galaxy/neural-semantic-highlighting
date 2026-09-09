from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from evaluate import predict_document_logits
from predict import decode_predictions, load_model, select_device
from regexp_challenge import ExpectedSpan, metric_block, parse_marked_source, safe_divide, span_key

DEFAULT_CHALLENGE_PATH = Path("packs/typescript/challenges/regexp-paired-context.json")
DEFAULT_OUTPUT_PATH = Path("artifacts/typescript/regexp-paired-context-challenge.json")
DEFAULT_CHECKPOINTS = (
    (
        "base",
        Path(
            "artifacts/typescript/"
            "v3-local-role-dual-view-hard-string-regexp/"
            "best-epoch19.pt"
        ),
    ),
    ("step300", Path("artifacts/typescript/v3-regexp-surgery-probe/step-0300.pt")),
    ("step400", Path("artifacts/typescript/v3-regexp-surgery-probe/step-0400.pt")),
)
REGEXP_PLACEHOLDER = "{REGEXP}"
OPEN_MARKER = "⟦"
CLOSE_MARKER = "⟧"


@dataclass(frozen=True)
class PairSide:
    source: str
    expected: ExpectedSpan


@dataclass(frozen=True)
class PairedCase:
    pair_id: str
    family: str
    document_kind: str
    regexp: str
    isolated: PairSide
    contextual: PairSide
    note: str | None


@dataclass(frozen=True)
class SideResult:
    exact: bool
    tp: int
    fp: int
    fn: int
    predicted_regexp: tuple[dict[str, Any], ...]


def render_side(template: str, regexp: str) -> PairSide:
    if template.count(REGEXP_PLACEHOLDER) != 1:
        raise ValueError(
            "Each paired RegExp source template must contain exactly one "
            f"{REGEXP_PLACEHOLDER} placeholder."
        )

    marked = template.replace(
        REGEXP_PLACEHOLDER,
        f"{OPEN_MARKER}{regexp}{CLOSE_MARKER}",
    )
    source, expected = parse_marked_source(marked)

    if len(expected) != 1:
        raise ValueError("Each paired RegExp side must contain exactly one expected span.")
    if expected[0].text != regexp:
        raise ValueError(
            "Rendered expected regexp does not match pair regexp: "
            f"{expected[0].text!r} != {regexp!r}"
        )

    return PairSide(source=source, expected=expected[0])


def load_pairs(path: Path) -> list[PairedCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != "nsh-typescript-regexp-paired-context-challenge-v1":
        raise ValueError(f"Unexpected paired challenge format in {path}.")

    pairs: list[PairedCase] = []
    seen_ids: set[str] = set()
    for raw in payload.get("pairs", []):
        pair_id = raw["id"]
        if pair_id in seen_ids:
            raise ValueError(f'Duplicate paired challenge id "{pair_id}".')
        seen_ids.add(pair_id)

        regexp = raw["regexp"]
        if not regexp.startswith("/"):
            raise ValueError(f'Pair "{pair_id}" regexp must start with "/".')

        isolated = render_side(raw["isolated"], regexp)
        contextual = render_side(raw["contextual"], regexp)
        isolated_bytes = len(isolated.source.encode("utf-8"))
        contextual_bytes = len(contextual.source.encode("utf-8"))

        if isolated_bytes >= contextual_bytes:
            raise ValueError(
                f'Pair "{pair_id}" must have a longer contextual source '
                f"({isolated_bytes}B vs {contextual_bytes}B)."
            )
        if isolated_bytes > 96:
            raise ValueError(
                f'Pair "{pair_id}" isolated source is not tiny enough: {isolated_bytes}B.'
            )
        if not 160 <= contextual_bytes <= 480:
            raise ValueError(
                f'Pair "{pair_id}" contextual source must be 160..480B, '
                f"got {contextual_bytes}B."
            )

        pairs.append(
            PairedCase(
                pair_id=pair_id,
                family=raw["family"],
                document_kind=raw.get("documentKind", "typescript"),
                regexp=regexp,
                isolated=isolated,
                contextual=contextual,
                note=raw.get("note"),
            )
        )

    if not pairs:
        raise ValueError("Paired RegExp challenge has no pairs.")
    return pairs


def parse_checkpoint(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            "Checkpoint must use NAME=PATH, for example base=artifacts/.../best.pt"
        )
    name, path = value.split("=", 1)
    name = name.strip()
    path = path.strip()
    if not name or not path:
        raise argparse.ArgumentTypeError("Checkpoint NAME and PATH must be non-empty.")
    return name, Path(path)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--challenge", type=Path, default=DEFAULT_CHALLENGE_PATH)
    parser.add_argument("--checkpoint", action="append", type=parse_checkpoint)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--stride", type=int, default=256)
    parser.add_argument("--fusion", choices=("uniform", "center"), default="uniform")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def print_inventory(pairs: list[PairedCase]) -> None:
    family_counts = Counter(pair.family for pair in pairs)
    isolated_lengths = [len(pair.isolated.source.encode("utf-8")) for pair in pairs]
    contextual_lengths = [len(pair.contextual.source.encode("utf-8")) for pair in pairs]

    print("Paired RegExp challenge inventory")
    print("---------------------------------")
    print(f"Pairs:              {len(pairs)}")
    print(f"Evaluated sources:  {len(pairs) * 2}")
    print(
        "Isolated bytes:     "
        f"avg={mean(isolated_lengths):.1f} "
        f"min={min(isolated_lengths)} max={max(isolated_lengths)}"
    )
    print(
        "Contextual bytes:   "
        f"avg={mean(contextual_lengths):.1f} "
        f"min={min(contextual_lengths)} max={max(contextual_lengths)}"
    )
    print("")
    print("Families:")
    for family, count in sorted(family_counts.items()):
        print(f"  {family:<22} {count:>3}")


def evaluate_side(*, model, side: PairSide, config, device, stride, fusion, token_types, modifiers) -> SideResult:
    boundary_logits, type_logits, modifier_logits = predict_document_logits(
        model,
        side.source,
        max_length=config["max_length"],
        device=device,
        stride=stride,
        fusion=fusion,
    )
    predictions = decode_predictions(
        side.source,
        boundary_logits,
        type_logits,
        modifier_logits,
        token_types=token_types,
        modifiers=modifiers,
        modifier_threshold=0.60,
    )
    regexp_predictions = [
        prediction for prediction in predictions if prediction.token_type == "regexp"
    ]

    gold = {span_key(side.expected.start, side.expected.end)}
    predicted = {span_key(item.start, item.end) for item in regexp_predictions}
    tp = len(gold & predicted)
    fp = len(predicted - gold)
    fn = len(gold - predicted)

    return SideResult(
        exact=(gold == predicted),
        tp=tp,
        fp=fp,
        fn=fn,
        predicted_regexp=tuple(
            {"start": item.start, "end": item.end, "text": item.text}
            for item in regexp_predictions
        ),
    )


def summarize_side(results: list[SideResult]) -> dict[str, Any]:
    tp = sum(result.tp for result in results)
    fp = sum(result.fp for result in results)
    fn = sum(result.fn for result in results)
    exact = sum(result.exact for result in results)
    return {
        **metric_block(tp, fp, fn),
        "exact_cases": exact,
        "exact_rate": safe_divide(exact, len(results)),
        "cases": len(results),
    }


def evaluate_checkpoint(*, name: str, checkpoint_path: Path, pairs: list[PairedCase], stride: int, fusion: str) -> dict[str, Any]:
    device = select_device()
    model, checkpoint = load_model(checkpoint_path, device)
    config = checkpoint["config"]
    token_types = tuple(checkpoint["schema"]["token_types"])
    modifiers = tuple(checkpoint["schema"]["modifiers"])

    isolated_results: list[SideResult] = []
    contextual_results: list[SideResult] = []
    family: dict[str, dict[str, list[SideResult]]] = defaultdict(
        lambda: {"isolated": [], "contextual": []}
    )
    pair_records: list[dict[str, Any]] = []
    transitions = Counter()

    print("")
    print(f"Evaluating {name}: {checkpoint_path}")
    for index, pair in enumerate(pairs, start=1):
        isolated = evaluate_side(
            model=model,
            side=pair.isolated,
            config=config,
            device=device,
            stride=stride,
            fusion=fusion,
            token_types=token_types,
            modifiers=modifiers,
        )
        contextual = evaluate_side(
            model=model,
            side=pair.contextual,
            config=config,
            device=device,
            stride=stride,
            fusion=fusion,
            token_types=token_types,
            modifiers=modifiers,
        )
        isolated_results.append(isolated)
        contextual_results.append(contextual)
        family[pair.family]["isolated"].append(isolated)
        family[pair.family]["contextual"].append(contextual)

        if isolated.exact and contextual.exact:
            transition = "both_exact"
        elif isolated.exact:
            transition = "isolated_only"
        elif contextual.exact:
            transition = "contextual_only"
        else:
            transition = "neither_exact"
        transitions[transition] += 1

        pair_records.append(
            {
                "id": pair.pair_id,
                "family": pair.family,
                "regexp": pair.regexp,
                "note": pair.note,
                "isolated": {
                    "source_bytes": len(pair.isolated.source.encode("utf-8")),
                    "expected": asdict(pair.isolated.expected),
                    "result": asdict(isolated),
                },
                "contextual": {
                    "source_bytes": len(pair.contextual.source.encode("utf-8")),
                    "expected": asdict(pair.contextual.expected),
                    "result": asdict(contextual),
                },
                "transition": transition,
            }
        )
        if index % 10 == 0 or index == len(pairs):
            print(f"  evaluated {index}/{len(pairs)} pairs", flush=True)

    isolated_summary = summarize_side(isolated_results)
    contextual_summary = summarize_side(contextual_results)
    family_report = {
        family_name: {
            "isolated": summarize_side(side_results["isolated"]),
            "contextual": summarize_side(side_results["contextual"]),
        }
        for family_name, side_results in sorted(family.items())
    }

    report = {
        "checkpoint_name": name,
        "checkpoint": str(checkpoint_path),
        "inference": {
            "max_length": config["max_length"],
            "stride": stride,
            "fusion": fusion,
            "decoder": "greedy",
        },
        "isolated": isolated_summary,
        "contextual": contextual_summary,
        "context_exact_delta": contextual_summary["exact_rate"] - isolated_summary["exact_rate"],
        "transitions": dict(transitions),
        "families": family_report,
        "pairs": pair_records,
    }

    print("")
    print(f"{name} summary")
    print("-" * (len(name) + 8))
    print(
        "Isolated:   "
        f"F1={isolated_summary['f1']:.4f} "
        f"exact={isolated_summary['exact_cases']}/{isolated_summary['cases']} "
        f"({isolated_summary['exact_rate']:.2%})"
    )
    print(
        "Contextual: "
        f"F1={contextual_summary['f1']:.4f} "
        f"exact={contextual_summary['exact_cases']}/{contextual_summary['cases']} "
        f"({contextual_summary['exact_rate']:.2%})"
    )
    print(f"Context exact delta: {report['context_exact_delta']:+.2%}")
    print(
        "Transitions: "
        f"both={transitions['both_exact']} "
        f"context-rescued={transitions['contextual_only']} "
        f"context-hurt={transitions['isolated_only']} "
        f"neither={transitions['neither_exact']}"
    )
    return report


def main() -> None:
    args = parse_arguments()
    pairs = load_pairs(args.challenge)

    print("Neural Semantic Highlighting")
    print("TypeScript Paired Contextual RegExp Challenge")
    print("")
    print_inventory(pairs)

    if args.validate_only:
        print("")
        print("Paired challenge validation passed.")
        return

    checkpoints = args.checkpoint or list(DEFAULT_CHECKPOINTS)
    names = [name for name, _ in checkpoints]
    if len(set(names)) != len(names):
        raise ValueError("Checkpoint names must be unique.")

    reports = [
        evaluate_checkpoint(
            name=name,
            checkpoint_path=checkpoint_path,
            pairs=pairs,
            stride=args.stride,
            fusion=args.fusion,
        )
        for name, checkpoint_path in checkpoints
    ]

    output = {
        "format": "nsh-typescript-regexp-paired-context-challenge-result-v1",
        "challenge": str(args.challenge),
        "pair_count": len(pairs),
        "models": reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("")
    print("Comparison")
    print("----------")
    print(
        f"{'model':<12} {'isolated F1':>12} {'isol exact':>11} "
        f"{'context F1':>12} {'ctx exact':>10} {'ctx delta':>10}"
    )
    for report in reports:
        print(
            f"{report['checkpoint_name']:<12} "
            f"{report['isolated']['f1']:>12.4f} "
            f"{report['isolated']['exact_rate']:>10.2%} "
            f"{report['contextual']['f1']:>12.4f} "
            f"{report['contextual']['exact_rate']:>9.2%} "
            f"{report['context_exact_delta']:>+9.2%}"
        )

    print("")
    print(f"JSON: {args.output}")


if __name__ == "__main__":
    main()
