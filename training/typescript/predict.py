from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import torch

from config import CHECKPOINT_FORMAT, DEFAULT_BEST_CHECKPOINT_PATH
from dataset import (
    BOUNDARY_BEGIN_ID,
    BOUNDARY_INSIDE_ID,
    BOUNDARY_OUTSIDE_ID,
)
from inference import predict_document_logits
from model import SemanticTransformer


DEFAULT_CHECKPOINT_PATH = DEFAULT_BEST_CHECKPOINT_PATH

DEFAULT_SOURCE = """class UserService {
  async getUser(id: string): Promise<User> {
    return fetchUser(id);
  }
}
"""


@dataclass(frozen=True)
class CharacterPoint:
    utf16_start: int
    utf16_end: int
    byte_start: int
    text: str


@dataclass(frozen=True)
class PredictedSpan:
    start: int
    end: int
    text: str
    token_type: str
    modifiers: tuple[str, ...]


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


def load_model(
    checkpoint_path: Path,
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

    config = checkpoint["config"]

    model = SemanticTransformer(
        vocab_size=config["vocab_size"],
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
        local_kernel=config.get('local_kernel', 1),
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
                text=character,
            )
        )

        utf16_offset += utf16_length
        byte_offset += len(character.encode("utf-8"))

    return points



def decode_predictions(
    source: str,
    boundary_logits: torch.Tensor,
    token_type_logits: torch.Tensor,
    modifier_logits: torch.Tensor,
    *,
    token_types: tuple[str, ...],
    modifiers: tuple[str, ...],
    modifier_threshold: float,
) -> list[PredictedSpan]:
    points = build_character_points(
        source
    )

    if not points:
        return []

    boundary_ids = [
        int(
            boundary_logits[
                point.byte_start
            ]
            .argmax()
            .item()
        )
        for point in points
    ]

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
                modifiers,
                modifier_probabilities.tolist(),
                strict=True,
            )
            if probability >= modifier_threshold
        )

        spans.append(
            PredictedSpan(
                start=start_point.utf16_start,
                end=end_point.utf16_end,
                text="".join(
                    point.text
                    for point in span_points
                ),
                token_type=token_types[
                    token_type_id
                ],
                modifiers=predicted_modifiers,
            )
        )

    return spans


def read_source(
    *,
    text: str | None,
    file_path: Path | None,
) -> str:
    if (
        text is not None
        and file_path is not None
    ):
        raise ValueError(
            "Use either --text or "
            "--file, not both."
        )

    if file_path is not None:
        return file_path.read_text(
            encoding="utf-8"
        )

    if text is not None:
        return text

    return DEFAULT_SOURCE


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT_PATH,
    )

    parser.add_argument(
        "--text",
        type=str,
    )

    parser.add_argument(
        "--file",
        type=Path,
    )

    parser.add_argument(
        "--modifier-threshold",
        type=float,
        default=0.60,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if not (
        0.0
        <= args.modifier_threshold
        <= 1.0
    ):
        raise ValueError(
            "--modifier-threshold "
            "must be between 0 and 1."
        )

    device = select_device()

    model, checkpoint = load_model(
        args.checkpoint,
        device,
    )

    source = read_source(
        text=args.text,
        file_path=args.file,
    )

    (
        boundary_logits,
        token_type_logits,
        modifier_logits,
    ) = predict_document_logits(
        model,
        source,
        max_length=checkpoint["config"]["max_length"],
        device=device,
    )

    spans = decode_predictions(
        source,
        boundary_logits,
        token_type_logits,
        modifier_logits,
        token_types=tuple(
            checkpoint["schema"][
                "token_types"
            ]
        ),
        modifiers=tuple(
            checkpoint["schema"][
                "modifiers"
            ]
        ),
        modifier_threshold=(
            args.modifier_threshold
        ),
    )

    print("Neural Semantic Highlighting")
    print(
        "TypeScript Multitask Prediction"
    )
    print("")
    print(f"Device: {device}")
    print(
        f"Checkpoint: {args.checkpoint}"
    )
    print("")
    print("Source")
    print("------")
    print(source.rstrip())
    print("")
    print(
        "Predicted semantic spans"
    )
    print(
        "------------------------"
    )

    if not spans:
        print("(none)")
        return

    for span in spans:
        modifier_text = ""

        if span.modifiers:
            modifier_text = (
                " ["
                + ", ".join(
                    span.modifiers
                )
                + "]"
            )

        print(
            f"{span.start:>4}:"
            f"{span.end:<4} "
            f"{json.dumps(span.text, ensure_ascii=False):<28} "
            f"-> {span.token_type}"
            f"{modifier_text}"
        )


if __name__ == "__main__":
    main()
