from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass
class SemanticModelOutput:
    boundary_logits: torch.Tensor
    token_type_logits: torch.Tensor
    modifier_logits: torch.Tensor


class SemanticTransformer(nn.Module):
    def __init__(
        self,
        *,
        vocab_size: int,
        number_of_boundary_classes: int,
        number_of_token_types: int,
        number_of_modifiers: int,
        max_length: int = 512,
        embedding_dimension: int = 128,
        number_of_heads: int = 4,
        number_of_layers: int = 4,
        feed_forward_dimension: int = 512,
        dropout: float = 0.1,
        padding_id: int = 256,
    ) -> None:
        super().__init__()

        self.max_length = max_length

        self.byte_embedding = nn.Embedding(
            vocab_size,
            embedding_dimension,
            padding_idx=padding_id,
        )

        self.position_embedding = nn.Embedding(
            max_length,
            embedding_dimension,
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dimension,
            nhead=number_of_heads,
            dim_feedforward=feed_forward_dimension,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=number_of_layers,
            enable_nested_tensor=False,
        )

        self.final_norm = nn.LayerNorm(
            embedding_dimension
        )

        self.boundary_head = nn.Linear(
            embedding_dimension,
            number_of_boundary_classes,
        )

        self.token_type_head = nn.Linear(
            embedding_dimension,
            number_of_token_types,
        )

        self.modifier_head = nn.Linear(
            embedding_dimension,
            number_of_modifiers,
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> SemanticModelOutput:
        batch_size, sequence_length = input_ids.shape

        if sequence_length > self.max_length:
            raise ValueError(
                f"Sequence length {sequence_length} exceeds "
                f"maximum length {self.max_length}."
            )

        positions = torch.arange(
            sequence_length,
            device=input_ids.device,
        ).unsqueeze(0)

        positions = positions.expand(
            batch_size,
            sequence_length,
        )

        hidden_states = (
            self.byte_embedding(input_ids)
            + self.position_embedding(positions)
        )

        hidden_states = self.encoder(
            hidden_states,
            src_key_padding_mask=~attention_mask,
        )

        hidden_states = self.final_norm(
            hidden_states
        )

        return SemanticModelOutput(
            boundary_logits=self.boundary_head(
                hidden_states
            ),
            token_type_logits=self.token_type_head(
                hidden_states
            ),
            modifier_logits=self.modifier_head(
                hidden_states
            ),
        )


def count_parameters(
    model: nn.Module,
) -> int:
    return sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )


def main() -> None:
    model = SemanticTransformer(
        vocab_size=257,
        number_of_boundary_classes=3,
        number_of_token_types=24,
        number_of_modifiers=14,
    )

    input_ids = torch.randint(
        0,
        256,
        (2, 512),
        dtype=torch.long,
    )

    attention_mask = torch.ones(
        (2, 512),
        dtype=torch.bool,
    )

    output = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
    )

    print("Neural Semantic Highlighting")
    print("TypeScript V2 Multitask Transformer")
    print("")
    print(
        f"Parameters: {count_parameters(model):,}"
    )
    print(
        "Boundary logits:   "
        f"{tuple(output.boundary_logits.shape)}"
    )
    print(
        "Token type logits: "
        f"{tuple(output.token_type_logits.shape)}"
    )
    print(
        "Modifier logits:   "
        f"{tuple(output.modifier_logits.shape)}"
    )


if __name__ == "__main__":
    main()
