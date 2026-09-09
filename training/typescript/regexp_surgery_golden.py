from __future__ import annotations

from dataset import (
    IGNORE_LABEL_ID,
    encode_document,
    load_schema,
)
from regexp_surgery import RegexpSurgeryDataset


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
    source = "const re = /foo/g; const ratio = left / right;"
    document = build_document(
        source,
        [
            span(source, "const", "keyword"),
            span(source, "re", "variable"),
            span(source, "=", "operator"),
            span(source, "/foo/g", "regexp"),
            span(source, ";", "punctuation"),
            span(source, "ratio", "variable"),
            span(source, "left", "variable"),
            # The second slash is the operator negative.
            {
                "start": utf16_offset(source, "/ right"),
                "end": utf16_offset(source, "/ right") + 1,
                "tokenType": "operator",
            },
            span(source, "right", "variable"),
        ],
    )

    dataset = RegexpSurgeryDataset(
        [document],
        token_type_to_id=schema.token_type_to_id,
        number_of_modifiers=len(schema.modifiers),
        max_length=64,
        halo_bytes=4,
        context_before_bytes=8,
    )

    assert dataset.inventory.positive_regexp == 1
    assert dataset.inventory.negative_operator_slash == 1
    assert len(dataset) == 2

    positive_index = next(
        index
        for index, reference in enumerate(dataset.references)
        if reference.kind == "regexp-positive"
    )
    positive = dataset[positive_index]
    supervised = positive["boundary_labels"] != IGNORE_LABEL_ID
    assert bool(supervised.any())
    assert int(supervised.sum().item()) < len(source.encode("utf-8"))

    regexp_id = schema.token_type_to_id["regexp"]
    assert bool((positive["token_type_labels"] == regexp_id).any())

    # The right halo must include the semicolon boundary so surgery can learn
    # that `/foo/g` ends before `;` rather than swallowing it.
    punctuation_id = schema.token_type_to_id["punctuation"]
    assert bool((positive["token_type_labels"] == punctuation_id).any())

    negative_index = next(
        index
        for index, reference in enumerate(dataset.references)
        if reference.kind == "operator-slash-negative"
    )
    negative = dataset[negative_index]
    operator_id = schema.token_type_to_id["operator"]
    assert bool((negative["token_type_labels"] == operator_id).any())

    print("Neural Semantic Highlighting")
    print("TypeScript RegExp Surgery Golden")
    print("")
    print("PASS  positive focus contains regexp")
    print("PASS  positive right halo supervises following punctuation")
    print("PASS  labels outside the focus are ignored")
    print("PASS  operator slash negative is preserved")
    print("")
    print("Surgery golden cases: 4/4 passed")


if __name__ == "__main__":
    main()
