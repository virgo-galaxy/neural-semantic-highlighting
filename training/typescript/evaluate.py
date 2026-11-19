from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import torch

from config import (
    CHECKPOINT_FORMAT,
    DEFAULT_ARTIFACT_DIRECTORY,
    DEFAULT_BEST_CHECKPOINT_PATH,
)
from dataset import (
    BOUNDARY_BEGIN_ID,
    BOUNDARY_INSIDE_ID,
    BOUNDARY_OUTSIDE_ID,
    EncodedDocument,
    TypeScriptSemanticDataset,
)
from inference import predict_document_logits
from model import SemanticTransformer


DEFAULT_CHECKPOINT_PATH = DEFAULT_BEST_CHECKPOINT_PATH
DEFAULT_OUTPUT_PATH = DEFAULT_ARTIFACT_DIRECTORY / "test-metrics.json"


@dataclass(frozen=True)
class CharacterPoint:
    utf16_start: int
    utf16_end: int
    byte_start: int


@dataclass(frozen=True)
class PredictedSpan:
    start: int
    end: int
    token_type: str
    modifiers: tuple[str, ...]


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


def build_character_points(
    source: str,
) -> list[CharacterPoint]:
    points: list[CharacterPoint] = []

    utf16_offset = 0
    byte_offset = 0

    for character in source:
        utf16_length = (
            len(character.encode("utf-16-le")) // 2
        )

        points.append(
            CharacterPoint(
                utf16_start=utf16_offset,
                utf16_end=utf16_offset + utf16_length,
                byte_start=byte_offset,
            )
        )

        utf16_offset += utf16_length
        byte_offset += len(character.encode("utf-8"))

    return points


def load_model(
    checkpoint_path: Path,
    dataset: TypeScriptSemanticDataset,
    device: torch.device,
) -> tuple[SemanticTransformer, dict]:
    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
    )

    if (
        checkpoint.get("format")
        != CHECKPOINT_FORMAT
    ):
        raise ValueError(
            "Checkpoint is not an NSH "
            "TypeScript multitask checkpoint."
        )

    if (
        tuple(
            checkpoint["schema"][
                "token_types"
            ]
        )
        != dataset.schema.token_types
    ):
        raise ValueError(
            "Checkpoint token-type schema "
            "does not match the current schema."
        )

    if (
        tuple(
            checkpoint["schema"][
                "modifiers"
            ]
        )
        != dataset.schema.modifiers
    ):
        raise ValueError(
            "Checkpoint modifier schema "
            "does not match the current schema."
        )

    config = checkpoint["config"]

    model = SemanticTransformer(
        vocab_size=config["vocab_size"],
        local_kernel=config.get("local_kernel", 1),
        number_of_boundary_classes=(
            config[
                "number_of_boundary_classes"
            ]
        ),
        number_of_token_types=(
            config[
                "number_of_token_types"
            ]
        ),
        number_of_modifiers=(
            config[
                "number_of_modifiers"
            ]
        ),
        max_length=config["max_length"],
        embedding_dimension=(
            config[
                "embedding_dimension"
            ]
        ),
        number_of_heads=(
            config["number_of_heads"]
        ),
        number_of_layers=(
            config["number_of_layers"]
        ),
        feed_forward_dimension=(
            config[
                "feed_forward_dimension"
            ]
        ),
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(device)
    model.eval()

    return model, checkpoint



def decode_predicted_spans(
    document: EncodedDocument,
    boundary_logits: torch.Tensor,
    token_type_logits: torch.Tensor,
    modifier_logits: torch.Tensor,
    dataset: TypeScriptSemanticDataset,
    *,
    modifier_threshold: float = 0.60,
    decoder: str = "greedy",
    inside_ratio: float = 0.90,
) -> list[PredictedSpan]:
    points = build_character_points(
        document.source
    )

    if not points:
        return []

    if decoder not in {
        "greedy",
        "sticky",
    }:
        raise ValueError(
            f'Unknown boundary decoder "{decoder}".'
        )

    if not 0.0 < inside_ratio <= 1.0:
        raise ValueError(
            "inside_ratio must be in (0, 1], "
            f"got {inside_ratio}."
        )

    boundary_probabilities = torch.softmax(
        torch.stack(
            [
                boundary_logits[
                    point.byte_start
                ]
                for point in points
            ],
            dim=0,
        ),
        dim=-1,
    )

    greedy_boundary_ids = (
        boundary_probabilities.argmax(dim=-1)
    )

    boundary_ids: list[int] = []
    inside_span = False

    for index, greedy_id_tensor in enumerate(
        greedy_boundary_ids
    ):
        greedy_id = int(
            greedy_id_tensor.item()
        )

        boundary_id = greedy_id

        if (
            decoder == "sticky"
            and inside_span
            and greedy_id != BOUNDARY_INSIDE_ID
        ):
            probabilities = (
                boundary_probabilities[index]
            )

            inside_probability = float(
                probabilities[
                    BOUNDARY_INSIDE_ID
                ].item()
            )

            winning_probability = float(
                probabilities[
                    greedy_id
                ].item()
            )

            if (
                inside_probability
                >= winning_probability
                * inside_ratio
            ):
                boundary_id = (
                    BOUNDARY_INSIDE_ID
                )

        boundary_ids.append(boundary_id)

        if boundary_id == BOUNDARY_OUTSIDE_ID:
            inside_span = False
        elif boundary_id in {
            BOUNDARY_BEGIN_ID,
            BOUNDARY_INSIDE_ID,
        }:
            inside_span = True

    span_ranges: list[
        tuple[int, int]
    ] = []

    current_start: int | None = None

    def flush(end_index: int) -> None:
        nonlocal current_start

        if current_start is not None:
            span_ranges.append(
                (
                    current_start,
                    end_index,
                )
            )

        current_start = None

    for index, boundary_id in enumerate(
        boundary_ids
    ):
        if boundary_id == BOUNDARY_OUTSIDE_ID:
            flush(index)
            continue

        if boundary_id == BOUNDARY_BEGIN_ID:
            flush(index)
            current_start = index
            continue

        if boundary_id == BOUNDARY_INSIDE_ID:
            if current_start is None:
                current_start = index
            continue

    flush(len(points))

    spans: list[PredictedSpan] = []

    for start_index, end_index in span_ranges:
        span_points = points[
            start_index:end_index
        ]

        byte_positions = torch.tensor(
            [
                point.byte_start
                for point in span_points
            ],
            dtype=torch.long,
        )

        mean_type_logits = (
            token_type_logits[
                byte_positions
            ].mean(dim=0)
        )

        token_type_id = int(
            mean_type_logits.argmax().item()
        )

        start_point = span_points[0]
        end_point = span_points[-1]

        modifier_probabilities = torch.sigmoid(
            modifier_logits[
                start_point.byte_start
            ]
        )

        predicted_modifiers = tuple(
            modifier
            for modifier, probability
            in zip(
                dataset.schema.modifiers,
                modifier_probabilities.tolist(),
                strict=True,
            )
            if probability >= modifier_threshold
        )

        spans.append(
            PredictedSpan(
                start=start_point.utf16_start,
                end=end_point.utf16_end,
                token_type=(
                    dataset.schema.token_types[
                        token_type_id
                    ]
                ),
                modifiers=predicted_modifiers,
            )
        )

    return spans


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--split",
        choices=(
            "validation",
            "test",
        ),
        default="test",
        help=(
            "Dataset split to evaluate. Use validation "
            "for inference A/B experiments."
        ),
    )

    parser.add_argument(
        "--decoder",
        choices=(
            "greedy",
            "sticky",
        ),
        default="greedy",
        help=(
            "Boundary decoder. greedy preserves the current "
            "per-character argmax behavior. sticky keeps an "
            "active span alive when INSIDE is a near-tie with "
            "a competing boundary class."
        ),
    )

    parser.add_argument(
        "--inside-ratio",
        type=float,
        default=0.90,
        help=(
            "Sticky-decoder near-tie ratio. While inside a "
            "span, continue as INSIDE when p(I) >= "
            "p(winner) * ratio. 1.0 is effectively greedy; "
            "smaller values make spans stickier."
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

    evaluation_dataset = TypeScriptSemanticDataset(
        args.split,
        max_length=max_length,
    )

    model, checkpoint = load_model(
        args.checkpoint,
        evaluation_dataset,
        device,
    )

    predicted_set: set[
        tuple[str, int, int, str]
    ] = set()

    gold_set: set[
        tuple[str, int, int, str]
    ] = set()

    per_type_predicted = {
        token_type: set()
        for token_type
        in evaluation_dataset.schema.token_types
    }

    per_type_gold = {
        token_type: set()
        for token_type
        in evaluation_dataset.schema.token_types
    }

    print("Neural Semantic Highlighting")
    print(
        "TypeScript Multitask Evaluation"
    )
    print("")
    print(f"Device: {device}")
    print(
        f"Checkpoint: {args.checkpoint}"
    )
    print(
        f"Split: {args.split}"
    )
    print(
        f"Documents: "
        f"{len(evaluation_dataset.documents)}"
    )
    print(
        f"Window:    {max_length} bytes"
    )
    print("Windowing: adaptive cursor")
    print(
        f"Decoder:   {args.decoder}"
    )

    if args.decoder == "sticky":
        print(
            f"I-ratio:   {args.inside_ratio:.2f}"
        )

    for document in evaluation_dataset.documents:
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
            evaluation_dataset,
            decoder=args.decoder,
            inside_ratio=args.inside_ratio,
        )

        key = (
            f"{document.repository}:"
            f"{document.path}"
        )

        for span in predicted_spans:
            item = (
                key,
                span.start,
                span.end,
                span.token_type,
            )

            predicted_set.add(item)

            per_type_predicted[
                span.token_type
            ].add(item)

        for span in document.gold_spans:
            item = (
                key,
                span.start,
                span.end,
                span.token_type,
            )

            gold_set.add(item)

            per_type_gold[
                span.token_type
            ].add(item)

    tp = len(
        predicted_set & gold_set
    )
    fp = len(
        predicted_set - gold_set
    )
    fn = len(
        gold_set - predicted_set
    )

    precision = (
        tp / max(1, tp + fp)
    )

    recall = (
        tp / max(1, tp + fn)
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

    per_type = {}
    macro_values: list[float] = []

    for token_type in (
        evaluation_dataset.schema.token_types
    ):
        predicted = (
            per_type_predicted[
                token_type
            ]
        )

        gold = per_type_gold[
            token_type
        ]

        type_tp = len(
            predicted & gold
        )

        type_fp = len(
            predicted - gold
        )

        type_fn = len(
            gold - predicted
        )

        type_precision = (
            type_tp
            / max(
                1,
                type_tp + type_fp,
            )
        )

        type_recall = (
            type_tp
            / max(
                1,
                type_tp + type_fn,
            )
        )

        type_f1 = (
            2.0
            * type_precision
            * type_recall
            / max(
                1e-12,
                type_precision
                + type_recall,
            )
        )

        support = len(gold)

        per_type[token_type] = {
            "precision": type_precision,
            "recall": type_recall,
            "f1": type_f1,
            "support": support,
        }

        if support > 0:
            macro_values.append(
                type_f1
            )

    macro_f1 = (
        sum(macro_values)
        / len(macro_values)
        if macro_values
        else 0.0
    )

    metrics = {
        "span_exact_precision": precision,
        "span_exact_recall": recall,
        "span_exact_f1": f1,
        "span_exact_macro_f1": macro_f1,
        "predicted_spans": len(
            predicted_set
        ),
        "gold_spans": len(gold_set),
        "token_types": per_type,
        "inference": {
            "split": args.split,
            "max_length": max_length,
            "windowing": "adaptive-cursor",
            "decoder": args.decoder,
            "inside_ratio": (
                args.inside_ratio
                if args.decoder == "sticky"
                else None
            ),
        },
        "validation": checkpoint.get(
            "validation"
        ),
    }

    print("")
    print("Exact semantic spans")
    print("--------------------")
    print(
        f"Precision: {precision:.4f}"
    )
    print(
        f"Recall:    {recall:.4f}"
    )
    print(
        f"F1:        {f1:.4f}"
    )
    print(
        f"Macro F1:  {macro_f1:.4f}"
    )
    print(
        "Predicted: "
        f"{len(predicted_set)}"
    )
    print(
        f"Gold:      {len(gold_set)}"
    )

    print("")
    print("Per token type")
    print("--------------")
    print(
        f"{'token type':<18}"
        f"{'precision':>11}"
        f"{'recall':>11}"
        f"{'f1':>11}"
        f"{'support':>12}"
    )

    for token_type, values in (
        per_type.items()
    ):
        print(
            f"{token_type:<18}"
            f"{values['precision']:>11.4f}"
            f"{values['recall']:>11.4f}"
            f"{values['f1']:>11.4f}"
            f"{values['support']:>12}"
        )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            metrics,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print("")
    print(
        f"Written to {args.output}"
    )


if __name__ == "__main__":
    main()
