# YAML independent Golden

40 separately hand-marked cases cover keys/values, Core literal distinctions,
flow/block collections, quoted and multiline strings, block chomping/indentation,
header comments, anchors/aliases/merge-looking keys, opaque tags, directives,
complex keys, multi-document streams and original BOM/Unicode/CRLF ranges.
Fourteen focused tests also check cyclic/unresolved aliases without expansion,
block-key ranges and parser recovery rejection. Expectations are independent of
parser output. Teacher agreement, strict neural Golden agreement, visible displays
and real held-out accuracy remain separate. These files never enter training.
