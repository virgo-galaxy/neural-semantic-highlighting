from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import Dataset


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = Path(
    os.environ.get(
        "NSH_DATASET_ROOT",
        Path.home() / "Datasets" / "neural-semantic-highlighting",
    )
)

TYPESCRIPT_DATASET_ROOT = DATASET_ROOT / "typescript"
SCHEMA_PATH = REPOSITORY_ROOT / "packs" / "typescript" / "schema.json"

PAD_BYTE_ID = 256
OUTSIDE_TOKEN_ID = 0


@dataclass(frozen=True)
class SemanticSchema:
    token_types: tuple[str, ...]
    modifiers: tuple[str, ...]

    @property
    def token_type_to_id(self) -> dict[str, int]:
        return {
            token_type: index + 1
            for index, token_type in enumerate(self.token_types)
        }

    @property
    def modifier_to_id(self) -> dict[str, int]:
        return {
            modifier: index
            for index, modifier in enumerate(self.modifiers)
        }

    @property
    def number_of_token_classes(self) -> int:
        return len(self.token_types) + 1


@dataclass(frozen=True)
class EncodedDocument:
    repository: str
    path: str
    document_kind: str
    input_ids: torch.Tensor
    token_type_labels: torch.Tensor
    modifier_labels: torch.Tensor


@dataclass(frozen=True)
class WindowReference:
    document_index: int
    start: int
    end: int


def load_schema() -> SemanticSchema:
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    return SemanticSchema(
        token_types=tuple(entry["id"] for entry in data["tokenTypes"]),
        modifiers=tuple(entry["id"] for entry in data["tokenModifiers"]),
    )


def build_utf16_to_utf8_boundary_map(source: str) -> dict[int, int]:
    utf16_offset = 0
    utf8_offset = 0

    boundaries = {
        0: 0,
    }

    for character in source:
        utf16_offset += len(character.encode("utf-16-le")) // 2
        utf8_offset += len(character.encode("utf-8"))

        boundaries[utf16_offset] = utf8_offset

    return boundaries


def encode_document(
    sample: dict[str, Any],
    schema: SemanticSchema,
) -> EncodedDocument:
    source = sample["source"]
    source_bytes = source.encode("utf-8")

    input_ids = torch.tensor(
        list(source_bytes),
        dtype=torch.long,
    )

    token_type_labels = torch.full(
        (len(source_bytes),),
        OUTSIDE_TOKEN_ID,
        dtype=torch.long,
    )

    modifier_labels = torch.zeros(
        (len(source_bytes), len(schema.modifiers)),
        dtype=torch.uint8,
    )

    utf16_to_utf8 = build_utf16_to_utf8_boundary_map(source)

    token_type_to_id = schema.token_type_to_id
    modifier_to_id = schema.modifier_to_id

    for span in sample["result"]["spans"]:
        utf16_start = span["start"]
        utf16_end = span["end"]

        if utf16_start not in utf16_to_utf8:
            raise ValueError(
                f'{sample["repository"]}/{sample["path"]}: '
                f"span start {utf16_start} is not a valid UTF-16 boundary"
            )

        if utf16_end not in utf16_to_utf8:
            raise ValueError(
                f'{sample["repository"]}/{sample["path"]}: '
                f"span end {utf16_end} is not a valid UTF-16 boundary"
            )

        byte_start = utf16_to_utf8[utf16_start]
        byte_end = utf16_to_utf8[utf16_end]

        token_type = span["tokenType"]

        if token_type not in token_type_to_id:
            raise ValueError(
                f'{sample["repository"]}/{sample["path"]}: '
                f'unknown token type "{token_type}"'
            )

        token_type_labels[byte_start:byte_end] = token_type_to_id[token_type]

        for modifier in span.get("modifiers", []):
            if modifier not in modifier_to_id:
                raise ValueError(
                    f'{sample["repository"]}/{sample["path"]}: '
                    f'unknown modifier "{modifier}"'
                )

            modifier_id = modifier_to_id[modifier]

            modifier_labels[
                byte_start:byte_end,
                modifier_id,
            ] = 1

    return EncodedDocument(
        repository=sample["repository"],
        path=sample["path"],
        document_kind=sample["documentKind"],
        input_ids=input_ids,
        token_type_labels=token_type_labels,
        modifier_labels=modifier_labels,
    )


class TypeScriptSemanticDataset(Dataset):
    def __init__(
        self,
        split: str,
        *,
        max_length: int = 512,
    ) -> None:
        if split not in {
            "train",
            "validation",
            "test",
        }:
            raise ValueError(
                f'Unknown dataset split "{split}".'
            )

        self.schema = load_schema()
        self.max_length = max_length

        split_path = TYPESCRIPT_DATASET_ROOT / f"{split}.json"

        samples = json.loads(
            split_path.read_text(encoding="utf-8")
        )

        self.documents = [
            encode_document(sample, self.schema)
            for sample in samples
        ]

        self.windows: list[WindowReference] = []

        for document_index, document in enumerate(self.documents):
            length = document.input_ids.shape[0]

            for start in range(0, length, self.max_length):
                end = min(
                    start + self.max_length,
                    length,
                )

                self.windows.append(
                    WindowReference(
                        document_index=document_index,
                        start=start,
                        end=end,
                    )
                )

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(
        self,
        index: int,
    ) -> dict[str, torch.Tensor]:
        window = self.windows[index]
        document = self.documents[window.document_index]

        length = window.end - window.start

        input_ids = torch.full(
            (self.max_length,),
            PAD_BYTE_ID,
            dtype=torch.long,
        )

        attention_mask = torch.zeros(
            (self.max_length,),
            dtype=torch.bool,
        )

        token_type_labels = torch.full(
            (self.max_length,),
            -100,
            dtype=torch.long,
        )

        modifier_labels = torch.zeros(
            (
                self.max_length,
                len(self.schema.modifiers),
            ),
            dtype=torch.float32,
        )

        input_ids[:length] = document.input_ids[
            window.start : window.end
        ]

        attention_mask[:length] = True

        token_type_labels[:length] = (
            document.token_type_labels[
                window.start : window.end
            ]
        )

        modifier_labels[:length] = (
            document.modifier_labels[
                window.start : window.end
            ].float()
        )

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_labels": token_type_labels,
            "modifier_labels": modifier_labels,
        }


def main() -> None:
    print("Neural Semantic Highlighting")
    print("TypeScript Training Dataset")
    print("")

    for split in (
        "train",
        "validation",
        "test",
    ):
        dataset = TypeScriptSemanticDataset(split)

        print(
            f"{split}: "
            f"{len(dataset.documents)} documents, "
            f"{len(dataset)} windows"
        )

    schema = load_schema()

    print("")
    print(
        f"Token classes: "
        f"{schema.number_of_token_classes} "
        f"(including O)"
    )
    print(
        f"Modifiers: {len(schema.modifiers)}"
    )
    print(f"Byte vocabulary: 257 (256 bytes + PAD)")


if __name__ == "__main__":
    main()
