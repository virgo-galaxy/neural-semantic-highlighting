from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from config import DEFAULT_ARTIFACT_DIRECTORY, DEFAULT_BEST_CHECKPOINT_PATH
from inference import predict_document_logits
from predict import PredictedSpan, decode_predictions, load_model, select_device


DEFAULT_CHECKPOINT_PATH = DEFAULT_BEST_CHECKPOINT_PATH
DEFAULT_CHALLENGE_PATH = Path("packs/typescript/challenges/jsx-tsx.json")
DEFAULT_OUTPUT_PATH = DEFAULT_ARTIFACT_DIRECTORY / "jsx-tsx-challenge.json"
DEFAULT_FOCUS_TOKEN_TYPES = ("tag", "attribute")

OPEN_MARKER = "⟦"
CLOSE_MARKER = "⟧"
MARKER_SEPARATOR = "|"
OUTSIDE_TOKEN_TYPE = "outside"


@dataclass(frozen=True)
class ExpectedAssertion:
    start: int
    end: int
    text: str
    token_type: str


@dataclass(frozen=True)
class ChallengeCase:
    case_id: str
    category: str
    document_kind: str
    source: str
    expected: tuple[ExpectedAssertion, ...]
    note: str | None


@dataclass(frozen=True)
class ErrorRecord:
    case_id: str
    category: str
    document_kind: str
    kind: str
    source: str
    expected: dict[str, Any] | None
    predicted: dict[str, Any] | None
    note: str | None


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def parse_marked_source(
    marked_source: str,
) -> tuple[str, tuple[ExpectedAssertion, ...]]:
    output: list[str] = []
    expected: list[ExpectedAssertion] = []
    source_utf16_offset = 0
    index = 0

    while index < len(marked_source):
        if marked_source.startswith(OPEN_MARKER, index):
            close_index = marked_source.find(CLOSE_MARKER, index + len(OPEN_MARKER))
            if close_index < 0:
                raise ValueError("Unclosed JSX/TSX challenge marker.")

            payload = marked_source[index + len(OPEN_MARKER) : close_index]
            if MARKER_SEPARATOR not in payload:
                raise ValueError(
                    "JSX/TSX challenge marker must use ⟦tokenType|text⟧ syntax."
                )

            token_type, text = payload.split(MARKER_SEPARATOR, 1)
            if not token_type or not text:
                raise ValueError("JSX/TSX challenge marker has an empty field.")
            if OPEN_MARKER in text or CLOSE_MARKER in text:
                raise ValueError("Nested JSX/TSX challenge markers are not allowed.")

            start = source_utf16_offset
            output.append(text)
            source_utf16_offset += utf16_length(text)
            expected.append(
                ExpectedAssertion(
                    start=start,
                    end=source_utf16_offset,
                    text=text,
                    token_type=token_type,
                )
            )
            index = close_index + len(CLOSE_MARKER)
            continue

        character = marked_source[index]
        output.append(character)
        source_utf16_offset += utf16_length(character)
        index += 1

    source = "".join(output)
    if OPEN_MARKER in source or CLOSE_MARKER in source:
        raise ValueError("Challenge markers leaked into model input.")

    return source, tuple(expected)


def load_cases(path: Path) -> tuple[list[ChallengeCase], tuple[str, ...]]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if payload.get("format") != "nsh-typescript-jsx-tsx-challenge":
        raise ValueError(f'Unsupported challenge format in "{path}".')

    focus_token_types = tuple(payload.get("focusTokenTypes", DEFAULT_FOCUS_TOKEN_TYPES))
    if not focus_token_types:
        raise ValueError("JSX/TSX challenge must define at least one focus token type.")

    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("JSX/TSX challenge must contain a non-empty cases array.")

    seen_ids: set[str] = set()
    cases: list[ChallengeCase] = []

    for raw in raw_cases:
        case_id = raw["id"]
        category = raw["category"]
        document_kind = raw["documentKind"]
        marked_source = raw["source"]
        note = raw.get("note")

        if case_id in seen_ids:
            raise ValueError(f'Duplicate JSX/TSX challenge id "{case_id}".')
        if document_kind not in {"jsx", "tsx"}:
            raise ValueError(
                f'JSX/TSX challenge case "{case_id}" uses unsupported '
                f'document kind "{document_kind}".'
            )

        seen_ids.add(case_id)
        source, expected = parse_marked_source(marked_source)

        if not expected:
            raise ValueError(f'JSX/TSX challenge case "{case_id}" has no assertions.')

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

    return cases, focus_token_types


def span_key(start: int, end: int, token_type: str) -> tuple[int, int, str]:
    return start, end, token_type


def overlap_size(
    left_start: int,
    left_end: int,
    right_start: int,
    right_end: int,
) -> int:
    return max(0, min(left_end, right_end) - max(left_start, right_start))


def best_overlapping_prediction(
    expected: ExpectedAssertion,
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


def prediction_dict(prediction: PredictedSpan) -> dict[str, Any]:
    return {
        "start": prediction.start,
        "end": prediction.end,
        "text": prediction.text,
        "token_type": prediction.token_type,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT_PATH)
    parser.add_argument("--challenge", type=Path, default=DEFAULT_CHALLENGE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--max-errors", type=int, default=50)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def print_inventory(
    cases: list[ChallengeCase],
    focus_token_types: tuple[str, ...],
) -> None:
    categories = Counter(case.category for case in cases)
    document_kinds = Counter(case.document_kind for case in cases)
    assertions = Counter(
        assertion.token_type
        for case in cases
        for assertion in case.expected
    )

    print("JSX/TSX challenge inventory")
    print("---------------------------")
    print(f"Cases:       {len(cases)}")
    print(f"Assertions:  {sum(assertions.values())}")
    print(f"Focus types: {', '.join(focus_token_types)}")
    print("")
    print("Document kinds:")
    for document_kind, count in sorted(document_kinds.items()):
        print(f"  {document_kind:<10} {count:>4}")
    print("")
    print("Categories:")
    for category, count in sorted(categories.items()):
        print(f"  {category:<28} {count:>4}")
    print("")
    print("Assertions by expected type:")
    for token_type, count in sorted(assertions.items()):
        print(f"  {token_type:<20} {count:>4}")


def main() -> None:
    args = parse_arguments()
    cases, focus_token_types = load_cases(args.challenge)

    print("Neural Semantic Highlighting")
    print("TypeScript JSX/TSX Challenge")
    print("")
    print_inventory(cases, focus_token_types)

    if args.validate_only:
        print("")
        print("Challenge validation passed.")
        return

    device = select_device()
    model, checkpoint = load_model(args.checkpoint, device)
    config = checkpoint["config"]
    token_types = tuple(checkpoint["schema"]["token_types"])
    modifiers = tuple(checkpoint["schema"]["modifiers"])

    unknown_expected_types = sorted(
        {
            assertion.token_type
            for case in cases
            for assertion in case.expected
            if assertion.token_type not in token_types
            and assertion.token_type != OUTSIDE_TOKEN_TYPE
        }
    )
    if unknown_expected_types:
        raise ValueError(
            "Challenge uses token types missing from the checkpoint schema: "
            + ", ".join(unknown_expected_types)
        )

    total_assertions = 0
    exact_assertions = 0
    semantic_assertions = 0
    semantic_exact = 0
    outside_assertions = 0
    outside_clean = 0

    exact_cases = 0
    category_counts: dict[str, Counter[str]] = defaultdict(Counter)
    kind_counts: dict[str, Counter[str]] = defaultdict(Counter)
    type_counts: dict[str, Counter[str]] = defaultdict(Counter)
    error_kinds = Counter()
    errors: list[ErrorRecord] = []

    focus_tp = 0
    focus_fp = 0
    focus_fn = 0
    focus_type_counts: dict[str, Counter[str]] = defaultdict(Counter)

    print("")
    print(f"Device:     {device}")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Window:     {config['max_length']} bytes")
    print("Windowing:  adaptive cursor")
    print("")

    for index, case in enumerate(cases, start=1):
        boundary_logits, type_logits, modifier_logits = predict_document_logits(
            model,
            case.source,
            max_length=config["max_length"],
            device=device,
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

        case_exact = True

        expected_focus_keys = {
            span_key(assertion.start, assertion.end, assertion.token_type)
            for assertion in case.expected
            if assertion.token_type in focus_token_types
        }
        predicted_focus_keys = {
            span_key(prediction.start, prediction.end, prediction.token_type)
            for prediction in predictions
            if prediction.token_type in focus_token_types
        }

        focus_tp_keys = expected_focus_keys & predicted_focus_keys
        focus_fp_keys = predicted_focus_keys - expected_focus_keys
        focus_fn_keys = expected_focus_keys - predicted_focus_keys

        focus_tp += len(focus_tp_keys)
        focus_fp += len(focus_fp_keys)
        focus_fn += len(focus_fn_keys)

        predicted_focus_by_key = {
            span_key(prediction.start, prediction.end, prediction.token_type): prediction
            for prediction in predictions
            if prediction.token_type in focus_token_types
        }

        for key in sorted(focus_fp_keys):
            prediction = predicted_focus_by_key[key]
            error_kinds["focus-false-positive"] += 1
            errors.append(
                ErrorRecord(
                    case_id=case.case_id,
                    category=case.category,
                    document_kind=case.document_kind,
                    kind="focus-false-positive",
                    source=case.source,
                    expected=None,
                    predicted=prediction_dict(prediction),
                    note=case.note,
                )
            )

        for token_type in focus_token_types:
            expected_for_type = {
                key for key in expected_focus_keys if key[2] == token_type
            }
            predicted_for_type = {
                key for key in predicted_focus_keys if key[2] == token_type
            }
            counts = focus_type_counts[token_type]
            counts["tp"] += len(expected_for_type & predicted_for_type)
            counts["fp"] += len(predicted_for_type - expected_for_type)
            counts["fn"] += len(expected_for_type - predicted_for_type)

        for assertion in case.expected:
            total_assertions += 1
            category = category_counts[case.category]
            kind = kind_counts[case.document_kind]
            expected_type = type_counts[assertion.token_type]

            category["assertions"] += 1
            kind["assertions"] += 1
            expected_type["assertions"] += 1

            overlapping = best_overlapping_prediction(assertion, predictions)

            if assertion.token_type == OUTSIDE_TOKEN_TYPE:
                outside_assertions += 1
                clean = overlapping is None
                if clean:
                    outside_clean += 1
                    exact_assertions += 1
                    category["exact"] += 1
                    kind["exact"] += 1
                    expected_type["exact"] += 1
                else:
                    case_exact = False
                    error_kinds["outside-contamination"] += 1
                    errors.append(
                        ErrorRecord(
                            case_id=case.case_id,
                            category=case.category,
                            document_kind=case.document_kind,
                            kind="outside-contamination",
                            source=case.source,
                            expected=asdict(assertion),
                            predicted=prediction_dict(overlapping),
                            note=case.note,
                        )
                    )
                continue

            semantic_assertions += 1
            exact_prediction = next(
                (
                    prediction
                    for prediction in predictions
                    if prediction.start == assertion.start
                    and prediction.end == assertion.end
                ),
                None,
            )

            is_exact = (
                exact_prediction is not None
                and exact_prediction.token_type == assertion.token_type
            )

            if is_exact:
                exact_assertions += 1
                semantic_exact += 1
                category["exact"] += 1
                kind["exact"] += 1
                expected_type["exact"] += 1
                continue

            case_exact = False

            if exact_prediction is not None:
                error_kind = "wrong-type"
                error_prediction = exact_prediction
            elif overlapping is not None and overlapping.token_type == assertion.token_type:
                error_kind = "boundary-error"
                error_prediction = overlapping
            elif overlapping is not None:
                error_kind = "wrong-overlap-type"
                error_prediction = overlapping
            else:
                error_kind = "missing"
                error_prediction = None

            error_kinds[error_kind] += 1
            errors.append(
                ErrorRecord(
                    case_id=case.case_id,
                    category=case.category,
                    document_kind=case.document_kind,
                    kind=error_kind,
                    source=case.source,
                    expected=asdict(assertion),
                    predicted=(
                        prediction_dict(error_prediction)
                        if error_prediction is not None
                        else None
                    ),
                    note=case.note,
                )
            )

        if case_exact:
            exact_cases += 1
            category_counts[case.category]["exact_cases"] += 1
            kind_counts[case.document_kind]["exact_cases"] += 1

        category_counts[case.category]["cases"] += 1
        kind_counts[case.document_kind]["cases"] += 1

        if index % 10 == 0 or index == len(cases):
            print(f"  evaluated {index}/{len(cases)} cases", flush=True)

    focus_metrics = metric_block(focus_tp, focus_fp, focus_fn)

    def report_counts(counts: Counter[str]) -> dict[str, Any]:
        return {
            "cases": counts["cases"],
            "assertions": counts["assertions"],
            "exact_assertions": counts["exact"],
            "exact_assertion_rate": safe_divide(counts["exact"], counts["assertions"]),
            "exact_cases": counts["exact_cases"],
            "exact_case_rate": safe_divide(counts["exact_cases"], counts["cases"]),
        }

    category_report = {
        name: report_counts(counts)
        for name, counts in sorted(category_counts.items())
    }
    document_kind_report = {
        name: report_counts(counts)
        for name, counts in sorted(kind_counts.items())
    }
    expected_type_report = {
        name: {
            "assertions": counts["assertions"],
            "exact": counts["exact"],
            "exact_rate": safe_divide(counts["exact"], counts["assertions"]),
        }
        for name, counts in sorted(type_counts.items())
    }
    focus_type_report = {
        token_type: metric_block(counts["tp"], counts["fp"], counts["fn"])
        for token_type, counts in sorted(focus_type_counts.items())
    }

    report = {
        "format": "nsh-typescript-jsx-tsx-challenge-result",
        "checkpoint": str(args.checkpoint),
        "challenge": str(args.challenge),
        "inference": {
            "max_length": config["max_length"],
            "windowing": "adaptive-cursor",
            "decoder": "greedy",
        },
        "summary": {
            "cases": len(cases),
            "assertions": total_assertions,
            "exact_assertions": exact_assertions,
            "exact_assertion_rate": safe_divide(exact_assertions, total_assertions),
            "semantic_assertions": semantic_assertions,
            "semantic_exact": semantic_exact,
            "semantic_exact_rate": safe_divide(semantic_exact, semantic_assertions),
            "outside_assertions": outside_assertions,
            "outside_clean": outside_clean,
            "outside_clean_rate": safe_divide(outside_clean, outside_assertions),
            "exact_cases": exact_cases,
            "exact_case_rate": safe_divide(exact_cases, len(cases)),
            "focus_span_metrics": focus_metrics,
        },
        "focus_token_types": list(focus_token_types),
        "focus_by_token_type": focus_type_report,
        "document_kinds": document_kind_report,
        "categories": category_report,
        "expected_types": expected_type_report,
        "error_kinds": dict(error_kinds.most_common()),
        "errors": [asdict(error) for error in errors],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("")
    print("Assertion accuracy")
    print("------------------")
    print(
        f"Exact assertions: {exact_assertions}/{total_assertions} "
        f"({safe_divide(exact_assertions, total_assertions):.2%})"
    )
    print(
        f"Semantic exact:   {semantic_exact}/{semantic_assertions} "
        f"({safe_divide(semantic_exact, semantic_assertions):.2%})"
    )
    print(
        f"JSX text clean:   {outside_clean}/{outside_assertions} "
        f"({safe_divide(outside_clean, outside_assertions):.2%})"
    )
    print(
        f"Exact cases:      {exact_cases}/{len(cases)} "
        f"({safe_divide(exact_cases, len(cases)):.2%})"
    )

    print("")
    print("Tag / attribute exact spans")
    print("---------------------------")
    print(f"Precision: {focus_metrics['precision']:.4f}")
    print(f"Recall:    {focus_metrics['recall']:.4f}")
    print(f"F1:        {focus_metrics['f1']:.4f}")
    print(f"TP / FP / FN: {focus_tp} / {focus_fp} / {focus_fn}")

    print("")
    print("Per focus token type")
    print("--------------------")
    for token_type, block in focus_type_report.items():
        print(
            f"{token_type:<12} F1={block['f1']:.4f} "
            f"TP/FP/FN={block['true_positive']}/"
            f"{block['false_positive']}/{block['false_negative']}"
        )

    print("")
    print("Per document kind")
    print("-----------------")
    for document_kind, block in document_kind_report.items():
        print(
            f"{document_kind:<8} "
            f"assertions={block['exact_assertions']}/{block['assertions']} "
            f"({block['exact_assertion_rate']:.2%}) "
            f"cases={block['exact_cases']}/{block['cases']}"
        )

    print("")
    print("Per category")
    print("------------")
    for category, block in category_report.items():
        print(
            f"{category:<28} "
            f"assertions={block['exact_assertions']}/{block['assertions']} "
            f"({block['exact_assertion_rate']:.2%})"
        )

    if error_kinds:
        print("")
        print("Error kinds")
        print("-----------")
        for error_kind, count in error_kinds.most_common():
            print(f"  {error_kind:<24} {count}")

    if errors and args.max_errors > 0:
        print("")
        print("Representative errors")
        print("---------------------")
        for error in errors[: args.max_errors]:
            print(f"[{error.kind}] {error.case_id} ({error.category})")
            if error.expected is not None:
                print(f"  expected: {error.expected}")
            if error.predicted is not None:
                print(f"  predicted: {error.predicted}")
            print(f"  source: {error.source}")

    print("")
    print(f"JSON: {args.output}")


if __name__ == "__main__":
    main()
