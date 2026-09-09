from __future__ import annotations

import bisect

import torch

from dataset import BOUNDARY_BEGIN_ID, BOUNDARY_INSIDE_ID, PAD_BYTE_ID
from model import SemanticTransformer


def build_character_starts(source: str) -> tuple[int, ...]:
    starts = [0]
    offset = 0

    for character in source:
        offset += len(character.encode("utf-8"))
        starts.append(offset)

    return tuple(starts)




def choose_runtime_lookahead_bounds(
    character_starts: tuple[int, ...],
    *,
    cursor: int,
    limit: int,
) -> tuple[int, int]:
    """Choose a safe candidate plus one complete lookahead character.

    The returned chunk never crosses ``limit`` even when a multi-byte UTF-8
    character straddles the nominal context boundary.
    """
    chunk_end_index = bisect.bisect_right(character_starts, limit) - 1

    if chunk_end_index <= 0:
        raise RuntimeError("Unable to place runtime cursor lookahead.")

    chunk_end = character_starts[chunk_end_index]
    candidate_end = character_starts[chunk_end_index - 1]

    if candidate_end <= cursor or chunk_end > limit:
        raise RuntimeError("Invalid runtime cursor lookahead range.")

    return candidate_end, chunk_end


def choose_predicted_cursor_cut(
    boundary_logits: torch.Tensor,
    *,
    candidate: int,
    character_starts: tuple[int, ...],
) -> int:
    """Move a runtime cut left when the boundary head predicts INSIDE.

    `candidate` is a local byte offset whose character is included as one-byte/
    one-character lookahead in the current model window. If that character is
    predicted INSIDE, walk backward to the predicted BEGIN of the active span.
    """
    if candidate <= 0 or candidate >= boundary_logits.shape[0]:
        return candidate

    predicted = boundary_logits.argmax(dim=-1)

    if int(predicted[candidate].item()) != BOUNDARY_INSIDE_ID:
        return candidate

    index = bisect.bisect_left(character_starts, candidate) - 1

    for position_index in range(index, -1, -1):
        position = character_starts[position_index]
        label = int(predicted[position].item())

        if label == BOUNDARY_BEGIN_ID:
            return position if position > 0 else candidate

        if label != BOUNDARY_INSIDE_ID:
            return candidate

    return candidate


def _predict_window(
    model: SemanticTransformer,
    chunk: bytes,
    *,
    max_length: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
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

    return (
        output.boundary_logits[0, :length].detach().cpu(),
        output.token_type_logits[0, :length].detach().cpu(),
        output.modifier_logits[0, :length].detach().cpu(),
    )


def predict_document_logits(
    model: SemanticTransformer,
    source: str,
    *,
    max_length: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Predict a document with a runtime adaptive cursor.

    The first window starts at byte 0. For each later cut, the current window
    includes one full character of lookahead. If the boundary head predicts
    that lookahead character is INSIDE an active semantic span, the cursor
    moves left to that span's predicted BEGIN. Only the committed prefix is
    emitted; the discarded tail is re-read by the next window.

    There is no fixed overlap percentage and no fusion step.
    """
    source_bytes = source.encode("utf-8")
    total_length = len(source_bytes)

    if total_length == 0:
        return (
            torch.empty((0, 3)),
            torch.empty((0, 0)),
            torch.empty((0, 0)),
        )

    if max_length <= 4:
        raise ValueError("max_length must be greater than 4 bytes.")

    global_character_starts = build_character_starts(source)
    boundary_result: torch.Tensor | None = None
    token_type_result: torch.Tensor | None = None
    modifier_result: torch.Tensor | None = None

    cursor = 0

    with torch.no_grad():
        while cursor < total_length:
            remaining = total_length - cursor

            if remaining <= max_length:
                chunk_end = total_length
                commit_end = total_length
            else:
                limit = cursor + max_length
                candidate_end, chunk_end = choose_runtime_lookahead_bounds(
                    global_character_starts,
                    cursor=cursor,
                    limit=limit,
                )
                commit_end = candidate_end

            chunk = source_bytes[cursor:chunk_end]
            (
                boundary_logits,
                token_type_logits,
                modifier_logits,
            ) = _predict_window(
                model,
                chunk,
                max_length=max_length,
                device=device,
            )

            if boundary_result is None:
                boundary_result = torch.empty(
                    (total_length, boundary_logits.shape[-1]),
                    dtype=boundary_logits.dtype,
                )
                token_type_result = torch.empty(
                    (total_length, token_type_logits.shape[-1]),
                    dtype=token_type_logits.dtype,
                )
                modifier_result = torch.empty(
                    (total_length, modifier_logits.shape[-1]),
                    dtype=modifier_logits.dtype,
                )

            if commit_end < total_length:
                local_character_starts = tuple(
                    position - cursor
                    for position in global_character_starts
                    if cursor <= position <= chunk_end
                )
                candidate = commit_end - cursor
                safe_candidate = choose_predicted_cursor_cut(
                    boundary_logits,
                    candidate=candidate,
                    character_starts=local_character_starts,
                )

                if safe_candidate > 0:
                    commit_end = cursor + safe_candidate

            if commit_end <= cursor:
                raise RuntimeError("Adaptive cursor made no forward progress.")

            committed_length = commit_end - cursor
            boundary_result[cursor:commit_end] = boundary_logits[:committed_length]
            token_type_result[cursor:commit_end] = token_type_logits[:committed_length]
            modifier_result[cursor:commit_end] = modifier_logits[:committed_length]
            cursor = commit_end

    if (
        boundary_result is None
        or token_type_result is None
        or modifier_result is None
    ):
        raise RuntimeError("Inference produced no logits.")

    return boundary_result, token_type_result, modifier_result
