"""Predicted adaptive-cursor inference and greedy UTF-16 span decoding."""
from __future__ import annotations

from bisect import bisect_left, bisect_right

import torch

from training.shared.model import SemanticTransformer, ModelOutput


def character_map(source: str) -> tuple[list[int], list[int]]:
    byte, unit = 0, 0
    starts, units = [0], [0]
    for char in source:
        byte += len(char.encode("utf-8"))
        unit += 2 if ord(char) > 0xFFFF else 1
        starts.append(byte)
        units.append(unit)
    return starts, units


def predicted_cut(boundary: torch.Tensor, candidate: int, starts: list[int]) -> int:
    """Use one complete lookahead character; never consult Gold boundaries."""
    ids = boundary.argmax(-1).tolist()
    if candidate <= 0 or candidate >= len(ids) or ids[candidate] != 2:
        return candidate
    for index in range(bisect_left(starts, candidate) - 1, -1, -1):
        position = starts[index]
        if ids[position] == 1:
            return position if position > 0 else candidate
        if ids[position] != 2:
            return candidate
    return candidate


@torch.inference_mode()
def document_logits(model: SemanticTransformer, source: str, device: torch.device,
                    *, adaptive: bool = True) -> ModelOutput:
    raw = source.encode("utf-8")
    total, context = len(raw), model.config.context_bytes
    result = ModelOutput(torch.empty(total, 3), torch.empty(total, model.token_head.out_features),
                         torch.empty(total, model.modifier_head.out_features))
    if not total:
        return result
    starts, _ = character_map(source)
    cursor = 0
    model.eval()
    while cursor < total:
        end_index = bisect_right(starts, min(cursor + context, total)) - 1
        chunk_end = starts[end_index]
        commit = chunk_end
        if adaptive and chunk_end < total:
            commit = starts[end_index - 1]
        if commit <= cursor:
            raise RuntimeError("Inference cursor made no progress")
        ids = torch.tensor([list(raw[cursor:chunk_end])], dtype=torch.long, device=device)
        output = model(ids, torch.ones_like(ids, dtype=torch.bool))
        local = ModelOutput(output.boundary[0].cpu(), output.token_type[0].cpu(), output.modifier[0].cpu())
        if adaptive and chunk_end < total:
            begin_index = bisect_left(starts, cursor)
            local_starts = [value - cursor for value in starts[begin_index:end_index + 1]]
            commit = cursor + predicted_cut(local.boundary, commit - cursor, local_starts)
        if not cursor < commit <= chunk_end:
            raise RuntimeError("Invalid predicted cursor cut")
        count = commit - cursor
        result.boundary[cursor:commit] = local.boundary[:count]
        result.token_type[cursor:commit] = local.token_type[:count]
        result.modifier[cursor:commit] = local.modifier[:count]
        cursor = commit
    return result


def decode(source: str, logits: ModelOutput, schema: dict, *, threshold: float = .60,
           coalesce_types: tuple[str, ...] = (), modifier_roles: dict | None = None) -> dict:
    if not 0 < threshold < 1:
        raise ValueError("Modifier threshold must be between 0 and 1")
    starts, units = character_map(source)
    if logits.boundary.shape[0] != starts[-1]:
        raise ValueError("Source bytes and logits do not align")
    positions = starts[:-1]
    if not positions:
        return {"offsetEncoding": "utf-16", "spans": []}
    indices = torch.tensor(positions, dtype=torch.long)
    boundaries = logits.boundary[indices].argmax(-1).tolist()
    ranges, active = [], None
    for index, label in enumerate(boundaries):
        if label in (0, 1):
            if active is not None:
                ranges.append((active, index))
            active = index if label == 1 else None
        elif label == 2:
            if active is None:
                active = index
        else:
            raise ValueError("Unknown predicted boundary class")
    if active is not None:
        ranges.append((active, len(positions)))
    if not ranges:
        return {"offsetEncoding": "utf-16", "spans": []}
    lo = torch.tensor([a for a, _ in ranges], dtype=torch.long)
    hi = torch.tensor([b for _, b in ranges], dtype=torch.long)
    types = logits.token_type[indices]
    # Prefix sums implement mean-logit voting without a Python tensor operation
    # per span. Dividing by span length would not change argmax.
    # Accumulate on CPU in float64 to avoid cancellation for short spans late
    # in a long document. No float64 tensor is sent to the MPS device.
    prefix = torch.cat((torch.zeros(1, types.shape[-1], dtype=torch.float64),
                        types.cumsum(0, dtype=torch.float64)), dim=0)
    role_ids = (prefix[hi] - prefix[lo]).argmax(-1).tolist()
    modifier_flags = (logits.modifier[indices[lo]].sigmoid() >= threshold).tolist()
    spans = []
    for (a, b), role, flags in zip(ranges, role_ids, modifier_flags):
        item = {"start": units[a], "end": units[b], "tokenType": schema["tokenTypes"][role]}
        modifiers = [name for name, present in zip(schema["modifiers"], flags)
                     if present and (modifier_roles is None or name not in modifier_roles or item['tokenType'] in modifier_roles[name])]
        if modifiers:
            item["modifiers"] = modifiers
        if (spans and item['tokenType'] in coalesce_types and spans[-1]['tokenType']==item['tokenType']
                and spans[-1]['end']==item['start'] and spans[-1].get('modifiers',[])==item.get('modifiers',[])):
            # Match the pack's canonical adjacent-region contract. This does
            # not inspect source spelling or change any predicted token role.
            spans[-1]['end']=item['end']
        else:spans.append(item)
    return {"offsetEncoding": "utf-16", "spans": spans}
