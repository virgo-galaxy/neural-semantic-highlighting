"""Deterministic Go lexical scaffolding for neural semantic classification."""
from __future__ import annotations

from bisect import bisect_left
import json
import os
import subprocess

import torch

from inference import character_map
from model import ModelOutput
from trainer_data import REPOSITORY

IDENTIFIER_ROLES = (
    "namespace", "type", "interface", "type-parameter", "function", "method",
    "parameter", "variable", "property", "label",
)
LEXICAL_ROLES = {"keyword", "comment", "string", "number", "operator", "punctuation"}


def scan_documents(documents: dict[str, dict]) -> dict[str, dict]:
    requests = "".join(
        json.dumps({"id": doc_id, "source": doc["source"]}, ensure_ascii=False) + "\n"
        for doc_id, doc in documents.items()
    )
    env = os.environ.copy()
    env.setdefault("GOTOOLCHAIN", "go1.27.1")
    completed = subprocess.run(
        ["go", "run", "./lexical/cmd/nsh-go-lex"],
        cwd=REPOSITORY / "packs/go",
        input=requests,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"Go lexical scanner failed:\n{completed.stderr}")
    output: dict[str, dict] = {}
    for line in completed.stdout.splitlines():
        row = json.loads(line)
        if row.get("error"):
            raise RuntimeError(f"Go lexical scanner failed for {row.get('id')}: {row['error']}")
        doc_id = row.get("id")
        if not isinstance(doc_id, str) or doc_id in output:
            raise RuntimeError("Go lexical scanner returned an invalid/duplicate document id")
        output[doc_id] = row["result"]
    if set(output) != set(documents):
        raise RuntimeError("Go lexical scanner did not return exactly the requested documents")
    return output


def constrained_decode(source: str, logits: ModelOutput, lexical: dict, schema: dict,
                       *, modifier_threshold: float) -> dict:
    if lexical.get("offsetEncoding") != "utf-16":
        raise ValueError("Go lexical scaffold must use UTF-16 offsets")
    byte_starts, utf16_units = character_map(source)
    unit_to_byte = {unit: byte for byte, unit in zip(byte_starts, utf16_units)}
    character_positions = byte_starts[:-1]
    token_ids = {name: index for index, name in enumerate(schema["tokenTypes"])}
    modifier_names = list(schema["modifiers"])
    identifier_ids = torch.tensor([token_ids[name] for name in IDENTIFIER_ROLES], dtype=torch.long)
    spans = []
    for item in lexical.get("spans", []):
        start_u, end_u, kind = int(item["start"]), int(item["end"]), str(item["kind"])
        if start_u not in unit_to_byte or end_u not in unit_to_byte or start_u >= end_u:
            raise ValueError("Lexical span is not aligned to source character boundaries")
        start_b, end_b = unit_to_byte[start_u], unit_to_byte[end_u]
        if kind in LEXICAL_ROLES:
            role = kind
            modifiers: list[str] = []
        elif kind == "identifier":
            lo = bisect_left(character_positions, start_b)
            hi = bisect_left(character_positions, end_b)
            positions = torch.tensor(character_positions[lo:hi], dtype=torch.long)
            if not len(positions):
                raise ValueError("Identifier lexical span contains no character positions")
            scores = logits.token_type[positions].mean(0)
            local = scores[identifier_ids].argmax().item()
            role = IDENTIFIER_ROLES[local]
            flags = logits.modifier[start_b].sigmoid() >= modifier_threshold
            modifiers = [name for name, present in zip(modifier_names, flags.tolist()) if present]
        else:
            raise ValueError(f"Unknown Go lexical kind: {kind}")
        span = {"start": start_u, "end": end_u, "tokenType": role}
        if modifiers:
            span["modifiers"] = modifiers
        spans.append(span)
    return {"offsetEncoding": "utf-16", "spans": spans}
