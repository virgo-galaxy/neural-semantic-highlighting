# Dotenv source-local semantic contract

One `dotenv` kind/profile covers common .env/.env.* configuration text. Aliases
belong to the frontend API, not separate trained profiles. The teacher scans
original ranges and independently cross-checks every last-wins key/value against
official pinned dotenv 18.0.10 `parse()`, using existing Node only. No config(),
process.loadEnvFile(), expansion, environment injection or configuration execution
is used. Parser assets and BSD-2-Clause license stay in ignored verified cache.
See [dotenv reference](https://github.com/motdotla/dotenv) and
[Node environment-file rules](https://nodejs.org/api/environment_variables.html).

Names use the common Node-compatible ASCII form [A-Za-z_][A-Za-z0-9_]*. Each whole
name is variable+declaration; case and duplicate declarations stay visible.
Optional lowercase export is keyword, when followed by a valid assignment.
The = delimiter is punctuation. Root/plain assignments and empty values are
supported. Colon assignments, digit-leading/dotted/dashed names, valueless lines
and application-specific extra syntaxes are outside this bounded profile.

All nonempty values are strings, including numbers, booleans and JSON-looking
text. Bare values retain one original range, trimming only external ASCII spaces
and tabs. Single/double/backtick quoted values retain their complete original
quotes, source escapes and multiline whitespace. A multiline value remains one
string span, including embedded # lines, assignment-looking text and line breaks.
The parser's normalized/decoded values are used only for independent validation;
returned source, ranges and highlighted text are never rewritten.

Hash begins a full-line or inline comment outside quotes, even without preceding
space. Quoted hashes are ordinary data. Semicolons are value text. References
such as $PORT, ${HOST}, default-looking references and command-looking values
stay opaque strings. No expansion, command substitution, decryption, nested
language highlighting or application-schema checking is implied.

BOM is punctuation at original offset zero. Unicode and CRLF retain original
UTF-16 ranges. Empty/comment-only editor input is supported. Malformed or
unclosed quotes, text after a quoted value, invalid keys, bare CR/unsupported
control bytes, parser value/key disagreement, unknown source gaps and overlaps
fail closed. The reference parser can silently ignore malformed input; complete
independent source coverage prevents that from producing partial Gold. Parser
special names that do not survive a real own-key roundtrip are quarantined.

dotenv files have multiple platform-specific dialects; this is an explicit
common subset, not Shell or universal loader compatibility. Existing SDKs,
historical data/checkpoints and formal models are preserved. Frontend/Playground
inference runs selected neural float32 ONNX weights in the existing Worker,
without the offline parser, environment loading or regex/spelling repair.
Context is 512 original UTF-8 bytes; key/modifier, quote/comment and long/multiline
boundaries remain approximate. Example filenames such as hello.env are ordinary
raw display assets and are never loaded as the Playground's process environment.
