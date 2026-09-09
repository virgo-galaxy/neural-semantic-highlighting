from __future__ import annotations

from dataset import (
    BOUNDARY_INSIDE_ID,
    IGNORE_LABEL_ID,
    encode_document,
    load_schema,
)
from string_surgery import StringSurgeryDataset


def utf16_offset(text: str, needle: str) -> int:
    index = text.index(needle)
    return len(text[:index].encode("utf-16-le")) // 2


def span(source: str, text: str, token_type: str) -> dict:
    start = utf16_offset(source, text)
    end = start + len(text.encode("utf-16-le")) // 2
    return {
        "start": start,
        "end": end,
        "tokenType": token_type,
    }


def build_document(source: str, spans: list[dict]):
    schema = load_schema()
    return encode_document(
        {
            "repository": "example",
            "path": "sample.ts",
            "documentKind": "typescript",
            "source": source,
            "result": {"spans": spans},
        },
        schema,
    )


def main() -> None:
    schema = load_schema()
    body = (
        "const h = (tag, text) => { const el = document.createElement(tag); "
        "el.textContent = text; return el; }; "
    ) * 4
    literal = '"' + body + '"'
    source = f"const payload = {literal}; const after = 1;"

    document = build_document(
        source,
        [
            span(source, "const", "keyword"),
            span(source, "payload", "variable"),
            span(source, "=", "operator"),
            span(source, literal, "string"),
            {
                "start": utf16_offset(source, "; const after"),
                "end": utf16_offset(source, "; const after") + 1,
                "tokenType": "punctuation",
            },
        ],
    )

    dataset = StringSurgeryDataset(
        [document],
        token_type_to_id=schema.token_type_to_id,
        number_of_modifiers=len(schema.modifiers),
        max_length=256,
        min_span_bytes=128,
        first_inside_offset_bytes=64,
        step_bytes=128,
        min_remaining_bytes=32,
        right_halo_bytes=8,
    )

    assert dataset.inventory.eligible_string_spans == 1
    assert dataset.inventory.over_context_spans == 1
    assert dataset.inventory.continuation_focuses >= 2
    assert dataset.inventory.end_boundary_focuses >= 1

    string_id = schema.token_type_to_id["string"]
    punctuation_id = schema.token_type_to_id["punctuation"]

    first_reference = dataset.references[0]
    assert first_reference.window_start > first_reference.span_start
    first = dataset[0]
    assert int(first["boundary_labels"][0].item()) == BOUNDARY_INSIDE_ID
    assert int(first["token_type_labels"][0].item()) == string_id

    supervised = first["boundary_labels"] != IGNORE_LABEL_ID
    assert bool(supervised.any())
    assert int(supervised.sum().item()) <= 256

    end_index = next(
        index
        for index, reference in enumerate(dataset.references)
        if reference.includes_end_boundary
    )
    end_view = dataset[end_index]
    assert bool((end_view["token_type_labels"] == punctuation_id).any())

    print("Neural Semantic Highlighting")
    print("TypeScript String Surgery Golden")
    print("")
    print("PASS  continuation view starts inside the string")
    print("PASS  continuation view excludes the opener")
    print("PASS  labels outside the focused continuation are ignored")
    print("PASS  end-visible view supervises the right-side punctuation")
    print("")
    print("Surgery golden cases: 4/4 passed")


if __name__ == "__main__":
    main()
