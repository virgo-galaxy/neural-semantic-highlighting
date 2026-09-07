from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import torch

from dataset import (
    PAD_BYTE_ID,
    TypeScriptSemanticDataset,
)
from model import SemanticTransformer


DEFAULT_CHECKPOINT_PATH = Path(
    "artifacts/typescript/v1-bio/best.pt"
)

DEFAULT_OUTPUT_PATH = Path(
    "artifacts/typescript/v1-bio/test-metrics.json"
)


@dataclass(frozen=True)
class CharacterPoint:
    utf16_start: int
    utf16_end: int
    byte_start: int


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    token_type: str


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


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
        != "nsh-typescript-v1-bio"
    ):
        raise ValueError(
            "Checkpoint is not an NSH "
            "TypeScript V1 BIO checkpoint."
        )

    checkpoint_schema = (
        checkpoint["schema"]
    )

    if (
        tuple(
            checkpoint_schema[
                "token_types"
            ]
        )
        != dataset.schema.token_types
    ):
        raise ValueError(
            "Checkpoint token-type schema "
            "does not match the current "
            "TypeScript schema."
        )

    if (
        tuple(
            checkpoint_schema[
                "modifiers"
            ]
        )
        != dataset.schema.modifiers
    ):
        raise ValueError(
            "Checkpoint modifier schema "
            "does not match the current "
            "TypeScript schema."
        )

    config = checkpoint["config"]

    model = SemanticTransformer(
        vocab_size=(
            config["vocab_size"]
        ),
        number_of_semantic_tag_classes=(
            config[
                "number_of_semantic_tag_classes"
            ]
        ),
        number_of_modifiers=(
            config[
                "number_of_modifiers"
            ]
        ),
        max_length=(
            config["max_length"]
        ),
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


def build_character_points(
    source: str,
) -> list[CharacterPoint]:
    points: list[
        CharacterPoint
    ] = []

    utf16_offset = 0
    byte_offset = 0

    for character in source:
        utf16_length = (
            len(
                character.encode(
                    "utf-16-le"
                )
            )
            // 2
        )

        points.append(
            CharacterPoint(
                utf16_start=(
                    utf16_offset
                ),
                utf16_end=(
                    utf16_offset
                    + utf16_length
                ),
                byte_start=byte_offset,
            )
        )

        utf16_offset += utf16_length

        byte_offset += len(
            character.encode("utf-8")
        )

    return points


def predict_document_logits(
    model: SemanticTransformer,
    source: str,
    *,
    max_length: int,
    device: torch.device,
) -> tuple[
    torch.Tensor,
    torch.Tensor,
]:
    source_bytes = source.encode(
        "utf-8"
    )

    byte_count = len(source_bytes)

    if byte_count == 0:
        return (
            torch.empty((0, 0)),
            torch.empty((0, 0)),
        )

    tag_chunks: list[
        torch.Tensor
    ] = []

    modifier_chunks: list[
        torch.Tensor
    ] = []

    with torch.no_grad():
        for start in range(
            0,
            byte_count,
            max_length,
        ):
            chunk = source_bytes[
                start : start + max_length
            ]

            length = len(chunk)

            input_ids = torch.full(
                (1, max_length),
                PAD_BYTE_ID,
                dtype=torch.long,
                device=device,
            )

            attention_mask = torch.zeros(
                (1, max_length),
                dtype=torch.bool,
                device=device,
            )

            input_ids[
                0,
                :length,
            ] = torch.tensor(
                list(chunk),
                dtype=torch.long,
                device=device,
            )

            attention_mask[
                0,
                :length,
            ] = True

            output = model(
                input_ids=input_ids,
                attention_mask=(
                    attention_mask
                ),
            )

            tag_chunks.append(
                output.semantic_tag_logits[
                    0,
                    :length,
                ]
                .detach()
                .cpu()
            )

            modifier_chunks.append(
                output.modifier_logits[
                    0,
                    :length,
                ]
                .detach()
                .cpu()
            )

    return (
        torch.cat(
            tag_chunks,
            dim=0,
        ),
        torch.cat(
            modifier_chunks,
            dim=0,
        ),
    )


def decode_bio_spans(
    source: str,
    tag_ids_by_character: list[int],
    dataset: TypeScriptSemanticDataset,
) -> list[Span]:
    points = build_character_points(
        source
    )

    spans: list[Span] = []

    current_start: int | None = None
    current_end: int | None = None
    current_type: str | None = None

    def flush() -> None:
        nonlocal current_start
        nonlocal current_end
        nonlocal current_type

        if (
            current_start is not None
            and current_end is not None
            and current_type is not None
        ):
            spans.append(
                Span(
                    start=current_start,
                    end=current_end,
                    token_type=(
                        current_type
                    ),
                )
            )

        current_start = None
        current_end = None
        current_type = None

    for point, tag_id in zip(
        points,
        tag_ids_by_character,
        strict=True,
    ):
        decoded = (
            dataset.schema.decode_tag_id(
                tag_id
            )
        )

        if decoded is None:
            flush()
            continue

        prefix, token_type = decoded

        if prefix == "B":
            flush()
            current_start = (
                point.utf16_start
            )
            current_end = point.utf16_end
            current_type = token_type
            continue

        # Repair invalid I-X transitions as a new B-X.
        if (
            current_type
            != token_type
            or current_start is None
        ):
            flush()
            current_start = (
                point.utf16_start
            )
            current_end = point.utf16_end
            current_type = token_type
            continue

        current_end = point.utf16_end

    flush()

    return spans


def gold_spans_from_document(
    document,
    dataset: TypeScriptSemanticDataset,
) -> list[Span]:
    points = build_character_points(
        document.source
    )

    tag_ids = [
        int(
            document.semantic_tag_labels[
                point.byte_start
            ].item()
        )
        for point in points
    ]

    return decode_bio_spans(
        document.source,
        tag_ids,
        dataset,
    )


def score_spans(
    predicted: list[Span],
    gold: list[Span],
    token_types: tuple[str, ...],
) -> dict:
    predicted_set = {
        (
            span.start,
            span.end,
            span.token_type,
        )
        for span in predicted
    }

    gold_set = {
        (
            span.start,
            span.end,
            span.token_type,
        )
        for span in gold
    }

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

    per_type = {}

    macro_values = []

    for token_type in token_types:
        predicted_type = {
            item
            for item in predicted_set
            if item[2] == token_type
        }

        gold_type = {
            item
            for item in gold_set
            if item[2] == token_type
        }

        tp = len(
            predicted_type & gold_type
        )

        fp = len(
            predicted_type - gold_type
        )

        fn = len(
            gold_type - predicted_type
        )

        type_precision = (
            tp
            / max(1, tp + fp)
        )

        type_recall = (
            tp
            / max(1, tp + fn)
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

        support = len(gold_type)

        per_type[token_type] = {
            "precision": (
                type_precision
            ),
            "recall": type_recall,
            "f1": type_f1,
            "support": support,
        }

        if support > 0:
            macro_values.append(
                type_f1
            )

    span_macro_f1 = (
        sum(macro_values)
        / len(macro_values)
        if macro_values
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "macro_f1": span_macro_f1,
        "per_type": per_type,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=(
            DEFAULT_CHECKPOINT_PATH
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
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

    test_dataset = (
        TypeScriptSemanticDataset(
            "test",
            max_length=max_length,
        )
    )

    model, checkpoint = (
        load_model(
            args.checkpoint,
            test_dataset,
            device,
        )
    )

    all_predicted: list[
        tuple[str, Span]
    ] = []

    all_gold: list[
        tuple[str, Span]
    ] = []

    print(
        "Neural Semantic Highlighting"
    )
    print(
        "TypeScript V1 BIO Evaluation"
    )
    print("")
    print(f"Device: {device}")
    print(
        f"Checkpoint: "
        f"{args.checkpoint}"
    )
    print(
        "Test documents: "
        f"{len(test_dataset.documents)}"
    )

    for document in (
        test_dataset.documents
    ):
        (
            tag_logits,
            _,
        ) = predict_document_logits(
            model,
            document.source,
            max_length=max_length,
            device=device,
        )

        points = (
            build_character_points(
                document.source
            )
        )

        predicted_tag_ids = [
            int(
                tag_logits[
                    point.byte_start
                ]
                .argmax()
                .item()
            )
            for point in points
        ]

        predicted_spans = (
            decode_bio_spans(
                document.source,
                predicted_tag_ids,
                test_dataset,
            )
        )

        gold_spans = (
            gold_spans_from_document(
                document,
                test_dataset,
            )
        )

        key = (
            f"{document.repository}:"
            f"{document.path}"
        )

        all_predicted.extend(
            (key, span)
            for span
            in predicted_spans
        )

        all_gold.extend(
            (key, span)
            for span
            in gold_spans
        )

    # Include the document key in exact matching so equal offsets
    # from different files never collide.
    predicted_set = {
        (
            key,
            span.start,
            span.end,
            span.token_type,
        )
        for key, span in all_predicted
    }

    gold_set = {
        (
            key,
            span.start,
            span.end,
            span.token_type,
        )
        for key, span in all_gold
    }

    tp = len(
        predicted_set & gold_set
    )
    fp = len(
        predicted_set - gold_set
    )
    fn = len(
        gold_set - predicted_set
    )

    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)

    span_f1 = (
        2.0
        * precision
        * recall
        / max(
            1e-12,
            precision + recall,
        )
    )

    per_type = {}
    macro_values = []

    for token_type in (
        test_dataset.schema.token_types
    ):
        predicted_type = {
            item
            for item in predicted_set
            if item[3] == token_type
        }

        gold_type = {
            item
            for item in gold_set
            if item[3] == token_type
        }

        type_tp = len(
            predicted_type & gold_type
        )

        type_fp = len(
            predicted_type - gold_type
        )

        type_fn = len(
            gold_type - predicted_type
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

        support = len(gold_type)

        per_type[token_type] = {
            "precision": (
                type_precision
            ),
            "recall": type_recall,
            "f1": type_f1,
            "support": support,
        }

        if support > 0:
            macro_values.append(
                type_f1
            )

    span_macro_f1 = (
        sum(macro_values)
        / len(macro_values)
        if macro_values
        else 0.0
    )

    metrics = {
        "span_exact_precision": (
            precision
        ),
        "span_exact_recall": recall,
        "span_exact_f1": span_f1,
        "span_exact_macro_f1": (
            span_macro_f1
        ),
        "predicted_spans": len(
            predicted_set
        ),
        "gold_spans": len(gold_set),
        "token_types": per_type,
        "validation": checkpoint.get(
            "validation"
        ),
    }

    print("")
    print("Exact semantic spans")
    print("--------------------")
    print(
        "Precision: "
        f"{precision:.4f}"
    )
    print(
        "Recall:    "
        f"{recall:.4f}"
    )
    print(
        "F1:        "
        f"{span_f1:.4f}"
    )
    print(
        "Macro F1:  "
        f"{span_macro_f1:.4f}"
    )
    print(
        "Predicted: "
        f"{len(predicted_set)}"
    )
    print(
        "Gold:      "
        f"{len(gold_set)}"
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
        f"Written to "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()
