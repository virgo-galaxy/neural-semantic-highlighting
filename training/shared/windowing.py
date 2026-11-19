"""Optional position-weighted neural logit windows; never inspect source spelling."""
from __future__ import annotations

from bisect import bisect_right
import math
import torch


def validate(policy):
    if (not isinstance(policy, dict) or policy.get('format') != 'nsh-overlap-logits-v1'
            or type(policy.get('strideBytes')) is not int or policy['strideBytes'] not in [128, 256]
            or policy.get('edgeWeightCap') != 128
            or type(policy.get('adaptiveWeight')) not in [int, float]
            or policy['adaptiveWeight'] not in [0, .5]):
        raise ValueError('Invalid neural window-fusion policy')


@torch.inference_mode()
def overlap_logits(model, source, device, policy, *, window_cache=None):
    from training.shared.inference import character_map
    from training.shared.model import ModelOutput
    validate(policy)
    raw = source.encode('utf-8')
    starts, _ = character_map(source)
    shape = [3, model.token_head.out_features, model.modifier_head.out_features]
    sums = [torch.zeros(len(raw), columns, dtype=torch.float64) for columns in shape]
    counts = torch.zeros(len(raw), 1, dtype=torch.float64)
    cursor = 0
    while cursor < len(raw):
        end = starts[bisect_right(starts, min(cursor + 512, len(raw))) - 1]
        key = (cursor, end)
        if window_cache is not None and key in window_cache:
            output = window_cache[key]
        else:
            ids = torch.tensor([list(raw[cursor:end])], dtype=torch.long, device=device)
            output = model(ids, torch.ones_like(ids, dtype=torch.bool))
            if window_cache is not None:
                window_cache[key] = output
        length = end - cursor
        weights = torch.minimum(torch.arange(1, length + 1), torch.arange(length, 0, -1)).clamp(max=128).double().reshape(-1, 1)
        for total, values in zip(sums, [output.boundary, output.token_type, output.modifier]):
            total[cursor:end] += values[0].cpu().double() * weights
        counts[cursor:end] += weights
        if end == len(raw):
            break
        next_cursor = starts[bisect_right(starts, cursor + policy['strideBytes']) - 1]
        if next_cursor <= cursor:
            raise ValueError('Overlapping inference cursor made no progress')
        cursor = next_cursor
    return ModelOutput(*(total / counts for total in sums))
