# Diff/Patch line semantics

One standalone model highlights common unified and Git unified patch text.
`.diff` and `.patch` share canonical `diff`. Seven semantic roles describe complete
original physical lines, excluding LF or CRLF: addition, deletion, heading,
label, comment, text and punctuation. Original signs and all payload whitespace
remain present; UTF-8 source yields half-open UTF-16 offsets. BOM is punctuation.
The offline teacher supplies no modifiers.

`diff --git`, unified old/new file headers and Index headers are heading. Unified
`@@ -old[,count] +new[,count] @@` headers and their function suffix are label.
Inside a counted hunk, the entire `+` line is addition, `-` line deletion and
space-prefixed line text. A body line that looks like `---`, `+++`, `@@` or
`diff --git` retains its hunk-body role. No-newline markers, Git index/mode/
rename/copy/binary notices, binary payloads and recognized mail metadata are
comment. Mail descriptions and diff statistics are text. Headerless +/- editor
fragments are accepted separately without a complete-patch validity claim.

A checked original-coordinate range walker enforces hunk counts. Existing Git
independently parses complete source using `apply --numstat -z --no-index
--allow-empty`; it never applies a patch, loads source files or runs hooks/code.
Binary payloads stay opaque. Combined merge, normal/context and word-diff formats,
ANSI terminal color and complete mail/archive/patch applicability validation are
outside this baseline. Unsupported complete syntax is quarantined offline.

Runtime reads neural logits only. The existing decoder may coalesce touching
identical roles/modifiers to preserve long opaque lines; it never bridges gaps,
inspects prefixes, repairs counts or invokes Git/regex/parsers. Context remains
512 bytes. Very long lines, distant headers and unusual metadata can confuse
roles/boundaries. Code inside changed lines is opaque Diff content, not dispatched
to its original programming-language model. Marked Golden, visible displays,
natural validation and independent test evidence remain distinct.
