from __future__ import annotations

import argparse
import random
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader

from dataset import OUTSIDE_TOKEN_ID, TypeScriptSemanticDataset
from model import SemanticTransformer, count_parameters


DEFAULT_OUTPUT_PATH = Path("artifacts/typescript/best.pt")


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


def build_token_class_weights(
    dataset: TypeScriptSemanticDataset,
) -> torch.Tensor:
    number_of_classes = dataset.schema.number_of_token_classes

    counts = torch.zeros(
        number_of_classes,
        dtype=torch.long,
    )

    for document in dataset.documents:
        counts += torch.bincount(
            document.token_type_labels,
            minlength=number_of_classes,
        )

    present = counts > 0

    weights = torch.zeros(
        number_of_classes,
        dtype=torch.float32,
    )

    weights[present] = 1.0 / torch.sqrt(
        counts[present].float()
    )

    weights[present] /= weights[present].mean()

    weights = weights.clamp(
        min=0.25,
        max=4.0,
    )

    weights[~present] = 0.0

    return weights


def build_modifier_positive_weights(
    dataset: TypeScriptSemanticDataset,
) -> torch.Tensor:
    number_of_modifiers = len(dataset.schema.modifiers)

    positive_counts = torch.zeros(
        number_of_modifiers,
        dtype=torch.float32,
    )

    semantic_byte_count = 0

    for document in dataset.documents:
        semantic_mask = (
            document.token_type_labels != OUTSIDE_TOKEN_ID
        )

        semantic_byte_count += int(
            semantic_mask.sum().item()
        )

        if semantic_mask.any():
            positive_counts += (
                document.modifier_labels[
                    semantic_mask
                ]
                .sum(dim=0)
                .float()
            )

    negative_counts = (
        semantic_byte_count - positive_counts
    )

    positive_weights = (
        negative_counts
        / positive_counts.clamp_min(1.0)
    )

    positive_weights = positive_weights.clamp(
        min=1.0,
        max=20.0,
    )

    positive_weights[
        positive_counts == 0
    ] = 1.0

    return positive_weights


def train_epoch(
    model: SemanticTransformer,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    token_loss_function: nn.CrossEntropyLoss,
    modifier_positive_weights: torch.Tensor,
    device: torch.device,
    modifier_loss_weight: float,
) -> tuple[float, float, float]:
    model.train()

    total_loss = 0.0
    total_token_loss = 0.0
    total_modifier_loss = 0.0

    for step, batch in enumerate(loader, start=1):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(
            device
        )
        token_type_labels = batch[
            "token_type_labels"
        ].to(device)
        modifier_labels = batch[
            "modifier_labels"
        ].to(device)

        optimizer.zero_grad(set_to_none=True)

        output = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        token_loss = token_loss_function(
            output.token_type_logits.reshape(
                -1,
                output.token_type_logits.shape[-1],
            ),
            token_type_labels.reshape(-1),
        )

        modifier_loss_matrix = (
            F.binary_cross_entropy_with_logits(
                output.modifier_logits,
                modifier_labels,
                pos_weight=modifier_positive_weights,
                reduction="none",
            )
        )

        semantic_mask = (
            token_type_labels != -100
        ) & (
            token_type_labels != OUTSIDE_TOKEN_ID
        )

        if semantic_mask.any():
            modifier_loss = (
                modifier_loss_matrix[
                    semantic_mask
                ].mean()
            )
        else:
            modifier_loss = torch.zeros(
                (),
                device=device,
            )

        loss = (
            token_loss
            + modifier_loss_weight
            * modifier_loss
        )

        loss.backward()

        nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0,
        )

        optimizer.step()

        total_loss += float(loss.item())
        total_token_loss += float(
            token_loss.item()
        )
        total_modifier_loss += float(
            modifier_loss.item()
        )

        if step % 25 == 0 or step == len(loader):
            print(
                f"  step {step:>4}/{len(loader)} "
                f"loss={loss.item():.4f} "
                f"token={token_loss.item():.4f} "
                f"modifier={modifier_loss.item():.4f}"
            )

    number_of_batches = len(loader)

    return (
        total_loss / number_of_batches,
        total_token_loss / number_of_batches,
        total_modifier_loss / number_of_batches,
    )


def evaluate(
    model: SemanticTransformer,
    loader: DataLoader,
    device: torch.device,
    number_of_token_classes: int,
) -> dict[str, float]:
    model.eval()

    confusion = torch.zeros(
        (
            number_of_token_classes,
            number_of_token_classes,
        ),
        dtype=torch.long,
    )

    modifier_true_positive = 0
    modifier_false_positive = 0
    modifier_false_negative = 0

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(
                device
            )
            attention_mask = batch[
                "attention_mask"
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

            predictions = (
                output.token_type_logits.argmax(
                    dim=-1
                )
            )

            valid_mask = (
                token_type_labels != -100
            )

            targets = token_type_labels[
                valid_mask
            ].detach().cpu()

            predicted = predictions[
                valid_mask
            ].detach().cpu()

            indices = (
                targets
                * number_of_token_classes
                + predicted
            )

            confusion += torch.bincount(
                indices,
                minlength=(
                    number_of_token_classes
                    * number_of_token_classes
                ),
            ).reshape(
                number_of_token_classes,
                number_of_token_classes,
            )

            semantic_mask = valid_mask & (
                token_type_labels
                != OUTSIDE_TOKEN_ID
            )

            if semantic_mask.any():
                modifier_predictions = (
                    torch.sigmoid(
                        output.modifier_logits[
                            semantic_mask
                        ]
                    )
                    >= 0.5
                )

                modifier_targets = (
                    modifier_labels[
                        semantic_mask
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

    true_positive = confusion.diag().float()

    target_support = confusion.sum(
        dim=1
    ).float()

    prediction_support = confusion.sum(
        dim=0
    ).float()

    precision = (
        true_positive
        / prediction_support.clamp_min(1.0)
    )

    recall = (
        true_positive
        / target_support.clamp_min(1.0)
    )

    f1 = (
        2.0
        * precision
        * recall
        / (precision + recall).clamp_min(
            1e-12
        )
    )

    overall_accuracy = (
        true_positive.sum()
        / confusion.sum().clamp_min(1)
    ).item()

    semantic_support = target_support[
        1:
    ]

    semantic_correct = true_positive[
        1:
    ].sum()

    semantic_accuracy = (
        semantic_correct
        / semantic_support.sum().clamp_min(
            1.0
        )
    ).item()

    semantic_present = (
        semantic_support > 0
    )

    if semantic_present.any():
        semantic_macro_f1 = (
            f1[1:][semantic_present]
            .mean()
            .item()
        )
    else:
        semantic_macro_f1 = 0.0

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
        "overall_accuracy": overall_accuracy,
        "semantic_accuracy": semantic_accuracy,
        "semantic_macro_f1": semantic_macro_f1,
        "modifier_f1": modifier_f1,
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
            "model_state_dict": state_dict,
            "config": {
                "vocab_size": 257,
                "number_of_token_classes": (
                    dataset.schema
                    .number_of_token_classes
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
        default=0.25,
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
    print("TypeScript Semantic Training")
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
        generator=torch.Generator().manual_seed(
            args.seed
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
        number_of_token_classes=(
            train_dataset.schema
            .number_of_token_classes
        ),
        number_of_modifiers=len(
            train_dataset.schema.modifiers
        ),
        max_length=args.max_length,
    ).to(device)

    print(
        f"Parameters: {count_parameters(model):,}"
    )
    print(
        f"Train windows: {len(train_dataset)}"
    )
    print(
        "Validation windows: "
        f"{len(validation_dataset)}"
    )
    print("")

    token_class_weights = (
        build_token_class_weights(
            train_dataset
        ).to(device)
    )

    modifier_positive_weights = (
        build_modifier_positive_weights(
            train_dataset
        ).to(device)
    )

    token_loss_function = nn.CrossEntropyLoss(
        weight=token_class_weights,
        ignore_index=-100,
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
            f"Epoch {epoch}/{args.epochs}"
        )

        (
            training_loss,
            token_loss,
            modifier_loss,
        ) = train_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            token_loss_function=(
                token_loss_function
            ),
            modifier_positive_weights=(
                modifier_positive_weights
            ),
            device=device,
            modifier_loss_weight=(
                args.modifier_loss_weight
            ),
        )

        metrics = evaluate(
            model=model,
            loader=validation_loader,
            device=device,
            number_of_token_classes=(
                train_dataset.schema
                .number_of_token_classes
            ),
        )

        print("")
        print(
            f"  train loss:        "
            f"{training_loss:.4f}"
        )
        print(
            f"  token loss:        "
            f"{token_loss:.4f}"
        )
        print(
            f"  modifier loss:     "
            f"{modifier_loss:.4f}"
        )
        print(
            f"  overall accuracy:  "
            f"{metrics['overall_accuracy']:.4f}"
        )
        print(
            f"  semantic accuracy: "
            f"{metrics['semantic_accuracy']:.4f}"
        )
        print(
            f"  semantic macro F1: "
            f"{metrics['semantic_macro_f1']:.4f}"
        )
        print(
            f"  modifier F1:       "
            f"{metrics['modifier_f1']:.4f}"
        )
        print("")

        score = metrics[
            "semantic_macro_f1"
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
                "  ✓ saved new best checkpoint "
                f"to {args.output}"
            )
            print("")

    print("Training complete.")
    print(
        f"Best semantic macro F1: "
        f"{best_score:.4f}"
    )
    print(
        f"Checkpoint: {args.output}"
    )


if __name__ == "__main__":
    main()
