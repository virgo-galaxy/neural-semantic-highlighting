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
    build_dual_view_hard_string_regexp_windows,
    build_dual_view_hard_string_windows,
    build_dual_view_windows,
    build_hard_regexp_windows,
    build_hard_string_windows,
    build_span_aware_windows,
)

STRING_ID = 1
COMMENT_ID = 2
VARIABLE_ID = 3
REGEXP_ID = 4
OPERATOR_ID = 5
MAX_LENGTH = 8


def make_document(
    length: int,
    spans: list[tuple[int, int, int, str]],
    *,
    source: str | None = None,
) -> EncodedDocument:
    source = "x" * length if source is None else source

    if len(source.encode("utf-8")) != length:
        raise ValueError(
            "Synthetic source must be ASCII-sized to match length."
        )
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


def run_dual_view_case(
    name: str,
    *,
    document: EncodedDocument,
    expected_windows: list[tuple[int, int]],
    expected_fixed_count: int,
    expected_span_aware_count: int,
    expected_adjusted: int,
) -> None:
    (
        windows,
        stats,
        fixed_count,
        span_aware_count,
    ) = build_dual_view_windows(
        0,
        document,
        max_length=MAX_LENGTH,
    )

    actual_windows = window_pairs(windows)

    assert actual_windows == expected_windows, (
        f"{name}: windows {actual_windows} != {expected_windows}"
    )
    assert fixed_count == expected_fixed_count, (
        f"{name}: fixed_count {fixed_count} "
        f"!= {expected_fixed_count}"
    )
    assert span_aware_count == expected_span_aware_count, (
        f"{name}: span_aware_count {span_aware_count} "
        f"!= {expected_span_aware_count}"
    )
    assert stats.adjusted_span_cuts == expected_adjusted, (
        f"{name}: adjusted {stats.adjusted_span_cuts} "
        f"!= {expected_adjusted}"
    )

    print(f"PASS  {name}")



def run_hard_string_case(
    name: str,
    *,
    document: EncodedDocument,
    expected_windows: list[tuple[int, int]],
    expected_eligible_spans: int,
    expected_over_context_spans: int,
) -> None:
    windows, stats = build_hard_string_windows(
        0,
        document,
        max_length=MAX_LENGTH,
    )

    actual_windows = window_pairs(windows)

    assert actual_windows == expected_windows, (
        f"{name}: windows {actual_windows} != {expected_windows}"
    )
    assert stats.eligible_spans == expected_eligible_spans, (
        f"{name}: eligible {stats.eligible_spans} "
        f"!= {expected_eligible_spans}"
    )
    assert stats.over_context_spans == expected_over_context_spans, (
        f"{name}: over-context {stats.over_context_spans} "
        f"!= {expected_over_context_spans}"
    )
    assert stats.generated_windows == len(expected_windows), (
        f"{name}: generated {stats.generated_windows} "
        f"!= {len(expected_windows)}"
    )

    print(f"PASS  {name}")


def run_dual_view_hard_string_case(
    name: str,
    *,
    document: EncodedDocument,
    expected_windows: list[tuple[int, int]],
    expected_fixed_count: int,
    expected_span_aware_count: int,
    expected_hard_string_count: int,
) -> None:
    (
        windows,
        _,
        hard_stats,
        fixed_count,
        span_aware_count,
        hard_string_count,
    ) = build_dual_view_hard_string_windows(
        0,
        document,
        max_length=MAX_LENGTH,
    )

    actual_windows = window_pairs(windows)

    assert actual_windows == expected_windows, (
        f"{name}: windows {actual_windows} != {expected_windows}"
    )
    assert fixed_count == expected_fixed_count
    assert span_aware_count == expected_span_aware_count
    assert hard_string_count == expected_hard_string_count
    assert hard_stats.generated_windows == expected_hard_string_count

    print(f"PASS  {name}")

def run_hard_regexp_case(
    name: str,
    *,
    document: EncodedDocument,
    expected_windows: list[tuple[int, int]],
    expected_regexp_spans: int,
    expected_operator_slash_candidates: int,
    expected_negative_windows: int,
) -> None:
    windows, stats = build_hard_regexp_windows(
        0,
        document,
        max_length=MAX_LENGTH,
        operator_token_type_id=OPERATOR_ID,
    )

    actual_windows = window_pairs(windows)

    assert actual_windows == expected_windows, (
        f"{name}: windows {actual_windows} != {expected_windows}"
    )
    assert stats.regexp_spans == expected_regexp_spans
    assert (
        stats.operator_slash_candidates
        == expected_operator_slash_candidates
    )
    assert stats.negative_windows == expected_negative_windows
    assert stats.generated_windows == len(expected_windows)

    print(f"PASS  {name}")


def run_v3_full_curriculum_case(
    name: str,
    *,
    document: EncodedDocument,
    expected_windows: list[tuple[int, int]],
    expected_fixed_count: int,
    expected_span_aware_count: int,
    expected_hard_string_count: int,
    expected_hard_regexp_count: int,
) -> None:
    (
        windows,
        _,
        hard_string_stats,
        hard_regexp_stats,
        fixed_count,
        span_aware_count,
        hard_string_count,
        hard_regexp_count,
    ) = build_dual_view_hard_string_regexp_windows(
        0,
        document,
        max_length=MAX_LENGTH,
        operator_token_type_id=OPERATOR_ID,
    )

    actual_windows = window_pairs(windows)

    assert actual_windows == expected_windows, (
        f"{name}: windows {actual_windows} != {expected_windows}"
    )
    assert fixed_count == expected_fixed_count
    assert span_aware_count == expected_span_aware_count
    assert hard_string_count == expected_hard_string_count
    assert hard_regexp_count == expected_hard_regexp_count
    assert hard_string_stats.generated_windows == expected_hard_string_count
    assert hard_regexp_stats.generated_windows == expected_hard_regexp_count

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

    # Golden 6: dual-view keeps the complete fixed view and the complete
    # all-span-aware view. The fixed half teaches continuation; the
    # adaptive half teaches clean semantic boundaries.
    run_dual_view_case(
        "dual-view keeps both complete views",
        document=make_document(
            16,
            [(6, 10, STRING_ID, "string")],
        ),
        expected_windows=[
            (0, 8),
            (8, 16),
            (0, 6),
            (6, 14),
            (14, 16),
        ],
        expected_fixed_count=2,
        expected_span_aware_count=3,
        expected_adjusted=1,
    )

    # Golden 7: if both views happen to produce the same windows, retain
    # both copies. With half as many epochs this preserves roughly the
    # same total exposure budget as the 32-epoch fixed baseline.
    run_dual_view_case(
        "dual-view retains identical view copies",
        document=make_document(18, []),
        expected_windows=[
            (0, 8),
            (8, 16),
            (16, 18),
            (0, 8),
            (8, 16),
            (16, 18),
        ],
        expected_fixed_count=3,
        expected_span_aware_count=3,
        expected_adjusted=0,
    )

    # Golden 8: short strings are already well represented by the normal
    # dual views and are not upweighted by the hard-string curriculum.
    run_hard_string_case(
        "hard-string ignores short spans",
        document=make_document(16, [(2, 5, STRING_ID, "string")]),
        expected_windows=[],
        expected_eligible_spans=0,
        expected_over_context_spans=0,
    )

    # Golden 9: a long string receives deterministic interior starts.
    # With max_length=8, the curriculum threshold is 4 bytes, the first
    # interior start is +2, and subsequent starts are spaced by 4 bytes.
    run_hard_string_case(
        "hard-string adds interior continuation views",
        document=make_document(16, [(1, 11, STRING_ID, "string")]),
        expected_windows=[(3, 11), (7, 15)],
        expected_eligible_spans=1,
        expected_over_context_spans=1,
    )

    # Golden 10: V3 keeps both complete dual views and only appends the
    # targeted hard-string windows. The original curriculum is preserved.
    run_dual_view_hard_string_case(
        "v3 keeps dual-view plus hard-string curriculum",
        document=make_document(16, [(1, 11, STRING_ID, "string")]),
        expected_windows=[
            (0, 8),
            (8, 16),
            (0, 1),
            (1, 9),
            (9, 16),
            (3, 11),
            (7, 15),
        ],
        expected_fixed_count=2,
        expected_span_aware_count=3,
        expected_hard_string_count=2,
    )

    # Golden 11: every Gold regexp gets a context-rich boundary view.
    run_hard_regexp_case(
        "hard-regexp adds exact-boundary positive view",
        document=make_document(
            16,
            [(4, 8, REGEXP_ID, "regexp")],
            source="xxxx/ab/xxxxxxxx",
        ),
        expected_windows=[(2, 10)],
        expected_regexp_spans=1,
        expected_operator_slash_candidates=0,
        expected_negative_windows=0,
    )

    # Golden 12: regexp training also keeps Gold division-slash negatives,
    # preventing the positive oversampling from teaching that every slash
    # begins a regexp.
    run_hard_regexp_case(
        "hard-regexp adds controlled operator-slash negative",
        document=make_document(
            16,
            [
                (0, 3, REGEXP_ID, "regexp"),
                (6, 7, OPERATOR_ID, "operator"),
                (10, 11, OPERATOR_ID, "operator"),
            ],
            source="/r/ a / b / c xx",
        ),
        expected_windows=[(0, 8), (4, 12), (8, 16)],
        expected_regexp_spans=1,
        expected_operator_slash_candidates=2,
        expected_negative_windows=2,
    )

    # Golden 13: the final V3 curriculum preserves dual-view and the
    # hard-string add-on, then appends regexp positives and slash negatives.
    run_v3_full_curriculum_case(
        "v3 keeps dual-view plus string and regexp curricula",
        document=make_document(
            16,
            [
                (0, 3, REGEXP_ID, "regexp"),
                (4, 12, STRING_ID, "string"),
                (13, 14, OPERATOR_ID, "operator"),
            ],
            source="/r/ abcdefgh / z",
        ),
        expected_windows=[
            (0, 8),
            (8, 16),
            (0, 4),
            (4, 12),
            (12, 16),
            (6, 14),
            (10, 16),
            (0, 8),
            (11, 16),
        ],
        expected_fixed_count=2,
        expected_span_aware_count=3,
        expected_hard_string_count=2,
        expected_hard_regexp_count=2,
    )

    # Golden 14: slash negatives must not depend on the same document also
    # containing a regexp. This guards the corpus-level negative curriculum.
    run_hard_regexp_case(
        "hard-regexp keeps negative-only documents",
        document=make_document(
            16,
            [(8, 9, OPERATOR_ID, "operator")],
            source="const x / y = z;",
        ),
        expected_windows=[(6, 14)],
        expected_regexp_spans=0,
        expected_operator_slash_candidates=1,
        expected_negative_windows=1,
    )

    print("")
    print("Windowing golden cases: 14/14 passed")


if __name__ == "__main__":
    main()
