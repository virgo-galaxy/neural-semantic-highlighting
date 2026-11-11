# YAML source-local semantic contract

One `yaml` document kind/profile covers .yaml and .yml configuration/source text.
Supervision uses the pinned yaml 2.9.1 Document/CST APIs with explicit YAML 1.2
Core scalar resolution. YAML version directives retain their source ranges, but
legacy 1.1-specific boolean/date interpretation is not promised. In particular,
GitHub Actions `on` keys and plain yes/no/on/off values are not legacy booleans.

Scalar mapping keys are properties (quoted keys keep their quotes). Plain values
use the composed Core scalar kind: numbers are numbers, boolean/null tokens are
keywords, other scalars are strings. Quoted values stay strings. Complex keys
keep nested collection syntax; scalar block-key bodies are properties. Implicit
empty null values create no invented source token. Duplicate keys remain visible
source data; no conversion to JavaScript objects or application-schema validation
occurs. Core timestamps and underscored numeric-looking values remain strings.

Mapping/sequence indicators, flow delimiters, document markers and block-scalar
headers (including chomping/indent indicators) are punctuation. A block body is
one original string range, including its indentation and final source line breaks,
without semantic folding/chomping or embedded Shell/JSON/template highlighting.
Header comments remain separate comments. Plain/quoted multiline scalars retain
whole original ranges. Comments exclude their following line-ending bytes.

Anchor tokens use label+declaration; aliases use label without expansion or name
resolution. Tags use decorator; unknown local/verbatim tags are colored without
loading custom resolvers. Directives use keyword. Cycles, merge-looking keys,
CloudFormation/CI interpolation and external references do not execute or expand.

Pinned official npm assets and their ISC license remain in ignored project cache,
verified by archive SHA-512/SHA-256 and per-file hashes. Existing Node supplies the
offline teacher; no SDK/global package is installed. Parser errors, warnings other
than unresolved custom tags, recovery tokens, unknown lexical tokens, overlap and
nonspace coverage gaps fail closed. BOM, Unicode and original CRLF are preserved
and offsets are original UTF-16. Empty/comment-only editor input is supported.

Frontend inference uses selected neural ONNX weights in the existing Worker,
without the offline parser, schema lookup, execution, source regex or spelling
repair. Context is 512 UTF-8 bytes. Learned key/value roles, block/quoted scalar
boundaries, tags, anchors and nested/multi-document context remain approximate.

References: https://yaml.org/spec/1.2.2/ and https://eemeli.org/yaml/.
