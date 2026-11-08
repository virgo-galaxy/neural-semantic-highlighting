"""Reuse atomic files and per-run locks; all Vue paths remain independent."""
from training.html.io import atomic_json, training_lock
