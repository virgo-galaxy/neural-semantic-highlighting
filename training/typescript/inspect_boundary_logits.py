from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from dataset import (
    BOUNDARY_BEGIN_ID,
    BOUNDARY_INSIDE_ID,
    BOUNDARY_OUTSIDE_ID,
    TypeScriptSemanticDataset,
)
from evaluate import (
    build_character_points,
    load_model,
    predict_document_logits,
    select_device,
)


DEFAULT_CHECKPOINT_PATH = Path(
    "artifacts/typescript/v2-multitask/best.pt"
)
DEFAULT_OUTPUT_PATH = Path(
    "artifacts/typescript/v2-multitask/"
    "boundary-logit-analysis.json"
)


@dataclass(frozen=True)
class FragmentationPoint:
    repository: str
    path: str
    span_start: int
    span_end: int
    char_start: int
    char_end: int
    character: str
    winner: str
    p_outside: float
    p_begin: float
    p_inside: float
    winner_probability: float
    inside_to_winner_ratio: float
    winner_minus_inside: float
    context: str


BOUNDARY_NAMES = {
    BOUNDARY_OUTSIDE_ID: "O",
    BOUNDARY_BEGIN_ID: "B",
    BOUNDARY_INSIDE_ID: "I",
}


def extract_context(
    source: str,
    character_index: int,
    *,
    radius: int = 36,
) -> str:
    start = max(
        0,
        character_index - radius,
    )
    end = min(
        len(source),
        character_index + radius + 1,
    )

    snippet = source[start:end].replace(
        "\n",
        "\\n",
    )

    if start > 0:
        snippet = "…" + snippet

    if end < len(source):
        snippet += "…"

    return snippet


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT_PATH,
    )

    parser.add_argument(
        "--split",
        choices=(
            "validation",
            "test",
        ),
        default="validation",
    )

    parser.add_argument(
        "--stride",
        type=int,
        default=256,
    )

    parser.add_argument(
        "--fusion",
        choices=(
            "uniform",
            "center",
        ),
        default="uniform",
    )

    parser.add_argument(
        "--token-type",
        default="string",
        help=(
            "Gold token type whose interior boundary logits "
            "should be inspected."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--max-examples",
        type=int,
        default=30,
    )

    return parser.parse_args()


def ratio_bucket(ratio: float) -> str:
    if ratio >= 0.90:
        return ">=0.90"
    if ratio >= 0.80:
        return "0.80-0.90"
    if ratio >= 0.70:
        return "0.70-0.80"
    if ratio >= 0.50:
        return "0.50-0.70"
    return "<0.50"


def main() -> None:
    args = parse_arguments()

    device = select_device()

    checkpoint = torch.load(
        args.checkpoint,
        map_location="cpu",
    )

    max_length = checkpoint[
        "config"
    ]["max_length"]

    dataset = TypeScriptSemanticDataset(
        args.split,
        max_length=max_length,
    )

    model, _ = load_model(
        args.checkpoint,
        dataset,
        device,
    )

    total_interior_points = 0
    fragmentation_points: list[
        FragmentationPoint
    ] = []

    winner_counts: Counter[str] = Counter()
    ratio_buckets: Counter[str] = Counter()

    print(
        "Neural Semantic Highlighting"
    )
    print(
        "Boundary Logit Inspection"
    )
    print("")
    print(f"Device:     {device}")
    print(f"Split:      {args.split}")
    print(f"Token type: {args.token_type}")
    print(
        f"Window:     {max_length} bytes"
    )
    print(f"Stride:     {args.stride} bytes")
    print(f"Fusion:     {args.fusion}")
    print("")

    for document_index, document in enumerate(
        dataset.documents,
        start=1,
    ):
        (
            boundary_logits,
            _,
            _,
        ) = predict_document_logits(
            model,
            document.source,
            max_length=max_length,
            device=device,
            stride=args.stride,
            fusion=args.fusion,
        )

        points = build_character_points(
            document.source
        )

        if not points:
            continue

        probabilities = torch.softmax(
            torch.stack(
                [
                    boundary_logits[
                        point.byte_start
                    ]
                    for point in points
                ],
                dim=0,
            ),
            dim=-1,
        )

        point_by_utf16_start = {
            point.utf16_start: (
                index,
                point,
            )
            for index, point in enumerate(points)
        }

        for gold in document.gold_spans:
            if (
                gold.token_type
                != args.token_type
            ):
                continue

            for (
                character_index,
                point,
            ) in enumerate(points):
                if (
                    point.utf16_start
                    <= gold.start
                ):
                    continue

                if (
                    point.utf16_start
                    >= gold.end
                ):
                    break

                total_interior_points += 1

                row = probabilities[
                    character_index
                ]

                winner_id = int(
                    row.argmax().item()
                )

                if (
                    winner_id
                    == BOUNDARY_INSIDE_ID
                ):
                    continue

                p_outside = float(
                    row[
                        BOUNDARY_OUTSIDE_ID
                    ].item()
                )
                p_begin = float(
                    row[
                        BOUNDARY_BEGIN_ID
                    ].item()
                )
                p_inside = float(
                    row[
                        BOUNDARY_INSIDE_ID
                    ].item()
                )

                winner_probability = float(
                    row[winner_id].item()
                )

                ratio = (
                    p_inside
                    / max(
                        winner_probability,
                        1e-12,
                    )
                )

                winner_name = (
                    BOUNDARY_NAMES[
                        winner_id
                    ]
                )

                winner_counts[
                    winner_name
                ] += 1
                ratio_buckets[
                    ratio_bucket(ratio)
                ] += 1

                character = (
                    document.source[
                        character_index
                    ]
                )

                fragmentation_points.append(
                    FragmentationPoint(
                        repository=(
                            document.repository
                        ),
                        path=document.path,
                        span_start=gold.start,
                        span_end=gold.end,
                        char_start=(
                            point.utf16_start
                        ),
                        char_end=(
                            point.utf16_end
                        ),
                        character=character,
                        winner=winner_name,
                        p_outside=p_outside,
                        p_begin=p_begin,
                        p_inside=p_inside,
                        winner_probability=(
                            winner_probability
                        ),
                        inside_to_winner_ratio=(
                            ratio
                        ),
                        winner_minus_inside=(
                            winner_probability
                            - p_inside
                        ),
                        context=extract_context(
                            document.source,
                            character_index,
                        ),
                    )
                )

        if (
            document_index % 10 == 0
            or document_index
            == len(dataset.documents)
        ):
            print(
                f"  inspected "
                f"{document_index}/"
                f"{len(dataset.documents)} "
                f"documents",
                flush=True,
            )

    error_count = len(
        fragmentation_points
    )

    error_rate = (
        error_count
        / max(
            total_interior_points,
            1,
        )
    )

    rescuable_090 = sum(
        1
        for item in fragmentation_points
        if (
            item.inside_to_winner_ratio
            >= 0.90
        )
    )

    rescuable_080 = sum(
        1
        for item in fragmentation_points
        if (
            item.inside_to_winner_ratio
            >= 0.80
        )
    )

    rescuable_070 = sum(
        1
        for item in fragmentation_points
        if (
            item.inside_to_winner_ratio
            >= 0.70
        )
    )

    confident_wrong = sorted(
        fragmentation_points,
        key=lambda item: (
            item.inside_to_winner_ratio,
            -item.winner_probability,
        ),
    )

    report = {
        "format": (
            "nsh-boundary-logit-analysis-v1"
        ),
        "checkpoint": str(
            args.checkpoint
        ),
        "split": args.split,
        "token_type": args.token_type,
        "inference": {
            "max_length": max_length,
            "stride": args.stride,
            "fusion": args.fusion,
        },
        "summary": {
            "interior_points": (
                total_interior_points
            ),
            "fragmentation_points": (
                error_count
            ),
            "fragmentation_rate": (
                error_rate
            ),
            "winner_counts": dict(
                winner_counts
            ),
            "ratio_buckets": {
                key: ratio_buckets[key]
                for key in (
                    ">=0.90",
                    "0.80-0.90",
                    "0.70-0.80",
                    "0.50-0.70",
                    "<0.50",
                )
            },
            "rescuable_at_090": (
                rescuable_090
            ),
            "rescuable_at_080": (
                rescuable_080
            ),
            "rescuable_at_070": (
                rescuable_070
            ),
        },
        "most_confident_wrong": [
            asdict(item)
            for item in confident_wrong[
                :args.max_examples
            ]
        ],
        "all_fragmentation_points": [
            asdict(item)
            for item in fragmentation_points
        ],
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print("")
    print("Interior boundary summary")
    print("-------------------------")
    print(
        "Interior points:       "
        f"{total_interior_points}"
    )
    print(
        "Fragmentation points:  "
        f"{error_count}"
    )
    print(
        "Fragmentation rate:    "
        f"{error_rate:.4%}"
    )
    print(
        "Wrong winners:         "
        f"{dict(winner_counts)}"
    )
    print("")
    print("p(I) / p(winner)")
    print("----------------")
    for key in (
        ">=0.90",
        "0.80-0.90",
        "0.70-0.80",
        "0.50-0.70",
        "<0.50",
    ):
        print(
            f"{key:<12} "
            f"{ratio_buckets[key]}"
        )

    print("")
    print("Potential sticky rescues")
    print("------------------------")
    print(
        f"ratio >= 0.90: {rescuable_090}"
    )
    print(
        f"ratio >= 0.80: {rescuable_080}"
    )
    print(
        f"ratio >= 0.70: {rescuable_070}"
    )

    print("")
    print(
        "Most confident wrong "
        "interior boundaries"
    )
    print(
        "--------------------------------"
    )

    for index, item in enumerate(
        confident_wrong[
            :args.max_examples
        ],
        start=1,
    ):
        print(
            f"[{index}] "
            f"{item.repository}/"
            f"{item.path}"
        )
        print(
            f"  span: "
            f"{item.span_start}:"
            f"{item.span_end}"
        )
        print(
            f"  char: "
            f"{item.char_start}:"
            f"{item.char_end} "
            f"{item.character!r}"
        )
        print(
            f"  winner={item.winner} "
            f"O={item.p_outside:.4f} "
            f"B={item.p_begin:.4f} "
            f"I={item.p_inside:.4f}"
        )
        print(
            "  I/winner="
            f"{item.inside_to_winner_ratio:.4f} "
            "margin="
            f"{item.winner_minus_inside:.4f}"
        )
        print(
            f"  context: "
            f"{item.context}"
        )
        print("")

    print(f"JSON: {args.output}")


if __name__ == "__main__":
    main()
