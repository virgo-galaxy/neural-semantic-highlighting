from __future__ import annotations

import argparse
import bisect
import random
import time
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from dataset import (
    IGNORE_LABEL_ID,
    EncodedDocument,
    TypeScriptSemanticDataset,
    build_source_boundaries,
    encode_document,
)
from predict import load_model, select_device
from string_surgery import StringSurgeryDataset, _masked_losses, _next_batch
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
    "v3-string-surgery-synthetic-code-probe/"
    "step-0400.pt"
)

CODE_MARKERS = (
    "const ",
    "let ",
    "function ",
    "return ",
    "if (",
    "for (",
    "while (",
    "class ",
    "interface ",
    "type ",
    "import ",
    "export ",
    "async ",
    "await ",
    "new ",
    "=>",
)


@dataclass(frozen=True)
class SyntheticInventory:
    source_documents: int
    candidate_chunks: int
    selected_chunks: int
    rejected_low_score: int
    rejected_string_comment_heavy: int
    body_bytes_total: int
    body_bytes_min: int
    body_bytes_max: int

    @property
    def average_body_bytes(self) -> float:
        if self.selected_chunks == 0:
            return 0.0
        return self.body_bytes_total / self.selected_chunks


@dataclass(frozen=True)
class CandidateChunk:
    document_index: int
    start_byte: int
    end_byte: int
    score: float
    string_comment_ratio: float
    text: str


def _utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def _utf16_offset(text: str, character_index: int) -> int:
    return _utf16_length(text[:character_index])


def _snap_byte_to_character_start(candidate: int, starts: list[int]) -> int:
    if not starts:
        return 0
    index = bisect.bisect_right(starts, candidate) - 1
    return starts[max(0, index)]


def _byte_to_character_index(candidate: int, starts: list[int]) -> int:
    return bisect.bisect_left(starts, candidate)


def _slice_source_by_bytes(
    source: str,
    *,
    character_starts: list[int],
    total_bytes: int,
    start_byte: int,
    target_bytes: int,
) -> tuple[str, int, int]:
    starts = character_starts
    if not starts or total_bytes == 0:
        return "", 0, 0

    start = _snap_byte_to_character_start(max(0, start_byte), starts)
    end_target = min(total_bytes, start + target_bytes)
    end_index = bisect.bisect_right(starts, end_target) - 1
    end_index = max(0, min(end_index, len(starts) - 1))

    # end is exclusive and should include the character that starts before the
    # target byte. Using the next character start keeps UTF-8 boundaries exact.
    if end_index + 1 < len(starts):
        end = starts[end_index + 1]
        end_char = end_index + 1
    else:
        end = total_bytes
        end_char = len(source)

    start_char = _byte_to_character_index(start, starts)
    return source[start_char:end_char], start, end


def _code_like_score(text: str) -> float:
    if not text.strip():
        return 0.0

    marker_hits = sum(text.count(marker) for marker in CODE_MARKERS)
    structural = (
        text.count("{")
        + text.count("}")
        + text.count("(")
        + text.count(")")
        + text.count(";")
        + text.count("=>") * 2
    )
    member_access = text.count(".")
    newlines = text.count("\n")

    return (
        marker_hits * 4.0
        + structural * 0.35
        + min(member_access, 40) * 0.10
        + min(newlines, 40) * 0.10
    )


def _string_comment_ratio(
    document: EncodedDocument,
    *,
    start_byte: int,
    end_byte: int,
    string_id: int,
    comment_id: int,
) -> float:
    if end_byte <= start_byte:
        return 1.0

    labels = document.token_type_labels[start_byte:end_byte]
    supervised = labels != IGNORE_LABEL_ID
    if not bool(supervised.any()):
        return 0.0

    relevant = (labels == string_id) | (labels == comment_id)
    return float(relevant[supervised].float().mean().item())


def _line_start_bytes(source: str, total_bytes: int) -> list[int]:
    starts = [0]
    byte_offset = 0
    for line in source.splitlines(keepends=True):
        byte_offset += len(line.encode("utf-8"))
        if byte_offset < total_bytes:
            starts.append(byte_offset)
    return starts


def collect_code_like_chunks(
    documents: list[EncodedDocument],
    *,
    token_type_to_id: dict[str, int],
    target_body_bytes: int,
    min_body_bytes: int,
    max_synthetic_documents: int,
    max_per_source_document: int,
    score_threshold: float,
    max_string_comment_ratio: float,
    seed: int,
) -> tuple[list[CandidateChunk], SyntheticInventory]:
    string_id = token_type_to_id["string"]
    comment_id = token_type_to_id["comment"]
    rng = random.Random(seed)

    candidates: list[CandidateChunk] = []
    rejected_low_score = 0
    rejected_string_comment_heavy = 0

    document_order = list(range(len(documents)))
    rng.shuffle(document_order)

    for document_index in document_order:
        document = documents[document_index]
        source_bytes = len(document.source.encode("utf-8"))
        if source_bytes < min_body_bytes:
            continue

        _, _, character_starts_tuple = build_source_boundaries(document.source)
        character_starts = list(character_starts_tuple)
        if not character_starts:
            continue

        line_starts = _line_start_bytes(document.source, source_bytes)
        if not line_starts:
            continue

        # A few deterministic/randomized line starts per source are enough to
        # create diverse hard strings without letting one large repository file
        # dominate the probe.
        start_candidates = list(line_starts)
        rng.shuffle(start_candidates)
        accepted_for_document: list[CandidateChunk] = []

        for start_byte in start_candidates[: max(12, max_per_source_document * 8)]:
            body, actual_start, actual_end = _slice_source_by_bytes(
                document.source,
                character_starts=character_starts,
                total_bytes=source_bytes,
                start_byte=start_byte,
                target_bytes=target_body_bytes,
            )
            body_bytes = len(body.encode("utf-8"))
            if body_bytes < min_body_bytes:
                continue

            score = _code_like_score(body)
            if score < score_threshold:
                rejected_low_score += 1
                continue

            ratio = _string_comment_ratio(
                document,
                start_byte=actual_start,
                end_byte=actual_end,
                string_id=string_id,
                comment_id=comment_id,
            )
            if ratio > max_string_comment_ratio:
                rejected_string_comment_heavy += 1
                continue

            accepted_for_document.append(
                CandidateChunk(
                    document_index=document_index,
                    start_byte=actual_start,
                    end_byte=actual_end,
                    score=score,
                    string_comment_ratio=ratio,
                    text=body,
                )
            )

        accepted_for_document.sort(
            key=lambda item: (item.score, -item.string_comment_ratio),
            reverse=True,
        )
        candidates.extend(accepted_for_document[:max_per_source_document])

    # Keep the globally strongest chunks, then shuffle them so the generated
    # dataset is not ordered by repository/file score.
    candidates.sort(key=lambda item: item.score, reverse=True)
    selected = candidates[:max_synthetic_documents]
    rng.shuffle(selected)

    body_sizes = [len(candidate.text.encode("utf-8")) for candidate in selected]
    inventory = SyntheticInventory(
        source_documents=len(documents),
        candidate_chunks=len(candidates),
        selected_chunks=len(selected),
        rejected_low_score=rejected_low_score,
        rejected_string_comment_heavy=rejected_string_comment_heavy,
        body_bytes_total=sum(body_sizes),
        body_bytes_min=min(body_sizes) if body_sizes else 0,
        body_bytes_max=max(body_sizes) if body_sizes else 0,
    )
    return selected, inventory


def escape_template_body(text: str) -> str:
    # Preserve the visible code shape while keeping the generated TypeScript
    # template literal syntactically inert: no interpolation and no accidental
    # closing backtick. Backslashes are doubled first so later escapes remain
    # literal characters in the template body.
    return (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
        .replace("\x00", "\\0")
    )


def build_synthetic_document(
    candidate: CandidateChunk,
    *,
    schema,
    index: int,
) -> EncodedDocument:
    body = escape_template_body(candidate.text)
    prefix = "const syntheticPayload = `"
    suffix = "`;\nvoid syntheticPayload;\n"
    source = prefix + body + suffix

    literal_start_character = len(prefix) - 1
    literal_end_character = len(prefix) + len(body) + 1
    semicolon_character = literal_end_character

    literal_start = _utf16_offset(source, literal_start_character)
    literal_end = _utf16_offset(source, literal_end_character)
    semicolon_start = _utf16_offset(source, semicolon_character)
    semicolon_end = _utf16_offset(source, semicolon_character + 1)

    sample = {
        "repository": "synthetic-train",
        "path": f"code-looking-string-{index:05d}.ts",
        "documentKind": "typescript",
        "source": source,
        "result": {
            "spans": [
                {
                    "start": literal_start,
                    "end": literal_end,
                    "tokenType": "string",
                },
                {
                    "start": semicolon_start,
                    "end": semicolon_end,
                    "tokenType": "punctuation",
                },
            ]
        },
    }
    return encode_document(sample, schema)


def build_synthetic_documents(
    documents: list[EncodedDocument],
    *,
    schema,
    target_body_bytes: int,
    min_body_bytes: int,
    max_synthetic_documents: int,
    max_per_source_document: int,
    score_threshold: float,
    max_string_comment_ratio: float,
    seed: int,
) -> tuple[list[EncodedDocument], SyntheticInventory, list[CandidateChunk]]:
    selected, inventory = collect_code_like_chunks(
        documents,
        token_type_to_id=schema.token_type_to_id,
        target_body_bytes=target_body_bytes,
        min_body_bytes=min_body_bytes,
        max_synthetic_documents=max_synthetic_documents,
        max_per_source_document=max_per_source_document,
        score_threshold=score_threshold,
        max_string_comment_ratio=max_string_comment_ratio,
        seed=seed,
    )
    synthetic = [
        build_synthetic_document(candidate, schema=schema, index=index)
        for index, candidate in enumerate(selected)
    ]
    return synthetic, inventory, selected


def _cpu_state_dict(model) -> dict[str, torch.Tensor]:
    return {
        name: tensor.detach().cpu()
        for name, tensor in model.state_dict().items()
    }


def save_checkpoint(
    path: Path,
    *,
    base_checkpoint: dict,
    model,
    optimizer,
    step: int,
    args: argparse.Namespace,
    synthetic_inventory: SyntheticInventory,
    focus_inventory,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = dict(base_checkpoint)
    checkpoint["model_state_dict"] = _cpu_state_dict(model)
    checkpoint["optimizer_state_dict"] = cpu_optimizer_state_dict(optimizer)
    checkpoint["surgery"] = {
        "target": "synthetic-code-looking-string",
        "base_checkpoint": str(args.checkpoint),
        "step": step,
        "steps": args.steps,
        "learning_rate": args.learning_rate,
        "batch_size": args.batch_size,
        "target_body_bytes": args.target_body_bytes,
        "min_body_bytes": args.min_body_bytes,
        "max_synthetic_documents": args.max_synthetic_documents,
        "max_per_source_document": args.max_per_source_document,
        "score_threshold": args.score_threshold,
        "max_string_comment_ratio": args.max_string_comment_ratio,
        "first_inside_offset_bytes": args.first_inside_offset_bytes,
        "step_bytes": args.step_bytes,
        "min_remaining_bytes": args.min_remaining_bytes,
        "right_halo_bytes": args.right_halo_bytes,
        "replay_every": args.replay_every,
        "seed": args.seed,
        "synthetic_documents": synthetic_inventory.selected_chunks,
        "continuation_focuses": focus_inventory.continuation_focuses,
        "end_boundary_focuses": focus_inventory.end_boundary_focuses,
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
    parser.add_argument("--target-body-bytes", type=int, default=768)
    parser.add_argument("--min-body-bytes", type=int, default=640)
    parser.add_argument("--max-synthetic-documents", type=int, default=1200)
    parser.add_argument("--max-per-source-document", type=int, default=2)
    parser.add_argument("--score-threshold", type=float, default=18.0)
    parser.add_argument("--max-string-comment-ratio", type=float, default=0.35)
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
    if args.target_body_bytes < args.min_body_bytes:
        raise ValueError("--target-body-bytes must be >= --min-body-bytes")
    if args.min_body_bytes <= 0:
        raise ValueError("--min-body-bytes must be positive")
    if args.max_synthetic_documents <= 0:
        raise ValueError("--max-synthetic-documents must be positive")
    if args.max_per_source_document <= 0:
        raise ValueError("--max-per-source-document must be positive")
    if not 0.0 <= args.max_string_comment_ratio <= 1.0:
        raise ValueError("--max-string-comment-ratio must be between 0 and 1")

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = select_device()
    model, base_checkpoint = load_model(args.checkpoint, device)
    config = base_checkpoint["config"]
    max_length = int(config["max_length"])

    print("Neural Semantic Highlighting")
    print("TypeScript Synthetic Code-looking String Surgery Probe")
    print("")
    print(f"Device:                    {device}")
    print(f"Base checkpoint:           {args.checkpoint}")
    print(f"Steps:                     {args.steps}")
    print(f"Batch size:                {args.batch_size}")
    print(f"Learning rate:             {args.learning_rate:g}")
    print(f"Target/min body:           {args.target_body_bytes}/{args.min_body_bytes}B")
    print(f"Max synthetic documents:   {args.max_synthetic_documents}")
    print(f"Max per source document:   {args.max_per_source_document}")
    print(f"Code-like score threshold: {args.score_threshold:g}")
    print(f"Max string/comment ratio:  {args.max_string_comment_ratio:.2f}")
    print(f"Replay every:              {args.replay_every if args.replay_every else 'disabled'}")
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

    synthetic_documents, synthetic_inventory, selected_chunks = build_synthetic_documents(
        replay_dataset.documents,
        schema=replay_dataset.schema,
        target_body_bytes=args.target_body_bytes,
        min_body_bytes=args.min_body_bytes,
        max_synthetic_documents=args.max_synthetic_documents,
        max_per_source_document=args.max_per_source_document,
        score_threshold=args.score_threshold,
        max_string_comment_ratio=args.max_string_comment_ratio,
        seed=args.seed,
    )
    if not synthetic_documents:
        raise ValueError("Synthetic code-looking string generator produced no documents.")

    # Each synthetic document contains one long template string built only from
    # Train-split code. The normal StringSurgeryDataset then creates views that
    # begin inside that string, deliberately hiding the opener.
    focus_dataset = StringSurgeryDataset(
        synthetic_documents,
        token_type_to_id=replay_dataset.schema.token_type_to_id,
        number_of_modifiers=len(replay_dataset.schema.modifiers),
        max_length=max_length,
        min_span_bytes=args.min_body_bytes,
        first_inside_offset_bytes=args.first_inside_offset_bytes,
        step_bytes=args.step_bytes,
        min_remaining_bytes=args.min_remaining_bytes,
        right_halo_bytes=args.right_halo_bytes,
    )
    focus_inventory = focus_dataset.inventory
    if len(focus_dataset) == 0:
        raise ValueError("Synthetic string surgery produced no continuation focuses.")

    print("Synthetic curriculum inventory")
    print("------------------------------")
    print(f"Train source documents:      {synthetic_inventory.source_documents}")
    print(f"Accepted candidate chunks:   {synthetic_inventory.candidate_chunks}")
    print(f"Selected synthetic strings:  {synthetic_inventory.selected_chunks}")
    print(f"Rejected low code score:     {synthetic_inventory.rejected_low_score}")
    print(f"Rejected string/comment:     {synthetic_inventory.rejected_string_comment_heavy}")
    print(
        "Synthetic body bytes:        "
        f"avg={synthetic_inventory.average_body_bytes:.1f} "
        f"min={synthetic_inventory.body_bytes_min} "
        f"max={synthetic_inventory.body_bytes_max}"
    )
    print(f"Continuation focuses:        {focus_inventory.continuation_focuses}")
    print(f"End-visible focuses:         {focus_inventory.end_boundary_focuses}")
    print(f"Replay windows:              {len(replay_dataset)}")
    print("")

    # Give one compact example summary without dumping source text into logs.
    if selected_chunks:
        example = selected_chunks[0]
        print(
            "Example source chunk:       "
            f"train-doc={example.document_index} "
            f"bytes={len(example.text.encode('utf-8'))} "
            f"score={example.score:.1f} "
            f"string/comment={example.string_comment_ratio:.2f}"
        )
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
    running_focus_loss = 0.0

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
        if not use_replay:
            running_focus_loss += float(loss.item())

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
            if path != args.output:
                save_checkpoint(
                    path,
                    base_checkpoint=base_checkpoint,
                    model=model,
                    optimizer=optimizer,
                    step=step,
                    args=args,
                    synthetic_inventory=synthetic_inventory,
                    focus_inventory=focus_inventory,
                )
                print(f"  saved snapshot: {path}", flush=True)

    save_checkpoint(
        args.output,
        base_checkpoint=base_checkpoint,
        model=model,
        optimizer=optimizer,
        step=args.steps,
        args=args,
        synthetic_inventory=synthetic_inventory,
        focus_inventory=focus_inventory,
    )

    elapsed = time.perf_counter() - started
    print("")
    print("Surgery complete.")
    print(f"Focus/replay steps: {focus_steps}/{replay_steps}")
    print(f"Average total loss: {running_loss / args.steps:.4f}")
    print(
        "Average focus loss: "
        f"{running_focus_loss / max(focus_steps, 1):.4f}"
    )
    print(f"Elapsed:            {elapsed:.1f}s")
    print(f"Output:             {args.output}")


if __name__ == "__main__":
    main()
