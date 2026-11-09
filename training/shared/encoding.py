"""pack byte labels and windows. This module uses only the Python standard library."""
from __future__ import annotations

from training.shared.spec import current

from array import array
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

PAD = 256
IGNORE = -100
OUTSIDE, BEGIN, INSIDE = 0, 1, 2
COLUMNS = {"input_ids": "H", "boundary_labels": "b", "token_type_labels": "h", "modifier_bits": "H"}


@dataclass(frozen=True)
class Schema:
    token_types: tuple[str, ...]
    modifiers: tuple[str, ...]

    @classmethod
    def load(cls, path: Path) -> Schema:
        data = json.loads(path.read_text(encoding="utf-8"))
        result = cls(tuple(x["id"] for x in data["tokenTypes"]), tuple(x["id"] for x in data["tokenModifiers"]))
        if len(set(result.token_types)) != len(result.token_types) or len(set(result.modifiers)) != len(result.modifiers):
            raise ValueError("Duplicate schema ids")
        if len(result.modifiers) > 16 or len(result.token_types) > 32767:
            raise ValueError("Schema exceeds the binary encoding capacity")
        return result


@dataclass
class Encoded:
    columns: dict[str, array]
    starts: list[int]
    spans: list[tuple[int, int]]
    normalized_hash: str
    shape_hash: str


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def encode(record: dict[str, Any], schema: Schema) -> Encoded:
    """Validate UTF-16 Gold and encode labels only at UTF-8 character starts.

    Modifiers are supervised at span beginnings, matching the existing TypeScript
    byte-label convention. Continuation bytes and padding use IGNORE labels.
    """
    source = record["source"]
    raw = source.encode("utf-8")
    if not isinstance(record.get("documentKind"), str) or not record["documentKind"] or not raw:
        raise ValueError("Expected a nonempty pack document")
    if digest(raw) != record["contentHash"]:
        raise ValueError("Source content hash mismatch")
    result = record["result"]
    if result.get("offsetEncoding") != "utf-16":
        raise ValueError("Expected UTF-16 Gold offsets")
    mapping, starts = {0: 0}, []
    unit, offset = 0, 0
    for character in source:
        starts.append(offset)
        unit += 2 if ord(character) > 0xFFFF else 1
        offset += len(character.encode("utf-8"))
        mapping[unit] = offset
    columns = {
        "input_ids": array("H", list(raw)),
        "boundary_labels": array("b", [IGNORE]) * len(raw),
        "token_type_labels": array("h", [IGNORE]) * len(raw),
        "modifier_bits": array("H", [0]) * len(raw),
    }
    for position in starts:
        columns["boundary_labels"][position] = OUTSIDE
    token_ids = {value: index for index, value in enumerate(schema.token_types)}
    modifier_ids = {value: index for index, value in enumerate(schema.modifiers)}
    spans, lexical, shape, names = [], [], [], {}
    previous_end = 0
    identifier_roles = {"namespace", "type", "class", "interface", "enum", "enum-member", "constructor", "tag", "attribute", "function", "parameter", "variable", "property", "method", "decorator", "label"}
    for span in result["spans"]:
        lo, hi = span["start"], span["end"]
        if type(lo) is not int or type(hi) is not int or lo not in mapping or hi not in mapping or lo >= hi:
            raise ValueError(f"Invalid UTF-16 span {lo!r}..{hi!r}")
        start, end = mapping[lo], mapping[hi]
        if start < previous_end:
            raise ValueError("Overlapping or unsorted Gold spans")
        if raw[previous_end:start].decode("utf-8").strip():
            raise ValueError("Unlabeled non-whitespace source gap")
        previous_end = end
        role = span["tokenType"]
        if role not in token_ids:
            raise ValueError(f"Unknown token type: {role}")
        modifiers = span.get("modifiers", [])
        if len(set(modifiers)) != len(modifiers) or any(item not in modifier_ids for item in modifiers):
            raise ValueError("Invalid modifiers")
        first, last = bisect_left(starts, start), bisect_left(starts, end)
        for i in range(first, last):
            position = starts[i]
            columns["boundary_labels"][position] = BEGIN if i == first else INSIDE
            columns["token_type_labels"][position] = token_ids[role]
        columns["modifier_bits"][start] = sum(1 << modifier_ids[m] for m in modifiers)
        spans.append((start, end))
        if role == "comment":
            continue
        text = raw[start:end].decode("utf-8")
        if role == "punctuation" and start == 0 and text == "\ufeff":
            continue  # Original BOM stays supervised; it must not conceal a source copy.
        lexical.append(text)
        if role in identifier_roles and "default-library" not in modifiers:
            text = role + ":identifier:" + str(names.setdefault(text, len(names)))
        elif role in {"number", "string", "text", "entity"} or role.startswith("embedded-"):
            text = "literal:" + role
        shape.append(text)
    if raw[previous_end:].decode("utf-8").strip():
        raise ValueError("Unlabeled non-whitespace source suffix")
    canonical = lambda values: digest(json.dumps(values, ensure_ascii=True, separators=(",", ":")).encode())
    return Encoded(columns, starts + [len(raw)], spans, canonical(lexical), canonical(shape))


def windows(encoded: Encoded, max_length: int, adaptive: bool) -> tuple[list[tuple[int, int]], dict[str, int]]:
    """Contiguous cursor windows; validation/test cuts never consult Gold spans."""
    if max_length < 4:
        raise ValueError("Context must fit any UTF-8 code point (at least 4 bytes)")
    total = len(encoded.columns["input_ids"])
    span_starts = [span[0] for span in encoded.spans]
    output, cursor = [], 0
    stats = {"characterCuts": 0, "spanCuts": 0, "insideStarts": 0}
    while cursor < total:
        target = min(cursor + max_length, total)
        end = encoded.starts[bisect_right(encoded.starts, target) - 1]
        stats["characterCuts"] += end != target
        if adaptive and end < total:
            i = bisect_right(span_starts, end) - 1
            if i >= 0:
                lo, hi = encoded.spans[i]
                if cursor < lo < end < hi:
                    end = lo
                    stats["spanCuts"] += 1
        if end <= cursor:
            raise ValueError("Window cursor made no progress")
        stats["insideStarts"] += encoded.columns["boundary_labels"][cursor] == INSIDE
        output.append((cursor, end))
        cursor = end
    return output, stats


def padded_window(encoded: Encoded, start: int, end: int, size: int) -> dict[str, array]:
    defaults = {"input_ids": PAD, "boundary_labels": IGNORE, "token_type_labels": IGNORE, "modifier_bits": 0}
    return {name: values[start:end] + array(values.typecode, [defaults[name]]) * (size - end + start)
            for name, values in encoded.columns.items()}


def little_endian_bytes(values: array) -> bytes:
    if sys.byteorder == "little" or values.itemsize == 1:
        return values.tobytes()
    copy = values[:]
    copy.byteswap()
    return copy.tobytes()

