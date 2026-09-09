from __future__ import annotations

import argparse
import gc
import math
import time
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader

from config import CHECKPOINT_FORMAT, DEFAULT_BEST_CHECKPOINT_PATH
from dataset import (
    BOUNDARY_BEGIN_ID,
    IGNORE_LABEL_ID,
    TypeScriptSemanticDataset,
)
from model import (
    SemanticTransformer,
    count_parameters,
)
from train import (
    build_boundary_class_weights,
    build_modifier_positive_weights,
    build_token_type_class_weights,
    select_device,
)


DEFAULT_CHECKPOINT_PATH = DEFAULT_BEST_CHECKPOINT_PATH


@dataclass(frozen=True)
class BenchmarkResult:
    batch_size: int
    windows: int
    steps: int
    seconds: float
    windows_per_second: float
    steps_per_second: float
    peak_memory_bytes: int | None
    status: str


def synchronize(device: torch.device) -> None:
    if device.type == "mps":
        torch.mps.synchronize()
        return

    if device.type == "cuda":
        torch.cuda.synchronize(device)


def empty_device_cache(device: torch.device) -> None:
    gc.collect()

    if device.type == "mps":
        torch.mps.empty_cache()
        return

    if device.type == "cuda":
        torch.cuda.empty_cache()


def current_device_memory_bytes(
    device: torch.device,
) -> int | None:
    if device.type == "mps":
        return int(
            torch.mps.current_allocated_memory()
        )

    if device.type == "cuda":
        return int(
            torch.cuda.memory_allocated(device)
        )

    return None


def format_memory(number_of_bytes: int | None) -> str:
    if number_of_bytes is None:
        return "n/a"

    gibibytes = number_of_bytes / (1024**3)

    if gibibytes >= 1.0:
        return f"{gibibytes:.2f} GiB"

    mebibytes = number_of_bytes / (1024**2)
    return f"{mebibytes:.0f} MiB"


def load_checkpoint(
    checkpoint_path: Path,
) -> dict:
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f'Checkpoint not found: "{checkpoint_path}"'
        )

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )

    if (
        checkpoint.get("format")
        != CHECKPOINT_FORMAT
    ):
        raise ValueError(
            "Benchmark expects an NSH TypeScript "
            "multitask checkpoint."
        )

    return checkpoint


def build_model(
    checkpoint: dict,
    device: torch.device,
) -> SemanticTransformer:
    config = checkpoint["config"]

    model = SemanticTransformer(
        vocab_size=config["vocab_size"],
        number_of_boundary_classes=config[
            "number_of_boundary_classes"
        ],
        number_of_token_types=config[
            "number_of_token_types"
        ],
        number_of_modifiers=config[
            "number_of_modifiers"
        ],
        max_length=config["max_length"],
        embedding_dimension=config[
            "embedding_dimension"
        ],
        number_of_heads=config["number_of_heads"],
        number_of_layers=config[
            "number_of_layers"
        ],
        feed_forward_dimension=config[
            "feed_forward_dimension"
        ],
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    return model.to(device)


def build_loss_functions(
    dataset: TypeScriptSemanticDataset,
    device: torch.device,
) -> tuple[
    nn.CrossEntropyLoss,
    nn.CrossEntropyLoss,
    torch.Tensor,
]:
    boundary_weights = (
        build_boundary_class_weights(dataset).to(
            device
        )
    )

    token_type_weights = (
        build_token_type_class_weights(dataset).to(
            device
        )
    )

    modifier_positive_weights = (
        build_modifier_positive_weights(dataset).to(
            device
        )
    )

    boundary_loss_function = nn.CrossEntropyLoss(
        weight=boundary_weights,
        ignore_index=IGNORE_LABEL_ID,
    )

    token_type_loss_function = nn.CrossEntropyLoss(
        weight=token_type_weights,
        ignore_index=IGNORE_LABEL_ID,
    )

    return (
        boundary_loss_function,
        token_type_loss_function,
        modifier_positive_weights,
    )


def training_step(
    *,
    model: SemanticTransformer,
    optimizer: torch.optim.Optimizer,
    batch: dict[str, torch.Tensor],
    boundary_loss_function: nn.CrossEntropyLoss,
    token_type_loss_function: nn.CrossEntropyLoss,
    modifier_positive_weights: torch.Tensor,
    modifier_loss_weight: float,
    device: torch.device,
) -> float:
    input_ids = batch["input_ids"].to(device)
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

    optimizer.zero_grad(set_to_none=True)

    output = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
    )

    boundary_loss = boundary_loss_function(
        output.boundary_logits.reshape(
            -1,
            output.boundary_logits.shape[-1],
        ),
        boundary_labels.reshape(-1),
    )

    token_type_loss = token_type_loss_function(
        output.token_type_logits.reshape(
            -1,
            output.token_type_logits.shape[-1],
        ),
        token_type_labels.reshape(-1),
    )

    begin_mask = (
        boundary_labels == BOUNDARY_BEGIN_ID
    )

    if begin_mask.any():
        modifier_loss = (
            F.binary_cross_entropy_with_logits(
                output.modifier_logits[begin_mask],
                modifier_labels[begin_mask],
                pos_weight=modifier_positive_weights,
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
        + modifier_loss_weight * modifier_loss
    )

    loss.backward()

    nn.utils.clip_grad_norm_(
        model.parameters(),
        max_norm=1.0,
    )

    optimizer.step()

    return float(loss.item())


def benchmark_batch_size(
    *,
    batch_size: int,
    target_windows: int,
    warmup_steps: int,
    checkpoint: dict,
    dataset: TypeScriptSemanticDataset,
    device: torch.device,
    learning_rate: float,
    modifier_loss_weight: float,
) -> BenchmarkResult:
    empty_device_cache(device)

    model = build_model(
        checkpoint,
        device,
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=0.01,
    )

    (
        boundary_loss_function,
        token_type_loss_function,
        modifier_positive_weights,
    ) = build_loss_functions(
        dataset,
        device,
    )

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        drop_last=True,
    )

    available_steps = len(loader)
    requested_steps = math.ceil(
        target_windows / batch_size
    )
    timed_steps = min(
        available_steps,
        requested_steps,
    )

    if timed_steps <= 0:
        raise ValueError(
            "Benchmark dataset does not contain "
            "enough windows for this batch size."
        )

    model.train()

    peak_memory = current_device_memory_bytes(
        device
    )

    def sample_memory() -> None:
        nonlocal peak_memory

        current = current_device_memory_bytes(
            device
        )

        if current is None:
            return

        if peak_memory is None:
            peak_memory = current
            return

        peak_memory = max(
            peak_memory,
            current,
        )

    # Warm up MPS/CUDA kernels and allocator behavior. These
    # updates are discarded immediately afterward.
    warmup_loader = iter(loader)

    for _ in range(warmup_steps):
        try:
            batch = next(warmup_loader)
        except StopIteration:
            break

        training_step(
            model=model,
            optimizer=optimizer,
            batch=batch,
            boundary_loss_function=(
                boundary_loss_function
            ),
            token_type_loss_function=(
                token_type_loss_function
            ),
            modifier_positive_weights=(
                modifier_positive_weights
            ),
            modifier_loss_weight=(
                modifier_loss_weight
            ),
            device=device,
        )

        sample_memory()

    synchronize(device)

    # Restore the exact same model state for the timed portion so
    # every batch size starts from the same checkpoint.
    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=0.01,
    )

    synchronize(device)

    started = time.perf_counter()
    processed_windows = 0
    processed_steps = 0

    for step, batch in enumerate(
        loader,
        start=1,
    ):
        if step > timed_steps:
            break

        training_step(
            model=model,
            optimizer=optimizer,
            batch=batch,
            boundary_loss_function=(
                boundary_loss_function
            ),
            token_type_loss_function=(
                token_type_loss_function
            ),
            modifier_positive_weights=(
                modifier_positive_weights
            ),
            modifier_loss_weight=(
                modifier_loss_weight
            ),
            device=device,
        )

        processed_windows += batch[
            "input_ids"
        ].shape[0]
        processed_steps += 1
        sample_memory()

    synchronize(device)
    elapsed = time.perf_counter() - started

    windows_per_second = (
        processed_windows / elapsed
    )

    steps_per_second = (
        processed_steps / elapsed
    )

    del optimizer
    del model
    del boundary_loss_function
    del token_type_loss_function
    del modifier_positive_weights

    empty_device_cache(device)

    return BenchmarkResult(
        batch_size=batch_size,
        windows=processed_windows,
        steps=processed_steps,
        seconds=elapsed,
        windows_per_second=windows_per_second,
        steps_per_second=steps_per_second,
        peak_memory_bytes=peak_memory,
        status="ok",
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark NSH TypeScript training "
            "throughput across batch sizes."
        )
    )

    parser.add_argument(
        "--batch-sizes",
        type=int,
        nargs="+",
        default=[1, 2, 4, 8],
    )

    parser.add_argument(
        "--windows",
        type=int,
        default=64,
        help=(
            "Approximately how many training windows "
            "to process for each batch size."
        ),
    )

    parser.add_argument(
        "--warmup-steps",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT_PATH,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3e-4,
    )

    parser.add_argument(
        "--modifier-loss-weight",
        type=float,
        default=0.10,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if args.windows <= 0:
        raise ValueError(
            "--windows must be greater than zero."
        )

    if args.warmup_steps < 0:
        raise ValueError(
            "--warmup-steps cannot be negative."
        )

    if any(
        batch_size <= 0
        for batch_size in args.batch_sizes
    ):
        raise ValueError(
            "Every batch size must be greater than zero."
        )

    device = select_device()

    print("Neural Semantic Highlighting")
    print("TypeScript Training Throughput Benchmark")
    print("")
    print(f"Device: {device}")
    print(f"Checkpoint: {args.checkpoint}")
    print(
        "Batch sizes: "
        + ", ".join(
            str(batch_size)
            for batch_size in args.batch_sizes
        )
    )
    print(f"Timed windows per batch: ~{args.windows}")
    print(f"Warmup steps: {args.warmup_steps}")
    print("")

    checkpoint = load_checkpoint(
        args.checkpoint
    )

    max_length = checkpoint["config"][
        "max_length"
    ]

    dataset = TypeScriptSemanticDataset(
        "train",
        max_length=max_length,
        use_cache=True,
        show_progress=True,
    )

    probe_model = build_model(
        checkpoint,
        torch.device("cpu"),
    )

    print("")
    print(
        f"Parameters: {count_parameters(probe_model):,}"
    )
    print(f"Context: {max_length} bytes")
    print(f"Train windows: {len(dataset)}")
    print("")

    del probe_model

    results: list[BenchmarkResult] = []
    out_of_memory_seen = False

    for batch_size in args.batch_sizes:
        print(f"Batch {batch_size}")

        if out_of_memory_seen:
            result = BenchmarkResult(
                batch_size=batch_size,
                windows=0,
                steps=0,
                seconds=0.0,
                windows_per_second=0.0,
                steps_per_second=0.0,
                peak_memory_bytes=None,
                status="skipped after OOM",
            )

            results.append(result)
            print("  skipped after a smaller batch OOM")
            print("")
            continue

        try:
            result = benchmark_batch_size(
                batch_size=batch_size,
                target_windows=args.windows,
                warmup_steps=(
                    args.warmup_steps
                ),
                checkpoint=checkpoint,
                dataset=dataset,
                device=device,
                learning_rate=(
                    args.learning_rate
                ),
                modifier_loss_weight=(
                    args.modifier_loss_weight
                ),
            )
        except RuntimeError as error:
            message = str(error).lower()

            if (
                "out of memory" not in message
                and "mps backend out of memory"
                not in message
            ):
                raise

            out_of_memory_seen = True
            empty_device_cache(device)

            result = BenchmarkResult(
                batch_size=batch_size,
                windows=0,
                steps=0,
                seconds=0.0,
                windows_per_second=0.0,
                steps_per_second=0.0,
                peak_memory_bytes=None,
                status="OOM",
            )

            print("  OOM")
            print("")
            results.append(result)
            continue

        results.append(result)

        print(
            f"  windows: {result.windows:,}"
        )
        print(f"  steps: {result.steps:,}")
        print(
            f"  time: {result.seconds:.2f}s"
        )
        print(
            "  throughput: "
            f"{result.windows_per_second:,.1f} windows/s"
        )
        print(
            "  step rate: "
            f"{result.steps_per_second:.2f} steps/s"
        )
        print(
            "  observed MPS/CUDA memory: "
            f"{format_memory(result.peak_memory_bytes)}"
        )
        print("")

    successful = [
        result
        for result in results
        if result.status == "ok"
    ]

    print("Results")
    print("-------")
    print(
        f"{'batch':>7} "
        f"{'windows/s':>12} "
        f"{'relative':>10} "
        f"{'memory':>12} "
        f"status"
    )

    baseline = next(
        (
            result.windows_per_second
            for result in successful
            if result.batch_size
            == args.batch_sizes[0]
        ),
        None,
    )

    for result in results:
        if result.status == "ok":
            relative = (
                result.windows_per_second
                / baseline
                if baseline
                else 1.0
            )

            windows_per_second = (
                f"{result.windows_per_second:,.1f}"
            )
            relative_text = f"{relative:.2f}x"
            memory_text = format_memory(
                result.peak_memory_bytes
            )
        else:
            windows_per_second = "-"
            relative_text = "-"
            memory_text = "-"

        print(
            f"{result.batch_size:>7} "
            f"{windows_per_second:>12} "
            f"{relative_text:>10} "
            f"{memory_text:>12} "
            f"{result.status}"
        )

    if successful:
        best = max(
            successful,
            key=lambda result: (
                result.windows_per_second
            ),
        )

        print("")
        print(
            "Fastest batch size: "
            f"{best.batch_size} "
            f"({best.windows_per_second:,.1f} windows/s)"
        )
        print(
            "Benchmark weights were not saved; "
            "best.pt and last.pt were not modified."
        )


if __name__ == "__main__":
    main()
