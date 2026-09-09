from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from config import DEFAULT_ARTIFACT_DIRECTORY, DEFAULT_WINDOW_STRIDE
from dataset import BOUNDARY_INSIDE_ID, TypeScriptSemanticDataset
from evaluate import build_character_points, load_model, select_device
from inference import predict_document_logits


@dataclass(frozen=True)
class FragmentationPoint:
    repository: str
    path: str
    span_start: int
    span_end: int
    char_start: int
    character: str
    winner: str
    p_inside: float
    p_winner: float
    inside_to_winner_ratio: float
    context: str


BOUNDARY_NAMES = {0: "O", 1: "B", 2: "I"}


def extract_context(source: str, character_index: int, radius: int = 36) -> str:
    start = max(0, character_index - radius)
    end = min(len(source), character_index + radius + 1)
    snippet = source[start:end].replace("\n", "\\n")
    return ("…" if start else "") + snippet + ("…" if end < len(source) else "")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_ARTIFACT_DIRECTORY / "best.pt",
    )
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--token-type", default="string")
    parser.add_argument("--stride", type=int, default=DEFAULT_WINDOW_STRIDE)
    parser.add_argument("--fusion", choices=("uniform", "center"), default="center")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ARTIFACT_DIRECTORY / "fragmentation.json",
    )
    parser.add_argument("--max-examples", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    device = select_device()
    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    max_length = int(checkpoint["config"]["max_length"])

    dataset = TypeScriptSemanticDataset(
        args.split,
        max_length=max_length,
        stride=args.stride,
    )
    model, _ = load_model(args.checkpoint, dataset, device)

    interior_points = 0
    winner_counts: Counter[str] = Counter()
    points: list[FragmentationPoint] = []

    for document in dataset.documents:
        boundary_logits, _, _ = predict_document_logits(
            model,
            document.source,
            max_length=max_length,
            stride=args.stride,
            fusion=args.fusion,
            device=device,
        )
        characters = build_character_points(document.source)
        if not characters:
            continue

        probabilities = torch.softmax(
            torch.stack([boundary_logits[point.byte_start] for point in characters]),
            dim=-1,
        )

        for gold in document.gold_spans:
            if gold.token_type != args.token_type:
                continue

            for index, point in enumerate(characters):
                if point.utf16_start <= gold.start:
                    continue
                if point.utf16_start >= gold.end:
                    break

                interior_points += 1
                row = probabilities[index]
                winner_id = int(row.argmax().item())
                if winner_id == BOUNDARY_INSIDE_ID:
                    continue

                p_inside = float(row[BOUNDARY_INSIDE_ID].item())
                p_winner = float(row[winner_id].item())
                winner = BOUNDARY_NAMES[winner_id]
                winner_counts[winner] += 1

                points.append(
                    FragmentationPoint(
                        repository=document.repository,
                        path=document.path,
                        span_start=gold.start,
                        span_end=gold.end,
                        char_start=point.utf16_start,
                        character=document.source[index],
                        winner=winner,
                        p_inside=p_inside,
                        p_winner=p_winner,
                        inside_to_winner_ratio=p_inside / max(p_winner, 1e-12),
                        context=extract_context(document.source, index),
                    )
                )

    points.sort(key=lambda item: (item.inside_to_winner_ratio, -item.p_winner))
    fragmentation_count = len(points)
    report = {
        "checkpoint": str(args.checkpoint),
        "split": args.split,
        "token_type": args.token_type,
        "inference": {
            "max_length": max_length,
            "stride": args.stride,
            "fusion": args.fusion,
        },
        "summary": {
            "interior_points": interior_points,
            "fragmentation_points": fragmentation_count,
            "fragmentation_rate": fragmentation_count / max(interior_points, 1),
            "winner_counts": dict(winner_counts),
            "near_miss_ratio_ge_090": sum(
                point.inside_to_winner_ratio >= 0.90 for point in points
            ),
            "near_miss_ratio_ge_080": sum(
                point.inside_to_winner_ratio >= 0.80 for point in points
            ),
        },
        "most_confident_wrong": [
            asdict(point) for point in points[: args.max_examples]
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("Neural Semantic Highlighting")
    print("Fragmentation Inspection")
    print("")
    print(f"Token type:           {args.token_type}")
    print(f"Interior points:      {interior_points}")
    print(f"Fragmentation points: {fragmentation_count}")
    print(
        "Fragmentation rate:   "
        f"{fragmentation_count / max(interior_points, 1):.4%}"
    )
    print(f"Wrong winners:        {dict(winner_counts)}")
    print(f"Output:               {args.output}")


if __name__ == "__main__":
    main()
