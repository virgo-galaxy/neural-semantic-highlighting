# R pack

Original `.R`, `.r` and explicit `.Rprofile` syntax: functions and lexical names,
assignments, pipes, formulas, data-frame/list indexing, namespace calls, properties,
backticks, standard/raw strings and comments. Common dplyr/tidyr/purrr/ggplot code
uses the same R model without claiming dependency or tidy-evaluation resolution.

See [semantics](SEMANTICS.md), [dataset](dataset/README.md), [Golden](fixtures/README.md)
and [training](../../training/r/README.md). Offline CST Gold uses pinned
[r-lib tree-sitter-r](https://github.com/r-lib/tree-sitter-r), not R execution.
No R SDK, interpreter or global package is installed. Modern accepted syntax
includes native pipes and short anonymous functions; it is bounded by the grammar.
