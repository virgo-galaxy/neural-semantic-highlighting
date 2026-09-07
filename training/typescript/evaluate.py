from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from dataset import OUTSIDE_TOKEN_ID, TypeScriptSemanticDataset
from model import SemanticTransformer


DEFAULT_CHECKPOINT_PATH = Path("artifacts/typescript/best.pt")
DEFAULT_OUTPUT_PATH = Path("artifacts/typescript/test-metrics.json")


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def safe_divide(numerator: torch.Tensor, denominator: torch.Tensor) -> torch.Tensor:
    return numerator / denominator.clamp_min(1.0)


def load_model(
    checkpoint_path: Path,
    dataset: TypeScriptSemanticDataset,
    device: torch.device,
) -> tuple[SemanticTransformer, dict]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    checkpoint_schema = checkpoint["schema"]

    if tuple(checkpoint_schema["token_types"]) != dataset.schema.token_types:
        raise ValueError(
            "Checkpoint token-type schema does not match the current TypeScript schema."
        )

    if tuple(checkpoint_schema["modifiers"]) != dataset.schema.modifiers:
        raise ValueError(
            "Checkpoint modifier schema does not match the current TypeScript schema."
        )

    config = checkpoint["config"]

    model = SemanticTransformer(
        vocab_size=config["vocab_size"],
        number_of_token_classes=config["number_of_token_classes"],
        number_of_modifiers=config["number_of_modifiers"],
        max_length=config["max_length"],
        embedding_dimension=config["embedding_dimension"],
        number_of_heads=config["number_of_heads"],
        number_of_layers=config["number_of_layers"],
        feed_forward_dimension=config["feed_forward_dimension"],
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return model, checkpoint


def evaluate(
    model: SemanticTransformer,
    loader: DataLoader,
    dataset: TypeScriptSemanticDataset,
    device: torch.device,
) -> dict:
    number_of_token_classes = dataset.schema.number_of_token_classes
    number_of_modifiers = len(dataset.schema.modifiers)

    confusion = torch.zeros(
        (number_of_token_classes, number_of_token_classes),
        dtype=torch.long,
    )

    modifier_true_positive = torch.zeros(number_of_modifiers, dtype=torch.long)
    modifier_false_positive = torch.zeros(number_of_modifiers, dtype=torch.long)
    modifier_false_negative = torch.zeros(number_of_modifiers, dtype=torch.long)

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            token_type_labels = batch["token_type_labels"].to(device)
            modifier_labels = batch["modifier_labels"].to(device)

            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            token_predictions = output.token_type_logits.argmax(dim=-1)

            valid_mask = token_type_labels != -100

            targets = token_type_labels[valid_mask].detach().cpu()
            predictions = token_predictions[valid_mask].detach().cpu()

            indices = targets * number_of_token_classes + predictions

            confusion += torch.bincount(
                indices,
                minlength=number_of_token_classes * number_of_token_classes,
            ).reshape(number_of_token_classes, number_of_token_classes)

            semantic_mask = valid_mask & (
                token_type_labels != OUTSIDE_TOKEN_ID
            )

            if semantic_mask.any():
                predicted_modifiers = (
                    torch.sigmoid(output.modifier_logits[semantic_mask]) >= 0.5
                ).detach().cpu()

                target_modifiers = (
                    modifier_labels[semantic_mask] >= 0.5
                ).detach().cpu()

                modifier_true_positive += (
                    predicted_modifiers & target_modifiers
                ).sum(dim=0)

                modifier_false_positive += (
                    predicted_modifiers & ~target_modifiers
                ).sum(dim=0)

                modifier_false_negative += (
                    ~predicted_modifiers & target_modifiers
                ).sum(dim=0)

    true_positive = confusion.diag().float()
    target_support = confusion.sum(dim=1).float()
    prediction_support = confusion.sum(dim=0).float()

    precision = safe_divide(true_positive, prediction_support)
    recall = safe_divide(true_positive, target_support)

    f1 = (
        2.0
        * precision
        * recall
        / (precision + recall).clamp_min(1e-12)
    )

    overall_accuracy = (
        true_positive.sum() / confusion.sum().clamp_min(1)
    ).item()

    semantic_support = target_support[1:]
    semantic_correct = true_positive[1:].sum()

    semantic_accuracy = (
        semantic_correct / semantic_support.sum().clamp_min(1.0)
    ).item()

    semantic_present = semantic_support > 0

    if semantic_present.any():
        semantic_macro_f1 = f1[1:][semantic_present].mean().item()
    else:
        semantic_macro_f1 = 0.0

    token_names = ("O", *dataset.schema.token_types)

    token_metrics: dict[str, dict[str, float | int]] = {}

    for class_id, token_name in enumerate(token_names):
        token_metrics[token_name] = {
            "precision": float(precision[class_id].item()),
            "recall": float(recall[class_id].item()),
            "f1": float(f1[class_id].item()),
            "support": int(target_support[class_id].item()),
        }

    modifier_true_positive_f = modifier_true_positive.float()
    modifier_false_positive_f = modifier_false_positive.float()
    modifier_false_negative_f = modifier_false_negative.float()

    modifier_precision = safe_divide(
        modifier_true_positive_f,
        modifier_true_positive_f + modifier_false_positive_f,
    )

    modifier_recall = safe_divide(
        modifier_true_positive_f,
        modifier_true_positive_f + modifier_false_negative_f,
    )

    modifier_f1 = (
        2.0
        * modifier_precision
        * modifier_recall
        / (modifier_precision + modifier_recall).clamp_min(1e-12)
    )

    total_tp = int(modifier_true_positive.sum().item())
    total_fp = int(modifier_false_positive.sum().item())
    total_fn = int(modifier_false_negative.sum().item())

    modifier_micro_precision = total_tp / max(1, total_tp + total_fp)
    modifier_micro_recall = total_tp / max(1, total_tp + total_fn)

    modifier_micro_f1 = (
        2.0
        * modifier_micro_precision
        * modifier_micro_recall
        / max(
            1e-12,
            modifier_micro_precision + modifier_micro_recall,
        )
    )

    modifier_metrics: dict[str, dict[str, float | int]] = {}

    for modifier_id, modifier_name in enumerate(dataset.schema.modifiers):
        support = int(
            (
                modifier_true_positive[modifier_id]
                + modifier_false_negative[modifier_id]
            ).item()
        )

        modifier_metrics[modifier_name] = {
            "precision": float(modifier_precision[modifier_id].item()),
            "recall": float(modifier_recall[modifier_id].item()),
            "f1": float(modifier_f1[modifier_id].item()),
            "support": support,
        }

    return {
        "overall_accuracy": overall_accuracy,
        "semantic_accuracy": semantic_accuracy,
        "semantic_macro_f1": semantic_macro_f1,
        "modifier_micro_f1": modifier_micro_f1,
        "token_types": token_metrics,
        "modifiers": modifier_metrics,
    }


def print_metrics(metrics: dict, validation_metrics: dict | None) -> None:
    print("")
    print("Test summary")
    print("------------")
    print(f"Overall accuracy:    {metrics['overall_accuracy']:.4f}")
    print(f"Semantic accuracy:   {metrics['semantic_accuracy']:.4f}")
    print(f"Semantic macro F1:   {metrics['semantic_macro_f1']:.4f}")
    print(f"Modifier micro F1:   {metrics['modifier_micro_f1']:.4f}")

    if validation_metrics is not None:
        validation_macro_f1 = validation_metrics.get("semantic_macro_f1")

        if validation_macro_f1 is not None:
            print(f"Validation macro F1: {validation_macro_f1:.4f}")

    print("")
    print("Token types")
    print("-----------")
    print(
        f"{'token type':<18}"
        f"{'precision':>11}"
        f"{'recall':>11}"
        f"{'f1':>11}"
        f"{'support':>12}"
    )

    for token_name, values in metrics["token_types"].items():
        print(
            f"{token_name:<18}"
            f"{values['precision']:>11.4f}"
            f"{values['recall']:>11.4f}"
            f"{values['f1']:>11.4f}"
            f"{values['support']:>12}"
        )

    print("")
    print("Modifiers")
    print("---------")
    print(
        f"{'modifier':<18}"
        f"{'precision':>11}"
        f"{'recall':>11}"
        f"{'f1':>11}"
        f"{'support':>12}"
    )

    for modifier_name, values in metrics["modifiers"].items():
        print(
            f"{modifier_name:<18}"
            f"{values['precision']:>11.4f}"
            f"{values['recall']:>11.4f}"
            f"{values['f1']:>11.4f}"
            f"{values['support']:>12}"
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    device = select_device()

    print("Neural Semantic Highlighting")
    print("TypeScript Semantic Evaluation")
    print("")
    print(f"Device:     {device}")
    print(f"Checkpoint: {args.checkpoint}")

    checkpoint = torch.load(
        args.checkpoint,
        map_location="cpu",
    )

    max_length = checkpoint["config"]["max_length"]

    test_dataset = TypeScriptSemanticDataset(
        "test",
        max_length=max_length,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )

    model, checkpoint = load_model(
        checkpoint_path=args.checkpoint,
        dataset=test_dataset,
        device=device,
    )

    print(f"Test documents: {len(test_dataset.documents)}")
    print(f"Test windows:   {len(test_dataset)}")

    metrics = evaluate(
        model=model,
        loader=test_loader,
        dataset=test_dataset,
        device=device,
    )

    print_metrics(
        metrics,
        checkpoint.get("validation"),
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            metrics,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print("")
    print(f"Written to {args.output}")


if __name__ == "__main__":
    main()
