"""Export-only tensor graph using unchanged selected inference weights.

The selected encoders are pre-norm Transformer layers. Browser windows contain
only real UTF-8 bytes, so no padding mask or Python-side length extraction is
needed. Attention is expressed with portable tensor operators for ONNX/WASM.
"""
import math
import torch
from torch import nn
from torch.nn import functional as F
from training.html.model import relative_layer


class BrowserTransformer(nn.Module):
    def __init__(self, selected):
        super().__init__()
        self.byte_embedding = selected.byte_embedding
        self.position_embedding = selected.position_embedding
        self.local_context = getattr(selected, 'local_context', None)
        self.relative_bias = getattr(selected, 'relative_bias', None)
        self.layers = selected.encoder.layers if hasattr(selected, 'encoder') else selected.layers
        self.norm = selected.final_norm if hasattr(selected, 'final_norm') else selected.norm
        self.boundary_head = selected.boundary_head
        self.token_head = selected.token_type_head if hasattr(selected, 'token_type_head') else selected.token_head
        self.modifier_head = selected.modifier_head

    def forward(self, input_ids):
        length = input_ids.shape[1]
        hidden = self.byte_embedding(input_ids)
        if self.local_context is not None:
            hidden = hidden + self.local_context(hidden.transpose(1, 2)).transpose(1, 2)
        hidden = hidden + self.position_embedding(torch.arange(length, device=input_ids.device).unsqueeze(0))
        for index, layer in enumerate(self.layers):
            if self.relative_bias is not None:
                positions=torch.arange(length,device=input_ids.device)
                distance=(positions[:,None]-positions[None,:]).abs().to(hidden.dtype)
                hidden=relative_layer(hidden,layer,distance,self.relative_bias[index])
                continue
            normalized = layer.norm1(hidden)
            query, key, value = F.linear(normalized, layer.self_attn.in_proj_weight,
                                         layer.self_attn.in_proj_bias).chunk(3, dim=-1)
            heads = layer.self_attn.num_heads
            width = layer.self_attn.embed_dim
            dimension = width // heads
            query = query.reshape(1, length, heads, dimension).transpose(1, 2)
            key = key.reshape(1, length, heads, dimension).transpose(1, 2)
            value = value.reshape(1, length, heads, dimension).transpose(1, 2)
            scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(dimension)
            attended = torch.matmul(torch.softmax(scores, dim=-1), value)
            attended = attended.transpose(1, 2).reshape(1, length, width)
            hidden = hidden + layer.self_attn.out_proj(attended)
            hidden = hidden + layer.linear2(F.gelu(layer.linear1(layer.norm2(hidden))))
        hidden = self.norm(hidden)
        return self.boundary_head(hidden), self.token_head(hidden), self.modifier_head(hidden)
