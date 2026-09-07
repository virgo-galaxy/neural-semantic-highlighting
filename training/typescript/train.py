from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader

from dataset import (
    BOUNDARY_BEGIN_ID,
    BOUNDARY_INSIDE_ID,
    BOUNDARY_OUTSIDE_ID,
    IGNORE_LABEL_ID,
    NUMBER_OF_BOUNDARY_CLASSES,
    PAD_BYTE_ID,
    EncodedDocument,
    TypeScriptSemanticDataset,
)
from model import (
    SemanticTransformer,
    count_parameters,
)


DEFAULT_OUTPUT_PATH = Path(
    "artifacts/typescript/v2-multitask/best.pt"
)


@dataclass(frozen=True)
class CharacterPoint:
    utf16_start: int
    utf16_end: int
    byte_start: int


@dataclass(frozen=True)
class PredictedSpan:
    start: int
    end: int
    token_type: str
    modifiers: tuple[str, ...]


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


def build_character_points(
    source: str,
) -> list[CharacterPoint]:
    points: list[CharacterPoint] = []

    utf16_offset = 0
    byte_offset = 0

    for character in source:
        utf16_length = (
            len(character.encode("utf-16-le")) // 2
        )

        points.append(
            CharacterPoint(
                utf16_start=utf16_offset,
                utf16_end=utf16_offset + utf16_length,
                byte_start=byte_offset,
            )
        )

        utf16_offset += utf16_length
        byte_offset += len(character.encode("utf-8"))

    return points


def build_class_weights(
    labels: list[torch.Tensor],
    number_of_classes: int,
    *,
    min_weight: float,
    max_weight: float,
) -> torch.Tensor:
    counts = torch.zeros(
        number_of_classes,
        dtype=torch.long,
    )

    for label_tensor in labels:
        valid = label_tensor[
            label_tensor != IGNORE_LABEL_ID
        ]

        counts += torch.bincount(
            valid,
            minlength=number_of_classes,
        )

    present = counts > 0

    weights = torch.zeros(
        number_of_classes,
        dtype=torch.float32,
    )

    weights[present] = (
        1.0
        / torch.sqrt(
            counts[present].float()
        )
    )

    weights[present] /= weights[present].mean()

    weights = weights.clamp(
        min=min_weight,
        max=max_weight,
    )

    weights[~present] = 0.0

    return weights


def build_boundary_class_weights(
    dataset: TypeScriptSemanticDataset,
) -> torch.Tensor:
    return build_class_weights(
        [
            document.boundary_labels
            for document in dataset.documents
        ],
        NUMBER_OF_BOUNDARY_CLASSES,
        min_weight=0.5,
        max_weight=2.0,
    )


def build_token_type_class_weights(
    dataset: TypeScriptSemanticDataset,
) -> torch.Tensor:
    return build_class_weights(
        [
            document.token_type_labels
            for document in dataset.documents
        ],
        dataset.schema.number_of_token_types,
        min_weight=0.25,
        max_weight=4.0,
    )


def build_modifier_positive_weights(
    dataset: TypeScriptSemanticDataset,
) -> torch.Tensor:
    number_of_modifiers = len(
        dataset.schema.modifiers
    )

    positive_counts = torch.zeros(
        number_of_modifiers,
        dtype=torch.float32,
    )

    begin_count = 0

    for document in dataset.documents:
        begin_mask = (
            document.boundary_labels
            == BOUNDARY_BEGIN_ID
        )

        begin_count += int(
            begin_mask.sum().item()
        )

        if begin_mask.any():
            positive_counts += (
                document.modifier_labels[
                    begin_mask
                ]
                .sum(dim=0)
                .float()
            )

    negative_counts = (
        begin_count - positive_counts
    )

    positive_weights = (
        negative_counts
        / positive_counts.clamp_min(1.0)
    )

    positive_weights = positive_weights.clamp(
        min=1.0,
        max=4.0,
    )

    positive_weights[
        positive_counts == 0
    ] = 1.0

    return positive_weights


def predict_document_logits(
    model: SemanticTransformer,
    source: str,
    *,
    max_length: int,
    device: torch.device,
) -> tuple[
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
]:
    source_bytes = source.encode("utf-8")

    if not source_bytes:
        return (
            torch.empty((0, 3)),
            torch.empty((0, 0)),
            torch.empty((0, 0)),
        )

    boundary_chunks: list[torch.Tensor] = []
    token_type_chunks: list[torch.Tensor] = []
    modifier_chunks: list[torch.Tensor] = []

    with torch.no_grad():
        for start in range(
            0,
            len(source_bytes),
            max_length,
        ):
            chunk = source_bytes[
                start:start + max_length
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

            boundary_chunks.append(
                output.boundary_logits[
                    0,
                    :length,
                ]
                .detach()
                .cpu()
            )

            token_type_chunks.append(
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
        torch.cat(boundary_chunks, dim=0),
        torch.cat(token_type_chunks, dim=0),
        torch.cat(modifier_chunks, dim=0),
    )


def decode_predicted_spans(
    document: EncodedDocument,
    boundary_logits: torch.Tensor,
    token_type_logits: torch.Tensor,
    modifier_logits: torch.Tensor,
    dataset: TypeScriptSemanticDataset,
    *,
    modifier_threshold: float = 0.60,
) -> list[PredictedSpan]:
    points = build_character_points(
        document.source
    )

    if not points:
        return []

    boundary_ids = [
        int(
            boundary_logits[
                point.byte_start
            ]
            .argmax()
            .item()
        )
        for point in points
    ]

    span_ranges: list[
        tuple[int, int]
    ] = []

    current_start: int | None = None

    def flush(end_index: int) -> None:
        nonlocal current_start

        if current_start is not None:
            span_ranges.append(
                (
                    current_start,
                    end_index,
                )
            )

        current_start = None

    for index, boundary_id in enumerate(
        boundary_ids
    ):
        if boundary_id == BOUNDARY_OUTSIDE_ID:
            flush(index)
            continue

        if boundary_id == BOUNDARY_BEGIN_ID:
            flush(index)
            current_start = index
            continue

        if boundary_id == BOUNDARY_INSIDE_ID:
            if current_start is None:
                current_start = index
            continue

        raise ValueError(
            f"Unknown boundary id {boundary_id}."
        )

    flush(len(points))

    spans: list[PredictedSpan] = []

    token_types = dataset.schema.token_types
    modifiers = dataset.schema.modifiers

    for start_index, end_index in span_ranges:
        span_points = points[
            start_index:end_index
        ]

        byte_positions = torch.tensor(
            [
                point.byte_start
                for point in span_points
            ],
            dtype=torch.long,
        )

        mean_type_logits = (
            token_type_logits[
                byte_positions
            ].mean(dim=0)
        )

        token_type_id = int(
            mean_type_logits.argmax().item()
        )

        start_point = span_points[0]
        end_point = span_points[-1]

        modifier_probabilities = torch.sigmoid(
            modifier_logits[
                start_point.byte_start
            ]
        )

        predicted_modifiers = tuple(
            modifier
            for modifier, probability
            in zip(
                modifiers,
                modifier_probabilities.tolist(),
                strict=True,
            )
            if probability >= modifier_threshold
        )

        spans.append(
            PredictedSpan(
                start=start_point.utf16_start,
                end=end_point.utf16_end,
                token_type=token_types[
                    token_type_id
                ],
                modifiers=predicted_modifiers,
            )
        )

    return spans


def exact_span_metrics(
    dataset: TypeScriptSemanticDataset,
    model: SemanticTransformer,
    device: torch.device,
) -> dict[str, float]:
    predicted_set: set[
        tuple[str, int, int, str]
    ] = set()

    gold_set: set[
        tuple[str, int, int, str]
    ] = set()

    per_type_predicted: dict[
        str,
        set[tuple[str, int, int, str]],
    ] = {
        token_type: set()
        for token_type
        in dataset.schema.token_types
    }

    per_type_gold: dict[
        str,
        set[tuple[str, int, int, str]],
    ] = {
        token_type: set()
        for token_type
        in dataset.schema.token_types
    }

    for document in dataset.documents:
        (
            boundary_logits,
            token_type_logits,
            modifier_logits,
        ) = predict_document_logits(
            model,
            document.source,
            max_length=dataset.max_length,
            device=device,
        )

        predicted_spans = decode_predicted_spans(
            document,
            boundary_logits,
            token_type_logits,
            modifier_logits,
            dataset,
        )

        document_key = (
            f"{document.repository}:"
            f"{document.path}"
        )

        for span in predicted_spans:
            item = (
                document_key,
                span.start,
                span.end,
                span.token_type,
            )

            predicted_set.add(item)

            per_type_predicted[
                span.token_type
            ].add(item)

        for span in document.gold_spans:
            item = (
                document_key,
                span.start,
                span.end,
                span.token_type,
            )

            gold_set.add(item)

            per_type_gold[
                span.token_type
            ].add(item)

    true_positive = len(
        predicted_set & gold_set
    )

    false_positive = len(
        predicted_set - gold_set
    )

    false_negative = len(
        gold_set - predicted_set
    )

    precision = (
        true_positive
        / max(
            1,
            true_positive
            + false_positive,
        )
    )

    recall = (
        true_positive
        / max(
            1,
            true_positive
            + false_negative,
        )
    )

    f1 = (
        2.0
        * precision
        * recall
        / max(
            1e-12,
            precision + recall,
        )
    )

    macro_values: list[float] = []

    for token_type in (
        dataset.schema.token_types
    ):
        predicted = (
            per_type_predicted[
                token_type
            ]
        )

        gold = per_type_gold[
            token_type
        ]

        if not gold:
            continue

        tp = len(predicted & gold)
        fp = len(predicted - gold)
        fn = len(gold - predicted)

        type_precision = (
            tp / max(1, tp + fp)
        )

        type_recall = (
            tp / max(1, tp + fn)
        )

        type_f1 = (
            2.0
            * type_precision
            * type_recall
            / max(
                1e-12,
                type_precision
                + type_recall,
            )
        )

        macro_values.append(type_f1)

    macro_f1 = (
        sum(macro_values)
        / len(macro_values)
        if macro_values
        else 0.0
    )

    return {
        "exact_span_precision": precision,
        "exact_span_recall": recall,
        "exact_span_f1": f1,
        "exact_span_macro_f1": macro_f1,
        "predicted_spans": float(
            len(predicted_set)
        ),
        "gold_spans": float(
            len(gold_set)
        ),
    }


def diagnostic_metrics(
    model: SemanticTransformer,
    loader: DataLoader,
    dataset: TypeScriptSemanticDataset,
    device: torch.device,
) -> dict[str, float]:
    boundary_confusion = torch.zeros(
        (
            NUMBER_OF_BOUNDARY_CLASSES,
            NUMBER_OF_BOUNDARY_CLASSES,
        ),
        dtype=torch.long,
    )

    token_type_count = (
        dataset.schema.number_of_token_types
    )

    token_type_confusion = torch.zeros(
        (
            token_type_count,
            token_type_count,
        ),
        dtype=torch.long,
    )

    modifier_tp = 0
    modifier_fp = 0
    modifier_fn = 0

    model.eval()

    with torch.no_grad():
        for batch in loader:
            input_ids = batch[
                "input_ids"
            ].to(device)

            attention_mask = batch[
                "attention_mask"
            ].to(device)

            boundary_labels = batch[
                "boundary_labels"
            ].to(device)

            token_type_labels = batch[
                "token_type_labels"
            ].to(device)

            modifier_labels = batch[
                "modifier_labels"
            ].to(device)

            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            boundary_predictions = (
                output.boundary_logits.argmax(
                    dim=-1
                )
            )

            boundary_valid = (
                boundary_labels
                != IGNORE_LABEL_ID
            )

            boundary_targets = (
                boundary_labels[
                    boundary_valid
                ]
                .detach()
                .cpu()
            )

            boundary_predicted = (
                boundary_predictions[
                    boundary_valid
                ]
                .detach()
                .cpu()
            )

            boundary_indices = (
                boundary_targets
                * NUMBER_OF_BOUNDARY_CLASSES
                + boundary_predicted
            )

            boundary_confusion += torch.bincount(
                boundary_indices,
                minlength=(
                    NUMBER_OF_BOUNDARY_CLASSES
                    * NUMBER_OF_BOUNDARY_CLASSES
                ),
            ).reshape(
                NUMBER_OF_BOUNDARY_CLASSES,
                NUMBER_OF_BOUNDARY_CLASSES,
            )

            type_predictions = (
                output.token_type_logits.argmax(
                    dim=-1
                )
            )

            type_valid = (
                token_type_labels
                != IGNORE_LABEL_ID
            )

            type_targets = (
                token_type_labels[
                    type_valid
                ]
                .detach()
                .cpu()
            )

            type_predicted = (
                type_predictions[
                    type_valid
                ]
                .detach()
                .cpu()
            )

            type_indices = (
                type_targets
                * token_type_count
                + type_predicted
            )

            token_type_confusion += torch.bincount(
                type_indices,
                minlength=(
                    token_type_count
                    * token_type_count
                ),
            ).reshape(
                token_type_count,
                token_type_count,
            )

            begin_mask = (
                boundary_labels
                == BOUNDARY_BEGIN_ID
            )

            if begin_mask.any():
                modifier_predictions = (
                    torch.sigmoid(
                        output.modifier_logits[
                            begin_mask
                        ]
                    )
                    >= 0.60
                )

                modifier_targets = (
                    modifier_labels[
                        begin_mask
                    ]
                    >= 0.5
                )

                modifier_tp += int(
                    (
                        modifier_predictions
                        & modifier_targets
                    )
                    .sum()
                    .item()
                )

                modifier_fp += int(
                    (
                        modifier_predictions
                        & ~modifier_targets
                    )
                    .sum()
                    .item()
                )

                modifier_fn += int(
                    (
                        ~modifier_predictions
                        & modifier_targets
                    )
                    .sum()
                    .item()
                )

    def macro_f1(
        confusion: torch.Tensor,
    ) -> float:
        true_positive = (
            confusion.diag().float()
        )

        support = confusion.sum(
            dim=1
        ).float()

        predicted_support = confusion.sum(
            dim=0
        ).float()

        precision = (
            true_positive
            / predicted_support.clamp_min(
                1.0
            )
        )

        recall = (
            true_positive
            / support.clamp_min(1.0)
        )

        f1 = (
            2.0
            * precision
            * recall
            / (
                precision + recall
            ).clamp_min(1e-12)
        )

        present = support > 0

        return (
            f1[present].mean().item()
            if present.any()
            else 0.0
        )

    modifier_precision = (
        modifier_tp
        / max(
            1,
            modifier_tp + modifier_fp,
        )
    )

    modifier_recall = (
        modifier_tp
        / max(
            1,
            modifier_tp + modifier_fn,
        )
    )

    modifier_f1 = (
        2.0
        * modifier_precision
        * modifier_recall
        / max(
            1e-12,
            modifier_precision
            + modifier_recall,
        )
    )

    return {
        "boundary_macro_f1": macro_f1(
            boundary_confusion
        ),
        "token_type_macro_f1": macro_f1(
            token_type_confusion
        ),
        "modifier_f1": modifier_f1,
    }


def train_epoch(
    model: SemanticTransformer,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    boundary_loss_function: nn.CrossEntropyLoss,
    token_type_loss_function: nn.CrossEntropyLoss,
    modifier_positive_weights: torch.Tensor,
    device: torch.device,
    modifier_loss_weight: float,
) -> tuple[
    float,
    float,
    float,
    float,
]:
    model.train()

    total_loss = 0.0
    total_boundary_loss = 0.0
    total_type_loss = 0.0
    total_modifier_loss = 0.0

    for step, batch in enumerate(
        loader,
        start=1,
    ):
        input_ids = batch[
            "input_ids"
        ].to(device)

        attention_mask = batch[
            "attention_mask"
        ].to(device)

        boundary_labels = batch[
            "boundary_labels"
        ].to(device)

        token_type_labels = batch[
            "token_type_labels"
        ].to(device)

        modifier_labels = batch[
            "modifier_labels"
        ].to(device)

        optimizer.zero_grad(
            set_to_none=True
        )

        output = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        boundary_loss = (
            boundary_loss_function(
                output.boundary_logits.reshape(
                    -1,
                    output.boundary_logits.shape[
                        -1
                    ],
                ),
                boundary_labels.reshape(-1),
            )
        )

        token_type_loss = (
            token_type_loss_function(
                output.token_type_logits.reshape(
                    -1,
                    output.token_type_logits.shape[
                        -1
                    ],
                ),
                token_type_labels.reshape(-1),
            )
        )

        begin_mask = (
            boundary_labels
            == BOUNDARY_BEGIN_ID
        )

        if begin_mask.any():
            modifier_loss = (
                F.binary_cross_entropy_with_logits(
                    output.modifier_logits[
                        begin_mask
                    ],
                    modifier_labels[
                        begin_mask
                    ],
                    pos_weight=(
                        modifier_positive_weights
                    ),
                )
            )
        else:
            modifier_loss = torch.zeros(
                (),
                device=device,
            )

        loss = (
            boundary_loss
            + token_type_loss
            + modifier_loss_weight
            * modifier_loss
        )

        loss.backward()

        nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0,
        )

        optimizer.step()

        total_loss += float(
            loss.item()
        )

        total_boundary_loss += float(
            boundary_loss.item()
        )

        total_type_loss += float(
            token_type_loss.item()
        )

        total_modifier_loss += float(
            modifier_loss.item()
        )

        if (
            step % 25 == 0
            or step == len(loader)
        ):
            print(
                f"  step "
                f"{step:>4}/{len(loader)} "
                f"loss={loss.item():.4f} "
                f"boundary={boundary_loss.item():.4f} "
                f"type={token_type_loss.item():.4f} "
                f"modifier={modifier_loss.item():.4f}"
            )

    batches = len(loader)

    return (
        total_loss / batches,
        total_boundary_loss / batches,
        total_type_loss / batches,
        total_modifier_loss / batches,
    )


def save_checkpoint(
    model: SemanticTransformer,
    dataset: TypeScriptSemanticDataset,
    output_path: Path,
    validation_metrics: dict[str, float],
    max_length: int,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    state_dict = {
        name: tensor.detach().cpu()
        for name, tensor
        in model.state_dict().items()
    }

    torch.save(
        {
            "format": (
                "nsh-typescript-v2-multitask"
            ),
            "model_state_dict": state_dict,
            "config": {
                "vocab_size": 257,
                "number_of_boundary_classes": (
                    NUMBER_OF_BOUNDARY_CLASSES
                ),
                "number_of_token_types": (
                    dataset.schema
                    .number_of_token_types
                ),
                "number_of_modifiers": len(
                    dataset.schema.modifiers
                ),
                "max_length": max_length,
                "embedding_dimension": 128,
                "number_of_heads": 4,
                "number_of_layers": 4,
                "feed_forward_dimension": 512,
            },
            "schema": {
                "token_types": list(
                    dataset.schema.token_types
                ),
                "modifiers": list(
                    dataset.schema.modifiers
                ),
            },
            "validation": validation_metrics,
        },
        output_path,
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3e-4,
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
    )

    parser.add_argument(
        "--modifier-loss-weight",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = select_device()

    print("Neural Semantic Highlighting")
    print(
        "TypeScript V2 Multitask Training"
    )
    print("")
    print(f"Device: {device}")
    print("")

    train_dataset = TypeScriptSemanticDataset(
        "train",
        max_length=args.max_length,
    )

    validation_dataset = (
        TypeScriptSemanticDataset(
            "validation",
            max_length=args.max_length,
        )
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        generator=(
            torch.Generator().manual_seed(
                args.seed
            )
        ),
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )

    model = SemanticTransformer(
        vocab_size=257,
        number_of_boundary_classes=(
            NUMBER_OF_BOUNDARY_CLASSES
        ),
        number_of_token_types=(
            train_dataset.schema
            .number_of_token_types
        ),
        number_of_modifiers=len(
            train_dataset.schema.modifiers
        ),
        max_length=args.max_length,
    ).to(device)

    print(
        f"Parameters: "
        f"{count_parameters(model):,}"
    )
    print(
        "Boundary classes: 3 "
        "(O / B / I)"
    )
    print(
        "Token types: "
        f"{train_dataset.schema.number_of_token_types}"
    )
    print(
        f"Train windows: "
        f"{len(train_dataset)}"
    )
    print(
        "Validation windows: "
        f"{len(validation_dataset)}"
    )
    print("")

    boundary_weights = (
        build_boundary_class_weights(
            train_dataset
        ).to(device)
    )

    token_type_weights = (
        build_token_type_class_weights(
            train_dataset
        ).to(device)
    )

    modifier_positive_weights = (
        build_modifier_positive_weights(
            train_dataset
        ).to(device)
    )

    boundary_loss_function = (
        nn.CrossEntropyLoss(
            weight=boundary_weights,
            ignore_index=IGNORE_LABEL_ID,
        )
    )

    token_type_loss_function = (
        nn.CrossEntropyLoss(
            weight=token_type_weights,
            ignore_index=IGNORE_LABEL_ID,
        )
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=0.01,
    )

    best_score = -1.0

    for epoch in range(
        1,
        args.epochs + 1,
    ):
        print(
            f"Epoch "
            f"{epoch}/{args.epochs}"
        )

        (
            training_loss,
            boundary_loss,
            token_type_loss,
            modifier_loss,
        ) = train_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            boundary_loss_function=(
                boundary_loss_function
            ),
            token_type_loss_function=(
                token_type_loss_function
            ),
            modifier_positive_weights=(
                modifier_positive_weights
            ),
            device=device,
            modifier_loss_weight=(
                args.modifier_loss_weight
            ),
        )

        diagnostics = diagnostic_metrics(
            model,
            validation_loader,
            validation_dataset,
            device,
        )

        exact = exact_span_metrics(
            validation_dataset,
            model,
            device,
        )

        metrics = {
            **diagnostics,
            **exact,
        }

        print("")
        print(
            "  train loss:          "
            f"{training_loss:.4f}"
        )
        print(
            "  boundary loss:       "
            f"{boundary_loss:.4f}"
        )
        print(
            "  token type loss:     "
            f"{token_type_loss:.4f}"
        )
        print(
            "  modifier loss:       "
            f"{modifier_loss:.4f}"
        )
        print(
            "  boundary macro F1:   "
            f"{metrics['boundary_macro_f1']:.4f}"
        )
        print(
            "  token type macro F1: "
            f"{metrics['token_type_macro_f1']:.4f}"
        )
        print(
            "  exact span F1:       "
            f"{metrics['exact_span_f1']:.4f}"
        )
        print(
            "  exact span macro F1: "
            f"{metrics['exact_span_macro_f1']:.4f}"
        )
        print(
            "  predicted/gold spans:"
            f" {int(metrics['predicted_spans'])}"
            f"/{int(metrics['gold_spans'])}"
        )
        print(
            "  modifier F1:         "
            f"{metrics['modifier_f1']:.4f}"
        )
        print("")

        score = metrics[
            "exact_span_macro_f1"
        ]

        if score > best_score:
            best_score = score

            save_checkpoint(
                model=model,
                dataset=train_dataset,
                output_path=args.output,
                validation_metrics=metrics,
                max_length=args.max_length,
            )

            print(
                "  ✓ saved new best "
                "checkpoint to "
                f"{args.output}"
            )
            print("")

    print("Training complete.")
    print(
        "Best exact span macro F1: "
        f"{best_score:.4f}"
    )
    print(
        f"Checkpoint: "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()
