"""Reuse source-agnostic byte inference and UTF-16 BIO decoding; no HTML parsing."""
from training.html.inference import character_map, predicted_cut, document_logits, decode
