from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import torch

from dataset import (
    GoldSpan,
    TypeScriptSemanticDataset,
    build_source_boundaries,
)
from config import DEFAULT_ARTIFACT_DIRECTORY, DEFAULT_BEST_CHECKPOINT_PATH
from inference import predict_document_logits
from evaluate import (
    PredictedSpan,
    decode_predicted_spans,
    load_model,
    select_device,
)


DEFAULT_CHECKPOINT_PATH = DEFAULT_BEST_CHECKPOINT_PATH
DEFAULT_OUTPUT_PATH = DEFAULT_ARTIFACT_DIRECTORY / "error-analysis.json"
DEFAULT_TEXT_OUTPUT_PATH = DEFAULT_ARTIFACT_DIRECTORY / "error-analysis.txt"


@dataclass(frozen=True)
class SpanKey:
    start: int
    end: int
    token_type: str


@dataclass(frozen=True)
class ErrorExample:
    kind: str
    repository: str
    path: str
    start: int
    end: int
    text: str
    expected_type: str | None
    predicted_type: str | None
    context: str


@dataclass(frozen=True)
class BoundarySpan:
    start: int
    end: int
    token_type: str
    text: str


@dataclass(frozen=True)
class BoundaryMismatch:
    direction: str
    repository: str
    path: str
    relation: str
    structure: str
    overlap_size: int
    gold_spans_overlapped_by_prediction: int
    predicted_spans_overlapping_gold: int
    expected: BoundarySpan
    predicted: BoundarySpan
    context: str


@dataclass(frozen=True)
class TypeMetrics:
    precision: float
    recall: float
    f1: float
    support: int
    true_positive: int
    false_positive: int
    false_negative: int


def spans_overlap(
    left_start: int,
    left_end: int,
    right_start: int,
    right_end: int,
) -> bool:
    return max(left_start, right_start) < min(
        left_end,
        right_end,
    )


def span_overlap_size(
    left_start: int,
    left_end: int,
    right_start: int,
    right_end: int,
) -> int:
    return max(
        0,
        min(left_end, right_end)
        - max(left_start, right_start),
    )


def best_overlapping_span[
    SpanT: GoldSpan | PredictedSpan
](
    start: int,
    end: int,
    candidates: Iterable[SpanT],
) -> SpanT | None:
    overlapping = [
        candidate
        for candidate in candidates
        if spans_overlap(
            start,
            end,
            candidate.start,
            candidate.end,
        )
    ]

    if not overlapping:
        return None

    return max(
        overlapping,
        key=lambda candidate: span_overlap_size(
            start,
            end,
            candidate.start,
            candidate.end,
        ),
    )


def extract_span_text(
    source: str,
    start: int,
    end: int,
) -> str:
    (
        _,
        utf16_to_character_index,
        _,
    ) = build_source_boundaries(source)

    start_index = utf16_to_character_index.get(
        start
    )
    end_index = utf16_to_character_index.get(end)

    if start_index is None or end_index is None:
        return ""

    return source[start_index:end_index]


def extract_context(
    source: str,
    start: int,
    end: int,
    *,
    maximum_characters: int = 220,
) -> str:
    (
        _,
        utf16_to_character_index,
        _,
    ) = build_source_boundaries(source)

    start_index = utf16_to_character_index.get(
        start,
        0,
    )
    end_index = utf16_to_character_index.get(
        end,
        start_index,
    )

    line_start = source.rfind(
        "\n",
        0,
        start_index,
    )

    if line_start < 0:
        line_start = 0
    else:
        line_start += 1

    line_end = source.find(
        "\n",
        end_index,
    )

    if line_end < 0:
        line_end = len(source)

    line = source[
        line_start:line_end
    ]

    if len(line) <= maximum_characters:
        return line.strip()

    relative_start = max(
        0,
        start_index - line_start,
    )

    half = maximum_characters // 2
    context_start = max(
        0,
        relative_start - half,
    )
    context_end = min(
        len(line),
        context_start + maximum_characters,
    )

    context_start = max(
        0,
        context_end - maximum_characters,
    )

    cropped = line[
        context_start:context_end
    ].strip()

    if context_start > 0:
        cropped = "…" + cropped

    if context_end < len(line):
        cropped += "…"

    return cropped


def to_span_key(
    span: GoldSpan | PredictedSpan,
) -> SpanKey:
    return SpanKey(
        start=span.start,
        end=span.end,
        token_type=span.token_type,
    )


def calculate_type_metrics(
    token_types: tuple[str, ...],
    predicted_by_type: dict[str, set[tuple]],
    gold_by_type: dict[str, set[tuple]],
) -> tuple[
    dict[str, TypeMetrics],
    float,
]:
    metrics: dict[
        str,
        TypeMetrics,
    ] = {}

    macro_values: list[float] = []

    for token_type in token_types:
        predicted = predicted_by_type[
            token_type
        ]
        gold = gold_by_type[token_type]

        true_positive = len(
            predicted & gold
        )
        false_positive = len(
            predicted - gold
        )
        false_negative = len(
            gold - predicted
        )

        precision = (
            true_positive
            / max(
                1,
                true_positive
                + false_positive,
            )
        )

        recall = (
            true_positive
            / max(
                1,
                true_positive
                + false_negative,
            )
        )

        f1 = (
            2.0
            * precision
            * recall
            / max(
                1e-12,
                precision + recall,
            )
        )

        support = len(gold)

        metrics[token_type] = TypeMetrics(
            precision=precision,
            recall=recall,
            f1=f1,
            support=support,
            true_positive=true_positive,
            false_positive=false_positive,
            false_negative=false_negative,
        )

        if support > 0:
            macro_values.append(f1)

    macro_f1 = (
        sum(macro_values)
        / len(macro_values)
        if macro_values
        else 0.0
    )

    return metrics, macro_f1


def build_error_example(
    *,
    kind: str,
    repository: str,
    path: str,
    source: str,
    start: int,
    end: int,
    expected_type: str | None,
    predicted_type: str | None,
) -> ErrorExample:
    return ErrorExample(
        kind=kind,
        repository=repository,
        path=path,
        start=start,
        end=end,
        text=extract_span_text(
            source,
            start,
            end,
        ),
        expected_type=expected_type,
        predicted_type=predicted_type,
        context=extract_context(
            source,
            start,
            end,
        ),
    )


def build_boundary_span(
    source: str,
    span: GoldSpan | PredictedSpan,
) -> BoundarySpan:
    return BoundarySpan(
        start=span.start,
        end=span.end,
        token_type=span.token_type,
        text=extract_span_text(
            source,
            span.start,
            span.end,
        ),
    )


def classify_boundary_relation(
    expected: GoldSpan,
    predicted: PredictedSpan,
) -> str:
    if (
        expected.start == predicted.start
        and expected.end != predicted.end
    ):
        return "right-boundary-differs"

    if (
        expected.end == predicted.end
        and expected.start != predicted.start
    ):
        return "left-boundary-differs"

    if (
        expected.start < predicted.start
        and predicted.end < expected.end
    ):
        return "predicted-inside-gold"

    if (
        predicted.start < expected.start
        and expected.end < predicted.end
    ):
        return "gold-inside-predicted"

    if (
        predicted.start < expected.start
        < predicted.end
        < expected.end
    ):
        return "predicted-overlaps-left"

    if (
        expected.start < predicted.start
        < expected.end
        < predicted.end
    ):
        return "predicted-overlaps-right"

    return "other-overlap"


def classify_boundary_structure(
    *,
    gold_spans_overlapped_by_prediction: int,
    predicted_spans_overlapping_gold: int,
) -> str:
    if (
        gold_spans_overlapped_by_prediction > 1
        and predicted_spans_overlapping_gold > 1
    ):
        return "many-to-many"

    if gold_spans_overlapped_by_prediction > 1:
        return "merge-candidate"

    if predicted_spans_overlapping_gold > 1:
        return "split-candidate"

    return "one-to-one"


def build_boundary_mismatch(
    *,
    direction: str,
    repository: str,
    path: str,
    source: str,
    expected: GoldSpan,
    predicted: PredictedSpan,
    gold_spans: list[GoldSpan],
    predicted_spans: list[PredictedSpan],
) -> BoundaryMismatch:
    gold_spans_overlapped_by_prediction = sum(
        1
        for gold in gold_spans
        if spans_overlap(
            predicted.start,
            predicted.end,
            gold.start,
            gold.end,
        )
    )

    predicted_spans_overlapping_gold = sum(
        1
        for candidate in predicted_spans
        if spans_overlap(
            expected.start,
            expected.end,
            candidate.start,
            candidate.end,
        )
    )

    context_start = min(
        expected.start,
        predicted.start,
    )
    context_end = max(
        expected.end,
        predicted.end,
    )

    return BoundaryMismatch(
        direction=direction,
        repository=repository,
        path=path,
        relation=classify_boundary_relation(
            expected,
            predicted,
        ),
        structure=classify_boundary_structure(
            gold_spans_overlapped_by_prediction=(
                gold_spans_overlapped_by_prediction
            ),
            predicted_spans_overlapping_gold=(
                predicted_spans_overlapping_gold
            ),
        ),
        overlap_size=span_overlap_size(
            expected.start,
            expected.end,
            predicted.start,
            predicted.end,
        ),
        gold_spans_overlapped_by_prediction=(
            gold_spans_overlapped_by_prediction
        ),
        predicted_spans_overlapping_gold=(
            predicted_spans_overlapping_gold
        ),
        expected=build_boundary_span(
            source,
            expected,
        ),
        predicted=build_boundary_span(
            source,
            predicted,
        ),
        context=extract_context(
            source,
            context_start,
            context_end,
        ),
    )


def counter_items(
    counter: Counter,
    *,
    limit: int | None = None,
) -> list[dict]:
    items = counter.most_common(limit)

    return [
        {
            "key": key,
            "count": count,
        }
        for key, count in items
    ]


def type_pair_items(
    counter: Counter[tuple[str, str]],
    *,
    limit: int | None = None,
) -> list[dict]:
    return [
        {
            "expected": expected,
            "predicted": predicted,
            "count": count,
        }
        for (
            expected,
            predicted,
        ), count in counter.most_common(limit)
    ]


def write_text_report(
    output_path: Path,
    report: dict,
) -> None:
    lines: list[str] = []

    summary = report["summary"]

    lines.extend(
        [
            "Neural Semantic Highlighting",
            "TypeScript Error Analysis",
            "",
            f"Split: {report['split']}",
            f"Checkpoint: {report['checkpoint']}",
            f"Documents: {report['documents']}",
            (
                "Windowing: adaptive cursor "
                f"({report['inference']['max_length']} bytes max context)"
            ),
            "",
            "Exact semantic spans",
            "--------------------",
            f"Precision: {summary['precision']:.4f}",
            f"Recall:    {summary['recall']:.4f}",
            f"F1:        {summary['f1']:.4f}",
            f"Macro F1:  {summary['macro_f1']:.4f}",
            f"Predicted: {summary['predicted']}",
            f"Gold:      {summary['gold']}",
            "",
            "Error breakdown",
            "---------------",
            (
                "False positives: "
                f"{summary['false_positive']}"
            ),
            (
                "  wrong type:      "
                f"{summary['false_positive_wrong_type']}"
            ),
            (
                "  boundary:        "
                f"{summary['false_positive_boundary']}"
            ),
            (
                "  spurious:        "
                f"{summary['false_positive_spurious']}"
            ),
            (
                "False negatives: "
                f"{summary['false_negative']}"
            ),
            (
                "  wrong type:      "
                f"{summary['false_negative_wrong_type']}"
            ),
            (
                "  boundary:        "
                f"{summary['false_negative_boundary']}"
            ),
            (
                "  missed:          "
                f"{summary['false_negative_missed']}"
            ),
            "",
            "Weakest token types",
            "-------------------",
            (
                "token type          precision     recall"
                "         f1     support       fp       fn"
            ),
        ]
    )

    for item in report["weakest_token_types"]:
        lines.append(
            f"{item['token_type']:<20}"
            f"{item['precision']:>10.4f}"
            f"{item['recall']:>11.4f}"
            f"{item['f1']:>11.4f}"
            f"{item['support']:>12}"
            f"{item['false_positive']:>9}"
            f"{item['false_negative']:>9}"
        )

    lines.extend(
        [
            "",
            "Top same-boundary type confusions",
            "---------------------------------",
        ]
    )

    if report["type_confusions"]:
        for item in report[
            "type_confusions"
        ]:
            lines.append(
                f"{item['expected']} -> "
                f"{item['predicted']}: "
                f"{item['count']}"
            )
    else:
        lines.append("none")

    boundary = report["boundary_analysis"]

    lines.extend(
        [
            "",
            "Boundary mismatch analysis",
            "--------------------------",
            (
                "Predicted-side boundary mismatches: "
                f"{boundary['predicted_side_count']}"
            ),
            (
                "Gold-side boundary mismatches:      "
                f"{boundary['gold_side_count']}"
            ),
            "",
            "Predicted-side type pairs",
            "-------------------------",
        ]
    )

    if boundary["predicted_side_type_pairs"]:
        for item in boundary[
            "predicted_side_type_pairs"
        ]:
            lines.append(
                f"{item['expected']} -> "
                f"{item['predicted']}: "
                f"{item['count']}"
            )
    else:
        lines.append("none")

    lines.extend(
        [
            "",
            "Predicted-side relations",
            "------------------------",
        ]
    )

    if boundary["predicted_side_relations"]:
        for item in boundary[
            "predicted_side_relations"
        ]:
            lines.append(
                f"{item['key']}: {item['count']}"
            )
    else:
        lines.append("none")

    lines.extend(
        [
            "",
            "Predicted-side structures",
            "-------------------------",
        ]
    )

    if boundary["predicted_side_structures"]:
        for item in boundary[
            "predicted_side_structures"
        ]:
            lines.append(
                f"{item['key']}: {item['count']}"
            )
    else:
        lines.append("none")

    lines.extend(
        [
            "",
            "Top boundary-mismatch files",
            "---------------------------",
        ]
    )

    if boundary["predicted_side_files"]:
        for item in boundary[
            "predicted_side_files"
        ]:
            lines.append(
                f"{item['key']}: {item['count']}"
            )
    else:
        lines.append("none")

    lines.extend(
        [
            "",
            (
                "Full boundary records: JSON "
                "boundary_analysis.predicted_side / "
                "boundary_analysis.gold_side"
            ),
            "",
            "Representative errors",
            "---------------------",
        ]
    )

    for index, example in enumerate(
        report["examples"],
        start=1,
    ):
        lines.extend(
            [
                (
                    f"[{index}] "
                    f"{example['kind']}"
                ),
                (
                    "  file: "
                    f"{example['repository']}/"
                    f"{example['path']}"
                ),
                (
                    "  span: "
                    f"{example['start']}:"
                    f"{example['end']}"
                ),
                (
                    "  text: "
                    f"{json.dumps(example['text'], ensure_ascii=False)}"
                ),
                (
                    "  expected: "
                    f"{example['expected_type']}"
                ),
                (
                    "  predicted: "
                    f"{example['predicted_type']}"
                ),
                (
                    "  context: "
                    f"{example['context']}"
                ),
                "",
            ]
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT_PATH,
    )

    parser.add_argument(
        "--split",
        choices=(
            "train",
            "validation",
            "test",
        ),
        default="validation",
        help=(
            "Dataset split to inspect. Validation is the "
            "default so test remains a final held-out exam."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--text-output",
        type=Path,
        default=DEFAULT_TEXT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--max-examples",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--max-confusions",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--max-boundary-summary",
        type=int,
        default=20,
        help=(
            "Maximum rows shown for each boundary summary "
            "table. Full boundary records are always written "
            "to JSON."
        ),
    )


    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    device = select_device()

    checkpoint = torch.load(
        args.checkpoint,
        map_location="cpu",
    )

    max_length = checkpoint[
        "config"
    ]["max_length"]

    predicted_boundary_files: Counter[str] = Counter()
    gold_boundary_files: Counter[str] = Counter()

    print("Neural Semantic Highlighting")
    print("TypeScript Error Analysis")
    print("")
    print(f"Device: {device}")
    print(f"Checkpoint: {args.checkpoint}")
    print(f"Split: {args.split}")
    print(
        f"Documents: {len(dataset.documents)}"
    )
    print(
        f"Window: {max_length} bytes"
    )
    print("Windowing: adaptive cursor")
    print("")

    for document_index, document in enumerate(
        dataset.documents,
        start=1,
    ):
        (
            boundary_logits,
            token_type_logits,
            modifier_logits,
        ) = predict_document_logits(
            model,
            document.source,
            max_length=max_length,
            device=device,
        )

        predicted_spans = decode_predicted_spans(
            document,
            boundary_logits,
            token_type_logits,
            modifier_logits,
            dataset,
        )

        document_key = (
            f"{document.repository}:"
            f"{document.path}"
        )

        gold_spans = list(document.gold_spans)

        gold_by_boundary: dict[
            tuple[int, int],
            list[GoldSpan],
        ] = defaultdict(list)

        predicted_by_boundary: dict[
            tuple[int, int],
            list[PredictedSpan],
        ] = defaultdict(list)

        for span in gold_spans:
            gold_by_boundary[
                (span.start, span.end)
            ].append(span)

            item = (
                document_key,
                span.start,
                span.end,
                span.token_type,
            )

            gold_set.add(item)
            gold_by_type[
                span.token_type
            ].add(item)

        for span in predicted_spans:
            predicted_by_boundary[
                (span.start, span.end)
            ].append(span)

            item = (
                document_key,
                span.start,
                span.end,
                span.token_type,
            )

            predicted_set.add(item)
            predicted_by_type[
                span.token_type
            ].add(item)

        for predicted in predicted_spans:
            predicted_key = (
                document_key,
                predicted.start,
                predicted.end,
                predicted.token_type,
            )

            if predicted_key in gold_set:
                continue

            same_boundary_gold = gold_by_boundary.get(
                (predicted.start, predicted.end),
                [],
            )

            if same_boundary_gold:
                expected = same_boundary_gold[0]
                kind = "wrong-type"
                false_positive_kind[kind] += 1

                type_confusions[
                    (
                        expected.token_type,
                        predicted.token_type,
                    )
                ] += 1

                examples_by_kind[kind].append(
                    build_error_example(
                        kind=kind,
                        repository=document.repository,
                        path=document.path,
                        source=document.source,
                        start=predicted.start,
                        end=predicted.end,
                        expected_type=(
                            expected.token_type
                        ),
                        predicted_type=(
                            predicted.token_type
                        ),
                    )
                )

                continue

            overlapping_gold = best_overlapping_span(
                predicted.start,
                predicted.end,
                gold_spans,
            )

            if overlapping_gold is not None:
                kind = "boundary-mismatch"
                false_positive_kind[kind] += 1

                boundary_mismatch = build_boundary_mismatch(
                    direction="predicted-side",
                    repository=document.repository,
                    path=document.path,
                    source=document.source,
                    expected=overlapping_gold,
                    predicted=predicted,
                    gold_spans=gold_spans,
                    predicted_spans=predicted_spans,
                )

                predicted_boundary_mismatches.append(
                    boundary_mismatch
                )
                predicted_boundary_type_pairs[
                    (
                        overlapping_gold.token_type,
                        predicted.token_type,
                    )
                ] += 1
                predicted_boundary_relations[
                    boundary_mismatch.relation
                ] += 1
                predicted_boundary_structures[
                    boundary_mismatch.structure
                ] += 1
                predicted_boundary_files[
                    document_key
                ] += 1

                examples_by_kind[kind].append(
                    build_error_example(
                        kind=kind,
                        repository=document.repository,
                        path=document.path,
                        source=document.source,
                        start=predicted.start,
                        end=predicted.end,
                        expected_type=(
                            overlapping_gold.token_type
                        ),
                        predicted_type=(
                            predicted.token_type
                        ),
                    )
                )

                continue

            kind = "spurious"
            false_positive_kind[kind] += 1

            examples_by_kind[kind].append(
                build_error_example(
                    kind=kind,
                    repository=document.repository,
                    path=document.path,
                    source=document.source,
                    start=predicted.start,
                    end=predicted.end,
                    expected_type=None,
                    predicted_type=(
                        predicted.token_type
                    ),
                )
            )

        for gold in gold_spans:
            gold_key = (
                document_key,
                gold.start,
                gold.end,
                gold.token_type,
            )

            if gold_key in predicted_set:
                continue

            same_boundary_predicted = (
                predicted_by_boundary.get(
                    (gold.start, gold.end),
                    [],
                )
            )

            if same_boundary_predicted:
                kind = "wrong-type"
                false_negative_kind[kind] += 1
                continue

            overlapping_predicted = best_overlapping_span(
                gold.start,
                gold.end,
                predicted_spans,
            )

            if overlapping_predicted is not None:
                kind = "boundary-mismatch"
                false_negative_kind[kind] += 1

                boundary_mismatch = build_boundary_mismatch(
                    direction="gold-side",
                    repository=document.repository,
                    path=document.path,
                    source=document.source,
                    expected=gold,
                    predicted=overlapping_predicted,
                    gold_spans=gold_spans,
                    predicted_spans=predicted_spans,
                )

                gold_boundary_mismatches.append(
                    boundary_mismatch
                )
                gold_boundary_type_pairs[
                    (
                        gold.token_type,
                        overlapping_predicted.token_type,
                    )
                ] += 1
                gold_boundary_relations[
                    boundary_mismatch.relation
                ] += 1
                gold_boundary_structures[
                    boundary_mismatch.structure
                ] += 1
                gold_boundary_files[
                    document_key
                ] += 1

                continue

            kind = "missed"
            false_negative_kind[kind] += 1

            examples_by_kind[kind].append(
                build_error_example(
                    kind=kind,
                    repository=document.repository,
                    path=document.path,
                    source=document.source,
                    start=gold.start,
                    end=gold.end,
                    expected_type=gold.token_type,
                    predicted_type=None,
                )
            )

        if (
            document_index % 10 == 0
            or document_index
            == len(dataset.documents)
        ):
            print(
                f"  analyzed {document_index}/"
                f"{len(dataset.documents)} documents",
                flush=True,
            )

    true_positive = len(
        predicted_set & gold_set
    )
    false_positive = len(
        predicted_set - gold_set
    )
    false_negative = len(
        gold_set - predicted_set
    )

    precision = (
        true_positive
        / max(
            1,
            true_positive + false_positive,
        )
    )

    recall = (
        true_positive
        / max(
            1,
            true_positive + false_negative,
        )
    )

    f1 = (
        2.0
        * precision
        * recall
        / max(
            1e-12,
            precision + recall,
        )
    )

    type_metrics, macro_f1 = (
        calculate_type_metrics(
            dataset.schema.token_types,
            predicted_by_type,
            gold_by_type,
        )
    )

    weakest_token_types = [
        {
            "token_type": token_type,
            **asdict(metrics),
        }
        for token_type, metrics
        in sorted(
            type_metrics.items(),
            key=lambda item: (
                item[1].f1
                if item[1].support > 0
                else 2.0,
                -item[1].support,
                item[0],
            ),
        )
        if metrics.support > 0
    ]

    confusion_items = [
        {
            "expected": expected,
            "predicted": predicted,
            "count": count,
        }
        for (
            expected,
            predicted,
        ), count in type_confusions.most_common(
            args.max_confusions
        )
    ]

    boundary_summary_limit = (
        args.max_boundary_summary
        if args.max_boundary_summary > 0
        else None
    )

    boundary_analysis = {
        "predicted_side_count": len(
            predicted_boundary_mismatches
        ),
        "gold_side_count": len(
            gold_boundary_mismatches
        ),
        "predicted_side_type_pairs": type_pair_items(
            predicted_boundary_type_pairs,
            limit=boundary_summary_limit,
        ),
        "gold_side_type_pairs": type_pair_items(
            gold_boundary_type_pairs,
            limit=boundary_summary_limit,
        ),
        "predicted_side_relations": counter_items(
            predicted_boundary_relations,
            limit=boundary_summary_limit,
        ),
        "gold_side_relations": counter_items(
            gold_boundary_relations,
            limit=boundary_summary_limit,
        ),
        "predicted_side_structures": counter_items(
            predicted_boundary_structures,
            limit=boundary_summary_limit,
        ),
        "gold_side_structures": counter_items(
            gold_boundary_structures,
            limit=boundary_summary_limit,
        ),
        "predicted_side_files": counter_items(
            predicted_boundary_files,
            limit=boundary_summary_limit,
        ),
        "gold_side_files": counter_items(
            gold_boundary_files,
            limit=boundary_summary_limit,
        ),
        "predicted_side": [
            asdict(item)
            for item in predicted_boundary_mismatches
        ],
        "gold_side": [
            asdict(item)
            for item in gold_boundary_mismatches
        ],
    }

    example_order = (
        "wrong-type",
        "boundary-mismatch",
        "spurious",
        "missed",
    )

    selected_examples: list[
        ErrorExample
    ] = []

    if args.max_examples > 0:
        per_kind_limit = max(
            1,
            args.max_examples
            // len(example_order),
        )

        for kind in example_order:
            selected_examples.extend(
                examples_by_kind[kind][
                    :per_kind_limit
                ]
            )

        remaining = (
            args.max_examples
            - len(selected_examples)
        )

        if remaining > 0:
            leftovers: list[
                ErrorExample
            ] = []

            for kind in example_order:
                leftovers.extend(
                    examples_by_kind[kind][
                        per_kind_limit:
                    ]
                )

            selected_examples.extend(
                leftovers[:remaining]
            )

    report = {
        "format": (
            "nsh-typescript-error-analysis"
        ),
        "checkpoint": str(args.checkpoint),
        "split": args.split,
        "documents": len(dataset.documents),
        "inference": {
            "max_length": max_length,
            "windowing": "adaptive-cursor",
        },
        "summary": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "macro_f1": macro_f1,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "predicted": len(predicted_set),
            "gold": len(gold_set),
            "false_positive_wrong_type": (
                false_positive_kind[
                    "wrong-type"
                ]
            ),
            "false_positive_boundary": (
                false_positive_kind[
                    "boundary-mismatch"
                ]
            ),
            "false_positive_spurious": (
                false_positive_kind[
                    "spurious"
                ]
            ),
            "false_negative_wrong_type": (
                false_negative_kind[
                    "wrong-type"
                ]
            ),
            "false_negative_boundary": (
                false_negative_kind[
                    "boundary-mismatch"
                ]
            ),
            "false_negative_missed": (
                false_negative_kind[
                    "missed"
                ]
            ),
        },
        "token_types": {
            token_type: asdict(metrics)
            for token_type, metrics
            in type_metrics.items()
        },
        "weakest_token_types": (
            weakest_token_types
        ),
        "type_confusions": confusion_items,
        "boundary_analysis": boundary_analysis,
        "examples": [
            asdict(example)
            for example in selected_examples
        ],
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    write_text_report(
        args.text_output,
        report,
    )

    print("")
    print("Exact semantic spans")
    print("--------------------")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1:        {f1:.4f}")
    print(f"Macro F1:  {macro_f1:.4f}")
    print("")
    print("Weakest token types")
    print("-------------------")

    for item in weakest_token_types[:10]:
        print(
            f"{item['token_type']:<18} "
            f"F1={item['f1']:.4f} "
            f"P={item['precision']:.4f} "
            f"R={item['recall']:.4f} "
            f"support={item['support']}"
        )

    print("")
    print("Error breakdown")
    print("---------------")
    print(
        "FP wrong-type / boundary / spurious: "
        f"{false_positive_kind['wrong-type']} / "
        f"{false_positive_kind['boundary-mismatch']} / "
        f"{false_positive_kind['spurious']}"
    )
    print(
        "FN wrong-type / boundary / missed:   "
        f"{false_negative_kind['wrong-type']} / "
        f"{false_negative_kind['boundary-mismatch']} / "
        f"{false_negative_kind['missed']}"
    )
    print("")
    print("Boundary mismatch analysis")
    print("--------------------------")
    print(
        "Predicted-side: "
        f"{len(predicted_boundary_mismatches)}"
    )
    print(
        "Gold-side:      "
        f"{len(gold_boundary_mismatches)}"
    )

    print("")
    print("Top predicted-side type pairs")

    for item in boundary_analysis[
        "predicted_side_type_pairs"
    ][:10]:
        print(
            f"  {item['expected']} -> "
            f"{item['predicted']}: "
            f"{item['count']}"
        )

    print("")
    print("Predicted-side structures")

    for item in boundary_analysis[
        "predicted_side_structures"
    ]:
        print(
            f"  {item['key']}: {item['count']}"
        )

    print("")
    print(f"JSON: {args.output}")
    print(f"Text: {args.text_output}")


if __name__ == "__main__":
    main()
