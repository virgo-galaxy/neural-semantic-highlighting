from __future__ import annotations

import torch

from config import DEFAULT_MAX_LENGTH
from dataset import (
    BOUNDARY_BEGIN_ID,
    BOUNDARY_INSIDE_ID,
    BOUNDARY_OUTSIDE_ID,
    IGNORE_LABEL_ID,
    EncodedDocument,
    build_adaptive_windows,
)
from inference import (
    build_character_starts,
    choose_predicted_cursor_cut,
    choose_runtime_lookahead_bounds,
)


def check(name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: {actual!r} != {expected!r}")
    print(f"✓ {name}")


def ascii_document(
    length: int,
    *,
    spans: tuple[tuple[int, int], ...] = (),
) -> EncodedDocument:
    boundary_labels = torch.full(
        (length,),
        BOUNDARY_OUTSIDE_ID,
        dtype=torch.long,
    )
    token_type_labels = torch.full(
        (length,),
        IGNORE_LABEL_ID,
        dtype=torch.long,
    )

    for start, end in spans:
        boundary_labels[start] = BOUNDARY_BEGIN_ID
        boundary_labels[start + 1 : end] = BOUNDARY_INSIDE_ID
        token_type_labels[start:end] = 0

    return EncodedDocument(
        repository="fixture",
        path="fixture.ts",
        document_kind="typescript",
        source="a" * length,
        input_ids=torch.tensor([97] * length, dtype=torch.long),
        boundary_labels=boundary_labels,
        token_type_labels=token_type_labels,
        modifier_labels=torch.zeros((length, 0), dtype=torch.uint8),
        gold_spans=(),
    )


def ranges(windows: list[object]) -> list[tuple[int, int]]:
    return [(window.start, window.end) for window in windows]


def boundary_logits(labels: list[int]) -> torch.Tensor:
    logits = torch.full((len(labels), 3), -10.0)

    for index, label in enumerate(labels):
        logits[index, label] = 10.0

    return logits


def main() -> None:
    document = ascii_document(20, spans=((6, 10),))
    windows, stats = build_adaptive_windows(0, document, max_length=8)
    check(
        "training cursor moves a cut to the Gold span start",
        ranges(windows),
        [(0, 6), (6, 14), (14, 20)],
    )
    check("training cursor records one adjusted span cut", stats.adjusted_span_cuts, 1)
    check("training cursor records the exact shift", stats.shift_bytes, (2,))

    long_span = ascii_document(20, spans=((0, 12),))
    windows, stats = build_adaptive_windows(0, long_span, max_length=8)
    check(
        "over-context Gold spans still make forward progress",
        ranges(windows),
        [(0, 8), (8, 16), (16, 20)],
    )
    check(
        "over-context Gold span start is recorded as unavoidable",
        stats.unavoidable_inside_starts,
        1,
    )

    labels = [0, 0, 0, 0, 0, 0, 1, 2, 2, 0]
    check(
        "runtime cursor backs off to a predicted span start",
        choose_predicted_cursor_cut(
            boundary_logits(labels),
            candidate=8,
            character_starts=tuple(range(11)),
        ),
        6,
    )

    labels[8] = 0
    check(
        "runtime cursor keeps a safe predicted cut",
        choose_predicted_cursor_cut(
            boundary_logits(labels),
            candidate=8,
            character_starts=tuple(range(11)),
        ),
        8,
    )

    check(
        "runtime cursor tracks UTF-8 character starts",
        build_character_starts("a你b"),
        (0, 1, 4, 5),
    )

    multibyte_starts = build_character_starts(
        "a" * (DEFAULT_MAX_LENGTH - 1) + "你" + "b"
    )
    check(
        "runtime cursor keeps lookahead inside a UTF-8 byte limit",
        choose_runtime_lookahead_bounds(
            multibyte_starts,
            cursor=0,
            limit=DEFAULT_MAX_LENGTH,
        ),
        (DEFAULT_MAX_LENGTH - 2, DEFAULT_MAX_LENGTH - 1),
    )

    print("9/9 adaptive-cursor golden checks passed")


if __name__ == "__main__":
    main()
