# AWK baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic type to match.
Macro F1 averages represented roles; modifier-aware scoring also requires flags.
Natural upstream programs and original focused grammar remain separate.

| Adaptive evidence       | Documents | Exact-span F1 | Role macro F1 |
| ----------------------- | --------: | ------------: | ------------: |
| Natural validation, CPU |         6 |        98.55% |        98.15% |
| Focus validation, CPU   |        60 |        96.83% |        91.76% |
| First natural test, MPS |         6 |        96.89% |        91.66% |
| First focus test, MPS   |        56 |        99.87% |        99.91% |

The frozen epoch-15 candidate maximizes natural fixed-validation role macro F1
(0.9372), followed by actual adaptive real-source, Golden and rendered review.
Fixed and adaptive cuts differ; no evaluation feeds Gold boundaries to inference.
The first test was read once after candidate freezing, not used for further
training. Future evaluation on it is a known-test comparison. Six files from one
upstream distribution are not six independent projects.

## Data and lineage

The bounded corpus captures 73 complete GNU AWK 5.4.1 example/library programs,
with official archive SHA-256, original source bytes and complete GPL text.
No programs, includes, extensions, network clients or build steps are executed.
The offline adapter extends pinned Pygments 2.21.0 for GNU directives, typed
regex, coprocess `|&` and regex context across physical line continuations.
Original Unicode/CRLF coordinates are validated. Earlier quarantined labels
remain preserved in their original snapshot; the selected revision labels all
73 upstream programs and 600 original focused examples successfully.

Sixty exact duplicate records merge within frozen source/task families. The
remaining 613 distinct texts have no cross-family copies after exact, lexical
and normalized-shape auditing. Families split before windows; old assignments
never move across folds. Golden and Playground are outside collection.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| Train      |           61 |        424 |     621 |
| Validation |            6 |         60 |      78 |
| Test       |            6 |         56 |      74 |

Training transfers a complete Perl checkpoint, copying compatible backbone and
common label rows into the same four-layer, 128-wide, four-head Transformer with
FF512 and 512-byte context. A smoke reload check precedes 3 measured epochs and
12 continuation epochs, typically 2–3 seconds each, under `caffeinate -i`.
Selected inference exports never serve as training checkpoints.

Fourteen independently marked visible Golden probes are excluded from collection;
8 are fully exact including modifiers. Four separately authored display
examples were rendered with the actual HTML renderer/theme: counts, normalize
and report have entirely exact roles/ranges. The GNU file-phase example retains
a split regex span with correct visible regex roles. Raw predictions and real
validation errors remain in the selected bundle.
