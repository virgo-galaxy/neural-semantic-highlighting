# JSON / JSONC source-local semantic contract

One JSON-family model has two explicit document kinds/profiles: strict `json`
(.json) and comment-enabled `jsonc` (.jsonc). File extensions do not override an
explicit kind. Common named .json configuration files containing comments must
be requested as jsonc. No automatic source detection or schema lookup occurs.

Strict JSON follows RFC 8259 syntax: double-quoted property names/strings, decimal
numbers, true/false/null, objects and arrays. JSONC adds // and /* */ comments and
explicitly enables trailing commas for common configuration use. This permissive
trailing-comma policy is not a universal JSONC requirement. Single quotes, bare
keys, hex numbers, Infinity/NaN, hash comments and other JSON5 forms are excluded.

Original quoted object keys are property spans, including quotes and escapes.
Other quoted literals are strings; signed/fraction/exponent numbers each remain
one number span. True, false and null are keywords. Braces, brackets, colons and
commas are punctuation. Comments are comments without their line-ending bytes.
No declaration modifiers, variable/function roles, JSON Schema resolution or
special spelling rules apply. Duplicate/empty/numeric-looking and **proto** keys
remain ordinary data. Strings containing code, URLs, comment markers, templates
or encoded JSON remain whole strings; their contents never execute or compose.

Offline Gold uses pinned Microsoft jsonc-parser 3.3.1 in ignored project cache
with the existing Node runtime. Fault-tolerant parse results are accepted only
when the error list and scanner errors are empty. Scanner/AST original UTF-16
ranges distinguish keys from values without reserializing input or converting
numbers. Every nonspace source character must be covered, without overlap.
Only JSON ASCII whitespace is admitted in gaps; original CRLF, Unicode, escapes
and large numeric spellings remain unchanged. BOM and malformed/incomplete source
fail closed. Empty/whitespace editor input and JSONC comment-only input are
supported display inputs, not claims of strict JSON document validity.

This parser is development supervision only, never a frontend/runtime dependency.
Browser inference uses selected neural ONNX weights with the same original-byte
cursor and UTF-16 protocol as other packs. No parser/regex/spelling repair masks
prediction errors. Context is 512 UTF-8 bytes; long literal/comment boundaries,
key/value roles and nested structures remain measured model limitations.

References: https://www.rfc-editor.org/rfc/rfc8259.html,
https://jsonc.org/ and https://github.com/microsoft/node-jsonc-parser.
