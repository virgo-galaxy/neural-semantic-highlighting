"""Masked multitask losses; modifiers are supervised at span beginnings only."""
from __future__ import annotations

import torch
from torch.nn import functional as F

from encoding import IGNORE
from model import ModelOutput


def compute_loss(output: ModelOutput, batch: dict, weights: dict, modifier_weight: float = .1) -> tuple[torch.Tensor, dict]:
    def cross_entropy(logits: torch.Tensor, targets: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
        valid = targets != IGNORE
        if not bool(valid.any()):
            return logits.sum() * 0
        return F.cross_entropy(logits[valid], targets[valid], weight=weight)
    boundary = cross_entropy(output.boundary, batch["boundary_labels"], weights["boundary"])
    token = cross_entropy(output.token_type, batch["token_type_labels"], weights["token_type"])
    begins = batch["boundary_labels"] == 1
    if bool(begins.any()):
        modifier = F.binary_cross_entropy_with_logits(output.modifier[begins], batch["modifier_targets"][begins],
                                                      pos_weight=weights["modifier"])
    else:
        modifier = output.modifier.sum() * 0
    total = boundary + token + modifier_weight * modifier
    return total, {"total": float(total.detach()), "boundary": float(boundary.detach()),
                   "token_type": float(token.detach()), "modifier": float(modifier.detach())}
