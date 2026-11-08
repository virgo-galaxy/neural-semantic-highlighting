"""Reuse the same small Transformer implementation; Vue owns its labels and weights."""
from training.html.model import (HtmlSemanticTransformer as VueSemanticTransformer,
    ModelConfig, ModelOutput, parameter_count)
