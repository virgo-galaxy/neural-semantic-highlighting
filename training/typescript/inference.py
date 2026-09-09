from __future__ import annotations

import torch

from dataset import PAD_BYTE_ID, build_window_ranges
from model import SemanticTransformer


def build_fusion_weights(
    length: int,
    *,
    max_length: int,
    fusion: str,
) -> torch.Tensor:
    if fusion == "uniform":
        return torch.ones((length, 1), dtype=torch.float32)

    if fusion != "center":
        raise ValueError(f'Unknown inference fusion "{fusion}".')

    positions = torch.arange(length, dtype=torch.float32)
    center = (max_length - 1) / 2.0
    half_width = max(center, 1.0)
    distance = ((positions - center).abs() / half_width).clamp(0.0, 1.0)
    return (1.0 - 0.75 * distance).unsqueeze(1)


def predict_document_logits(
    model: SemanticTransformer,
    source: str,
    *,
    max_length: int,
    stride: int,
    device: torch.device,
    fusion: str = "center",
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    source_bytes = source.encode("utf-8")

    if not source_bytes:
        return (
            torch.empty((0, 3)),
            torch.empty((0, 0)),
            torch.empty((0, 0)),
        )

    boundary_sum: torch.Tensor | None = None
    token_type_sum: torch.Tensor | None = None
    modifier_sum: torch.Tensor | None = None
    weight_sum = torch.zeros((len(source_bytes), 1), dtype=torch.float32)

    with torch.no_grad():
        for start, end in build_window_ranges(
            len(source_bytes),
            max_length=max_length,
            stride=stride,
        ):
            chunk = source_bytes[start:end]
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

            output = model(input_ids=input_ids, attention_mask=attention_mask)
            boundary_logits = output.boundary_logits[0, :length].detach().cpu()
            token_type_logits = output.token_type_logits[0, :length].detach().cpu()
            modifier_logits = output.modifier_logits[0, :length].detach().cpu()

            if boundary_sum is None:
                boundary_sum = torch.zeros(
                    (len(source_bytes), boundary_logits.shape[-1]),
                    dtype=boundary_logits.dtype,
                )
                token_type_sum = torch.zeros(
                    (len(source_bytes), token_type_logits.shape[-1]),
                    dtype=token_type_logits.dtype,
                )
                modifier_sum = torch.zeros(
                    (len(source_bytes), modifier_logits.shape[-1]),
                    dtype=modifier_logits.dtype,
                )

            weights = build_fusion_weights(
                length,
                max_length=max_length,
                fusion=fusion,
            )
            boundary_sum[start:end] += boundary_logits * weights
            token_type_sum[start:end] += token_type_logits * weights
            modifier_sum[start:end] += modifier_logits * weights
            weight_sum[start:end] += weights

    if boundary_sum is None or token_type_sum is None or modifier_sum is None:
        raise RuntimeError("Inference produced no logits.")

    if torch.any(weight_sum == 0):
        raise RuntimeError("Sliding-window inference left uncovered bytes.")

    return (
        boundary_sum / weight_sum,
        token_type_sum / weight_sum,
        modifier_sum / weight_sum,
    )
