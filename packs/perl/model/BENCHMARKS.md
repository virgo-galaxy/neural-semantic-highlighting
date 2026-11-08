# Perl baseline evaluation

Exact-span F1 requires UTF-16 start, end and role to match. Macro F1 averages
represented roles; modifier-aware F1 additionally requires the modifier set.
Natural core modules and original focused programs remain separate.

| Evidence           | Documents | Exact-span F1 | Role macro F1 |
| ------------------ | --------: | ------------: | ------------: |
| Natural validation |         4 |        84.57% |        61.25% |
| Focus validation   |       124 |        94.60% |        91.61% |
| First natural test |         4 |        83.60% |        64.07% |
| First focus test   |       188 |        88.21% |        80.75% |

The final first test uses actual predicted-adaptive MPS inference, without Gold
cursor cuts or an inference parser. Validation review used the same adaptive
algorithm on CPU. Selection uses natural fixed-validation role macro F1 (0.6910),
then real-source/Golden/display review. Fixed and adaptive results differ. The
test was read once after freezing this candidate; future evaluation is a known
test comparison. Four core modules are not four independent real projects.

## Data and training

Forty original host Perl 5.34 core module files are copied with original bytes,
Perl Artistic/GPL texts, source hashes and complete capture locks. They are not
imported or compiled. PPI 1.270 source/binary provenance is frozen separately;
its LF coordinate view maps back to original CRLF, tabs and Unicode characters.
Native parsing does not execute `BEGIN` or other sample code.

Six hundred original grammar/mixed programs and a 640-fragment revision add
short positions, regex, declarations, functions, quotes, POD and Here Documents.
The latter crosses indentation, body openings and prefixes independently.
Earlier 400-fragment data and all snapshots/checkpoints remain preserved.
All 1,280 captured documents receive valid complete Gold. Twenty-four duplicate
records merge within families, retaining 1,256 distinct texts; no cross-family
copies remain. Related directory/task families split before windows and retain
their initial assignments. Golden and Playground are never collected.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| Train      |           32 |        904 |   1,566 |
| Validation |            4 |        124 |     204 |
| Test       |            4 |        188 |     268 |

The initial Go-full-checkpoint transfer completed 3 measured epochs, then a
bounded continuation stopped at epoch 21 after a validation plateau. Preserved
fragment runs completed 18 and 12 epochs, using explicit weights-only transfer
for changed data. Typical epochs take 9–10 seconds with `caffeinate -i`. The
architecture remains four 128-wide Transformer layers, four heads, FF512 and
512 UTF-8 bytes of context. No inference export was used for training.

Twelve independently marked Golden cases remain visible development probes;
5 are fully exact including modifiers. Most failures are a single
role/modifier or range error. Five separately authored Playground examples were
rendered through the real HTML/theme path. An additional combined Here Document
challenge is retained in `reports/display-challenges.json`, including its failure
on the second indented body's roles; it is not hidden by postprocessing.
