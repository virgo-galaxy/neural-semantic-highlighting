from __future__ import annotations

import argparse
import bisect
import time
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, Dataset

from dataset import (
    BOUNDARY_BEGIN_ID,
    BOUNDARY_INSIDE_ID,
    IGNORE_LABEL_ID,
    PAD_BYTE_ID,
    EncodedDocument,
    TypeScriptSemanticDataset,
    build_source_boundaries,
)
from predict import load_model, select_device
from train import (
    build_boundary_class_weights,
    build_modifier_positive_weights,
    build_token_type_class_weights,
    cpu_optimizer_state_dict,
)


DEFAULT_BASE_CHECKPOINT = Path(
    "artifacts/typescript/"
    "v3-local-role-dual-view-hard-string-regexp/"
    "best-epoch19.pt"
)
DEFAULT_OUTPUT = Path(
    "artifacts/typescript/"
    "v3-string-surgery-probe/"
    "step-0400.pt"
)


@dataclass(frozen=True)
class SurgeryReference:
    document_index: int
    window_start: int
    window_end: int
    focus_start: int
    focus_end: int
    span_start: int
    span_end: int
    includes_end_boundary: bool


@dataclass(frozen=True)
class SurgeryInventory:
    eligible_string_spans: int
    over_context_spans: int
    continuation_focuses: int
    end_boundary_focuses: int
    skipped_focuses: int

    @property
    def total(self) -> int:
        return self.continuation_focuses


class StringSurgeryDataset(Dataset):
    def __init__(
        self,
        documents: list[EncodedDocument],
        *,
        token_type_to_id: dict[str, int],
        number_of_modifiers: int,
        max_length: int,
        min_span_bytes: int,
        first_inside_offset_bytes: int,
        step_bytes: int,
        min_remaining_bytes: int,
        right_halo_bytes: int,
    ) -> None:
        self.documents = documents
        self.max_length = max_length
        self.number_of_modifiers = number_of_modifiers
        self.references, self.inventory = build_surgery_references(
            documents,
            token_type_to_id=token_type_to_id,
            max_length=max_length,
            min_span_bytes=min_span_bytes,
            first_inside_offset_bytes=first_inside_offset_bytes,
            step_bytes=step_bytes,
            min_remaining_bytes=min_remaining_bytes,
            right_halo_bytes=right_halo_bytes,
        )

    def __len__(self) -> int:
        return len(self.references)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        reference = self.references[index]
        document = self.documents[reference.document_index]
        length = reference.window_end - reference.window_start

        input_ids = torch.full(
            (self.max_length,),
            PAD_BYTE_ID,
            dtype=torch.long,
        )
        attention_mask = torch.zeros(
            (self.max_length,),
            dtype=torch.bool,
        )
        boundary_labels = torch.full(
            (self.max_length,),
            IGNORE_LABEL_ID,
            dtype=torch.long,
        )
        token_type_labels = torch.full(
            (self.max_length,),
            IGNORE_LABEL_ID,
            dtype=torch.long,
        )
        modifier_labels = torch.zeros(
            (self.max_length, self.number_of_modifiers),
            dtype=torch.float32,
        )

        input_ids[:length] = document.input_ids[
            reference.window_start:reference.window_end
        ]
        attention_mask[:length] = True

        focus_start = max(reference.focus_start, reference.window_start)
        focus_end = min(reference.focus_end, reference.window_end)
        local_start = focus_start - reference.window_start
        local_end = focus_end - reference.window_start

        boundary_labels[local_start:local_end] = document.boundary_labels[
            focus_start:focus_end
        ]
        token_type_labels[local_start:local_end] = document.token_type_labels[
            focus_start:focus_end
        ]
        modifier_labels[local_start:local_end] = document.modifier_labels[
            focus_start:focus_end
        ].float()

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "boundary_labels": boundary_labels,
            "token_type_labels": token_type_labels,
            "modifier_labels": modifier_labels,
        }


def _snap_to_character_boundary(
    candidate: int,
    character_starts: list[int],
) -> int:
    index = bisect.bisect_right(character_starts, candidate) - 1
    return character_starts[max(0, index)]


def build_surgery_references(
    documents: list[EncodedDocument],
    *,
    token_type_to_id: dict[str, int],
    max_length: int,
    min_span_bytes: int,
    first_inside_offset_bytes: int,
    step_bytes: int,
    min_remaining_bytes: int,
    right_halo_bytes: int,
) -> tuple[list[SurgeryReference], SurgeryInventory]:
    string_id = token_type_to_id["string"]
    references: list[SurgeryReference] = []
    eligible_spans = 0
    over_context_spans = 0
    end_boundary_focuses = 0
    skipped_focuses = 0

    for document_index, document in enumerate(documents):
        length = int(document.input_ids.shape[0])
        if length == 0:
            continue

        utf16_to_utf8, _, starts_tuple = build_source_boundaries(document.source)
        character_starts = list(starts_tuple)
        if not character_starts:
            continue

        for span in document.gold_spans:
            if span.token_type != "string":
                continue

            span_start = utf16_to_utf8.get(span.start)
            span_end = utf16_to_utf8.get(span.end)
            if span_start is None or span_end is None:
                continue

            span_length = span_end - span_start
            if span_length < min_span_bytes:
                continue

            eligible_spans += 1
            if span_length > max_length:
                over_context_spans += 1

            candidate = span_start + first_inside_offset_bytes
            seen_starts: set[int] = set()

            while candidate < span_end:
                remaining = span_end - candidate
                if remaining < min_remaining_bytes:
                    break

                window_start = _snap_to_character_boundary(candidate, character_starts)
                if window_start <= span_start:
                    candidate += step_bytes
                    continue
                if window_start >= span_end:
                    break
                if window_start in seen_starts:
                    candidate += step_bytes
                    continue
                seen_starts.add(window_start)

                if window_start >= document.boundary_labels.shape[0]:
                    skipped_focuses += 1
                    candidate += step_bytes
                    continue

                if int(document.boundary_labels[window_start].item()) != BOUNDARY_INSIDE_ID:
                    skipped_focuses += 1
                    candidate += step_bytes
                    continue

                if int(document.token_type_labels[window_start].item()) != string_id:
                    skipped_focuses += 1
                    candidate += step_bytes
                    continue

                window_end = min(length, window_start + max_length)
                focus_start = window_start
                focus_end = min(window_end, span_end + right_halo_bytes)
                includes_end_boundary = span_end < focus_end

                references.append(
                    SurgeryReference(
                        document_index=document_index,
                        window_start=window_start,
                        window_end=window_end,
                        focus_start=focus_start,
                        focus_end=focus_end,
                        span_start=span_start,
                        span_end=span_end,
                        includes_end_boundary=includes_end_boundary,
                    )
                )

                if includes_end_boundary:
                    end_boundary_focuses += 1

                candidate += step_bytes

    # Sanity checks: every focused view starts inside a Gold string and never
    # includes the opener. This is the exact continuation condition we want to
    # probe without changing the runtime context size.
    for reference in references:
        document = documents[reference.document_index]
        if reference.window_start <= reference.span_start:
            raise AssertionError("String surgery view unexpectedly includes the opener.")
        if int(document.boundary_labels[reference.window_start].item()) != BOUNDARY_INSIDE_ID:
            raise AssertionError("String surgery view does not start on an inside label.")
        if int(document.token_type_labels[reference.window_start].item()) != string_id:
            raise AssertionError("String surgery view does not start inside a string.")

    return references, SurgeryInventory(
        eligible_string_spans=eligible_spans,
        over_context_spans=over_context_spans,
        continuation_focuses=len(references),
        end_boundary_focuses=end_boundary_focuses,
        skipped_focuses=skipped_focuses,
    )


def _next_batch(iterator, loader):
    try:
        return next(iterator), iterator
    except StopIteration:
        iterator = iter(loader)
        return next(iterator), iterator


def _masked_losses(
    model,
    batch: dict[str, torch.Tensor],
    *,
    device: torch.device,
    boundary_loss_function: nn.CrossEntropyLoss,
    token_type_loss_function: nn.CrossEntropyLoss,
    modifier_positive_weights: torch.Tensor,
    include_modifier: bool,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    input_ids = batch["input_ids"].to(device)
    attention_mask = batch["attention_mask"].to(device)
    boundary_labels = batch["boundary_labels"].to(device)
    token_type_labels = batch["token_type_labels"].to(device)
    modifier_labels = batch["modifier_labels"].to(device)

    output = model(input_ids=input_ids, attention_mask=attention_mask)

    boundary_loss = boundary_loss_function(
        output.boundary_logits.reshape(-1, output.boundary_logits.shape[-1]),
        boundary_labels.reshape(-1),
    )
    type_loss = token_type_loss_function(
        output.token_type_logits.reshape(-1, output.token_type_logits.shape[-1]),
        token_type_labels.reshape(-1),
    )

    if include_modifier:
        begin_mask = boundary_labels == BOUNDARY_BEGIN_ID
        if begin_mask.any():
            modifier_loss = F.binary_cross_entropy_with_logits(
                output.modifier_logits[begin_mask],
                modifier_labels[begin_mask],
                pos_weight=modifier_positive_weights,
            )
        else:
            modifier_loss = torch.zeros((), device=device)
    else:
        modifier_loss = torch.zeros((), device=device)

    return boundary_loss + type_loss + 0.10 * modifier_loss, boundary_loss, type_loss, modifier_loss


def _cpu_state_dict(model) -> dict[str, torch.Tensor]:
    return {
        name: tensor.detach().cpu()
        for name, tensor in model.state_dict().items()
    }


def save_surgery_checkpoint(
    path: Path,
    *,
    base_checkpoint: dict,
    model,
    optimizer,
    step: int,
    args: argparse.Namespace,
    inventory: SurgeryInventory,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = dict(base_checkpoint)
    checkpoint["model_state_dict"] = _cpu_state_dict(model)
    checkpoint["optimizer_state_dict"] = cpu_optimizer_state_dict(optimizer)
    checkpoint["surgery"] = {
        "target": "string",
        "base_checkpoint": str(args.checkpoint),
        "step": step,
        "steps": args.steps,
        "learning_rate": args.learning_rate,
        "batch_size": args.batch_size,
        "min_span_bytes": args.min_span_bytes,
        "first_inside_offset_bytes": args.first_inside_offset_bytes,
        "step_bytes": args.step_bytes,
        "min_remaining_bytes": args.min_remaining_bytes,
        "right_halo_bytes": args.right_halo_bytes,
        "replay_every": args.replay_every,
        "seed": args.seed,
        "eligible_string_spans": inventory.eligible_string_spans,
        "over_context_spans": inventory.over_context_spans,
        "continuation_focuses": inventory.continuation_focuses,
        "end_boundary_focuses": inventory.end_boundary_focuses,
        "skipped_focuses": inventory.skipped_focuses,
    }
    torch.save(checkpoint, path)


def snapshot_path(output: Path, step: int) -> Path:
    return output.parent / f"step-{step:04d}.pt"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--min-span-bytes", type=int, default=256)
    parser.add_argument("--first-inside-offset-bytes", type=int, default=128)
    parser.add_argument("--step-bytes", type=int, default=256)
    parser.add_argument("--min-remaining-bytes", type=int, default=64)
    parser.add_argument("--right-halo-bytes", type=int, default=16)
    parser.add_argument(
        "--replay-every",
        type=int,
        default=5,
        help="Use one ordinary full-label replay batch every N optimizer steps. 0 disables replay.",
    )
    parser.add_argument("--snapshot-every", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    if args.steps <= 0:
        raise ValueError("--steps must be positive")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive")
    if args.min_span_bytes <= 0:
        raise ValueError("--min-span-bytes must be positive")
    if args.first_inside_offset_bytes <= 0:
        raise ValueError("--first-inside-offset-bytes must be positive")
    if args.step_bytes <= 0:
        raise ValueError("--step-bytes must be positive")
    if args.min_remaining_bytes <= 0:
        raise ValueError("--min-remaining-bytes must be positive")
    if args.right_halo_bytes < 0:
        raise ValueError("--right-halo-bytes cannot be negative")

    torch.manual_seed(args.seed)
    device = select_device()
    model, base_checkpoint = load_model(args.checkpoint, device)
    config = base_checkpoint["config"]
    max_length = int(config["max_length"])

    print("Neural Semantic Highlighting")
    print("TypeScript String Surgery Probe")
    print("")
    print(f"Device:              {device}")
    print(f"Base checkpoint:     {args.checkpoint}")
    print(f"Steps:               {args.steps}")
    print(f"Batch size:          {args.batch_size}")
    print(f"Learning rate:       {args.learning_rate:g}")
    print(f"Min string span:     {args.min_span_bytes}B")
    print(f"First inside offset: {args.first_inside_offset_bytes}B")
    print(f"Continuation step:   {args.step_bytes}B")
    print(f"Min remaining:       {args.min_remaining_bytes}B")
    print(f"Right halo:          {args.right_halo_bytes}B")
    print(f"Replay every:        {args.replay_every if args.replay_every else 'disabled'}")
    print("")

    replay_dataset = TypeScriptSemanticDataset(
        "train",
        max_length=max_length,
        stride=max_length,
        window_strategy="fixed",
        use_cache=True,
        show_progress=True,
    )

    checkpoint_token_types = tuple(base_checkpoint["schema"]["token_types"])
    checkpoint_modifiers = tuple(base_checkpoint["schema"]["modifiers"])
    if checkpoint_token_types != replay_dataset.schema.token_types:
        raise ValueError("Checkpoint token types do not match current dataset schema.")
    if checkpoint_modifiers != replay_dataset.schema.modifiers:
        raise ValueError("Checkpoint modifiers do not match current dataset schema.")

    focus_dataset = StringSurgeryDataset(
        replay_dataset.documents,
        token_type_to_id=replay_dataset.schema.token_type_to_id,
        number_of_modifiers=len(replay_dataset.schema.modifiers),
        max_length=max_length,
        min_span_bytes=args.min_span_bytes,
        first_inside_offset_bytes=args.first_inside_offset_bytes,
        step_bytes=args.step_bytes,
        min_remaining_bytes=args.min_remaining_bytes,
        right_halo_bytes=args.right_halo_bytes,
    )

    inventory = focus_dataset.inventory
    if len(focus_dataset) == 0:
        raise ValueError("String surgery produced no focused samples.")

    print("Surgery inventory")
    print("-----------------")
    print(f"Eligible long strings: {inventory.eligible_string_spans}")
    print(f"Over-context strings:   {inventory.over_context_spans}")
    print(f"Continuation focuses:   {inventory.continuation_focuses}")
    print(f"With end boundary:      {inventory.end_boundary_focuses}")
    print(f"Skipped focuses:        {inventory.skipped_focuses}")
    print(f"Replay windows:         {len(replay_dataset)}")
    print("")

    focus_loader = DataLoader(
        focus_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        generator=torch.Generator().manual_seed(args.seed),
    )
    replay_loader = DataLoader(
        replay_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        generator=torch.Generator().manual_seed(args.seed + 1),
    )
    focus_iterator = iter(focus_loader)
    replay_iterator = iter(replay_loader)

    boundary_weights = build_boundary_class_weights(replay_dataset).to(device)
    token_type_weights = build_token_type_class_weights(replay_dataset).to(device)
    modifier_positive_weights = build_modifier_positive_weights(replay_dataset).to(device)
    boundary_loss_function = nn.CrossEntropyLoss(
        weight=boundary_weights,
        ignore_index=IGNORE_LABEL_ID,
    )
    token_type_loss_function = nn.CrossEntropyLoss(
        weight=token_type_weights,
        ignore_index=IGNORE_LABEL_ID,
    )

    model.train()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=0.01,
    )

    started = time.perf_counter()
    focus_steps = 0
    replay_steps = 0
    running_loss = 0.0

    for step in range(1, args.steps + 1):
        use_replay = bool(args.replay_every and step % args.replay_every == 0)
        if use_replay:
            batch, replay_iterator = _next_batch(replay_iterator, replay_loader)
            replay_steps += 1
        else:
            batch, focus_iterator = _next_batch(focus_iterator, focus_loader)
            focus_steps += 1

        optimizer.zero_grad(set_to_none=True)
        loss, boundary_loss, type_loss, modifier_loss = _masked_losses(
            model,
            batch,
            device=device,
            boundary_loss_function=boundary_loss_function,
            token_type_loss_function=token_type_loss_function,
            modifier_positive_weights=modifier_positive_weights,
            include_modifier=use_replay,
        )
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        running_loss += float(loss.item())

        if step % 25 == 0 or step == args.steps:
            elapsed = max(time.perf_counter() - started, 1e-9)
            steps_per_second = step / elapsed
            remaining = max(0.0, (args.steps - step) / max(steps_per_second, 1e-9))
            mode = "replay" if use_replay else "focus"
            print(
                f"step {step:>4}/{args.steps} "
                f"mode={mode:<6} "
                f"loss={loss.item():.4f} "
                f"boundary={boundary_loss.item():.4f} "
                f"type={type_loss.item():.4f} "
                f"modifier={modifier_loss.item():.4f} "
                f"ETA={remaining:05.1f}s",
                flush=True,
            )

        if args.snapshot_every > 0 and step % args.snapshot_every == 0:
            path = snapshot_path(args.output, step)
            if path == args.output:
                continue
            save_surgery_checkpoint(
                path,
                base_checkpoint=base_checkpoint,
                model=model,
                optimizer=optimizer,
                step=step,
                args=args,
                inventory=inventory,
            )
            print(f"  saved snapshot: {path}", flush=True)

    save_surgery_checkpoint(
        args.output,
        base_checkpoint=base_checkpoint,
        model=model,
        optimizer=optimizer,
        step=args.steps,
        args=args,
        inventory=inventory,
    )

    elapsed = time.perf_counter() - started
    print("")
    print("Surgery complete.")
    print(f"Focus/replay steps: {focus_steps}/{replay_steps}")
    print(f"Average loss:       {running_loss / args.steps:.4f}")
    print(f"Elapsed:            {elapsed:.1f}s")
    print(f"Output:             {args.output}")


if __name__ == "__main__":
    main()
