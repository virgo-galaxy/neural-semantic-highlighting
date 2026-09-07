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
IGNORE_LABEL_ID = -100
OUTSIDE_TAG_ID = 0


@dataclass(frozen=True)
class SemanticSchema:
    token_types: tuple[str, ...]
    modifiers: tuple[str, ...]

    @property
    def token_type_to_index(self) -> dict[str, int]:
        return {
            token_type: index
            for index, token_type in enumerate(self.token_types)
        }

    @property
    def modifier_to_index(self) -> dict[str, int]:
        return {
            modifier: index
            for index, modifier in enumerate(self.modifiers)
        }

    @property
    def number_of_token_types(self) -> int:
        return len(self.token_types)

    @property
    def number_of_semantic_tag_classes(self) -> int:
        return 1 + 2 * len(self.token_types)

    @property
    def semantic_tag_names(self) -> tuple[str, ...]:
        return (
            "O",
            *(f"B-{token_type}" for token_type in self.token_types),
            *(f"I-{token_type}" for token_type in self.token_types),
        )

    def begin_tag_id(self, token_type: str) -> int:
        return 1 + self.token_type_to_index[token_type]

    def inside_tag_id(self, token_type: str) -> int:
        return (
            1
            + self.number_of_token_types
            + self.token_type_to_index[token_type]
        )

    def decode_tag_id(self, tag_id: int) -> tuple[str, str] | None:
        if tag_id == OUTSIDE_TAG_ID:
            return None

        if 1 <= tag_id <= self.number_of_token_types:
            return (
                "B",
                self.token_types[tag_id - 1],
            )

        inside_index = (
            tag_id
            - 1
            - self.number_of_token_types
        )

        if 0 <= inside_index < self.number_of_token_types:
            return (
                "I",
                self.token_types[inside_index],
            )

        raise ValueError(f"Unknown semantic tag id {tag_id}.")

    def collapse_tag_id_to_token_type_id(
        self,
        tag_id: int,
    ) -> int:
        if tag_id <= OUTSIDE_TAG_ID:
            return OUTSIDE_TAG_ID

        return (
            (tag_id - 1)
            % self.number_of_token_types
        ) + 1


@dataclass(frozen=True)
class EncodedDocument:
    repository: str
    path: str
    document_kind: str
    source: str
    input_ids: torch.Tensor
    semantic_tag_labels: torch.Tensor
    modifier_labels: torch.Tensor


@dataclass(frozen=True)
class WindowReference:
    document_index: int
    start: int
    end: int


def load_schema() -> SemanticSchema:
    data = json.loads(
        SCHEMA_PATH.read_text(encoding="utf-8")
    )

    return SemanticSchema(
        token_types=tuple(
            entry["id"]
            for entry in data["tokenTypes"]
        ),
        modifiers=tuple(
            entry["id"]
            for entry in data["tokenModifiers"]
        ),
    )


def build_source_boundaries(
    source: str,
) -> tuple[
    dict[int, int],
    tuple[int, ...],
]:
    utf16_to_utf8 = {
        0: 0,
    }

    character_byte_starts: list[int] = []

    utf16_offset = 0
    utf8_offset = 0

    for character in source:
        character_byte_starts.append(
            utf8_offset
        )

        utf16_offset += (
            len(
                character.encode(
                    "utf-16-le"
                )
            )
            // 2
        )

        utf8_offset += len(
            character.encode("utf-8")
        )

        utf16_to_utf8[
            utf16_offset
        ] = utf8_offset

    return (
        utf16_to_utf8,
        tuple(character_byte_starts),
    )


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

    semantic_tag_labels = torch.full(
        (len(source_bytes),),
        IGNORE_LABEL_ID,
        dtype=torch.long,
    )

    modifier_labels = torch.zeros(
        (
            len(source_bytes),
            len(schema.modifiers),
        ),
        dtype=torch.uint8,
    )

    (
        utf16_to_utf8,
        character_byte_starts,
    ) = build_source_boundaries(source)

    # Only the first byte of each Unicode character is supervised.
    # UTF-8 continuation bytes remain part of the model input/context,
    # but do not create duplicate semantic decisions.
    if character_byte_starts:
        semantic_tag_labels[
            torch.tensor(
                character_byte_starts,
                dtype=torch.long,
            )
        ] = OUTSIDE_TAG_ID

    modifier_to_index = (
        schema.modifier_to_index
    )

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

        byte_start = utf16_to_utf8[
            utf16_start
        ]

        byte_end = utf16_to_utf8[
            utf16_end
        ]

        token_type = span["tokenType"]

        if (
            token_type
            not in schema.token_type_to_index
        ):
            raise ValueError(
                f'{sample["repository"]}/{sample["path"]}: '
                f'unknown token type "{token_type}"'
            )

        span_character_starts = [
            byte_offset
            for byte_offset
            in character_byte_starts
            if byte_start
            <= byte_offset
            < byte_end
        ]

        if not span_character_starts:
            raise ValueError(
                f'{sample["repository"]}/{sample["path"]}: '
                f"semantic span {utf16_start}-{utf16_end} "
                "contains no Unicode character boundary"
            )

        semantic_tag_labels[
            span_character_starts[0]
        ] = schema.begin_tag_id(
            token_type
        )

        for byte_offset in (
            span_character_starts[1:]
        ):
            semantic_tag_labels[
                byte_offset
            ] = schema.inside_tag_id(
                token_type
            )

        for modifier in span.get(
            "modifiers",
            [],
        ):
            if (
                modifier
                not in modifier_to_index
            ):
                raise ValueError(
                    f'{sample["repository"]}/{sample["path"]}: '
                    f'unknown modifier "{modifier}"'
                )

            modifier_labels[
                span_character_starts[0],
                modifier_to_index[modifier],
            ] = 1

    return EncodedDocument(
        repository=sample["repository"],
        path=sample["path"],
        document_kind=sample[
            "documentKind"
        ],
        source=source,
        input_ids=input_ids,
        semantic_tag_labels=(
            semantic_tag_labels
        ),
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

        split_path = (
            TYPESCRIPT_DATASET_ROOT
            / f"{split}.json"
        )

        samples = json.loads(
            split_path.read_text(
                encoding="utf-8"
            )
        )

        self.documents = [
            encode_document(
                sample,
                self.schema,
            )
            for sample in samples
        ]

        self.windows: list[
            WindowReference
        ] = []

        for (
            document_index,
            document,
        ) in enumerate(self.documents):
            length = (
                document.input_ids.shape[0]
            )

            for start in range(
                0,
                length,
                self.max_length,
            ):
                end = min(
                    start
                    + self.max_length,
                    length,
                )

                self.windows.append(
                    WindowReference(
                        document_index=(
                            document_index
                        ),
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

        document = self.documents[
            window.document_index
        ]

        length = (
            window.end - window.start
        )

        input_ids = torch.full(
            (self.max_length,),
            PAD_BYTE_ID,
            dtype=torch.long,
        )

        attention_mask = torch.zeros(
            (self.max_length,),
            dtype=torch.bool,
        )

        semantic_tag_labels = torch.full(
            (self.max_length,),
            IGNORE_LABEL_ID,
            dtype=torch.long,
        )

        modifier_labels = torch.zeros(
            (
                self.max_length,
                len(self.schema.modifiers),
            ),
            dtype=torch.float32,
        )

        input_ids[:length] = (
            document.input_ids[
                window.start : window.end
            ]
        )

        attention_mask[:length] = True

        semantic_tag_labels[:length] = (
            document.semantic_tag_labels[
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
            "attention_mask": (
                attention_mask
            ),
            "semantic_tag_labels": (
                semantic_tag_labels
            ),
            "modifier_labels": (
                modifier_labels
            ),
        }


def main() -> None:
    print(
        "Neural Semantic Highlighting"
    )
    print(
        "TypeScript BIO Training Dataset"
    )
    print("")

    for split in (
        "train",
        "validation",
        "test",
    ):
        dataset = (
            TypeScriptSemanticDataset(
                split
            )
        )

        print(
            f"{split}: "
            f"{len(dataset.documents)} documents, "
            f"{len(dataset)} windows"
        )

    schema = load_schema()

    print("")
    print(
        "Semantic tag classes: "
        f"{schema.number_of_semantic_tag_classes} "
        "(O + B/I for each token type)"
    )
    print(
        f"Token types: "
        f"{schema.number_of_token_types}"
    )
    print(
        f"Modifiers: "
        f"{len(schema.modifiers)}"
    )
    print(
        "Byte vocabulary: "
        "257 (256 bytes + PAD)"
    )


if __name__ == "__main__":
    main()
