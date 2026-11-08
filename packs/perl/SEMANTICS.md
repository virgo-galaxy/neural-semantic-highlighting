# Perl semantic contract

One `perl` document kind covers Perl 5 scripts/modules/tests. Raku is a separate
language. Offline Gold uses the host PPI 1.270 source parser, never `perl -c`,
`do`, `require` or execution of input code. PPI reads source as a document; the
worker's error-catching block does not evaluate the input program. Pure neural
inference imports neither PPI nor the offline teacher.

Comments, POD, data/end sections use `comment`; quoted/quote-like words and Here
Documents use whole `string` regions, without interpreting interpolation. Regex
match/substitution/transliteration/compiled-regex tokens use whole `regexp`.
Here Document introducers and physical body/terminator ranges are separate, with
original punctuation between them. Queued/indented documents use original lines.
Operators, structural punctuation, numbers and reserved words have direct roles.

Symbols and magic variables use `variable`; visible lexical/global declarations
add `declaration`. Named subs use `function+declaration`; locally visible sub
references use `function`. PPI method calls use `method`; modules following
`package`/`use`/`require`/`no` use `namespace`. Bare hash keys use `property`,
recognized builtin calls use `function+default-library`, unknown call-like words
use `function`, and other barewords use `string`. This is source-local display,
not import resolution or execution semantics. Prototypes/signatures are currently
opaque `parameter` regions rather than individual argument bindings. Attributes
use `property` and labels use `label+declaration`.

Ranges use original UTF-16 offsets, including CRLF, tabs and non-BMP Unicode.
An LF view required by PPI maps every boundary back to original characters; stored
source is unchanged. Split Unicode sigil/name tokens are joined offline. Complete
non-whitespace coverage, no overlap and original token bytes are checked. Unknown
or mismatched tokens are quarantined. PPI is not a full language interpreter;
new/experimental syntax and deep context are bounded coverage.

The decoder uses predicted boundaries/roles only. Modifier-role masks remove
impossible combinations but do not inspect spelling or repair valid-looking
wrong predictions. Golden and Playground remain outside collection. Families and
normalized copies split before windows; natural/focus evidence stays separate.
