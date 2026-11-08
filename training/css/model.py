"""Small byte-level CSS model; no compiler, parser, transport, or theme dependency."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class ModelConfig:
    context_bytes: int = 512
    width: int = 128
    heads: int = 4
    layers: int = 4
    feed_forward: int = 512
    dropout: float = 0.1

    def validate(self) -> None:
        if self.context_bytes < 8 or min(self.width, self.heads, self.layers, self.feed_forward) < 1:
            raise ValueError("Invalid model dimensions")
        if self.width % self.heads or not 0 <= self.dropout < 1:
            raise ValueError("Width must be divisible by heads; dropout must be in [0, 1)")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ModelOutput:
    boundary: torch.Tensor
    token_type: torch.Tensor
    modifier: torch.Tensor


class CssSemanticTransformer(nn.Module):
    def __init__(self, config: ModelConfig, token_types: int, modifiers: int) -> None:
        super().__init__()
        config.validate()
        if token_types < 1 or modifiers < 1:
            raise ValueError("A CSS schema must have token types and modifiers")
        self.config = config
        self.byte_embedding = nn.Embedding(257, config.width, padding_idx=256)
        self.position_embedding = nn.Embedding(config.context_bytes, config.width)
        # Construct each layer separately: cloned layers must not start with
        # identical parameters. The architecture matches the TS baseline family.
        self.layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config.width, nhead=config.heads,
                dim_feedforward=config.feed_forward, dropout=config.dropout,
                activation="gelu", batch_first=True, norm_first=True,
            ) for _ in range(config.layers)
        ])
        self.norm = nn.LayerNorm(config.width)
        self.boundary_head = nn.Linear(config.width, 3)
        self.token_head = nn.Linear(config.width, token_types)
        self.modifier_head = nn.Linear(config.width, modifiers)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> ModelOutput:
        if input_ids.ndim != 2 or attention_mask.shape != input_ids.shape:
            raise ValueError("Expected matching [batch, bytes] input and attention mask")
        length = input_ids.shape[1]
        if not 0 < length <= self.config.context_bytes:
            raise ValueError("Input length is outside the checkpoint context")
        positions = torch.arange(length, device=input_ids.device).unsqueeze(0)
        hidden = self.byte_embedding(input_ids) + self.position_embedding(positions)
        for layer in self.layers:
            hidden = layer(hidden, src_key_padding_mask=~attention_mask)
        hidden = self.norm(hidden)
        return ModelOutput(self.boundary_head(hidden), self.token_head(hidden), self.modifier_head(hidden))


def parameter_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
