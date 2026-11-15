# TOML source-local semantic contract

One `toml` kind covers TOML configuration source. The pinned independent
`toml-eslint-parser` 1.0.3 AST/token API uses explicit `tomlVersion: "1.1.0"`.
Common TOML 1.0 syntax and tested 1.1 additions share one profile. The upstream
parser still labels 1.1 support experimental; this pack does not certify every
specification edge case. Independent cases exercise multiline/trailing-comma
inline tables, new escape sequences and optional seconds against the published
[TOML 1.1 specification](https://toml.io/en/v1.1.0).

Table/array-table header key segments use namespace; ordinary assignment and
inline-table key segments use property. Quoted keys include original quotes;
dots and brackets remain separate punctuation. `=`, commas and braces are
punctuation. No declaration modifiers are assigned. Values use whole original
ranges: all four string forms use string, boolean literals use keyword, integers,
floats (including infinity/NaN) and all four date/time forms use number. Signs,
separators, fractions, timezone offsets, quotes, multiline whitespace and escape
sequences retain their original bytes. Quoted date/boolean-looking text remains
string. Embedded-looking Shell/JSON/markup stays opaque string data. Comments
include the # marker but exclude line endings. No interpolation is evaluated.

No project is compiled, dependencies installed or configuration commands executed.
No semantic object/date conversion is used for offsets or highlighted text.
The parser validates source and duplicate/redefined keys before producing Gold;
invalid syntax, unknown nodes/tokens, overlap and nonspace coverage gaps fail
closed. Empty/comment-only editor input is supported. BOM is rejected by the
pinned strict parser rather than silently stripped. Unicode/CRLF offsets remain
original UTF-16. Git originals and upstream licenses are preserved externally.

Parser and visitor-key dependency assets and MIT/Apache notices are pinned by
archive SHA512/SHA256 plus every extracted file hash under ignored project cache,
using existing Node only. They are offline training tools, never frontend runtime
dependencies. Browser inference uses the selected 512-byte neural ONNX model in
the existing Worker, without parser, source regex or spelling repair. Learned
header/key/value roles, long multiline strings and literal boundaries remain
approximate. `.toml` is the public extension; explicitly selected TOML lockfile
examples are supported without assigning every `.lock` file to this language.
