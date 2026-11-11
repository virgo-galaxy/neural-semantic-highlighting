# R dataset

`make dataset-r` retains pinned original R source, licenses and blob hashes under
`~/Datasets/neural-semantic-highlighting/r`. Four bounded upstream captures use
dplyr, ggplot2, tidyr and purrr. The original curriculum generates 50 separate
families with 24 variants each, including mixed raw strings and common statistical /
data syntax. Golden, tests and Playground are excluded from collection roots.

Corpus/Gold/prepared revisions are immutable. Exact and cross-family copies are
audited before windowing, and source families are frozen before training. Real
natural and authored focus streams remain separate. Full optimizer/RNG checkpoints
stay under artifacts/r, never in the committed inference bundle.

`make dataset-r-tools` compiles fixed tree-sitter runtime/grammar sources with the
existing Clang into ignored project cache. Original licenses, Git revisions/blob
hashes, compiler and binary provenance are retained. No R environment is installed;
collected source and dependencies never run. Parser/Unicode/coverage errors fail
closed and quarantines are reported rather than silently rewritten.
