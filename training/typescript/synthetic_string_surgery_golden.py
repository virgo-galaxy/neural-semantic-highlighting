from __future__ import annotations

from dataset import BOUNDARY_INSIDE_ID, IGNORE_LABEL_ID, encode_document, load_schema
from string_surgery import StringSurgeryDataset
from synthetic_string_surgery import (
    CandidateChunk,
    build_synthetic_document,
    collect_code_like_chunks,
    escape_template_body,
)


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def build_train_document(source: str):
    schema = load_schema()
    spans = []
    for token, token_type in [
        ("const", "keyword"),
        ("return", "keyword"),
    ]:
        start_char = source.index(token)
        spans.append(
            {
                "start": utf16_length(source[:start_char]),
                "end": utf16_length(source[: start_char + len(token)]),
                "tokenType": token_type,
            }
        )
    return encode_document(
        {
            "repository": "example",
            "path": "source.ts",
            "documentKind": "typescript",
            "source": source,
            "result": {"spans": spans},
        },
        schema,
    )


def main() -> None:
    schema = load_schema()
    code = (
        "const h = (tag, text) => {\n"
        "  const el = document.createElement(tag);\n"
        "  el.textContent = text;\n"
        "  if (el.dataset.active) return el;\n"
        "  return document.body.appendChild(el);\n"
        "}\n"
    ) * 5
    source_document = build_train_document(code)

    selected, inventory = collect_code_like_chunks(
        [source_document],
        token_type_to_id=schema.token_type_to_id,
        target_body_bytes=512,
        min_body_bytes=400,
        max_synthetic_documents=2,
        max_per_source_document=2,
        score_threshold=5.0,
        max_string_comment_ratio=0.5,
        seed=42,
    )
    assert selected
    assert inventory.selected_chunks >= 1

    candidate = CandidateChunk(
        document_index=0,
        start_byte=0,
        end_byte=len(code.encode("utf-8")),
        score=100.0,
        string_comment_ratio=0.0,
        text=code + "const marker = `${notInterpolation}`; const tick = `x`;\\n",
    )

    escaped = escape_template_body(candidate.text)
    assert "\\${notInterpolation}" in escaped
    assert "\\`x\\`" in escaped

    synthetic = build_synthetic_document(candidate, schema=schema, index=0)
    assert synthetic.source.startswith("const syntheticPayload = `")
    assert len(synthetic.gold_spans) == 2
    assert synthetic.gold_spans[0].token_type == "string"
    assert synthetic.gold_spans[1].token_type == "punctuation"

    dataset = StringSurgeryDataset(
        [synthetic],
        token_type_to_id=schema.token_type_to_id,
        number_of_modifiers=len(schema.modifiers),
        max_length=256,
        min_span_bytes=256,
        first_inside_offset_bytes=64,
        step_bytes=128,
        min_remaining_bytes=32,
        right_halo_bytes=8,
    )
    assert dataset.inventory.continuation_focuses >= 2
    assert dataset.inventory.end_boundary_focuses >= 1

    first_reference = dataset.references[0]
    first = dataset[0]
    string_id = schema.token_type_to_id["string"]
    assert first_reference.window_start > first_reference.span_start
    assert int(first["boundary_labels"][0].item()) == BOUNDARY_INSIDE_ID
    assert int(first["token_type_labels"][0].item()) == string_id
    assert bool((first["boundary_labels"] != IGNORE_LABEL_ID).any())

    end_index = next(
        index
        for index, reference in enumerate(dataset.references)
        if reference.includes_end_boundary
    )
    end_view = dataset[end_index]
    punctuation_id = schema.token_type_to_id["punctuation"]
    assert bool((end_view["token_type_labels"] == punctuation_id).any())

    # Make sure this is a genuinely code-looking continuation, not a normal
    # prose string: the model-facing string body contains source-code markers.
    assert "document.createElement" in synthetic.source
    assert "return document.body" in synthetic.source

    print("Neural Semantic Highlighting")
    print("TypeScript Synthetic Code-looking String Surgery Golden")
    print("")
    print("PASS  collector selects code-looking chunks from Train documents")
    print("PASS  generated body is code-looking Train-style text")
    print("PASS  template delimiters/interpolation are escaped")
    print("PASS  continuation view starts inside synthetic string")
    print("PASS  continuation view excludes the opener")
    print("PASS  end-visible view supervises trailing punctuation")
    print("")
    print("Surgery golden cases: 6/6 passed")


if __name__ == "__main__":
    main()
