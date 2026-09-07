from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import torch

from dataset import PAD_BYTE_ID
from model import SemanticTransformer


DEFAULT_CHECKPOINT_PATH = Path("artifacts/typescript/best.pt")

DEFAULT_SOURCE = """class UserService {
  async getUser(id: string): Promise<User> {
    return fetchUser(id);
  }
}
"""


@dataclass(frozen=True)
class CharacterPrediction:
    start: int
    end: int
    text: str
    token_type: str | None
    modifiers: tuple[str, ...]


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

    config = checkpoint["config"]

    model = SemanticTransformer(
        vocab_size=config["vocab_size"],
        number_of_token_classes=config["number_of_token_classes"],
        number_of_modifiers=config["number_of_modifiers"],
        max_length=config["max_length"],
        embedding_dimension=config["embedding_dimension"],
        number_of_heads=config["number_of_heads"],
        number_of_layers=config["number_of_layers"],
        feed_forward_dimension=config["feed_forward_dimension"],
    )

    model.load_state_dict(
        checkpoint["model_state_dict"],
    )

    model.to(device)
    model.eval()

    return model, checkpoint


def predict_byte_logits(
    model: SemanticTransformer,
    source: str,
    *,
    max_length: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    source_bytes = source.encode("utf-8")
    byte_count = len(source_bytes)

    if byte_count == 0:
        return (
            torch.empty((0, 0)),
            torch.empty((0, 0)),
        )

    token_chunks: list[torch.Tensor] = []
    modifier_chunks: list[torch.Tensor] = []

    with torch.no_grad():
        for start in range(0, byte_count, max_length):
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

            input_ids[0, :length] = torch.tensor(
                list(chunk),
                dtype=torch.long,
                device=device,
            )

            attention_mask[0, :length] = True

            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            token_chunks.append(
                output.token_type_logits[
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
        torch.cat(token_chunks, dim=0),
        torch.cat(modifier_chunks, dim=0),
    )


def predict_characters(
    source: str,
    token_logits: torch.Tensor,
    modifier_logits: torch.Tensor,
    *,
    token_types: tuple[str, ...],
    modifiers: tuple[str, ...],
    modifier_threshold: float,
) -> list[CharacterPrediction]:
    predictions: list[CharacterPrediction] = []

    byte_offset = 0
    utf16_offset = 0

    for character in source:
        encoded = character.encode("utf-8")

        byte_end = byte_offset + len(encoded)

        character_token_logits = token_logits[
            byte_offset:byte_end
        ].mean(dim=0)

        class_id = int(
            character_token_logits.argmax().item()
        )

        if class_id == 0:
            token_type = None
        else:
            token_type = token_types[class_id - 1]

        character_modifier_logits = modifier_logits[
            byte_offset:byte_end
        ].mean(dim=0)

        modifier_probabilities = torch.sigmoid(
            character_modifier_logits
        )

        predicted_modifiers = tuple(
            modifier
            for modifier, probability in zip(
                modifiers,
                modifier_probabilities.tolist(),
                strict=True,
            )
            if probability >= modifier_threshold
        )

        utf16_length = (
            len(character.encode("utf-16-le")) // 2
        )

        predictions.append(
            CharacterPrediction(
                start=utf16_offset,
                end=utf16_offset + utf16_length,
                text=character,
                token_type=token_type,
                modifiers=(
                    predicted_modifiers
                    if token_type is not None
                    else ()
                ),
            )
        )

        byte_offset = byte_end
        utf16_offset += utf16_length

    return predictions


def merge_predictions(
    predictions: list[CharacterPrediction],
) -> list[PredictedSpan]:
    spans: list[PredictedSpan] = []

    for prediction in predictions:
        if prediction.token_type is None:
            continue

        if (
            spans
            and spans[-1].end == prediction.start
            and spans[-1].token_type
            == prediction.token_type
            and spans[-1].modifiers
            == prediction.modifiers
        ):
            previous = spans[-1]

            spans[-1] = PredictedSpan(
                start=previous.start,
                end=prediction.end,
                text=previous.text + prediction.text,
                token_type=previous.token_type,
                modifiers=previous.modifiers,
            )

            continue

        spans.append(
            PredictedSpan(
                start=prediction.start,
                end=prediction.end,
                text=prediction.text,
                token_type=prediction.token_type,
                modifiers=prediction.modifiers,
            )
        )

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
    print("Predicted semantic spans")
    print("------------------------")

    if not spans:
        print("(none)")
        return

    for span in spans:
        modifiers = ""

        if span.modifiers:
            modifiers = (
                " ["
                + ", ".join(span.modifiers)
                + "]"
            )

        print(
            f"{span.start:>4}:{span.end:<4} "
            f"{json.dumps(span.text, ensure_ascii=False):<28} "
            f"-> {span.token_type}{modifiers}"
        )


def read_source(
    *,
    text: str | None,
    file_path: Path | None,
) -> str:
    if text is not None and file_path is not None:
        raise ValueError(
            "Use either --text or --file, not both."
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
        default=0.5,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if not 0.0 <= args.modifier_threshold <= 1.0:
        raise ValueError(
            "--modifier-threshold must be between 0 and 1."
        )

    device = select_device()

    model, checkpoint = load_model(
        checkpoint_path=args.checkpoint,
        device=device,
    )

    source = read_source(
        text=args.text,
        file_path=args.file,
    )

    token_types = tuple(
        checkpoint["schema"]["token_types"]
    )

    modifiers = tuple(
        checkpoint["schema"]["modifiers"]
    )

    max_length = checkpoint["config"]["max_length"]

    token_logits, modifier_logits = (
        predict_byte_logits(
            model=model,
            source=source,
            max_length=max_length,
            device=device,
        )
    )

    if source:
        character_predictions = (
            predict_characters(
                source=source,
                token_logits=token_logits,
                modifier_logits=modifier_logits,
                token_types=token_types,
                modifiers=modifiers,
                modifier_threshold=(
                    args.modifier_threshold
                ),
            )
        )

        spans = merge_predictions(
            character_predictions
        )
    else:
        spans = []

    print("Neural Semantic Highlighting")
    print("TypeScript Semantic Prediction")
    print("")
    print(f"Device:     {device}")
    print(f"Checkpoint: {args.checkpoint}")

    print_predictions(
        source=source,
        spans=spans,
    )


if __name__ == "__main__":
    main()
