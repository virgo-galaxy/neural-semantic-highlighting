from __future__ import annotations

import argparse
import bisect
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn

CHECKPOINT_FORMAT = "nsh-typescript-checkpoint"
PAD_BYTE_ID = 256
BOUNDARY_OUTSIDE_ID = 0
BOUNDARY_BEGIN_ID = 1
BOUNDARY_INSIDE_ID = 2

PACK_DIRECTORY = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PACK_DIRECTORY / "model" / "model.pt"
DEFAULT_MODEL_METADATA_PATH = PACK_DIRECTORY / "model" / "model.json"
DEFAULT_MANIFEST_PATH = PACK_DIRECTORY / "manifest.json"


@dataclass
class SemanticModelOutput:
    boundary_logits: torch.Tensor
    token_type_logits: torch.Tensor
    modifier_logits: torch.Tensor


class SemanticTransformer(nn.Module):
    """Inference architecture used by the selected TypeScript model."""

    def __init__(
        self,
        *,
        vocab_size: int,
        number_of_boundary_classes: int,
        number_of_token_types: int,
        number_of_modifiers: int,
        max_length: int,
        embedding_dimension: int,
        number_of_heads: int,
        number_of_layers: int,
        feed_forward_dimension: int,
        padding_id: int = PAD_BYTE_ID,
    ) -> None:
        super().__init__()

        self.max_length = max_length
        self.byte_embedding = nn.Embedding(
            vocab_size,
            embedding_dimension,
            padding_idx=padding_id,
        )
        self.position_embedding = nn.Embedding(max_length, embedding_dimension)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dimension,
            nhead=number_of_heads,
            dim_feedforward=feed_forward_dimension,
            dropout=0.0,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=number_of_layers,
            enable_nested_tensor=False,
        )
        self.final_norm = nn.LayerNorm(embedding_dimension)
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

        active_length = int(attention_mask.sum(dim=1).max().item())
        active_length = max(1, active_length)

        if active_length < sequence_length:
            input_ids = input_ids[:, :active_length]
            attention_mask = attention_mask[:, :active_length]

        positions = torch.arange(
            active_length,
            device=input_ids.device,
        ).unsqueeze(0)
        positions = positions.expand(batch_size, active_length)

        hidden_states = self.byte_embedding(input_ids) + self.position_embedding(positions)
        hidden_states = self.encoder(
            hidden_states,
            src_key_padding_mask=~attention_mask,
        )
        hidden_states = self.final_norm(hidden_states)

        boundary_logits = self.boundary_head(hidden_states)
        token_type_logits = self.token_type_head(hidden_states)
        modifier_logits = self.modifier_head(hidden_states)

        if active_length < sequence_length:
            padding_length = sequence_length - active_length

            def pad_logits(logits: torch.Tensor) -> torch.Tensor:
                return torch.cat(
                    (
                        logits,
                        logits.new_zeros(
                            (
                                batch_size,
                                padding_length,
                                logits.shape[-1],
                            )
                        ),
                    ),
                    dim=1,
                )

            boundary_logits = pad_logits(boundary_logits)
            token_type_logits = pad_logits(token_type_logits)
            modifier_logits = pad_logits(modifier_logits)

        return SemanticModelOutput(
            boundary_logits=boundary_logits,
            token_type_logits=token_type_logits,
            modifier_logits=modifier_logits,
        )


@dataclass(frozen=True)
class CharacterPoint:
    utf16_start: int
    utf16_end: int
    byte_start: int


class TypeScriptLocalPack:
    """Run the selected TypeScript pack locally in a long-lived Python process."""

    def __init__(
        self,
        *,
        model_path: Path = DEFAULT_MODEL_PATH,
        model_metadata_path: Path = DEFAULT_MODEL_METADATA_PATH,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
        device: torch.device | None = None,
    ) -> None:
        self.device = device or select_device()
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.model_metadata = json.loads(
            model_metadata_path.read_text(encoding="utf-8")
        )
        self.document_kinds = frozenset(
            item["id"] for item in self.manifest["documentKinds"]
        )
        self.modifier_threshold = float(
            self.model_metadata["inference"]["modifierThreshold"]
        )
        self.model, self.checkpoint = load_model(model_path, self.device)

        checkpoint_token_types = tuple(self.checkpoint["schema"]["token_types"])
        checkpoint_modifiers = tuple(self.checkpoint["schema"]["modifiers"])
        metadata_token_types = tuple(
            self.model_metadata["orderedLabels"]["tokenTypes"]
        )
        metadata_modifiers = tuple(
            self.model_metadata["orderedLabels"]["modifiers"]
        )

        if checkpoint_token_types != metadata_token_types:
            raise ValueError("Model token type order does not match model.json.")

        if checkpoint_modifiers != metadata_modifiers:
            raise ValueError("Model modifier order does not match model.json.")

        self.token_types = checkpoint_token_types
        self.modifiers = checkpoint_modifiers

    def highlight(self, *, source: str, document_kind: str) -> dict[str, Any]:
        if document_kind not in self.document_kinds:
            raise ValueError(f'Unsupported document kind "{document_kind}".')

        boundary_logits, token_type_logits, modifier_logits = predict_document_logits(
            self.model,
            source,
            max_length=int(self.checkpoint["config"]["max_length"]),
            device=self.device,
        )

        spans = decode_predictions(
            source,
            boundary_logits,
            token_type_logits,
            modifier_logits,
            token_types=self.token_types,
            modifiers=self.modifiers,
            modifier_threshold=self.modifier_threshold,
        )

        return {
            "offsetEncoding": "utf-16",
            "spans": spans,
        }


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


def load_model(
    model_path: Path,
    device: torch.device,
) -> tuple[SemanticTransformer, dict[str, Any]]:
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

    if checkpoint.get("format") != CHECKPOINT_FORMAT:
        raise ValueError("Model is not an NSH TypeScript multitask checkpoint.")

    config = checkpoint["config"]
    model = SemanticTransformer(
        vocab_size=config["vocab_size"],
        number_of_boundary_classes=config["number_of_boundary_classes"],
        number_of_token_types=config["number_of_token_types"],
        number_of_modifiers=config["number_of_modifiers"],
        max_length=config["max_length"],
        embedding_dimension=config["embedding_dimension"],
        number_of_heads=config["number_of_heads"],
        number_of_layers=config["number_of_layers"],
        feed_forward_dimension=config["feed_forward_dimension"],
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    return model, checkpoint


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


def predict_window(
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

    output = model(input_ids=input_ids, attention_mask=attention_mask)

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
            boundary_logits, token_type_logits, modifier_logits = predict_window(
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

    if boundary_result is None or token_type_result is None or modifier_result is None:
        raise RuntimeError("Inference produced no logits.")

    return boundary_result, token_type_result, modifier_result


def build_character_points(source: str) -> list[CharacterPoint]:
    points: list[CharacterPoint] = []
    utf16_offset = 0
    byte_offset = 0

    for character in source:
        utf16_length = len(character.encode("utf-16-le")) // 2
        points.append(
            CharacterPoint(
                utf16_start=utf16_offset,
                utf16_end=utf16_offset + utf16_length,
                byte_start=byte_offset,
            )
        )
        utf16_offset += utf16_length
        byte_offset += len(character.encode("utf-8"))

    return points


def decode_predictions(
    source: str,
    boundary_logits: torch.Tensor,
    token_type_logits: torch.Tensor,
    modifier_logits: torch.Tensor,
    *,
    token_types: tuple[str, ...],
    modifiers: tuple[str, ...],
    modifier_threshold: float,
) -> list[dict[str, Any]]:
    points = build_character_points(source)

    if not points:
        return []

    boundary_ids = [
        int(boundary_logits[point.byte_start].argmax().item()) for point in points
    ]
    span_ranges: list[tuple[int, int]] = []
    current_start: int | None = None

    def flush(end_index: int) -> None:
        nonlocal current_start

        if current_start is not None:
            span_ranges.append((current_start, end_index))

        current_start = None

    for index, boundary_id in enumerate(boundary_ids):
        if boundary_id == BOUNDARY_OUTSIDE_ID:
            flush(index)
            continue

        if boundary_id == BOUNDARY_BEGIN_ID:
            flush(index)
            current_start = index
            continue

        if boundary_id == BOUNDARY_INSIDE_ID and current_start is None:
            current_start = index

    flush(len(points))
    spans: list[dict[str, Any]] = []

    for start_index, end_index in span_ranges:
        span_points = points[start_index:end_index]
        byte_positions = torch.tensor(
            [point.byte_start for point in span_points],
            dtype=torch.long,
        )
        mean_type_logits = token_type_logits[byte_positions].mean(dim=0)
        token_type_id = int(mean_type_logits.argmax().item())
        start_point = span_points[0]
        end_point = span_points[-1]
        modifier_probabilities = torch.sigmoid(modifier_logits[start_point.byte_start])
        predicted_modifiers = [
            modifier
            for modifier, probability in zip(
                modifiers,
                modifier_probabilities.tolist(),
                strict=True,
            )
            if probability >= modifier_threshold
        ]
        span: dict[str, Any] = {
            "start": start_point.utf16_start,
            "end": end_point.utf16_end,
            "tokenType": token_types[token_type_id],
        }

        if predicted_modifiers:
            span["modifiers"] = predicted_modifiers

        spans.append(span)

    return spans


def run_stdio(pack: TypeScriptLocalPack) -> None:
    """Serve newline-delimited HighlightRequest messages over stdin/stdout."""

    for line in sys.stdin:
        line = line.strip()

        if not line:
            continue

        request_id: Any = None

        try:
            request = json.loads(line)

            if not isinstance(request, dict):
                raise ValueError("Request must be a JSON object.")

            request_id = request.get("id")
            source = request.get("source")
            document_kind = request.get("documentKind")

            if not isinstance(source, str):
                raise ValueError('Request field "source" must be a string.')

            if not isinstance(document_kind, str):
                raise ValueError('Request field "documentKind" must be a string.')

            response = {
                "id": request_id,
                "result": pack.highlight(
                    source=source,
                    document_kind=document_kind,
                ),
            }
        except Exception as error:
            response = {
                "id": request_id,
                "error": {"message": str(error)},
            }

        print(
            json.dumps(
                response,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            flush=True,
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--text")
    source_group.add_argument("--file", type=Path)
    source_group.add_argument(
        "--stdio",
        action="store_true",
        help="Keep the model loaded and exchange JSONL messages over stdin/stdout.",
    )
    parser.add_argument("--document-kind", default="typescript")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    pack = TypeScriptLocalPack()

    if args.stdio:
        run_stdio(pack)
        return

    if args.file is not None:
        source = args.file.read_text(encoding="utf-8")
    elif args.text is not None:
        source = args.text
    else:
        source = "const value = 1;"

    result = pack.highlight(source=source, document_kind=args.document_kind)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
