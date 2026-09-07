from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import torch

from dataset import PAD_BYTE_ID
from model import SemanticTransformer


DEFAULT_CHECKPOINT_PATH = Path(
    "artifacts/typescript/v1-bio/best.pt"
)

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
        != "nsh-typescript-v1-bio"
    ):
        raise ValueError(
            "Checkpoint is not an NSH "
            "TypeScript V1 BIO checkpoint."
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
                text=character,
            )
        )

        utf16_offset += utf16_length

        byte_offset += len(
            character.encode("utf-8")
        )

    return points


def predict_logits(
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

    tag_chunks = []
    modifier_chunks = []

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


def decode_tag_id(
    tag_id: int,
    token_types: tuple[str, ...],
) -> tuple[str, str] | None:
    if tag_id == 0:
        return None

    number_of_token_types = len(
        token_types
    )

    if (
        1
        <= tag_id
        <= number_of_token_types
    ):
        return (
            "B",
            token_types[
                tag_id - 1
            ],
        )

    inside_index = (
        tag_id
        - 1
        - number_of_token_types
    )

    if (
        0
        <= inside_index
        < number_of_token_types
    ):
        return (
            "I",
            token_types[
                inside_index
            ],
        )

    raise ValueError(
        f"Unknown semantic tag id "
        f"{tag_id}."
    )


def decode_predictions(
    source: str,
    tag_logits: torch.Tensor,
    modifier_logits: torch.Tensor,
    *,
    token_types: tuple[str, ...],
    modifiers: tuple[str, ...],
    modifier_threshold: float,
) -> list[PredictedSpan]:
    points = build_character_points(
        source
    )

    spans: list[
        PredictedSpan
    ] = []

    current_start: int | None = None
    current_end: int | None = None
    current_text = ""
    current_type: str | None = None
    current_modifiers: tuple[
        str,
        ...
    ] = ()

    def flush() -> None:
        nonlocal current_start
        nonlocal current_end
        nonlocal current_text
        nonlocal current_type
        nonlocal current_modifiers

        if (
            current_start is not None
            and current_end is not None
            and current_type is not None
        ):
            spans.append(
                PredictedSpan(
                    start=current_start,
                    end=current_end,
                    text=current_text,
                    token_type=(
                        current_type
                    ),
                    modifiers=(
                        current_modifiers
                    ),
                )
            )

        current_start = None
        current_end = None
        current_text = ""
        current_type = None
        current_modifiers = ()

    for point in points:
        tag_id = int(
            tag_logits[
                point.byte_start
            ]
            .argmax()
            .item()
        )

        decoded = decode_tag_id(
            tag_id,
            token_types,
        )

        if decoded is None:
            flush()
            continue

        prefix, token_type = decoded

        if prefix == "B":
            flush()

            probabilities = (
                torch.sigmoid(
                    modifier_logits[
                        point.byte_start
                    ]
                )
            )

            predicted_modifiers = (
                tuple(
                    modifier
                    for (
                        modifier,
                        probability,
                    ) in zip(
                        modifiers,
                        probabilities.tolist(),
                        strict=True,
                    )
                    if probability
                    >= modifier_threshold
                )
            )

            current_start = (
                point.utf16_start
            )
            current_end = (
                point.utf16_end
            )
            current_text = point.text
            current_type = token_type
            current_modifiers = (
                predicted_modifiers
            )

            continue

        if (
            current_type
            != token_type
            or current_start is None
        ):
            # Repair invalid I-X transitions as a new span.
            flush()

            current_start = (
                point.utf16_start
            )
            current_end = (
                point.utf16_end
            )
            current_text = point.text
            current_type = token_type
            current_modifiers = ()

            continue

        current_end = point.utf16_end
        current_text += point.text

    flush()

    return spans


def print_predictions(
    source: str,
    spans: list[PredictedSpan],
) -> None:
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
        default=(
            DEFAULT_CHECKPOINT_PATH
        ),
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

    token_types = tuple(
        checkpoint["schema"][
            "token_types"
        ]
    )

    modifiers = tuple(
        checkpoint["schema"][
            "modifiers"
        ]
    )

    max_length = checkpoint[
        "config"
    ]["max_length"]

    (
        tag_logits,
        modifier_logits,
    ) = predict_logits(
        model,
        source,
        max_length=max_length,
        device=device,
    )

    spans = (
        decode_predictions(
            source,
            tag_logits,
            modifier_logits,
            token_types=(
                token_types
            ),
            modifiers=modifiers,
            modifier_threshold=(
                args.modifier_threshold
            ),
        )
        if source
        else []
    )

    print(
        "Neural Semantic Highlighting"
    )
    print(
        "TypeScript V1 BIO Prediction"
    )
    print("")
    print(f"Device: {device}")
    print(
        f"Checkpoint: "
        f"{args.checkpoint}"
    )

    print_predictions(
        source,
        spans,
    )


if __name__ == "__main__":
    main()
