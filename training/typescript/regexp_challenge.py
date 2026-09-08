from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evaluate import predict_document_logits
from predict import (
    PredictedSpan,
    decode_predictions,
    load_model,
    select_device,
)


DEFAULT_CHECKPOINT_PATH = Path(
    "artifacts/typescript/"
    "v2-multitask-train-dual-view50/"
    "best-epoch20.pt"
)
DEFAULT_CHALLENGE_PATH = Path(
    "packs/typescript/challenges/regexp.json"
)
DEFAULT_OUTPUT_PATH = Path(
    "artifacts/typescript/regexp-challenge-v2-epoch20.json"
)

OPEN_MARKER = "⟦"
CLOSE_MARKER = "⟧"


@dataclass(frozen=True)
class ExpectedSpan:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class ChallengeCase:
    case_id: str
    category: str
    document_kind: str
    source: str
    expected: tuple[ExpectedSpan, ...]
    note: str | None


@dataclass(frozen=True)
class ErrorRecord:
    case_id: str
    category: str
    kind: str
    source: str
    expected: dict[str, Any] | None
    predicted: dict[str, Any] | None
    overlapping_predicted_type: str | None
    note: str | None


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def parse_marked_source(marked_source: str) -> tuple[str, tuple[ExpectedSpan, ...]]:
    output: list[str] = []
    expected: list[ExpectedSpan] = []

    source_utf16_offset = 0
    span_start: int | None = None
    span_text: list[str] = []

    for character in marked_source:
        if character == OPEN_MARKER:
            if span_start is not None:
                raise ValueError("Nested regexp challenge markers are not allowed.")
            span_start = source_utf16_offset
            span_text = []
            continue

        if character == CLOSE_MARKER:
            if span_start is None:
                raise ValueError("Found a closing regexp marker without an opener.")

            text = "".join(span_text)
            expected.append(
                ExpectedSpan(
                    start=span_start,
                    end=source_utf16_offset,
                    text=text,
                )
            )
            span_start = None
            span_text = []
            continue

        output.append(character)
        source_utf16_offset += utf16_length(character)

        if span_start is not None:
            span_text.append(character)

    if span_start is not None:
        raise ValueError("Unclosed regexp challenge marker.")

    source = "".join(output)

    if OPEN_MARKER in source or CLOSE_MARKER in source:
        raise ValueError("Challenge markers leaked into model input.")

    return source, tuple(expected)


def load_cases(path: Path) -> list[ChallengeCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if payload.get("format") != "nsh-typescript-regexp-challenge-v1":
        raise ValueError(f'Unsupported challenge format in "{path}".')

    raw_cases = payload.get("cases")

    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Regexp challenge must contain a non-empty cases array.")

    seen_ids: set[str] = set()
    cases: list[ChallengeCase] = []

    for raw in raw_cases:
        case_id = raw["id"]
        category = raw["category"]
        document_kind = raw.get("documentKind", "typescript")
        marked_source = raw["source"]
        note = raw.get("note")

        if case_id in seen_ids:
            raise ValueError(f'Duplicate regexp challenge id "{case_id}".')

        seen_ids.add(case_id)
        source, expected = parse_marked_source(marked_source)

        if category.startswith("positive/") and not expected:
            raise ValueError(f'Positive case "{case_id}" has no expected regexp span.')

        if category.startswith("negative/") and expected:
            raise ValueError(f'Negative case "{case_id}" unexpectedly contains regexp markers.')

        cases.append(
            ChallengeCase(
                case_id=case_id,
                category=category,
                document_kind=document_kind,
                source=source,
                expected=expected,
                note=note,
            )
        )

    return cases


def span_key(start: int, end: int) -> tuple[int, int]:
    return start, end


def overlap_size(
    left_start: int,
    left_end: int,
    right_start: int,
    right_end: int,
) -> int:
    return max(0, min(left_end, right_end) - max(left_start, right_start))


def best_overlapping_prediction(
    expected: ExpectedSpan,
    predictions: list[PredictedSpan],
) -> PredictedSpan | None:
    overlapping = [
        prediction
        for prediction in predictions
        if overlap_size(
            expected.start,
            expected.end,
            prediction.start,
            prediction.end,
        )
        > 0
    ]

    if not overlapping:
        return None

    return max(
        overlapping,
        key=lambda prediction: overlap_size(
            expected.start,
            expected.end,
            prediction.start,
            prediction.end,
        ),
    )


def source_slice_utf16(source: str, start: int, end: int) -> str:
    offset = 0
    characters: list[str] = []

    for character in source:
        next_offset = offset + utf16_length(character)

        if next_offset <= start:
            offset = next_offset
            continue

        if offset >= end:
            break

        characters.append(character)
        offset = next_offset

    return "".join(characters)


def safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def metric_block(tp: int, fp: int, fn: int) -> dict[str, Any]:
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)

    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1_score(precision, recall),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT_PATH,
    )
    parser.add_argument(
        "--challenge",
        type=Path,
        default=DEFAULT_CHALLENGE_PATH,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=256,
    )
    parser.add_argument(
        "--fusion",
        choices=("uniform", "center"),
        default="uniform",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=40,
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
    )

    return parser.parse_args()


def print_inventory(cases: list[ChallengeCase]) -> None:
    categories = Counter(case.category for case in cases)
    positive_cases = sum(1 for case in cases if case.expected)
    negative_cases = len(cases) - positive_cases
    expected_spans = sum(len(case.expected) for case in cases)

    print("Regexp challenge inventory")
    print("--------------------------")
    print(f"Cases:           {len(cases)}")
    print(f"Positive cases:  {positive_cases}")
    print(f"Negative cases:  {negative_cases}")
    print(f"Expected regexps: {expected_spans}")
    print("")
    print("Categories:")

    for category, count in sorted(categories.items()):
        print(f"  {category:<30} {count:>4}")


def main() -> None:
    args = parse_arguments()
    cases = load_cases(args.challenge)

    print("Neural Semantic Highlighting")
    print("TypeScript RegExp Challenge")
    print("")
    print_inventory(cases)

    if args.validate_only:
        print("")
        print("Challenge validation passed.")
        return

    device = select_device()
    model, checkpoint = load_model(args.checkpoint, device)
    config = checkpoint["config"]
    token_types = tuple(checkpoint["schema"]["token_types"])
    modifiers = tuple(checkpoint["schema"]["modifiers"])

    total_tp = 0
    total_fp = 0
    total_fn = 0
    exact_cases = 0
    positive_exact_cases = 0
    negative_clean_cases = 0
    positive_case_count = 0
    negative_case_count = 0

    category_counts: dict[str, Counter[str]] = defaultdict(Counter)
    missed_as = Counter()
    errors: list[ErrorRecord] = []

    print("")
    print(f"Device:     {device}")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Window:     {config['max_length']} bytes")
    print(f"Stride:     {args.stride} bytes")
    print(f"Fusion:     {args.fusion}")
    print("")

    for index, case in enumerate(cases, start=1):
        boundary_logits, type_logits, modifier_logits = predict_document_logits(
            model,
            case.source,
            max_length=config["max_length"],
            device=device,
            stride=args.stride,
            fusion=args.fusion,
        )

        predictions = decode_predictions(
            case.source,
            boundary_logits,
            type_logits,
            modifier_logits,
            token_types=token_types,
            modifiers=modifiers,
            modifier_threshold=0.60,
        )

        predicted_regexp = [
            prediction
            for prediction in predictions
            if prediction.token_type == "regexp"
        ]

        gold_keys = {
            span_key(span.start, span.end)
            for span in case.expected
        }
        predicted_keys = {
            span_key(span.start, span.end)
            for span in predicted_regexp
        }

        tp_keys = gold_keys & predicted_keys
        fp_keys = predicted_keys - gold_keys
        fn_keys = gold_keys - predicted_keys

        tp = len(tp_keys)
        fp = len(fp_keys)
        fn = len(fn_keys)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        category = category_counts[case.category]
        category["cases"] += 1
        category["tp"] += tp
        category["fp"] += fp
        category["fn"] += fn
        category["gold"] += len(gold_keys)
        category["predicted"] += len(predicted_keys)

        is_exact = gold_keys == predicted_keys

        if is_exact:
            exact_cases += 1
            category["exact_cases"] += 1

        if gold_keys:
            positive_case_count += 1
            category["positive_cases"] += 1
            if is_exact:
                positive_exact_cases += 1
        else:
            negative_case_count += 1
            category["negative_cases"] += 1
            if not predicted_keys:
                negative_clean_cases += 1
                category["negative_clean_cases"] += 1

        expected_by_key = {
            span_key(span.start, span.end): span
            for span in case.expected
        }
        predicted_by_key = {
            span_key(span.start, span.end): span
            for span in predicted_regexp
        }

        for key in sorted(fn_keys):
            expected = expected_by_key[key]
            overlapping = best_overlapping_prediction(expected, predictions)
            overlapping_type = (
                overlapping.token_type
                if overlapping is not None
                else None
            )
            missed_as[overlapping_type or "<none>"] += 1

            errors.append(
                ErrorRecord(
                    case_id=case.case_id,
                    category=case.category,
                    kind="false-negative",
                    source=case.source,
                    expected=asdict(expected),
                    predicted=(
                        {
                            "start": overlapping.start,
                            "end": overlapping.end,
                            "text": overlapping.text,
                            "token_type": overlapping.token_type,
                        }
                        if overlapping is not None
                        else None
                    ),
                    overlapping_predicted_type=overlapping_type,
                    note=case.note,
                )
            )

        for key in sorted(fp_keys):
            predicted = predicted_by_key[key]
            errors.append(
                ErrorRecord(
                    case_id=case.case_id,
                    category=case.category,
                    kind="false-positive",
                    source=case.source,
                    expected=None,
                    predicted={
                        "start": predicted.start,
                        "end": predicted.end,
                        "text": source_slice_utf16(
                            case.source,
                            predicted.start,
                            predicted.end,
                        ),
                        "token_type": predicted.token_type,
                    },
                    overlapping_predicted_type=None,
                    note=case.note,
                )
            )

        if index % 20 == 0 or index == len(cases):
            print(f"  evaluated {index}/{len(cases)} cases", flush=True)

    metrics = metric_block(total_tp, total_fp, total_fn)

    category_report: dict[str, Any] = {}

    for category_name, counts in sorted(category_counts.items()):
        block = metric_block(counts["tp"], counts["fp"], counts["fn"])
        block.update(
            {
                "cases": counts["cases"],
                "gold": counts["gold"],
                "predicted": counts["predicted"],
                "exact_cases": counts["exact_cases"],
                "exact_case_rate": safe_divide(
                    counts["exact_cases"],
                    counts["cases"],
                ),
                "negative_clean_cases": counts["negative_clean_cases"],
                "negative_clean_rate": (
                    safe_divide(
                        counts["negative_clean_cases"],
                        counts["negative_cases"],
                    )
                    if counts["negative_cases"]
                    else None
                ),
            }
        )
        category_report[category_name] = block

    report = {
        "format": "nsh-typescript-regexp-challenge-result-v1",
        "checkpoint": str(args.checkpoint),
        "challenge": str(args.challenge),
        "inference": {
            "max_length": config["max_length"],
            "stride": args.stride,
            "fusion": args.fusion,
            "decoder": "greedy",
        },
        "summary": {
            **metrics,
            "cases": len(cases),
            "positive_cases": positive_case_count,
            "negative_cases": negative_case_count,
            "exact_cases": exact_cases,
            "exact_case_rate": safe_divide(exact_cases, len(cases)),
            "positive_exact_cases": positive_exact_cases,
            "positive_exact_rate": safe_divide(
                positive_exact_cases,
                positive_case_count,
            ),
            "negative_clean_cases": negative_clean_cases,
            "negative_clean_rate": safe_divide(
                negative_clean_cases,
                negative_case_count,
            ),
        },
        "categories": category_report,
        "missed_regexp_overlapping_type": dict(missed_as.most_common()),
        "errors": [asdict(error) for error in errors],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("")
    print("Exact RegExp spans")
    print("------------------")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1:        {metrics['f1']:.4f}")
    print(f"TP / FP / FN: {total_tp} / {total_fp} / {total_fn}")
    print("")
    print("Case-level")
    print("----------")
    print(
        "Exact cases:          "
        f"{exact_cases}/{len(cases)} "
        f"({safe_divide(exact_cases, len(cases)):.2%})"
    )
    print(
        "Positive exact cases: "
        f"{positive_exact_cases}/{positive_case_count} "
        f"({safe_divide(positive_exact_cases, positive_case_count):.2%})"
    )
    print(
        "Negative clean cases: "
        f"{negative_clean_cases}/{negative_case_count} "
        f"({safe_divide(negative_clean_cases, negative_case_count):.2%})"
    )

    print("")
    print("Per category")
    print("------------")

    for category_name, block in category_report.items():
        if block["gold"]:
            metric_text = f"F1={block['f1']:.4f}"
        else:
            metric_text = (
                "clean="
                f"{block['negative_clean_cases']}/{block['cases']}"
            )

        print(
            f"{category_name:<30} "
            f"{metric_text:<16} "
            f"TP/FP/FN={block['true_positive']}/"
            f"{block['false_positive']}/"
            f"{block['false_negative']}"
        )

    if missed_as:
        print("")
        print("Missed regexp overlapped as")
        print("---------------------------")
        for token_type, count in missed_as.most_common():
            print(f"  {token_type:<20} {count}")

    if errors and args.max_errors > 0:
        print("")
        print("Representative errors")
        print("---------------------")
        for error in errors[: args.max_errors]:
            print(
                f"[{error.kind}] {error.case_id} "
                f"({error.category})"
            )
            if error.expected is not None:
                print(f"  expected: {error.expected}")
            if error.predicted is not None:
                print(f"  predicted: {error.predicted}")
            print(f"  source: {error.source}")

    print("")
    print(f"JSON: {args.output}")


if __name__ == "__main__":
    main()
