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
    "v3-regexp-surgery-probe/"
    "step-0400.pt"
)


@dataclass(frozen=True)
class SurgeryReference:
    document_index: int
    window_start: int
    window_end: int
    focus_start: int
    focus_end: int
    kind: str


@dataclass(frozen=True)
class SurgeryInventory:
    positive_regexp: int
    negative_operator_slash: int
    skipped_over_context: int

    @property
    def total(self) -> int:
        return self.positive_regexp + self.negative_operator_slash


class RegexpSurgeryDataset(Dataset):
    def __init__(
        self,
        documents: list[EncodedDocument],
        *,
        token_type_to_id: dict[str, int],
        number_of_modifiers: int,
        max_length: int,
        halo_bytes: int,
        context_before_bytes: int,
    ) -> None:
        self.documents = documents
        self.max_length = max_length
        self.number_of_modifiers = number_of_modifiers
        self.references, self.inventory = build_surgery_references(
            documents,
            token_type_to_id=token_type_to_id,
            max_length=max_length,
            halo_bytes=halo_bytes,
            context_before_bytes=context_before_bytes,
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


def _bounded_character_start(
    character_starts: list[int],
    *,
    desired: int,
    lower: int,
    upper: int,
) -> int:
    if lower > upper:
        raise ValueError(f"Invalid start bounds: {lower}>{upper}")

    desired = max(lower, min(desired, upper))
    index = bisect.bisect_right(character_starts, desired) - 1

    if index >= 0 and character_starts[index] >= lower:
        candidate = character_starts[index]
        if candidate <= upper:
            return candidate

    index = bisect.bisect_left(character_starts, lower)
    if index >= len(character_starts):
        return lower

    return min(character_starts[index], upper)


def _make_reference(
    document_index: int,
    document: EncodedDocument,
    *,
    focus_start: int,
    focus_end: int,
    anchor: int,
    kind: str,
    max_length: int,
    context_before_bytes: int,
) -> SurgeryReference | None:
    length = int(document.input_ids.shape[0])
    focus_start = max(0, focus_start)
    focus_end = min(length, focus_end)

    if focus_start >= focus_end:
        return None

    if focus_end - focus_start > max_length:
        return None

    _, _, starts_tuple = build_source_boundaries(document.source)
    character_starts = list(starts_tuple)

    if not character_starts:
        return None

    lower = max(0, focus_end - max_length)
    upper = min(focus_start, max(0, length - 1))
    desired = max(0, anchor - context_before_bytes)
    window_start = _bounded_character_start(
        character_starts,
        desired=desired,
        lower=lower,
        upper=upper,
    )
    window_end = min(length, window_start + max_length)

    if focus_start < window_start or focus_end > window_end:
        return None

    return SurgeryReference(
        document_index=document_index,
        window_start=window_start,
        window_end=window_end,
        focus_start=focus_start,
        focus_end=focus_end,
        kind=kind,
    )


def build_surgery_references(
    documents: list[EncodedDocument],
    *,
    token_type_to_id: dict[str, int],
    max_length: int,
    halo_bytes: int,
    context_before_bytes: int,
) -> tuple[list[SurgeryReference], SurgeryInventory]:
    regexp_id = token_type_to_id["regexp"]
    operator_id = token_type_to_id["operator"]
    references: list[SurgeryReference] = []
    positive = 0
    negative = 0
    skipped = 0

    for document_index, document in enumerate(documents):
        utf16_to_utf8, _, starts_tuple = build_source_boundaries(document.source)

        for span in document.gold_spans:
            if span.token_type != "regexp":
                continue

            span_start = utf16_to_utf8.get(span.start)
            span_end = utf16_to_utf8.get(span.end)
            if span_start is None or span_end is None:
                continue

            reference = _make_reference(
                document_index,
                document,
                focus_start=span_start - halo_bytes,
                focus_end=span_end + halo_bytes,
                anchor=span_start,
                kind="regexp-positive",
                max_length=max_length,
                context_before_bytes=context_before_bytes,
            )

            if reference is None:
                skipped += 1
                continue

            references.append(reference)
            positive += 1

        for character, byte_start in zip(
            document.source,
            starts_tuple,
            strict=True,
        ):
            if character != "/":
                continue

            if byte_start >= document.token_type_labels.shape[0]:
                continue

            if int(document.token_type_labels[byte_start].item()) != operator_id:
                continue

            reference = _make_reference(
                document_index,
                document,
                focus_start=byte_start - halo_bytes,
                focus_end=byte_start + 1 + halo_bytes,
                anchor=byte_start,
                kind="operator-slash-negative",
                max_length=max_length,
                context_before_bytes=context_before_bytes,
            )

            if reference is None:
                continue

            references.append(reference)
            negative += 1

    # Sanity check: every positive focus must contain at least one regexp label.
    for reference in references:
        if reference.kind != "regexp-positive":
            continue
        document = documents[reference.document_index]
        labels = document.token_type_labels[reference.focus_start:reference.focus_end]
        if not bool((labels == regexp_id).any()):
            raise AssertionError("Regexp surgery focus lost its regexp label.")

    return references, SurgeryInventory(
        positive_regexp=positive,
        negative_operator_slash=negative,
        skipped_over_context=skipped,
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
        "target": "regexp",
        "base_checkpoint": str(args.checkpoint),
        "step": step,
        "steps": args.steps,
        "learning_rate": args.learning_rate,
        "batch_size": args.batch_size,
        "halo_bytes": args.halo_bytes,
        "context_before_bytes": args.context_before_bytes,
        "replay_every": args.replay_every,
        "seed": args.seed,
        "positive_regexp": inventory.positive_regexp,
        "negative_operator_slash": inventory.negative_operator_slash,
        "skipped_over_context": inventory.skipped_over_context,
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
    parser.add_argument("--halo-bytes", type=int, default=16)
    parser.add_argument("--context-before-bytes", type=int, default=128)
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
    if args.halo_bytes < 0:
        raise ValueError("--halo-bytes cannot be negative")

    torch.manual_seed(args.seed)
    device = select_device()
    model, base_checkpoint = load_model(args.checkpoint, device)
    config = base_checkpoint["config"]
    max_length = int(config["max_length"])

    print("Neural Semantic Highlighting")
    print("TypeScript RegExp Surgery Probe")
    print("")
    print(f"Device:          {device}")
    print(f"Base checkpoint: {args.checkpoint}")
    print(f"Steps:           {args.steps}")
    print(f"Batch size:      {args.batch_size}")
    print(f"Learning rate:   {args.learning_rate:g}")
    print(f"Halo:            {args.halo_bytes}B")
    print(f"Context before:  {args.context_before_bytes}B")
    print(f"Replay every:    {args.replay_every if args.replay_every else 'disabled'}")
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

    focus_dataset = RegexpSurgeryDataset(
        replay_dataset.documents,
        token_type_to_id=replay_dataset.schema.token_type_to_id,
        number_of_modifiers=len(replay_dataset.schema.modifiers),
        max_length=max_length,
        halo_bytes=args.halo_bytes,
        context_before_bytes=args.context_before_bytes,
    )

    inventory = focus_dataset.inventory
    print("Surgery inventory")
    print("-----------------")
    print(f"Positive regexp focuses: {inventory.positive_regexp}")
    print(f"Operator slash negatives: {inventory.negative_operator_slash}")
    print(f"Skipped over-context:     {inventory.skipped_over_context}")
    print(f"Focused samples:          {inventory.total}")
    print(f"Replay windows:           {len(replay_dataset)}")
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
