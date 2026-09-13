"""Canonical Go semantic role groups shared by training and lexical inference."""
from __future__ import annotations

IDENTIFIER_ROLES = (
    "namespace", "type", "interface", "type-parameter", "function", "method",
    "parameter", "variable", "property", "label",
)
LEXICAL_ROLES = {"keyword", "comment", "string", "number", "operator", "punctuation"}
