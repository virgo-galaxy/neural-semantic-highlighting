from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import Dataset

from config import DEFAULT_MAX_LENGTH, DEFAULT_WINDOW_STRIDE


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = Path(
    os.environ.get(
        "NSH_DATASET_ROOT",
        Path.home() / "Datasets" / "neural-semantic-highlighting",
    )
)

TYPESCRIPT_DATASET_ROOT = DATASET_ROOT / "typescript"
SCHEMA_PATH = REPOSITORY_ROOT / "packs" / "typescript" / "schema.json"

CACHE_FORMAT = "nsh-typescript-cache"
CACHE_DIRECTORY = TYPESCRIPT_DATASET_ROOT / ".cache"

PAD_BYTE_ID = 256
IGNORE_LABEL_ID = -100

BOUNDARY_OUTSIDE_ID = 0
BOUNDARY_BEGIN_ID = 1
BOUNDARY_INSIDE_ID = 2
NUMBER_OF_BOUNDARY_CLASSES = 3


@dataclass(frozen=True)
class SemanticSchema:
    token_types: tuple[str, ...]
    modifiers: tuple[str, ...]

    @property
    def token_type_to_id(self) -> dict[str, int]:
        return {
            token_type: index
            for index, token_type in enumerate(self.token_types)
        }

    @property
    def modifier_to_id(self) -> dict[str, int]:
        return {
            modifier: index
            for index, modifier in enumerate(self.modifiers)
        }

    @property
    def number_of_token_types(self) -> int:
        return len(self.token_types)


@dataclass(frozen=True)
class GoldSpan:
    start: int
    end: int
    token_type: str
    modifiers: tuple[str, ...]


@dataclass(frozen=True)
class EncodedDocument:
    repository: str
    path: str
    document_kind: str
    source: str
    input_ids: torch.Tensor
    boundary_labels: torch.Tensor
    token_type_labels: torch.Tensor
    modifier_labels: torch.Tensor
    gold_spans: tuple[GoldSpan, ...]


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
    dict[int, int],
    tuple[int, ...],
]:
    utf16_to_utf8 = {0: 0}
    utf16_to_character_index = {0: 0}
    character_byte_starts: list[int] = []

    utf16_offset = 0
    utf8_offset = 0

    for character_index, character in enumerate(source):
        character_byte_starts.append(utf8_offset)

        utf16_offset += (
            len(character.encode("utf-16-le")) // 2
        )
        utf8_offset += len(character.encode("utf-8"))

        utf16_to_utf8[utf16_offset] = utf8_offset
        utf16_to_character_index[utf16_offset] = character_index + 1

    return (
        utf16_to_utf8,
        utf16_to_character_index,
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

    boundary_labels = torch.full(
        (len(source_bytes),),
        IGNORE_LABEL_ID,
        dtype=torch.long,
    )

    token_type_labels = torch.full(
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
        utf16_to_character_index,
        character_byte_starts,
    ) = build_source_boundaries(source)

    if character_byte_starts:
        character_start_tensor = torch.tensor(
            character_byte_starts,
            dtype=torch.long,
        )

        boundary_labels[
            character_start_tensor
        ] = BOUNDARY_OUTSIDE_ID

    token_type_to_id = schema.token_type_to_id
    modifier_to_id = schema.modifier_to_id

    gold_spans: list[GoldSpan] = []

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

        start_character_index = utf16_to_character_index[utf16_start]
        end_character_index = utf16_to_character_index[utf16_end]

        span_character_starts = character_byte_starts[
            start_character_index:end_character_index
        ]

        if not span_character_starts:
            raise ValueError(
                f'{sample["repository"]}/{sample["path"]}: '
                f"semantic span {utf16_start}-{utf16_end} contains no characters"
            )

        token_type = span["tokenType"]

        if token_type not in token_type_to_id:
            raise ValueError(
                f'{sample["repository"]}/{sample["path"]}: '
                f'unknown token type "{token_type}"'
            )

        token_type_id = token_type_to_id[token_type]

        boundary_labels[
            span_character_starts[0]
        ] = BOUNDARY_BEGIN_ID

        for byte_offset in span_character_starts[1:]:
            boundary_labels[
                byte_offset
            ] = BOUNDARY_INSIDE_ID

        for byte_offset in span_character_starts:
            token_type_labels[
                byte_offset
            ] = token_type_id

        span_modifiers = tuple(
            span.get("modifiers", [])
        )

        for modifier in span_modifiers:
            if modifier not in modifier_to_id:
                raise ValueError(
                    f'{sample["repository"]}/{sample["path"]}: '
                    f'unknown modifier "{modifier}"'
                )

            modifier_labels[
                span_character_starts[0],
                modifier_to_id[modifier],
            ] = 1

        gold_spans.append(
            GoldSpan(
                start=utf16_start,
                end=utf16_end,
                token_type=token_type,
                modifiers=span_modifiers,
            )
        )

    return EncodedDocument(
        repository=sample["repository"],
        path=sample["path"],
        document_kind=sample["documentKind"],
        source=source,
        input_ids=input_ids,
        boundary_labels=boundary_labels,
        token_type_labels=token_type_labels,
        modifier_labels=modifier_labels,
        gold_spans=tuple(gold_spans),
    )


def serialize_document(
    document: EncodedDocument,
) -> dict[str, Any]:
    return {
        "repository": document.repository,
        "path": document.path,
        "document_kind": document.document_kind,
        "source": document.source,
        "input_ids": document.input_ids,
        "boundary_labels": document.boundary_labels,
        "token_type_labels": document.token_type_labels,
        "modifier_labels": document.modifier_labels,
        "gold_spans": [
            {
                "start": span.start,
                "end": span.end,
                "token_type": span.token_type,
                "modifiers": list(span.modifiers),
            }
            for span in document.gold_spans
        ],
    }


def deserialize_document(
    data: dict[str, Any],
) -> EncodedDocument:
    return EncodedDocument(
        repository=data["repository"],
        path=data["path"],
        document_kind=data["document_kind"],
        source=data["source"],
        input_ids=data["input_ids"],
        boundary_labels=data["boundary_labels"],
        token_type_labels=data["token_type_labels"],
        modifier_labels=data["modifier_labels"],
        gold_spans=tuple(
            GoldSpan(
                start=span["start"],
                end=span["end"],
                token_type=span["token_type"],
                modifiers=tuple(span["modifiers"]),
            )
            for span in data["gold_spans"]
        ),
    )


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))

    hours, remainder = divmod(
        seconds,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if hours > 0:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def cache_key(
    split_bytes: bytes,
    schema_bytes: bytes,
) -> str:
    digest = hashlib.sha256()

    digest.update(
        CACHE_FORMAT.encode(
            "utf-8"
        )
    )

    digest.update(b"\0")
    digest.update(schema_bytes)
    digest.update(b"\0")
    digest.update(split_bytes)

    return digest.hexdigest()[:16]


def build_or_load_documents(
    split: str,
    schema: SemanticSchema,
    *,
    use_cache: bool,
    show_progress: bool,
) -> list[EncodedDocument]:
    split_path = (
        TYPESCRIPT_DATASET_ROOT
        / f"{split}.json"
    )

    if show_progress:
        print(
            f"Reading {split} split...",
            flush=True,
        )

    split_bytes = split_path.read_bytes()
    schema_bytes = SCHEMA_PATH.read_bytes()

    key = cache_key(
        split_bytes,
        schema_bytes,
    )

    cache_path = (
        CACHE_DIRECTORY
        / f"{split}-{key}.pt"
    )

    if (
        use_cache
        and cache_path.exists()
    ):
        started = time.perf_counter()

        if show_progress:
            print(
                f"Loading {split} cache: "
                f"{cache_path}",
                flush=True,
            )

        payload = torch.load(
            cache_path,
            map_location="cpu",
            weights_only=False,
        )

        if (
            payload.get("format")
            != CACHE_FORMAT
        ):
            raise ValueError(
                f"Unsupported cache format "
                f'in "{cache_path}".'
            )

        documents = [
            deserialize_document(
                document
            )
            for document in payload[
                "documents"
            ]
        ]

        if show_progress:
            elapsed = (
                time.perf_counter()
                - started
            )

            print(
                f"Loaded {split}: "
                f"{len(documents)} documents "
                f"in {format_duration(elapsed)}",
                flush=True,
            )

        return documents

    samples = json.loads(split_bytes)

    documents: list[
        EncodedDocument
    ] = []

    total = len(samples)
    started = time.perf_counter()

    if show_progress:
        print(
            f"Encoding {split}: "
            f"0/{total} docs | "
            f"0.0 docs/s | "
            f"ETA --:--",
            end="",
            flush=True,
        )

    for index, sample in enumerate(
        samples,
        start=1,
    ):
        documents.append(
            encode_document(
                sample,
                schema,
            )
        )

        if (
            show_progress
            and (
                index % 100 == 0
                or index == total
            )
        ):
            elapsed = (
                time.perf_counter()
                - started
            )

            rate = (
                index / elapsed
                if elapsed > 0
                else 0.0
            )

            remaining = (
                (total - index) / rate
                if rate > 0
                else 0.0
            )

            print(
                f"\r\033[K"
                f"Encoding {split}: "
                f"{index}/{total} docs | "
                f"{rate:,.1f} docs/s | "
                f"ETA {format_duration(remaining)}",
                end="",
                flush=True,
            )

    if show_progress:
        print()

    if use_cache:
        CACHE_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        if show_progress:
            print(
                f"Saving {split} cache: "
                f"{cache_path}",
                flush=True,
            )

        torch.save(
            {
                "format": (
                    CACHE_FORMAT
                ),
                "documents": [
                    serialize_document(
                        document
                    )
                    for document
                    in documents
                ],
            },
            cache_path,
        )

    if show_progress:
        elapsed = (
            time.perf_counter()
            - started
        )

        print(
            f"Prepared {split}: "
            f"{len(documents)} documents "
            f"in {format_duration(elapsed)}",
            flush=True,
        )

    return documents


def build_window_ranges(
    length: int,
    *,
    max_length: int,
    stride: int,
) -> list[tuple[int, int]]:
    if max_length <= 0:
        raise ValueError("max_length must be positive.")

    if stride <= 0 or stride > max_length:
        raise ValueError(
            "stride must be in the range "
            f"1..{max_length}, got {stride}."
        )

    if length <= 0:
        return []

    if length <= max_length:
        return [(0, length)]

    starts = [0]

    while starts[-1] + max_length < length:
        next_start = starts[-1] + stride

        # Keep the final window full-sized whenever possible so the
        # file tail gets the same amount of context as interior bytes.
        if next_start + max_length >= length:
            next_start = length - max_length

        if next_start <= starts[-1]:
            break

        starts.append(next_start)

    return [
        (start, min(start + max_length, length))
        for start in starts
    ]


def build_windows(
    document_index: int,
    document: EncodedDocument,
    *,
    max_length: int,
    stride: int,
) -> list[WindowReference]:
    return [
        WindowReference(
            document_index=document_index,
            start=start,
            end=end,
        )
        for start, end in build_window_ranges(
            int(document.input_ids.shape[0]),
            max_length=max_length,
            stride=stride,
        )
    ]


class TypeScriptSemanticDataset(Dataset):
    def __init__(
        self,
        split: str,
        *,
        max_length: int = DEFAULT_MAX_LENGTH,
        stride: int | None = None,
        use_cache: bool = True,
        show_progress: bool = True,
    ) -> None:
        if split not in {"train", "validation", "test"}:
            raise ValueError(f'Unknown dataset split "{split}".')

        self.schema = load_schema()
        self.max_length = max_length
        self.stride = (
            min(DEFAULT_WINDOW_STRIDE, max_length)
            if stride is None
            else stride
        )

        if self.stride <= 0 or self.stride > self.max_length:
            raise ValueError(
                "Dataset stride must be in the range "
                f"1..{self.max_length}, got {self.stride}."
            )

        self.documents = build_or_load_documents(
            split,
            self.schema,
            use_cache=use_cache,
            show_progress=show_progress,
        )

        self.windows = [
            window
            for document_index, document in enumerate(self.documents)
            for window in build_windows(
                document_index,
                document,
                max_length=self.max_length,
                stride=self.stride,
            )
        ]

        if show_progress:
            print(
                f"Built {split}: "
                f"{len(self.documents)} documents, "
                f"{len(self.windows)} windows "
                f"(window={self.max_length}, "
                f"stride={self.stride}, "
                f"overlap={self.max_length - self.stride})",
                flush=True,
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
        boundary_labels = torch.full(
            (self.max_length,),
            IGNORE_LABEL_ID,
            dtype=torch.long,
        )
        token_type_labels = torch.full(
            (self.max_length,),
            IGNORE_LABEL_ID,
            dtype=torch.long,
        )
        modifier_labels = torch.zeros(
            (self.max_length, len(self.schema.modifiers)),
            dtype=torch.float32,
        )

        source_slice = slice(window.start, window.end)
        input_ids[:length] = document.input_ids[source_slice]
        attention_mask[:length] = True
        boundary_labels[:length] = document.boundary_labels[source_slice]
        token_type_labels[:length] = document.token_type_labels[source_slice]
        modifier_labels[:length] = document.modifier_labels[source_slice].float()

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "boundary_labels": boundary_labels,
            "token_type_labels": token_type_labels,
            "modifier_labels": modifier_labels,
        }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-length", type=int, default=DEFAULT_MAX_LENGTH)
    parser.add_argument("--stride", type=int, default=DEFAULT_WINDOW_STRIDE)
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    print("Neural Semantic Highlighting")
    print("TypeScript Multitask Dataset")
    print("")

    for split in ("train", "validation", "test"):
        dataset = TypeScriptSemanticDataset(
            split,
            max_length=args.max_length,
            stride=args.stride,
            show_progress=True,
        )
        print(
            f"{split}: {len(dataset.documents)} documents, "
            f"{len(dataset)} windows, "
            f"stride={dataset.stride}"
        )

    schema = load_schema()
    print("")
    print("Boundary classes: 3 (O / B / I)")
    print(f"Token types: {schema.number_of_token_types}")
    print(f"Modifiers: {len(schema.modifiers)}")
    print("Byte vocabulary: 257 (256 bytes + PAD)")


if __name__ == "__main__":
    main()
