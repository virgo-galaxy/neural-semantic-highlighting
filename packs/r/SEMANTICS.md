# R source-local semantic contract

Original `.R`, `.r` and explicit `.Rprofile` code uses one `r` model. The pinned
r-lib tree-sitter-r 1.3.0 grammar supplies offline CST supervision. No R interpreter,
SDK, package install, project execution or imported code is required. Only parser
sources compile with existing Clang in ignored project cache. Frontend inference
uses neural weights without a lexer, parser, R process or source-spelling repair.

Functions assigned with `<-`, `=`, or `->` have function declaration roles.
Arguments and defaults bind source-local parameters; lexical scope is a function,
not every brace block. Ordinary assignments/loop names bind variables. Super
assignments have variable roles without claiming a new local declaration. Known
function parameters retain their parameter role when called. Other direct calls
are functions and extracted calls are methods. No capitalization/type heuristics
or resolution of dynamic environments, promises, S3/S4 dispatch or NSE occurs.

Namespace qualifiers are namespaces. `$` fields and `@` slots are properties;
named argument labels are parameters. Backticks retain original identifier spans.
Formulas, base/magrittr pipes and custom percent operators are syntax, without
interpreting formula names or tidy-evaluation semantics. Standard/raw/delimited
strings remain entire strings: R has no implicit string interpolation. Complex,
integer/hex and real literals are numbers; logical, missing, null and infinity /
NaN literal nodes are keywords. Roxygen and ordinary comments are comments.

The grammar hides semicolon statement separators as extras. Offline coverage
admits only literal semicolons and a leading BOM in otherwise whitespace parser
gaps, assigning punctuation to these original bytes; every other nonspace gap
fails closed. Unicode boundaries and original CRLF/CR text remain unchanged.
Parser error/missing nodes, permissive incomplete calls/namespace/extraction,
unknown tokens, overlap and coverage gaps are rejected. Grammar acceptance is
not compiler validity or support for every R release, R Markdown or R documentation.
