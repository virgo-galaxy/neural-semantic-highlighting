from __future__ import annotations

import argparse
import random
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader

from dataset import (
    IGNORE_LABEL_ID,
    OUTSIDE_TAG_ID,
    TypeScriptSemanticDataset,
)
from model import (
    SemanticTransformer,
    count_parameters,
)


DEFAULT_OUTPUT_PATH = Path(
    "artifacts/typescript/v1-bio/best.pt"
)


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


def build_semantic_tag_class_weights(
    dataset: TypeScriptSemanticDataset,
) -> torch.Tensor:
    number_of_classes = (
        dataset.schema
        .number_of_semantic_tag_classes
    )

    counts = torch.zeros(
        number_of_classes,
        dtype=torch.long,
    )

    for document in dataset.documents:
        labels = (
            document.semantic_tag_labels
        )

        valid_labels = labels[
            labels != IGNORE_LABEL_ID
        ]

        counts += torch.bincount(
            valid_labels,
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

    weights[present] /= (
        weights[present].mean()
    )

    # Boundary classes are naturally rarer than inside classes,
    # so inverse-square-root weighting gives them extra attention
    # without letting a tiny class dominate the objective.
    weights = weights.clamp(
        min=0.25,
        max=4.0,
    )

    weights[~present] = 0.0

    return weights


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

    number_of_token_types = (
        dataset.schema
        .number_of_token_types
    )

    for document in dataset.documents:
        labels = (
            document.semantic_tag_labels
        )

        begin_mask = (
            (labels >= 1)
            & (
                labels
                <= number_of_token_types
            )
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
        begin_count
        - positive_counts
    )

    positive_weights = (
        negative_counts
        / positive_counts.clamp_min(1.0)
    )

    # V0 over-predicted rare modifiers. V1 keeps the correction
    # deliberately conservative.
    positive_weights = (
        positive_weights.clamp(
            min=1.0,
            max=4.0,
        )
    )

    positive_weights[
        positive_counts == 0
    ] = 1.0

    return positive_weights


def collapse_tag_ids_to_token_type_ids(
    tag_ids: torch.Tensor,
    number_of_token_types: int,
) -> torch.Tensor:
    result = torch.zeros_like(
        tag_ids
    )

    semantic_mask = (
        tag_ids > OUTSIDE_TAG_ID
    )

    result[semantic_mask] = (
        (
            tag_ids[semantic_mask]
            - 1
        )
        % number_of_token_types
    ) + 1

    return result


def train_epoch(
    model: SemanticTransformer,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    semantic_tag_loss_function: nn.CrossEntropyLoss,
    modifier_positive_weights: torch.Tensor,
    device: torch.device,
    number_of_token_types: int,
    modifier_loss_weight: float,
) -> tuple[float, float, float]:
    model.train()

    total_loss = 0.0
    total_tag_loss = 0.0
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

        semantic_tag_labels = batch[
            "semantic_tag_labels"
        ].to(device)

        modifier_labels = batch[
            "modifier_labels"
        ].to(device)

        optimizer.zero_grad(
            set_to_none=True
        )

        output = model(
            input_ids=input_ids,
            attention_mask=(
                attention_mask
            ),
        )

        semantic_tag_loss = (
            semantic_tag_loss_function(
                output.semantic_tag_logits.reshape(
                    -1,
                    output.semantic_tag_logits.shape[
                        -1
                    ],
                ),
                semantic_tag_labels.reshape(
                    -1
                ),
            )
        )

        begin_mask = (
            (semantic_tag_labels >= 1)
            & (
                semantic_tag_labels
                <= number_of_token_types
            )
        )

        if begin_mask.any():
            modifier_loss_matrix = (
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
                    reduction="none",
                )
            )

            modifier_loss = (
                modifier_loss_matrix.mean()
            )
        else:
            modifier_loss = torch.zeros(
                (),
                device=device,
            )

        loss = (
            semantic_tag_loss
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

        total_tag_loss += float(
            semantic_tag_loss.item()
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
                f"tag={semantic_tag_loss.item():.4f} "
                f"modifier={modifier_loss.item():.4f}"
            )

    number_of_batches = len(
        loader
    )

    return (
        total_loss / number_of_batches,
        total_tag_loss
        / number_of_batches,
        total_modifier_loss
        / number_of_batches,
    )


def evaluate(
    model: SemanticTransformer,
    loader: DataLoader,
    device: torch.device,
    number_of_semantic_tag_classes: int,
    number_of_token_types: int,
) -> dict[str, float]:
    model.eval()

    tag_confusion = torch.zeros(
        (
            number_of_semantic_tag_classes,
            number_of_semantic_tag_classes,
        ),
        dtype=torch.long,
    )

    type_confusion = torch.zeros(
        (
            number_of_token_types + 1,
            number_of_token_types + 1,
        ),
        dtype=torch.long,
    )

    modifier_true_positive = 0
    modifier_false_positive = 0
    modifier_false_negative = 0

    with torch.no_grad():
        for batch in loader:
            input_ids = batch[
                "input_ids"
            ].to(device)

            attention_mask = batch[
                "attention_mask"
            ].to(device)

            semantic_tag_labels = (
                batch[
                    "semantic_tag_labels"
                ].to(device)
            )

            modifier_labels = batch[
                "modifier_labels"
            ].to(device)

            output = model(
                input_ids=input_ids,
                attention_mask=(
                    attention_mask
                ),
            )

            predictions = (
                output.semantic_tag_logits.argmax(
                    dim=-1
                )
            )

            valid_mask = (
                semantic_tag_labels
                != IGNORE_LABEL_ID
            )

            targets = (
                semantic_tag_labels[
                    valid_mask
                ]
                .detach()
                .cpu()
            )

            predicted = (
                predictions[
                    valid_mask
                ]
                .detach()
                .cpu()
            )

            tag_indices = (
                targets
                * number_of_semantic_tag_classes
                + predicted
            )

            tag_confusion += torch.bincount(
                tag_indices,
                minlength=(
                    number_of_semantic_tag_classes
                    * number_of_semantic_tag_classes
                ),
            ).reshape(
                number_of_semantic_tag_classes,
                number_of_semantic_tag_classes,
            )

            target_types = (
                collapse_tag_ids_to_token_type_ids(
                    targets,
                    number_of_token_types,
                )
            )

            predicted_types = (
                collapse_tag_ids_to_token_type_ids(
                    predicted,
                    number_of_token_types,
                )
            )

            type_indices = (
                target_types
                * (number_of_token_types + 1)
                + predicted_types
            )

            type_confusion += torch.bincount(
                type_indices,
                minlength=(
                    (number_of_token_types + 1)
                    * (number_of_token_types + 1)
                ),
            ).reshape(
                number_of_token_types + 1,
                number_of_token_types + 1,
            )

            begin_mask = (
                (semantic_tag_labels >= 1)
                & (
                    semantic_tag_labels
                    <= number_of_token_types
                )
            )

            if begin_mask.any():
                modifier_predictions = (
                    torch.sigmoid(
                        output.modifier_logits[
                            begin_mask
                        ]
                    )
                    >= 0.5
                )

                modifier_targets = (
                    modifier_labels[
                        begin_mask
                    ]
                    >= 0.5
                )

                modifier_true_positive += int(
                    (
                        modifier_predictions
                        & modifier_targets
                    )
                    .sum()
                    .item()
                )

                modifier_false_positive += int(
                    (
                        modifier_predictions
                        & ~modifier_targets
                    )
                    .sum()
                    .item()
                )

                modifier_false_negative += int(
                    (
                        ~modifier_predictions
                        & modifier_targets
                    )
                    .sum()
                    .item()
                )

    tag_true_positive = (
        tag_confusion.diag().float()
    )

    tag_support = (
        tag_confusion.sum(
            dim=1
        ).float()
    )

    tag_prediction_support = (
        tag_confusion.sum(
            dim=0
        ).float()
    )

    tag_precision = (
        tag_true_positive
        / tag_prediction_support.clamp_min(
            1.0
        )
    )

    tag_recall = (
        tag_true_positive
        / tag_support.clamp_min(1.0)
    )

    tag_f1 = (
        2.0
        * tag_precision
        * tag_recall
        / (
            tag_precision
            + tag_recall
        ).clamp_min(1e-12)
    )

    tag_present = tag_support > 0

    tag_macro_f1 = (
        tag_f1[tag_present]
        .mean()
        .item()
        if tag_present.any()
        else 0.0
    )

    type_true_positive = (
        type_confusion.diag().float()
    )

    type_support = (
        type_confusion.sum(
            dim=1
        ).float()
    )

    type_prediction_support = (
        type_confusion.sum(
            dim=0
        ).float()
    )

    type_precision = (
        type_true_positive
        / type_prediction_support.clamp_min(
            1.0
        )
    )

    type_recall = (
        type_true_positive
        / type_support.clamp_min(
            1.0
        )
    )

    type_f1 = (
        2.0
        * type_precision
        * type_recall
        / (
            type_precision
            + type_recall
        ).clamp_min(1e-12)
    )

    semantic_support = (
        type_support[1:]
    )

    semantic_correct = (
        type_true_positive[1:].sum()
    )

    semantic_type_accuracy = (
        semantic_correct
        / semantic_support.sum().clamp_min(
            1.0
        )
    ).item()

    semantic_present = (
        semantic_support > 0
    )

    semantic_type_macro_f1 = (
        type_f1[1:][semantic_present]
        .mean()
        .item()
        if semantic_present.any()
        else 0.0
    )

    modifier_precision = (
        modifier_true_positive
        / max(
            1,
            modifier_true_positive
            + modifier_false_positive,
        )
    )

    modifier_recall = (
        modifier_true_positive
        / max(
            1,
            modifier_true_positive
            + modifier_false_negative,
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
        "tag_macro_f1": (
            tag_macro_f1
        ),
        "semantic_type_accuracy": (
            semantic_type_accuracy
        ),
        "semantic_type_macro_f1": (
            semantic_type_macro_f1
        ),
        "modifier_f1": (
            modifier_f1
        ),
    }


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
            "format": "nsh-typescript-v1-bio",
            "model_state_dict": state_dict,
            "config": {
                "vocab_size": 257,
                "number_of_semantic_tag_classes": (
                    dataset.schema
                    .number_of_semantic_tag_classes
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
                "semantic_tags": list(
                    dataset.schema
                    .semantic_tag_names
                ),
            },
            "validation": (
                validation_metrics
            ),
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

    print(
        "Neural Semantic Highlighting"
    )
    print(
        "TypeScript BIO Semantic Training"
    )
    print("")
    print(f"Device: {device}")
    print("")

    train_dataset = (
        TypeScriptSemanticDataset(
            "train",
            max_length=args.max_length,
        )
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
        number_of_semantic_tag_classes=(
            train_dataset.schema
            .number_of_semantic_tag_classes
        ),
        number_of_modifiers=len(
            train_dataset.schema.modifiers
        ),
        max_length=args.max_length,
    ).to(device)

    print(
        "Parameters: "
        f"{count_parameters(model):,}"
    )
    print(
        "Semantic tag classes: "
        f"{train_dataset.schema.number_of_semantic_tag_classes}"
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

    semantic_tag_class_weights = (
        build_semantic_tag_class_weights(
            train_dataset
        ).to(device)
    )

    modifier_positive_weights = (
        build_modifier_positive_weights(
            train_dataset
        ).to(device)
    )

    semantic_tag_loss_function = (
        nn.CrossEntropyLoss(
            weight=(
                semantic_tag_class_weights
            ),
            ignore_index=(
                IGNORE_LABEL_ID
            ),
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
            tag_loss,
            modifier_loss,
        ) = train_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            semantic_tag_loss_function=(
                semantic_tag_loss_function
            ),
            modifier_positive_weights=(
                modifier_positive_weights
            ),
            device=device,
            number_of_token_types=(
                train_dataset.schema
                .number_of_token_types
            ),
            modifier_loss_weight=(
                args.modifier_loss_weight
            ),
        )

        metrics = evaluate(
            model=model,
            loader=validation_loader,
            device=device,
            number_of_semantic_tag_classes=(
                train_dataset.schema
                .number_of_semantic_tag_classes
            ),
            number_of_token_types=(
                train_dataset.schema
                .number_of_token_types
            ),
        )

        print("")
        print(
            "  train loss:            "
            f"{training_loss:.4f}"
        )
        print(
            "  semantic tag loss:     "
            f"{tag_loss:.4f}"
        )
        print(
            "  modifier loss:         "
            f"{modifier_loss:.4f}"
        )
        print(
            "  tag macro F1:          "
            f"{metrics['tag_macro_f1']:.4f}"
        )
        print(
            "  semantic type accuracy:"
            f" {metrics['semantic_type_accuracy']:.4f}"
        )
        print(
            "  semantic type macro F1:"
            f" {metrics['semantic_type_macro_f1']:.4f}"
        )
        print(
            "  modifier F1:           "
            f"{metrics['modifier_f1']:.4f}"
        )
        print("")

        score = metrics[
            "semantic_type_macro_f1"
        ]

        if score > best_score:
            best_score = score

            save_checkpoint(
                model=model,
                dataset=train_dataset,
                output_path=(
                    args.output
                ),
                validation_metrics=(
                    metrics
                ),
                max_length=(
                    args.max_length
                ),
            )

            print(
                "  ✓ saved new best "
                "checkpoint to "
                f"{args.output}"
            )
            print("")

    print("Training complete.")
    print(
        "Best semantic type macro F1: "
        f"{best_score:.4f}"
    )
    print(
        f"Checkpoint: {args.output}"
    )


if __name__ == "__main__":
    main()
