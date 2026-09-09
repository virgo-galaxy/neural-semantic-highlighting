from __future__ import annotations

import argparse
import copy
import random
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader

from config import (
    CHECKPOINT_FORMAT,
    DEFAULT_BEST_CHECKPOINT_PATH,
    DEFAULT_LAST_CHECKPOINT_PATH,
    DEFAULT_MAX_LENGTH,
    DEFAULT_TRAIN_BATCH_SIZE,
    MODEL_EMBEDDING_DIMENSION,
    MODEL_FEED_FORWARD_DIMENSION,
    MODEL_NUMBER_OF_HEADS,
    MODEL_NUMBER_OF_LAYERS,
    REGEXP_FOCUS_BATCH_SIZE,
    REGEXP_FOCUS_CONTEXT_BEFORE_BYTES,
    REGEXP_FOCUS_HALO_BYTES,
    REGEXP_FOCUS_WINDOW_LENGTH,
)
from dataset import (
    BOUNDARY_BEGIN_ID,
    BOUNDARY_INSIDE_ID,
    BOUNDARY_OUTSIDE_ID,
    IGNORE_LABEL_ID,
    NUMBER_OF_BOUNDARY_CLASSES,
    EncodedDocument,
    RegExpFocusDataset,
    TypeScriptSemanticDataset,
)
from inference import predict_document_logits
from model import (
    SemanticTransformer,
    count_parameters,
)


DEFAULT_OUTPUT_PATH = DEFAULT_BEST_CHECKPOINT_PATH
DEFAULT_LAST_OUTPUT_PATH = DEFAULT_LAST_CHECKPOINT_PATH

AUXILIARY_BEST_METRICS = {
    "exact": "exact_span_f1",
    "boundary": "boundary_macro_f1",
    "token-type": "token_type_macro_f1",
    "modifier": "modifier_f1",
}


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


def build_character_points(
    source: str,
) -> list[CharacterPoint]:
    points: list[
        CharacterPoint
    ] = []

    utf16_offset = 0
    byte_offset = 0

    for character in source:
        utf16_length = (
            len(
                character.encode(
                    "utf-16-le"
                )
            )
            // 2
        )

        points.append(
            CharacterPoint(
                utf16_start=(
                    utf16_offset
                ),
                utf16_end=(
                    utf16_offset
                    + utf16_length
                ),
                byte_start=byte_offset,
            )
        )

        utf16_offset += (
            utf16_length
        )

        byte_offset += len(
            character.encode("utf-8")
        )

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
            label_tensor
            != IGNORE_LABEL_ID
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

    weights[present] /= (
        weights[present].mean()
    )

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
            for document
            in dataset.documents
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
            for document
            in dataset.documents
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
        begin_count
        - positive_counts
    )

    positive_weights = (
        negative_counts
        / positive_counts.clamp_min(1.0)
    )

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

    current_start: int | None = (
        None
    )

    def flush(
        end_index: int,
    ) -> None:
        nonlocal current_start

        if current_start is not None:
            span_ranges.append(
                (
                    current_start,
                    end_index,
                )
            )

        current_start = None

    for (
        index,
        boundary_id,
    ) in enumerate(boundary_ids):
        if (
            boundary_id
            == BOUNDARY_OUTSIDE_ID
        ):
            flush(index)
            continue

        if (
            boundary_id
            == BOUNDARY_BEGIN_ID
        ):
            flush(index)
            current_start = index
            continue

        if (
            boundary_id
            == BOUNDARY_INSIDE_ID
        ):
            if current_start is None:
                current_start = index

            continue

        raise ValueError(
            f"Unknown boundary id "
            f"{boundary_id}."
        )

    flush(len(points))

    spans: list[
        PredictedSpan
    ] = []

    token_types = (
        dataset.schema.token_types
    )

    modifiers = (
        dataset.schema.modifiers
    )

    for (
        start_index,
        end_index,
    ) in span_ranges:
        span_points = points[
            start_index:end_index
        ]

        byte_positions = torch.tensor(
            [
                point.byte_start
                for point
                in span_points
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

        modifier_probabilities = (
            torch.sigmoid(
                modifier_logits[
                    start_point.byte_start
                ]
            )
        )

        predicted_modifiers = tuple(
            modifier
            for (
                modifier,
                probability,
            ) in zip(
                modifiers,
                modifier_probabilities.tolist(),
                strict=True,
            )
            if probability
            >= modifier_threshold
        )

        spans.append(
            PredictedSpan(
                start=(
                    start_point.utf16_start
                ),
                end=(
                    end_point.utf16_end
                ),
                token_type=(
                    token_types[
                        token_type_id
                    ]
                ),
                modifiers=(
                    predicted_modifiers
                ),
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
        set[
            tuple[
                str,
                int,
                int,
                str,
            ]
        ],
    ] = {
        token_type: set()
        for token_type
        in dataset.schema.token_types
    }

    per_type_gold: dict[
        str,
        set[
            tuple[
                str,
                int,
                int,
                str,
            ]
        ],
    ] = {
        token_type: set()
        for token_type
        in dataset.schema.token_types
    }

    for document in (
        dataset.documents
    ):
        (
            boundary_logits,
            token_type_logits,
            modifier_logits,
        ) = predict_document_logits(
            model,
            document.source,
            max_length=(
                dataset.max_length
            ),
            device=device,
        )

        predicted_spans = (
            decode_predicted_spans(
                document,
                boundary_logits,
                token_type_logits,
                modifier_logits,
                dataset,
            )
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

        for span in (
            document.gold_spans
        ):
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

    macro_values: list[
        float
    ] = []

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

        tp = len(
            predicted & gold
        )

        fp = len(
            predicted - gold
        )

        fn = len(
            gold - predicted
        )

        type_precision = (
            tp
            / max(1, tp + fp)
        )

        type_recall = (
            tp
            / max(1, tp + fn)
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

        macro_values.append(
            type_f1
        )

    macro_f1 = (
        sum(macro_values)
        / len(macro_values)
        if macro_values
        else 0.0
    )

    return {
        "exact_span_precision": (
            precision
        ),
        "exact_span_recall": recall,
        "exact_span_f1": f1,
        "exact_span_macro_f1": (
            macro_f1
        ),
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
    boundary_confusion = (
        torch.zeros(
            (
                NUMBER_OF_BOUNDARY_CLASSES,
                NUMBER_OF_BOUNDARY_CLASSES,
            ),
            dtype=torch.long,
        )
    )

    token_type_count = (
        dataset.schema
        .number_of_token_types
    )

    token_type_confusion = (
        torch.zeros(
            (
                token_type_count,
                token_type_count,
            ),
            dtype=torch.long,
        )
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
                attention_mask=(
                    attention_mask
                ),
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

            boundary_confusion += (
                torch.bincount(
                    boundary_indices,
                    minlength=(
                        NUMBER_OF_BOUNDARY_CLASSES
                        * NUMBER_OF_BOUNDARY_CLASSES
                    ),
                ).reshape(
                    NUMBER_OF_BOUNDARY_CLASSES,
                    NUMBER_OF_BOUNDARY_CLASSES,
                )
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

            token_type_confusion += (
                torch.bincount(
                    type_indices,
                    minlength=(
                        token_type_count
                        * token_type_count
                    ),
                ).reshape(
                    token_type_count,
                    token_type_count,
                )
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

        support = (
            confusion.sum(
                dim=1
            ).float()
        )

        predicted_support = (
            confusion.sum(
                dim=0
            ).float()
        )

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
            f1[present]
            .mean()
            .item()
            if present.any()
            else 0.0
        )

    modifier_precision = (
        modifier_tp
        / max(
            1,
            modifier_tp
            + modifier_fp,
        )
    )

    modifier_recall = (
        modifier_tp
        / max(
            1,
            modifier_tp
            + modifier_fn,
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
        "boundary_macro_f1": (
            macro_f1(
                boundary_confusion
            )
        ),
        "token_type_macro_f1": (
            macro_f1(
                token_type_confusion
            )
        ),
        "modifier_f1": (
            modifier_f1
        ),
    }


def _optimizer_step(
    model: SemanticTransformer,
    batch: dict[str, torch.Tensor],
    optimizer: torch.optim.Optimizer,
    boundary_loss_function: nn.CrossEntropyLoss,
    token_type_loss_function: nn.CrossEntropyLoss,
    modifier_positive_weights: torch.Tensor,
    device: torch.device,
    modifier_loss_weight: float,
    *,
    include_modifier: bool,
) -> tuple[float, float, float, float]:
    input_ids = batch["input_ids"].to(device)
    attention_mask = batch["attention_mask"].to(device)
    boundary_labels = batch["boundary_labels"].to(device)
    token_type_labels = batch["token_type_labels"].to(device)
    modifier_labels = batch["modifier_labels"].to(device)

    optimizer.zero_grad(set_to_none=True)

    output = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
    )

    boundary_loss = boundary_loss_function(
        output.boundary_logits.reshape(-1, output.boundary_logits.shape[-1]),
        boundary_labels.reshape(-1),
    )
    token_type_loss = token_type_loss_function(
        output.token_type_logits.reshape(-1, output.token_type_logits.shape[-1]),
        token_type_labels.reshape(-1),
    )

    begin_mask = boundary_labels == BOUNDARY_BEGIN_ID
    if include_modifier and begin_mask.any():
        modifier_loss = F.binary_cross_entropy_with_logits(
            output.modifier_logits[begin_mask],
            modifier_labels[begin_mask],
            pos_weight=modifier_positive_weights,
        )
    else:
        modifier_loss = torch.zeros((), device=device)

    loss = (
        boundary_loss
        + token_type_loss
        + modifier_loss_weight * modifier_loss
    )

    loss.backward()
    nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()

    return (
        float(loss.item()),
        float(boundary_loss.item()),
        float(token_type_loss.item()),
        float(modifier_loss.item()),
    )


def train_epoch(
    model: SemanticTransformer,
    loader: DataLoader,
    regexp_focus_loader: DataLoader,
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
    float,
    int,
    float,
]:
    model.train()

    total_loss = 0.0
    total_boundary_loss = 0.0
    total_type_loss = 0.0
    total_modifier_loss = 0.0

    regexp_focus_loss = 0.0
    regexp_focus_steps = 0

    normal_steps = len(loader)
    focus_steps = len(regexp_focus_loader)
    total_optimizer_steps = normal_steps + focus_steps
    completed_optimizer_steps = 0

    focus_iterator = iter(regexp_focus_loader)
    started = time.perf_counter()

    for step, batch in enumerate(loader, start=1):
        (
            loss,
            boundary_loss,
            token_type_loss,
            modifier_loss,
        ) = _optimizer_step(
            model,
            batch,
            optimizer,
            boundary_loss_function,
            token_type_loss_function,
            modifier_positive_weights,
            device,
            modifier_loss_weight,
            include_modifier=True,
        )

        total_loss += loss
        total_boundary_loss += boundary_loss
        total_type_loss += token_type_loss
        total_modifier_loss += modifier_loss
        completed_optimizer_steps += 1

        target_focus_steps = (step * focus_steps) // max(normal_steps, 1)
        while regexp_focus_steps < target_focus_steps:
            focus_batch = next(focus_iterator)
            (
                focus_loss,
                _,
                _,
                _,
            ) = _optimizer_step(
                model,
                focus_batch,
                optimizer,
                boundary_loss_function,
                token_type_loss_function,
                modifier_positive_weights,
                device,
                modifier_loss_weight,
                include_modifier=False,
            )
            regexp_focus_loss += focus_loss
            regexp_focus_steps += 1
            completed_optimizer_steps += 1

        if step % 25 == 0 or step == normal_steps:
            elapsed = max(time.perf_counter() - started, 1e-9)
            rate = completed_optimizer_steps / elapsed
            remaining = (
                (total_optimizer_steps - completed_optimizer_steps) / rate
                if rate > 0
                else 0.0
            )

            print(
                f"  main {step:>4}/{normal_steps} "
                f"regexp {regexp_focus_steps:>3}/{focus_steps} "
                f"loss={loss:.4f} "
                f"boundary={boundary_loss:.4f} "
                f"type={token_type_loss:.4f} "
                f"modifier={modifier_loss:.4f} "
                f"ETA={format_duration(remaining)}",
                flush=True,
            )

    if regexp_focus_steps != focus_steps:
        raise RuntimeError(
            f"RegExp focus curriculum ran {regexp_focus_steps}/{focus_steps} batches."
        )

    elapsed = time.perf_counter() - started

    return (
        total_loss / max(normal_steps, 1),
        total_boundary_loss / max(normal_steps, 1),
        total_type_loss / max(normal_steps, 1),
        total_modifier_loss / max(normal_steps, 1),
        regexp_focus_loss / max(regexp_focus_steps, 1),
        regexp_focus_steps,
        elapsed,
    )

def cpu_optimizer_state_dict(
    optimizer: torch.optim.Optimizer,
) -> dict:
    state_dict = copy.deepcopy(
        optimizer.state_dict()
    )

    for state in (
        state_dict["state"].values()
    ):
        for key, value in list(
            state.items()
        ):
            if torch.is_tensor(value):
                state[key] = (
                    value.detach().cpu()
                )

    return state_dict


def save_checkpoint(
    model: SemanticTransformer,
    optimizer: torch.optim.Optimizer,
    dataset: TypeScriptSemanticDataset,
    output_path: Path,
    validation_metrics: dict[str, float],
    max_length: int,
    epoch: int,
    best_score: float,
    best_epoch: int,
    epochs_without_improvement: int,
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
                CHECKPOINT_FORMAT
            ),
            "epoch": epoch,
            "model_state_dict": (
                state_dict
            ),
            "optimizer_state_dict": (
                cpu_optimizer_state_dict(
                    optimizer
                )
            ),
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
                "train_windowing": "adaptive-cursor",
                "embedding_dimension": MODEL_EMBEDDING_DIMENSION,
                "number_of_heads": MODEL_NUMBER_OF_HEADS,
                "number_of_layers": MODEL_NUMBER_OF_LAYERS,
                "feed_forward_dimension": MODEL_FEED_FORWARD_DIMENSION,
                "regexp_focus_window_length": REGEXP_FOCUS_WINDOW_LENGTH,
                "regexp_focus_halo_bytes": REGEXP_FOCUS_HALO_BYTES,
                "regexp_focus_context_before_bytes": (
                    REGEXP_FOCUS_CONTEXT_BEFORE_BYTES
                ),
                "regexp_focus_batch_size": REGEXP_FOCUS_BATCH_SIZE,
            },
            "schema": {
                "token_types": list(
                    dataset.schema.token_types
                ),
                "modifiers": list(
                    dataset.schema.modifiers
                ),
            },
            "validation": (
                validation_metrics
            ),
            "training_state": {
                "best_score": (
                    best_score
                ),
                "best_epoch": (
                    best_epoch
                ),
                "epochs_without_improvement": (
                    epochs_without_improvement
                ),
            },
        },
        output_path,
    )


def move_optimizer_state_to_device(
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> None:
    for state in (
        optimizer.state.values()
    ):
        for key, value in list(
            state.items()
        ):
            if torch.is_tensor(value):
                state[key] = value.to(
                    device
                )


def load_resume_checkpoint(
    checkpoint_path: Path,
    model: SemanticTransformer,
    optimizer: torch.optim.Optimizer,
    dataset: TypeScriptSemanticDataset,
    device: torch.device,
) -> tuple[int, float, int, int]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    if checkpoint.get("format") != CHECKPOINT_FORMAT:
        raise ValueError("Resume checkpoint is not the current NSH TypeScript checkpoint format.")

    if tuple(checkpoint["schema"]["token_types"]) != dataset.schema.token_types:
        raise ValueError("Resume checkpoint token-type schema does not match the current dataset.")

    if tuple(checkpoint["schema"]["modifiers"]) != dataset.schema.modifiers:
        raise ValueError("Resume checkpoint modifier schema does not match the current dataset.")

    config = checkpoint["config"]

    if int(config["max_length"]) != dataset.max_length:
        raise ValueError("Resume checkpoint max_length does not match the current run.")

    if config["train_windowing"] != "adaptive-cursor":
        raise ValueError("Resume checkpoint windowing does not match the current run.")

    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    move_optimizer_state_to_device(optimizer, device)

    training_state = checkpoint["training_state"]
    return (
        int(checkpoint["epoch"]),
        float(training_state["best_score"]),
        int(training_state["best_epoch"]),
        int(training_state["epochs_without_improvement"]),
    )


def auxiliary_checkpoint_path(
    best_output_path: Path,
    name: str,
) -> Path:
    return best_output_path.with_name(
        f"{best_output_path.stem}-{name}{best_output_path.suffix}"
    )


def load_available_metric_bests(
    best_output_path: Path,
    last_output_path: Path,
) -> dict[str, tuple[float, int, Path | None]]:
    metric_bests = {
        name: (-1.0, 0, None)
        for name in AUXILIARY_BEST_METRICS
    }

    checkpoint_paths = [
        best_output_path,
        last_output_path,
        *(
            auxiliary_checkpoint_path(
                best_output_path,
                name,
            )
            for name in AUXILIARY_BEST_METRICS
        ),
    ]

    for checkpoint_path in checkpoint_paths:
        if not checkpoint_path.exists():
            continue

        checkpoint = torch.load(
            checkpoint_path,
            map_location="cpu",
        )

        if checkpoint.get("format") != CHECKPOINT_FORMAT:
            raise ValueError(
                "Metric checkpoint is not the current NSH TypeScript "
                "checkpoint format."
            )

        validation = checkpoint["validation"]
        epoch = int(checkpoint["epoch"])

        for name, metric_key in AUXILIARY_BEST_METRICS.items():
            score = float(validation[metric_key])
            current_score, _, _ = metric_bests[name]

            if score > current_score:
                metric_bests[name] = (
                    score,
                    epoch,
                    checkpoint_path,
                )

    return metric_bests


def bootstrap_auxiliary_best_checkpoints(
    best_output_path: Path,
    metric_bests: dict[str, tuple[float, int, Path | None]],
) -> None:
    for name, (_, _, source_path) in metric_bests.items():
        if source_path is None:
            continue

        destination = auxiliary_checkpoint_path(
            best_output_path,
            name,
        )

        if source_path == destination:
            continue

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        shutil.copy2(
            source_path,
            destination,
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=8,
        help=(
            "Number of epochs to run "
            "in this invocation."
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_TRAIN_BATCH_SIZE,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3e-4,
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=DEFAULT_MAX_LENGTH,
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

    parser.add_argument(
        "--last-output",
        type=Path,
        default=(
            DEFAULT_LAST_OUTPUT_PATH
        ),
    )

    parser.add_argument(
        "--resume",
        type=Path,
    )

    parser.add_argument(
        "--patience",
        type=int,
        default=3,
        help=(
            "Stop after this many "
            "epochs without improving "
            "validation exact-span "
            "macro F1. Use 0 to "
            "disable early stopping."
        ),
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
        "TypeScript Multitask Training"
    )
    print("")
    print(f"Device: {device}")
    print("")

    print(
        "Preparing train dataset...",
        flush=True,
    )

    train_dataset = (
        TypeScriptSemanticDataset(
            "train",
            max_length=(
                args.max_length
            ),
            use_cache=True,
            show_progress=True,
        )
    )

    regexp_focus_dataset = RegExpFocusDataset(
        train_dataset.documents,
        token_type_to_id=(
            train_dataset.schema.token_type_to_id
        ),
        number_of_modifiers=len(
            train_dataset.schema.modifiers
        ),
        window_length=REGEXP_FOCUS_WINDOW_LENGTH,
        halo_bytes=REGEXP_FOCUS_HALO_BYTES,
        context_before_bytes=(
            REGEXP_FOCUS_CONTEXT_BEFORE_BYTES
        ),
    )

    print(
        "Preparing validation "
        "dataset...",
        flush=True,
    )

    validation_dataset = (
        TypeScriptSemanticDataset(
            "validation",
            max_length=(
                args.max_length
            ),
            use_cache=True,
            show_progress=True,
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

    regexp_focus_loader = DataLoader(
        regexp_focus_dataset,
        batch_size=REGEXP_FOCUS_BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        generator=(
            torch.Generator().manual_seed(
                args.seed + 1
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
        max_length=(
            args.max_length
        ),
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=0.01,
    )

    start_epoch = 0
    best_score = -1.0
    best_epoch = 0
    epochs_without_improvement = 0

    if args.resume is not None:
        print(
            f"Resuming from: "
            f"{args.resume}",
            flush=True,
        )

        (
            start_epoch,
            best_score,
            best_epoch,
            epochs_without_improvement,
        ) = load_resume_checkpoint(
            args.resume,
            model,
            optimizer,
            train_dataset,
            device,
        )

        print(
            f"Resume epoch: "
            f"{start_epoch}",
            flush=True,
        )

        print(
            "Existing best "
            "exact-span macro F1: "
            f"{best_score:.4f} "
            f"(epoch {best_epoch})",
            flush=True,
        )

        print(
            "Epochs without "
            "improvement: "
            f"{epochs_without_improvement}",
            flush=True,
        )

    metric_bests = load_available_metric_bests(
        args.output,
        args.last_output,
    )

    bootstrap_auxiliary_best_checkpoints(
        args.output,
        metric_bests,
    )

    existing_metric_bests = [
        (name, score, epoch)
        for name, (score, epoch, _) in metric_bests.items()
        if score >= 0.0
    ]

    if existing_metric_bests:
        print("Available metric bests:", flush=True)

        for name, score, epoch in existing_metric_bests:
            print(
                f"  {name:<10} {score:.4f} "
                f"(epoch {epoch})",
                flush=True,
            )

    print("")
    print(
        f"Parameters: "
        f"{count_parameters(model):,}"
    )

    print(
        "Boundary classes: "
        "3 (O / B / I)"
    )

    print(
        "Token types: "
        f"{train_dataset.schema.number_of_token_types}"
    )

    print(
        f"Train windows: "
        f"{len(train_dataset)}"
    )

    print("Train windowing: adaptive cursor")
    print(
        "Adaptive cuts: "
        f"{train_dataset.windowing_stats.adjusted_span_cuts} "
        "span cuts, "
        f"{train_dataset.windowing_stats.unavoidable_inside_starts} "
        "unavoidable inside starts"
    )

    regexp_inventory = (
        regexp_focus_dataset.inventory
    )

    print(
        "RegExp focus samples: "
        f"{len(regexp_focus_dataset)} "
        f"({regexp_inventory.positive_regexp} regexp, "
        f"{regexp_inventory.negative_operator_slash} "
        "operator-slash negatives)"
    )

    print(
        "RegExp focus window:  "
        f"{REGEXP_FOCUS_WINDOW_LENGTH} "
        f"(halo={REGEXP_FOCUS_HALO_BYTES}, "
        "context-before="
        f"{REGEXP_FOCUS_CONTEXT_BEFORE_BYTES})"
    )

    print(
        "Validation windows: "
        f"{len(validation_dataset)}"
    )

    print(
        f"Batch size: "
        f"{args.batch_size}"
    )

    main_steps_per_epoch = len(train_loader)
    regexp_steps_per_epoch = len(regexp_focus_loader)
    steps_per_epoch = (
        main_steps_per_epoch
        + regexp_steps_per_epoch
    )

    print(
        "Optimizer steps/epoch: "
        f"{steps_per_epoch} "
        f"({main_steps_per_epoch} main + "
        f"{regexp_steps_per_epoch} regexp)"
    )

    print(
        f"Planned optimizer steps: "
        f"{steps_per_epoch * args.epochs}"
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
            ignore_index=(
                IGNORE_LABEL_ID
            ),
        )
    )

    token_type_loss_function = (
        nn.CrossEntropyLoss(
            weight=token_type_weights,
            ignore_index=(
                IGNORE_LABEL_ID
            ),
        )
    )

    for local_epoch in range(
        1,
        args.epochs + 1,
    ):
        global_epoch = (
            start_epoch
            + local_epoch
        )

        print(
            f"Epoch "
            f"{global_epoch} "
            f"(run {local_epoch}/"
            f"{args.epochs})"
        )

        (
            training_loss,
            boundary_loss,
            token_type_loss,
            modifier_loss,
            regexp_focus_loss,
            regexp_focus_steps,
            epoch_seconds,
        ) = train_epoch(
            model=model,
            loader=train_loader,
            regexp_focus_loader=(
                regexp_focus_loader
            ),
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

        print(
            "  validating...",
            flush=True,
        )

        diagnostics = (
            diagnostic_metrics(
                model,
                validation_loader,
                validation_dataset,
                device,
            )
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
            "  regexp focus loss:   "
            f"{regexp_focus_loss:.4f} "
            f"({regexp_focus_steps} steps)"
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

        print(
            "  epoch time:          "
            f"{format_duration(epoch_seconds)}"
        )

        print("")

        score = metrics[
            "exact_span_macro_f1"
        ]

        is_new_best = (
            score > best_score
        )

        if is_new_best:
            best_score = score
            best_epoch = global_epoch
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        save_checkpoint(
            model=model,
            optimizer=optimizer,
            dataset=train_dataset,
            output_path=(
                args.last_output
            ),
            validation_metrics=metrics,
            max_length=(
                args.max_length
            ),
            epoch=global_epoch,
            best_score=best_score,
            best_epoch=best_epoch,
            epochs_without_improvement=(
                epochs_without_improvement
            ),
        )

        if is_new_best:
            save_checkpoint(
                model=model,
                optimizer=optimizer,
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
                epoch=global_epoch,
                best_score=best_score,
                best_epoch=best_epoch,
                epochs_without_improvement=0,
            )

            print(
                "  ✓ saved new best "
                "checkpoint to "
                f"{args.output}"
            )

            print("")
        else:
            print(
                "  no new macro-F1 "
                "best "
                f"({epochs_without_improvement}"
                f"/{args.patience})"
            )

            print("")

        auxiliary_updates: list[
            tuple[str, float, int, Path]
        ] = []

        for name, metric_key in AUXILIARY_BEST_METRICS.items():
            metric_score = float(metrics[metric_key])
            previous_score, _, _ = metric_bests[name]

            if metric_score <= previous_score:
                continue

            checkpoint_path = auxiliary_checkpoint_path(
                args.output,
                name,
            )

            metric_bests[name] = (
                metric_score,
                global_epoch,
                checkpoint_path,
            )

            save_checkpoint(
                model=model,
                optimizer=optimizer,
                dataset=train_dataset,
                output_path=checkpoint_path,
                validation_metrics=metrics,
                max_length=args.max_length,
                epoch=global_epoch,
                best_score=best_score,
                best_epoch=best_epoch,
                epochs_without_improvement=(
                    epochs_without_improvement
                ),
            )

            auxiliary_updates.append(
                (
                    name,
                    metric_score,
                    global_epoch,
                    checkpoint_path,
                )
            )

        for (
            name,
            metric_score,
            metric_epoch,
            checkpoint_path,
        ) in auxiliary_updates:
            print(
                f"  ✓ saved best {name} checkpoint "
                f"({metric_score:.4f}, epoch {metric_epoch}) "
                f"to {checkpoint_path}"
            )

        if auxiliary_updates:
            print("")

        if (
            args.patience > 0
            and epochs_without_improvement
            >= args.patience
        ):
            print(
                "Early stopping: "
                "validation exact-span "
                "macro F1 did not "
                "improve.",
                flush=True,
            )

            break

    print("Training complete.")

    print(
        "Best exact span macro F1: "
        f"{best_score:.4f} "
        f"(epoch {best_epoch})"
    )

    print(
        f"Best checkpoint: "
        f"{args.output}"
    )

    print(
        f"Last checkpoint: "
        f"{args.last_output}"
    )

    print("Metric best checkpoints:")

    for name, (score, epoch, _) in metric_bests.items():
        if score < 0.0:
            continue

        print(
            f"  {name:<10} {score:.4f} "
            f"(epoch {epoch}) → "
            f"{auxiliary_checkpoint_path(args.output, name)}"
        )


if __name__ == "__main__":
    main()
