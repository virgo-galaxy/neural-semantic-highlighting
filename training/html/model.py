"""Small byte-level HTML model; no compiler, parser, transport, or theme dependency."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import torch
from torch import nn
from torch.nn import functional as F


def relative_layer(hidden, layer, distance, slopes, attention_mask=None):
    """Portable differentiable attention, shared with the browser export graph."""
    batch,length,width=hidden.shape;heads=layer.self_attn.num_heads;dimension=width//heads
    normalized=layer.norm1(hidden)
    query,key,value=F.linear(normalized,layer.self_attn.in_proj_weight,layer.self_attn.in_proj_bias).chunk(3,dim=-1)
    query=query.reshape(batch,length,heads,dimension).transpose(1,2)
    key=key.reshape(batch,length,heads,dimension).transpose(1,2)
    value=value.reshape(batch,length,heads,dimension).transpose(1,2)
    scores=torch.matmul(query,key.transpose(-2,-1))/math.sqrt(dimension)
    scores=scores-slopes.reshape(1,heads,1,1)*distance.reshape(1,1,length,length)
    if attention_mask is not None:scores=scores.masked_fill(~attention_mask[:,None,None,:],float('-inf'))
    weights=F.dropout(torch.softmax(scores,dim=-1),p=layer.self_attn.dropout,training=layer.training)
    attended=torch.matmul(weights,value).transpose(1,2).reshape(batch,length,width)
    hidden=hidden+layer.dropout1(layer.self_attn.out_proj(attended))
    return hidden+layer.dropout2(layer.linear2(layer.dropout(layer.activation(layer.linear1(layer.norm2(hidden))))))


@dataclass(frozen=True)
class ModelConfig:
    context_bytes: int = 512
    width: int = 128
    heads: int = 4
    layers: int = 4
    feed_forward: int = 512
    dropout: float = 0.1
    local_kernel: int = 1
    relative_attention: bool = False

    def validate(self) -> None:
        if self.context_bytes < 8 or min(self.width, self.heads, self.layers, self.feed_forward) < 1:
            raise ValueError("Invalid model dimensions")
        if self.width % self.heads or not 0 <= self.dropout < 1:
            raise ValueError("Width must be divisible by heads; dropout must be in [0, 1)")
        if self.local_kernel not in (1, 3, 5):
            raise ValueError("Local character context kernel must be 1, 3 or 5")
        if type(self.relative_attention) is not bool:
            raise ValueError('Relative attention must be explicitly enabled')

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ModelOutput:
    boundary: torch.Tensor
    token_type: torch.Tensor
    modifier: torch.Tensor


class HtmlSemanticTransformer(nn.Module):
    def __init__(self, config: ModelConfig, token_types: int, modifiers: int) -> None:
        super().__init__()
        config.validate()
        if token_types < 1 or modifiers < 1:
            raise ValueError("A HTML schema must have token types and modifiers")
        self.config = config
        self.relative_bias = nn.Parameter(torch.zeros(config.layers, config.heads)) if config.relative_attention else None
        self.byte_embedding = nn.Embedding(257, config.width, padding_idx=256)
        # Optional zero-initialized residual preserves the source backbone at
        # transfer time. It learns adjacent-byte context; no source grammar is
        # encoded here. Kernel one keeps historical checkpoints unchanged.
        self.local_context = None
        if config.local_kernel > 1:
            self.local_context = nn.Conv1d(config.width, config.width, config.local_kernel,
                                          padding=config.local_kernel // 2, groups=config.width)
            nn.init.zeros_(self.local_context.weight)
            nn.init.zeros_(self.local_context.bias)
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
        hidden = self.byte_embedding(input_ids)
        if self.local_context is not None:
            hidden = hidden + self.local_context(hidden.transpose(1, 2)).transpose(1, 2)
        hidden = hidden + self.position_embedding(positions)
        distance = (positions[0,:,None]-positions[0,None,:]).abs().to(hidden.dtype) if self.relative_bias is not None else None
        for index, layer in enumerate(self.layers):
            if self.relative_bias is None:
                hidden = layer(hidden, src_key_padding_mask=~attention_mask)
            else:
                hidden = relative_layer(hidden,layer,distance,self.relative_bias[index],attention_mask)
        hidden = self.norm(hidden)
        return ModelOutput(self.boundary_head(hidden), self.token_head(hidden), self.modifier_head(hidden))


def parameter_count(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
