from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import os
import time
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

CACHE_FORMAT_VERSION = "nsh-typescript-v2-multitask-cache-v1"
CACHE_DIRECTORY = TYPESCRIPT_DATASET_ROOT / ".cache" / "v2-multitask"

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


@dataclass(frozen=True)
class WindowingStats:
    adjusted_span_cuts: int = 0
    adjusted_character_cuts: int = 0
    unavoidable_inside_starts: int = 0
    unprotected_inside_starts: int = 0
    total_shift_bytes: int = 0
    max_shift_bytes: int = 0
    shift_bytes: tuple[int, ...] = ()

    @property
    def p95_shift_bytes(self) -> int:
        if not self.shift_bytes:
            return 0

        ordered = sorted(self.shift_bytes)
        index = max(
            0,
            min(
                len(ordered) - 1,
                (95 * len(ordered) + 99) // 100 - 1,
            ),
        )
        return ordered[index]


@dataclass(frozen=True)
class HardStringStats:
    eligible_spans: int = 0
    over_context_spans: int = 0
    generated_windows: int = 0
    min_span_bytes: int = 0
    first_inside_offset_bytes: int = 0
    step_bytes: int = 0
    min_remaining_bytes: int = 0


@dataclass(frozen=True)
class HardRegexpStats:
    regexp_spans: int = 0
    over_context_spans: int = 0
    positive_windows: int = 0
    operator_slash_candidates: int = 0
    negative_windows: int = 0
    generated_windows: int = 0
    context_before_bytes: int = 0
    negative_divisor: int = 0


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
        CACHE_FORMAT_VERSION.encode(
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
            != CACHE_FORMAT_VERSION
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
                    CACHE_FORMAT_VERSION
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


def _valid_character_starts(
    document: EncodedDocument,
) -> list[int]:
    starts = torch.nonzero(
        document.boundary_labels
        != IGNORE_LABEL_ID,
        as_tuple=False,
    ).flatten().tolist()

    starts.append(
        int(document.input_ids.shape[0])
    )

    return starts


def _snap_cut_to_character_boundary(
    target: int,
    character_starts: list[int],
) -> int:
    index = bisect.bisect_right(
        character_starts,
        target,
    ) - 1

    return character_starts[max(0, index)]


def _find_active_span_start(
    document: EncodedDocument,
    cut: int,
    character_starts: list[int],
    *,
    protected_token_type_ids: frozenset[int] | None,
) -> int | None:
    if cut >= document.input_ids.shape[0]:
        return None

    if (
        int(document.boundary_labels[cut].item())
        != BOUNDARY_INSIDE_ID
    ):
        return None

    token_type_id = int(
        document.token_type_labels[cut].item()
    )

    if (
        protected_token_type_ids is not None
        and token_type_id not in protected_token_type_ids
    ):
        return None

    # Walk left over character starts until we reach the B
    # that opened the currently active semantic span.
    position_index = max(
        0,
        bisect.bisect_left(
            character_starts,
            cut,
        ) - 1,
    )

    for index in range(position_index, -1, -1):
        position = character_starts[index]

        if position >= document.input_ids.shape[0]:
            continue

        label = int(
            document.boundary_labels[position].item()
        )

        if label == BOUNDARY_BEGIN_ID:
            return position

        if label == BOUNDARY_OUTSIDE_ID:
            return None

    return None


def build_fixed_windows(
    document_index: int,
    document: EncodedDocument,
    *,
    max_length: int,
    stride: int,
) -> list[WindowReference]:
    length = int(document.input_ids.shape[0])

    return [
        WindowReference(
            document_index=document_index,
            start=start,
            end=min(start + max_length, length),
        )
        for start in range(0, length, stride)
    ]


def build_span_aware_windows(
    document_index: int,
    document: EncodedDocument,
    *,
    max_length: int,
    protected_token_type_ids: frozenset[int] | None = None,
) -> tuple[list[WindowReference], WindowingStats]:
    length = int(document.input_ids.shape[0])

    if length == 0:
        return [], WindowingStats()

    character_starts = _valid_character_starts(
        document
    )

    windows: list[WindowReference] = []
    adjusted_span_cuts = 0
    adjusted_character_cuts = 0
    unavoidable_inside_starts = 0
    unprotected_inside_starts = 0
    shifts: list[int] = []

    cursor = 0

    while cursor < length:
        target = min(
            cursor + max_length,
            length,
        )

        if target == length:
            end = length
        else:
            end = _snap_cut_to_character_boundary(
                target,
                character_starts,
            )

            if end != target:
                adjusted_character_cuts += 1

            active_span_start = (
                _find_active_span_start(
                    document,
                    end,
                    character_starts,
                    protected_token_type_ids=(
                        protected_token_type_ids
                    ),
                )
            )

            if (
                active_span_start is not None
                and active_span_start > cursor
            ):
                shift = end - active_span_start
                end = active_span_start
                adjusted_span_cuts += 1
                shifts.append(shift)

        if end <= cursor:
            # This can only happen for an unavoidable span that
            # itself is longer than max_length. In that case we
            # must make progress even though the next window may
            # begin inside the span.
            end = _snap_cut_to_character_boundary(
                min(cursor + max_length, length),
                character_starts,
            )

            if end <= cursor:
                end = min(
                    cursor + max_length,
                    length,
                )

        windows.append(
            WindowReference(
                document_index=document_index,
                start=cursor,
                end=end,
            )
        )

        cursor = end

        if (
            cursor < length
            and cursor < document.boundary_labels.shape[0]
            and int(
                document.boundary_labels[cursor].item()
            ) == BOUNDARY_INSIDE_ID
        ):
            token_type_id = int(
                document.token_type_labels[cursor].item()
            )

            if (
                protected_token_type_ids is None
                or token_type_id in protected_token_type_ids
            ):
                unavoidable_inside_starts += 1
            else:
                unprotected_inside_starts += 1

    return (
        windows,
        WindowingStats(
            adjusted_span_cuts=adjusted_span_cuts,
            adjusted_character_cuts=(
                adjusted_character_cuts
            ),
            unavoidable_inside_starts=(
                unavoidable_inside_starts
            ),
            unprotected_inside_starts=(
                unprotected_inside_starts
            ),
            total_shift_bytes=sum(shifts),
            max_shift_bytes=max(shifts, default=0),
            shift_bytes=tuple(shifts),
        ),
    )


def build_dual_view_windows(
    document_index: int,
    document: EncodedDocument,
    *,
    max_length: int,
) -> tuple[
    list[WindowReference],
    WindowingStats,
    int,
    int,
]:
    # Keep both complete views. The fixed view teaches recovery when a
    # runtime window starts in the middle of a span; the span-aware view
    # teaches clean span starts and ends. We intentionally do not dedupe
    # identical windows: dual-view training runs for half as many epochs,
    # so identical regions keep roughly the same total exposure budget.
    fixed_windows = build_fixed_windows(
        document_index,
        document,
        max_length=max_length,
        stride=max_length,
    )

    span_aware_windows, stats = build_span_aware_windows(
        document_index,
        document,
        max_length=max_length,
        protected_token_type_ids=None,
    )

    return (
        fixed_windows + span_aware_windows,
        stats,
        len(fixed_windows),
        len(span_aware_windows),
    )


def build_hard_string_windows(
    document_index: int,
    document: EncodedDocument,
    *,
    max_length: int,
    string_token_type: str = "string",
) -> tuple[list[WindowReference], HardStringStats]:
    """Build a small deterministic continuation curriculum for long strings.

    The ordinary fixed view already teaches arbitrary runtime cuts, while the
    span-aware view teaches clean boundaries. This third view only adds novel
    starts *inside* long Gold string spans so code-looking template/string
    bodies are seen without their opener more often.
    """

    length = int(document.input_ids.shape[0])

    if length == 0:
        return [], HardStringStats()

    min_span_bytes = max(2, max_length // 2)
    first_inside_offset = max(1, max_length // 4)
    step_bytes = max(1, max_length // 2)
    min_remaining_bytes = max(1, max_length // 8)

    (
        utf16_to_utf8,
        _,
        character_starts_tuple,
    ) = build_source_boundaries(document.source)

    character_starts = list(character_starts_tuple)
    character_starts.append(length)

    windows: list[WindowReference] = []
    eligible_spans = 0
    over_context_spans = 0

    for span in document.gold_spans:
        if span.token_type != string_token_type:
            continue

        span_start = utf16_to_utf8.get(span.start)
        span_end = utf16_to_utf8.get(span.end)

        if span_start is None or span_end is None:
            continue

        span_length = span_end - span_start

        if span_length < min_span_bytes:
            continue

        eligible_spans += 1

        if span_length > max_length:
            over_context_spans += 1

        candidate = span_start + first_inside_offset
        seen_starts: set[int] = set()

        while candidate < span_end:
            remaining = span_end - candidate

            if remaining < min_remaining_bytes:
                break

            start = _snap_cut_to_character_boundary(
                candidate,
                character_starts,
            )

            if start <= span_start:
                candidate += step_bytes
                continue

            if start >= span_end:
                break

            if start in seen_starts:
                candidate += step_bytes
                continue

            seen_starts.add(start)

            windows.append(
                WindowReference(
                    document_index=document_index,
                    start=start,
                    end=min(start + max_length, length),
                )
            )

            candidate += step_bytes

    return (
        windows,
        HardStringStats(
            eligible_spans=eligible_spans,
            over_context_spans=over_context_spans,
            generated_windows=len(windows),
            min_span_bytes=min_span_bytes,
            first_inside_offset_bytes=(
                first_inside_offset
            ),
            step_bytes=step_bytes,
            min_remaining_bytes=min_remaining_bytes,
        ),
    )


def build_dual_view_hard_string_windows(
    document_index: int,
    document: EncodedDocument,
    *,
    max_length: int,
) -> tuple[
    list[WindowReference],
    WindowingStats,
    HardStringStats,
    int,
    int,
    int,
]:
    (
        dual_view_windows,
        windowing_stats,
        fixed_count,
        span_aware_count,
    ) = build_dual_view_windows(
        document_index,
        document,
        max_length=max_length,
    )

    hard_string_windows, hard_string_stats = (
        build_hard_string_windows(
            document_index,
            document,
            max_length=max_length,
        )
    )

    return (
        dual_view_windows + hard_string_windows,
        windowing_stats,
        hard_string_stats,
        fixed_count,
        span_aware_count,
        len(hard_string_windows),
    )


def _window_around_anchor(
    document_index: int,
    *,
    anchor: int,
    length: int,
    max_length: int,
    character_starts: list[int],
    context_before: int,
) -> WindowReference:
    target = max(0, anchor - context_before)
    start = _snap_cut_to_character_boundary(
        target,
        character_starts,
    )

    return WindowReference(
        document_index=document_index,
        start=start,
        end=min(start + max_length, length),
    )


def _evenly_select_positions(
    positions: list[int],
    limit: int,
) -> list[int]:
    if limit <= 0 or not positions:
        return []

    if len(positions) <= limit:
        return list(positions)

    if limit == 1:
        return [positions[len(positions) // 2]]

    last = len(positions) - 1
    indexes = [
        (index * last) // (limit - 1)
        for index in range(limit)
    ]

    return [positions[index] for index in indexes]


def build_hard_regexp_windows(
    document_index: int,
    document: EncodedDocument,
    *,
    max_length: int,
    operator_token_type_id: int,
    regexp_token_type: str = "regexp",
    negative_divisor: int = 1,
) -> tuple[list[WindowReference], HardRegexpStats]:
    """Upweight exact regexp boundaries plus a small slash-negative set.

    Every Gold regexp contributes one context-rich view with the opener and
    closing slash/flags visible when the span fits in one context. Very long
    regexps also get an end-boundary view. To avoid teaching that every slash
    starts a regexp, Gold operator slashes (division and `/=`) are also added
    as hard negatives. These are scarce in the training corpus, so the default
    keeps every candidate instead of restricting negatives to documents that
    already contain a regexp.
    """

    length = int(document.input_ids.shape[0])

    if length == 0:
        return [], HardRegexpStats()

    context_before = max(1, max_length // 4)
    negative_divisor = max(1, negative_divisor)

    (
        utf16_to_utf8,
        _,
        character_starts_tuple,
    ) = build_source_boundaries(document.source)

    character_starts = list(character_starts_tuple)
    character_starts.append(length)

    positive_windows: list[WindowReference] = []
    regexp_span_count = 0
    over_context_spans = 0

    for span in document.gold_spans:
        if span.token_type != regexp_token_type:
            continue

        span_start = utf16_to_utf8.get(span.start)
        span_end = utf16_to_utf8.get(span.end)

        if span_start is None or span_end is None:
            continue

        regexp_span_count += 1

        first_window = _window_around_anchor(
            document_index,
            anchor=span_start,
            length=length,
            max_length=max_length,
            character_starts=character_starts,
            context_before=context_before,
        )
        positive_windows.append(first_window)

        if span_end - span_start > max_length:
            over_context_spans += 1
            end_target = max(
                0,
                span_end - max_length + context_before,
            )
            end_start = _snap_cut_to_character_boundary(
                end_target,
                character_starts,
            )
            end_window = WindowReference(
                document_index=document_index,
                start=end_start,
                end=min(end_start + max_length, length),
            )

            if (
                end_window.start != first_window.start
                or end_window.end != first_window.end
            ):
                positive_windows.append(end_window)

    operator_slash_candidates: list[int] = []

    for character, byte_start in zip(
        document.source,
        character_starts_tuple,
        strict=True,
    ):
        if character != "/":
            continue

        if byte_start >= document.token_type_labels.shape[0]:
            continue

        if int(document.token_type_labels[byte_start].item()) != operator_token_type_id:
            continue

        operator_slash_candidates.append(byte_start)

    negative_budget = 0

    if operator_slash_candidates:
        negative_budget = max(
            1,
            len(operator_slash_candidates) // negative_divisor,
        )

    selected_negative_positions = _evenly_select_positions(
        operator_slash_candidates,
        min(negative_budget, len(operator_slash_candidates)),
    )

    negative_windows = [
        _window_around_anchor(
            document_index,
            anchor=position,
            length=length,
            max_length=max_length,
            character_starts=character_starts,
            context_before=context_before,
        )
        for position in selected_negative_positions
    ]

    windows = positive_windows + negative_windows

    return (
        windows,
        HardRegexpStats(
            regexp_spans=regexp_span_count,
            over_context_spans=over_context_spans,
            positive_windows=len(positive_windows),
            operator_slash_candidates=len(operator_slash_candidates),
            negative_windows=len(negative_windows),
            generated_windows=len(windows),
            context_before_bytes=context_before,
            negative_divisor=negative_divisor,
        ),
    )


def build_dual_view_hard_string_regexp_windows(
    document_index: int,
    document: EncodedDocument,
    *,
    max_length: int,
    operator_token_type_id: int,
) -> tuple[
    list[WindowReference],
    WindowingStats,
    HardStringStats,
    HardRegexpStats,
    int,
    int,
    int,
    int,
]:
    (
        base_windows,
        windowing_stats,
        hard_string_stats,
        fixed_count,
        span_aware_count,
        hard_string_count,
    ) = build_dual_view_hard_string_windows(
        document_index,
        document,
        max_length=max_length,
    )

    hard_regexp_windows, hard_regexp_stats = (
        build_hard_regexp_windows(
            document_index,
            document,
            max_length=max_length,
            operator_token_type_id=operator_token_type_id,
        )
    )

    return (
        base_windows + hard_regexp_windows,
        windowing_stats,
        hard_string_stats,
        hard_regexp_stats,
        fixed_count,
        span_aware_count,
        hard_string_count,
        len(hard_regexp_windows),
    )


class TypeScriptSemanticDataset(Dataset):
    def __init__(
        self,
        split: str,
        *,
        max_length: int = 512,
        stride: int | None = None,
        window_strategy: str = "fixed",
        use_cache: bool = True,
        show_progress: bool = True,
    ) -> None:
        if split not in {
            "train",
            "validation",
            "test",
        }:
            raise ValueError(
                f'Unknown dataset split "{split}".'
            )

        if window_strategy not in {
            "fixed",
            "span-aware",
            "string-aware",
            "dual-view",
            "dual-view-hard-string",
            "dual-view-hard-string-regexp",
        }:
            raise ValueError(
                "Window strategy must be fixed, span-aware, "
                "string-aware, dual-view, dual-view-hard-string, "
                "or dual-view-hard-string-regexp, got "
                f"{window_strategy!r}."
            )

        self.schema = load_schema()
        self.max_length = max_length
        self.window_strategy = window_strategy
        self.stride = (
            max_length
            if stride is None
            else stride
        )

        if (
            self.stride <= 0
            or self.stride > self.max_length
        ):
            raise ValueError(
                "Dataset stride must be in the range "
                f"1..{self.max_length}, got {self.stride}."
            )

        if (
            self.window_strategy in {
                "span-aware",
                "string-aware",
                "dual-view",
                "dual-view-hard-string",
                "dual-view-hard-string-regexp",
            }
            and self.stride != self.max_length
        ):
            raise ValueError(
                "Adaptive windowing uses a dynamic cursor "
                "and requires stride=max_length. "
                f"Got stride={self.stride}, "
                f"max_length={self.max_length}."
            )

        self.documents = (
            build_or_load_documents(
                split,
                self.schema,
                use_cache=use_cache,
                show_progress=(
                    show_progress
                ),
            )
        )

        self.windows: list[WindowReference] = []
        self.fixed_view_window_count = 0
        self.span_aware_view_window_count = 0
        self.hard_string_window_count = 0
        self.hard_string_eligible_span_count = 0
        self.hard_string_over_context_span_count = 0
        self.hard_string_stats = HardStringStats()
        self.hard_regexp_window_count = 0
        self.hard_regexp_span_count = 0
        self.hard_regexp_over_context_span_count = 0
        self.hard_regexp_positive_window_count = 0
        self.hard_regexp_operator_slash_candidate_count = 0
        self.hard_regexp_negative_window_count = 0
        self.hard_regexp_stats = HardRegexpStats()

        total_adjusted_span_cuts = 0
        total_adjusted_character_cuts = 0
        total_unavoidable_inside_starts = 0
        total_unprotected_inside_starts = 0
        all_shifts: list[int] = []

        for (
            document_index,
            document,
        ) in enumerate(self.documents):
            if self.window_strategy == "fixed":
                document_windows = build_fixed_windows(
                    document_index,
                    document,
                    max_length=self.max_length,
                    stride=self.stride,
                )
                stats = WindowingStats()
                hard_string_stats = HardStringStats()
                hard_regexp_stats = HardRegexpStats()
                fixed_view_count = len(document_windows)
                span_aware_view_count = 0
                hard_string_view_count = 0
                hard_regexp_view_count = 0
            elif self.window_strategy == "dual-view":
                (
                    document_windows,
                    stats,
                    fixed_view_count,
                    span_aware_view_count,
                ) = build_dual_view_windows(
                    document_index,
                    document,
                    max_length=self.max_length,
                )
                hard_string_stats = HardStringStats()
                hard_regexp_stats = HardRegexpStats()
                hard_string_view_count = 0
                hard_regexp_view_count = 0
            elif self.window_strategy == "dual-view-hard-string":
                (
                    document_windows,
                    stats,
                    hard_string_stats,
                    fixed_view_count,
                    span_aware_view_count,
                    hard_string_view_count,
                ) = build_dual_view_hard_string_windows(
                    document_index,
                    document,
                    max_length=self.max_length,
                )
                hard_regexp_stats = HardRegexpStats()
                hard_regexp_view_count = 0
            elif self.window_strategy == "dual-view-hard-string-regexp":
                (
                    document_windows,
                    stats,
                    hard_string_stats,
                    hard_regexp_stats,
                    fixed_view_count,
                    span_aware_view_count,
                    hard_string_view_count,
                    hard_regexp_view_count,
                ) = build_dual_view_hard_string_regexp_windows(
                    document_index,
                    document,
                    max_length=self.max_length,
                    operator_token_type_id=(
                        self.schema.token_type_to_id["operator"]
                    ),
                )
            else:
                protected_token_type_ids = None

                if self.window_strategy == "string-aware":
                    protected_token_type_ids = frozenset(
                        {
                            self.schema.token_type_to_id[
                                "string"
                            ]
                        }
                    )

                (
                    document_windows,
                    stats,
                ) = build_span_aware_windows(
                    document_index,
                    document,
                    max_length=self.max_length,
                    protected_token_type_ids=(
                        protected_token_type_ids
                    ),
                )
                fixed_view_count = 0
                span_aware_view_count = len(document_windows)
                hard_string_stats = HardStringStats()
                hard_regexp_stats = HardRegexpStats()
                hard_string_view_count = 0
                hard_regexp_view_count = 0

            self.windows.extend(document_windows)
            self.fixed_view_window_count += fixed_view_count
            self.span_aware_view_window_count += (
                span_aware_view_count
            )
            self.hard_string_window_count += (
                hard_string_view_count
            )
            self.hard_string_eligible_span_count += (
                hard_string_stats.eligible_spans
            )
            self.hard_string_over_context_span_count += (
                hard_string_stats.over_context_spans
            )
            if hard_string_stats.min_span_bytes:
                self.hard_string_stats = hard_string_stats
            self.hard_regexp_window_count += hard_regexp_view_count
            self.hard_regexp_span_count += hard_regexp_stats.regexp_spans
            self.hard_regexp_over_context_span_count += (
                hard_regexp_stats.over_context_spans
            )
            self.hard_regexp_positive_window_count += (
                hard_regexp_stats.positive_windows
            )
            self.hard_regexp_operator_slash_candidate_count += (
                hard_regexp_stats.operator_slash_candidates
            )
            self.hard_regexp_negative_window_count += (
                hard_regexp_stats.negative_windows
            )
            if hard_regexp_stats.context_before_bytes:
                self.hard_regexp_stats = hard_regexp_stats
            total_adjusted_span_cuts += (
                stats.adjusted_span_cuts
            )
            total_adjusted_character_cuts += (
                stats.adjusted_character_cuts
            )
            total_unavoidable_inside_starts += (
                stats.unavoidable_inside_starts
            )
            total_unprotected_inside_starts += (
                stats.unprotected_inside_starts
            )
            all_shifts.extend(stats.shift_bytes)

        self.windowing_stats = WindowingStats(
            adjusted_span_cuts=(
                total_adjusted_span_cuts
            ),
            adjusted_character_cuts=(
                total_adjusted_character_cuts
            ),
            unavoidable_inside_starts=(
                total_unavoidable_inside_starts
            ),
            unprotected_inside_starts=(
                total_unprotected_inside_starts
            ),
            total_shift_bytes=sum(all_shifts),
            max_shift_bytes=max(all_shifts, default=0),
            shift_bytes=tuple(all_shifts),
        )

        if show_progress:
            print(
                f"Built {split}: "
                f"{len(self.documents)} documents, "
                f"{len(self.windows)} windows "
                f"(window={self.max_length}, "
                f"strategy={self.window_strategy}, "
                f"stride={self.stride})",
                flush=True,
            )

            if self.window_strategy in {
                "dual-view",
                "dual-view-hard-string",
                "dual-view-hard-string-regexp",
            }:
                total_views = max(1, len(self.windows))
                mix = (
                    "  dual-view mix: "
                    f"fixed={self.fixed_view_window_count} "
                    f"({self.fixed_view_window_count / total_views:.2%}), "
                    "span-aware="
                    f"{self.span_aware_view_window_count} "
                    f"({self.span_aware_view_window_count / total_views:.2%})"
                )

                if self.window_strategy in {
                    "dual-view-hard-string",
                    "dual-view-hard-string-regexp",
                }:
                    mix += (
                        ", hard-string="
                        f"{self.hard_string_window_count} "
                        f"({self.hard_string_window_count / total_views:.2%})"
                    )

                if self.window_strategy == "dual-view-hard-string-regexp":
                    mix += (
                        ", hard-regexp="
                        f"{self.hard_regexp_window_count} "
                        f"({self.hard_regexp_window_count / total_views:.2%})"
                    )

                print(mix, flush=True)

                if self.window_strategy in {
                    "dual-view-hard-string",
                    "dual-view-hard-string-regexp",
                }:
                    hard = self.hard_string_stats
                    print(
                        "  hard-string curriculum: "
                        f"eligible-spans={self.hard_string_eligible_span_count}, "
                        "over-context-spans="
                        f"{self.hard_string_over_context_span_count}, "
                        f"windows={self.hard_string_window_count}, "
                        f"min-span={hard.min_span_bytes}B, "
                        "first-inside="
                        f"{hard.first_inside_offset_bytes}B, "
                        f"step={hard.step_bytes}B, "
                        f"min-remaining={hard.min_remaining_bytes}B",
                        flush=True,
                    )

                if self.window_strategy == "dual-view-hard-string-regexp":
                    hard_regexp = self.hard_regexp_stats
                    print(
                        "  hard-regexp curriculum: "
                        f"regexp-spans={self.hard_regexp_span_count}, "
                        "over-context-spans="
                        f"{self.hard_regexp_over_context_span_count}, "
                        "positive-windows="
                        f"{self.hard_regexp_positive_window_count}, "
                        "operator-slash-candidates="
                        f"{self.hard_regexp_operator_slash_candidate_count}, "
                        "negative-windows="
                        f"{self.hard_regexp_negative_window_count}, "
                        f"windows={self.hard_regexp_window_count}, "
                        "context-before="
                        f"{hard_regexp.context_before_bytes}B, "
                        "negative-divisor="
                        f"{hard_regexp.negative_divisor}",
                        flush=True,
                    )

            if self.window_strategy in {
                "span-aware",
                "string-aware",
                "dual-view",
                "dual-view-hard-string",
                "dual-view-hard-string-regexp",
            }:
                stats = self.windowing_stats
                label = (
                    "dual-view span-aware"
                    if self.window_strategy in {
                        "dual-view",
                        "dual-view-hard-string",
                        "dual-view-hard-string-regexp",
                    }
                    else self.window_strategy
                )
                print(
                    f"  {label} cuts: "
                    f"adjusted={stats.adjusted_span_cuts}, "
                    "unavoidable-protected-inside-starts="
                    f"{stats.unavoidable_inside_starts}, "
                    "allowed-unprotected-inside-starts="
                    f"{stats.unprotected_inside_starts}, "
                    "avg-shift="
                    f"{(stats.total_shift_bytes / max(1, stats.adjusted_span_cuts)):.1f}B, "
                    f"p95-shift={stats.p95_shift_bytes}B, "
                    f"max-shift={stats.max_shift_bytes}B",
                    flush=True,
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
            (
                self.max_length,
                len(self.schema.modifiers),
            ),
            dtype=torch.float32,
        )

        input_ids[:length] = (
            document.input_ids[
                window.start:window.end
            ]
        )

        attention_mask[:length] = True

        boundary_labels[:length] = (
            document.boundary_labels[
                window.start:window.end
            ]
        )

        token_type_labels[:length] = (
            document.token_type_labels[
                window.start:window.end
            ]
        )

        modifier_labels[:length] = (
            document.modifier_labels[
                window.start:window.end
            ].float()
        )

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "boundary_labels": boundary_labels,
            "token_type_labels": token_type_labels,
            "modifier_labels": modifier_labels,
        }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
    )

    parser.add_argument(
        "--train-stride",
        type=int,
        default=None,
        help=(
            "Train-window stride in UTF-8 bytes. "
            "Defaults to max_length (no overlap). "
            "Validation and test remain non-overlapping."
        ),
    )

    parser.add_argument(
        "--train-window-strategy",
        choices=(
            "fixed",
            "span-aware",
            "string-aware",
            "dual-view",
            "dual-view-hard-string",
            "dual-view-hard-string-regexp",
        ),
        default="fixed",
        help=(
            "Train window strategy. span-aware protects all "
            "Gold spans. string-aware only protects string "
            "spans. dual-view keeps both the full fixed view "
            "and the full span-aware view for mixed training. "
            "dual-view-hard-string adds a small deterministic "
            "continuation curriculum for string spans at least "
            "half a context window long. "
            "dual-view-hard-string-regexp additionally upweights "
            "exact regexp boundaries and a controlled subset of "
            "operator-slash negatives."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    print(
        "Neural Semantic Highlighting"
    )
    print(
        "TypeScript Multitask Dataset"
    )
    print("")

    for split in (
        "train",
        "validation",
        "test",
    ):
        dataset = (
            TypeScriptSemanticDataset(
                split,
                max_length=args.max_length,
                stride=(
                    args.train_stride
                    if split == "train"
                    else args.max_length
                ),
                window_strategy=(
                    args.train_window_strategy
                    if split == "train"
                    else "fixed"
                ),
                show_progress=True,
            )
        )

        print(
            f"{split}: "
            f"{len(dataset.documents)} documents, "
            f"{len(dataset)} windows, "
            f"strategy={dataset.window_strategy}, "
            f"stride={dataset.stride}"
        )

    schema = load_schema()

    print("")
    print(
        "Boundary classes: "
        "3 (O / B / I)"
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
