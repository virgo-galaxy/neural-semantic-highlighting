from __future__ import annotations

import torch

from dataset import (
    BOUNDARY_BEGIN_ID,
    BOUNDARY_INSIDE_ID,
    BOUNDARY_OUTSIDE_ID,
    IGNORE_LABEL_ID,
    EncodedDocument,
    GoldSpan,
    WindowReference,
    build_span_aware_windows,
)

STRING_ID = 1
COMMENT_ID = 2
VARIABLE_ID = 3
MAX_LENGTH = 8


def make_document(
    length: int,
    spans: list[tuple[int, int, int, str]],
) -> EncodedDocument:
    source = "x" * length
    input_ids = torch.tensor(
        list(source.encode("utf-8")),
        dtype=torch.long,
    )

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
    modifier_labels = torch.zeros(
        (length, 1),
        dtype=torch.uint8,
    )

    gold_spans: list[GoldSpan] = []

    for start, end, token_type_id, token_type in spans:
        if not (0 <= start < end <= length):
            raise ValueError(
                f"Invalid synthetic span {start}:{end} for length {length}."
            )

        boundary_labels[start] = BOUNDARY_BEGIN_ID
        if end - start > 1:
            boundary_labels[start + 1 : end] = BOUNDARY_INSIDE_ID
        token_type_labels[start:end] = token_type_id

        gold_spans.append(
            GoldSpan(
                start=start,
                end=end,
                token_type=token_type,
                modifiers=(),
            )
        )

    return EncodedDocument(
        repository="golden",
        path="windowing.ts",
        document_kind="ts",
        source=source,
        input_ids=input_ids,
        boundary_labels=boundary_labels,
        token_type_labels=token_type_labels,
        modifier_labels=modifier_labels,
        gold_spans=tuple(gold_spans),
    )


def window_pairs(
    windows: list[WindowReference],
) -> list[tuple[int, int]]:
    return [
        (window.start, window.end)
        for window in windows
    ]


def run_case(
    name: str,
    *,
    document: EncodedDocument,
    expected_windows: list[tuple[int, int]],
    expected_adjusted: int,
    expected_unavoidable_protected: int,
    expected_allowed_unprotected: int,
) -> None:
    windows, stats = build_span_aware_windows(
        0,
        document,
        max_length=MAX_LENGTH,
        protected_token_type_ids=frozenset({STRING_ID}),
    )

    actual_windows = window_pairs(windows)

    assert actual_windows == expected_windows, (
        f"{name}: windows {actual_windows} != {expected_windows}"
    )
    assert stats.adjusted_span_cuts == expected_adjusted, (
        f"{name}: adjusted {stats.adjusted_span_cuts} "
        f"!= {expected_adjusted}"
    )
    assert (
        stats.unavoidable_inside_starts
        == expected_unavoidable_protected
    ), (
        f"{name}: unavoidable protected starts "
        f"{stats.unavoidable_inside_starts} "
        f"!= {expected_unavoidable_protected}"
    )
    assert (
        stats.unprotected_inside_starts
        == expected_allowed_unprotected
    ), (
        f"{name}: allowed unprotected starts "
        f"{stats.unprotected_inside_starts} "
        f"!= {expected_allowed_unprotected}"
    )

    print(f"PASS  {name}")


def main() -> None:
    # Golden 1: a normal string crossing the candidate cut is protected.
    # The cut moves from 8 back to the string start at 6.
    run_case(
        "protect string at candidate cut",
        document=make_document(
            16,
            [(6, 10, STRING_ID, "string")],
        ),
        expected_windows=[(0, 6), (6, 14), (14, 16)],
        expected_adjusted=1,
        expected_unavoidable_protected=0,
        expected_allowed_unprotected=0,
    )

    # Golden 2: a comment crossing the same cut is intentionally NOT
    # protected. The next window starts inside the comment so the model
    # keeps learning comment continuation without seeing its opener.
    run_case(
        "preserve mid-comment continuation",
        document=make_document(
            16,
            [(6, 10, COMMENT_ID, "comment")],
        ),
        expected_windows=[(0, 8), (8, 16)],
        expected_adjusted=0,
        expected_unavoidable_protected=0,
        expected_allowed_unprotected=1,
    )

    # Golden 3: unrelated semantic spans remain on the fixed cursor too.
    run_case(
        "do not protect unrelated token types",
        document=make_document(
            16,
            [(6, 10, VARIABLE_ID, "variable")],
        ),
        expected_windows=[(0, 8), (8, 16)],
        expected_adjusted=0,
        expected_unavoidable_protected=0,
        expected_allowed_unprotected=1,
    )

    # Golden 4: when no protected span crosses the cut, behavior is the
    # same as fixed non-overlapping 8-byte windows.
    run_case(
        "keep ordinary fixed cut",
        document=make_document(18, []),
        expected_windows=[(0, 8), (8, 16), (16, 18)],
        expected_adjusted=0,
        expected_unavoidable_protected=0,
        expected_allowed_unprotected=0,
    )

    # Golden 5: a protected string longer than the model context cannot
    # fit in one window. We move to its true start once, then allow the
    # unavoidable split so the cursor always makes progress.
    run_case(
        "long string falls back without looping",
        document=make_document(
            20,
            [(2, 14, STRING_ID, "string")],
        ),
        expected_windows=[(0, 2), (2, 10), (10, 18), (18, 20)],
        expected_adjusted=1,
        expected_unavoidable_protected=1,
        expected_allowed_unprotected=0,
    )

    print("")
    print("String-aware windowing golden cases: 5/5 passed")


if __name__ == "__main__":
    main()
