# Makefile semantic contract

One standalone model highlights common GNU Make source selected explicitly as
`makefile` (`make`, `mk`, `mak`, `gnumake` aliases). Examples include `Makefile`,
`makefile`, `GNUmakefile`, `.mk` and `.mak`; filenames do not execute or select a
build system. CMake, NMake, Automake input and complete BSD make are separate
unsupported dialects. This is source-local display supervision, not build
validation, dependency resolution, expansion or execution.

Original UTF-8 bytes, UTF-16 `[start,end)` spans, BOM, CRLF, tabs, whitespace,
case, quotes and Unicode are preserved. All non-whitespace source is covered
without overlaps. An independent pinned Tree-sitter Make 1.1.1 CST establishes
structure offline. Parser errors, controls and unsupported forms are quarantined.

- Plain rule targets are `label+declaration`, including special targets such as
  `.PHONY`. Plain prerequisites, patterns and paths are strings. Rule colons,
  double/grouped colons, static-pattern separators and inline-recipe semicolons
  are punctuation; the order-only pipe is operator. No target/path is resolved.
- Assignment/define names are `variable+declaration`; assignment signs are
  operators. Ordinary values are literal strings or standalone numeric atoms.
  Make quotes remain original literal data; they do not suppress Make comments.
- `$(NAME)`, `${NAME}`, single-character/automatic variables and substitution
  references are complete variable spans. Built-in Make function names are
  `function+default-library`, dollar introducers operators and delimiters/argument
  commas punctuation. Nested references keep their original ranges. Functions,
  including shell/eval/file, are never evaluated. Escaped dollars outside recipes
  remain literal strings; recipe `$$name` denotes a source-local shell variable.
- Include/export/override/private/undefine/vpath/conditional/define/endef directive
  words are keywords. Bare names in ifdef/ifndef/export lists are variables.
  No included file is opened, and both conditional branches remain source.
- `define` values are opaque original strings, including comments/newlines and
  recipe-looking content. Their eventual expansion language is not guessed.
- Outside references and define/recipe bodies, unescaped `#` begins a Make
  comment even inside quote characters. Escaped hashes are literal; hashes
  within Make references/functions remain literal. Continued Make comments
  retain their entire original range. Make backslash-newlines are punctuation.
- Recipes and explicit shell-assignment/`$(shell ...)` command regions reuse the
  existing pinned offline Bash teacher. Recipe `@`, `-`, `+` prefixes are
  operators. True Make expansions are classified separately, never confused
  with shell substitutions. A checked character projection masks only Make
  expansions and collapses escaped dollars for lexical supervision, then maps
  every span back to original text. No projected source is executed or emitted.
  An explicit foreign/computed SHELL conservatively leaves shell bodies opaque
  throughout that source document. No complete platform/shell support is claimed.
- Literal unconditional one-ASCII-character `.RECIPEPREFIX` changes and an empty
  reset are accepted through a checked original-coordinate parse projection;
  custom prefix characters are punctuation. Conditional/computed prefix state
  is rejected. A virtual final newline is parser/lexer-only and never enters
  source or output. Make and recipe continuations retain separate contexts.

Only variable/label/function may carry declaration, and only function may carry
`default-library`. The existing source-blind decoder coalesces only touching
string spans with equal modifiers; no whitespace gap is bridged, role corrected
or source inspected. Inference loads one neural model, with no Make executable,
Tree-sitter, Bash lexer, parser, regex, fallback or spelling repair.

The pinned grammar has limits (including newer `:::=` assignments and some
computed/nested define or unusual recipe forms). Literal prefix projection is
bounded; no dynamic Make evaluation is attempted. `.ONESHELL` here-documents,
long bodies and distant target/variable context remain especially difficult.
Golden and visible displays never enter collection roots. Natural family splits
are frozen before labeling/training, reviewed validation and visible probes
precede model freeze, and the first independent adaptive test is never used for
further training. Tool/source/license hashes, immutable datasets, checkpoints,
original rejected files and all earlier model/data history remain preserved.

References: [GNU Make source contents](https://www.gnu.org/software/make/manual/html_node/Makefile-Contents.html),
[rule syntax](https://www.gnu.org/software/make/manual/html_node/Rule-Syntax.html),
[special variables](https://www.gnu.org/software/make/manual/html_node/Special-Variables.html),
[pinned grammar](https://github.com/tree-sitter-grammars/tree-sitter-make/tree/v1.1.1).
