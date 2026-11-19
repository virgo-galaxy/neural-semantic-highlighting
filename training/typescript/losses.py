"""Optional source-end emphasis, independent of source spelling and token role."""
import torch
from torch.nn import functional as F


def weighted_token_loss(logits, targets, criterion, position_weights=None):
    flat=logits.reshape(-1,logits.shape[-1]);labels=targets.reshape(-1)
    if position_weights is None:return criterion(flat,labels)
    weights=position_weights.reshape(-1).to(device=logits.device,dtype=logits.dtype)
    if weights.shape!=labels.shape:raise ValueError('Loss weights must align with source positions')
    valid=labels!=criterion.ignore_index
    safe=labels.masked_fill(~valid,0)
    classes=criterion.weight[safe]if criterion.weight is not None else torch.ones_like(weights)
    losses=F.cross_entropy(flat,labels,weight=criterion.weight,ignore_index=criterion.ignore_index,reduction='none')
    return (losses*weights).sum()/(classes*weights*valid).sum().clamp_min(1e-8)
