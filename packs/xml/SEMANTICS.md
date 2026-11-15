# XML / SVG source-local semantic contract

One `xml` pack, two preserved document kinds/profiles: `xml` and `svg`. SVG is
XML source, not rendered graphics or a second model. Both kinds share the exact
same eight roles, closing modifier and 512-byte Transformer weights. The
Playground and public API retain separate names and separately measured results.
See [XML 1.0](https://www.w3.org/TR/xml/), [XML namespaces](https://www.w3.org/TR/xml-names/)
and [Expat](https://docs.python.org/3.12/library/pyexpat.html).

| Source                                           | Role          | Original boundaries                                              |
| ------------------------------------------------ | ------------- | ---------------------------------------------------------------- |
| XML declaration, processing instruction, doctype | `keyword`     | Whole declaration, including delimiters/internal subset          |
| Comment                                          | `comment`     | Whole original `<!-- ... -->`                                    |
| Start/end element name                           | `tag`         | Case-sensitive qualified name; end names have `closing`          |
| Delimiters and attribute equals                  | `punctuation` | `<`, `</`, `>`, `/>`, `=` separately                             |
| Attribute / namespace declaration name           | `attribute`   | Whole qualified name; no namespace rewriting                     |
| Attribute value                                  | `string`      | Whole original single/double quotes, including references        |
| CDATA                                            | `string`      | Whole original `<![CDATA[...]]>`; no reference expansion         |
| Non-whitespace character-data run                | `text`        | Whole run including its adjacent whitespace, split at references |
| Character reference in text                      | `entity`      | Original five predefined or numeric reference spelling           |

Whitespace-only character data and whitespace between markup tokens remain
outside spans. BOM is punctuation. Every non-whitespace Gold character is covered
with sorted nonoverlapping UTF-16 ranges; Unicode, CRLF, case and source escapes
are never rewritten. Independent hand-marked Golden is not teacher-generated.

Offline original-range scanning is cross-checked against existing CPython Expat
raw tag/ordered-attribute events. A second namespace-aware parse validates prefix
bindings and duplicate expanded attributes. Malformed, partial or mismatched
markup, illegal names/references, unquoted attributes, parser disagreement and
unknown gaps fail closed. Empty/whitespace/comment-only editor input is accepted;
training otherwise uses well-formed documents, not HTML's tolerant recovery rules.

UTF-8 XML 1.0 is the bounded profile. Default attributes, custom general/parameter
entity declarations/expansion, XML 1.1, non-UTF-8 encodings and DTD/schema validation
are outside scope. External DTD identifiers are opaque text, never fetched;
parameter-entity parsing is disabled, entity declarations are rejected before
expansion, and no schema, stylesheet, script or configuration is executed.
Common XML vocabularies (configuration, feeds, namespaces, XSD/XSLT source and
property lists) share lexical roles; highlighting does not prove their validity.

SVG covers common shapes, paths, groups/transforms, symbols/use, defs, gradients,
masks/clip paths, filters, text/accessibility and animation attributes. Path data,
paint values, CSS/class/Tailwind/style/event attributes remain whole strings.
Style/script text remains text, or one string when wrapped in CDATA. Embedded
CSS/JS, SVG path command parsing, template dialects, binary SVGZ and automatic
language detection are not claimed in this baseline. Namespace URIs and hrefs
never cause resource loading.

Runtime is pure neural ONNX in the existing browser Worker, with no Expat, source
parser, spelling lookup or regex repair. Its output on incomplete editor text is
still approximate highlighting, not a validator. Long attribute/CDATA/comment
boundaries across 512 bytes and closing modifiers must be measured independently
of convenient overall scores. Preserve all old data, full artifacts checkpoints
and formal models; inference bundles are never continuation checkpoints.
