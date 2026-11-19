# BAT / CMD baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic type to match.
Role macro F1 averages represented roles; modifier-aware results are separate in JSON.
Natural source and original focused tasks are reported separately.

| Evidence                          | Documents | Exact-span F1 | Role macro F1 |
| --------------------------------- | --------: | ------------: | ------------: |
| Adaptive natural validation (CPU) |         4 |        76.59% |        61.85% |
| Adaptive focus validation (CPU)   |        96 |        90.92% |        91.35% |
| First natural test (MPS)          |         3 |        74.29% |        71.78% |
| First focus test (MPS)            |       234 |        96.27% |        95.38% |

Selected full checkpoint: `artifacts/bat/context512-fragments-20261108-01/candidates/epoch-0003.pt`.
The run's best natural fixed-validation role macro F1 is 0.6261.
Candidate review included adaptive real-source inference, Golden and rendered
examples before the first independent test. Test results were never used for
further tuning; future evaluation on this archived test is a known-test comparison.
Fixed validation and adaptive inference use different cuts, without Gold at runtime.

## Data and lineage

Snapshot: `7789e75e064c7b9dc8c0ab737c69415926e0e9133863e0a16e2d0bcde7980e06`.
1,403 input records, 95 exact duplicates
merged within families and 0 cross-family copies excluded;
1,308 records / 1,308 distinct source texts retained.
Source/task families split before windows with exact, lexical and normalized-copy
auditing. Frozen assignments are committed; Golden and Playground are excluded.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |            4 |        967 |     997 |
| validation |            4 |         96 |     103 |
| test       |            3 |        234 |     238 |

12 independently marked visible Golden probes remain development evidence;
7 are fully exact including modifiers. They are not an independent corpus score.

| Separately authored display probe | Exact-span F1 |
| --------------------------------- | ------------: |
| arguments.bat                     |        92.63% |
| build.bat                         |        90.91% |
| functions.cmd                     |        84.44% |
| records.cmd                       |        84.51% |

Display probes are development diagnostics, not held-out test evidence.

Small source-family holdouts from bounded upstream captures do not certify every
project, dialect, module or execution environment. Read KNOWN_ISSUES.md alongside
the raw reports. Original sources, complete licenses, locks and Gold remain in
the external dataset; all resumable checkpoints remain under artifacts.

The bounded natural capture contains eleven original batch scripts from VS Code
1.106.0 at a pinned official revision, with complete MIT license and Git blob /
SHA-256 locks. Related launchers and integration variants stay together. Original
curriculum contains 960 records; the later 432-record short-label revision shares
original task family IDs and all 36 frozen assignments. No Golden/display source
is copied and no native Windows environment is installed or executed.

The original offline lexer was bounded to one physical line for FOR /F quote
matching after a real upstream nested-quote input exposed excessive backtracking.
The original full script is preserved and a regression covers later-line recovery.
All 1,403 source records label successfully in the selected revision.

A full PowerShell training checkpoint initialized the same four-layer, width-128,
four-head, FF512, 512-byte-context model (893,582 parameters). Smoke reload preceded
3 measured + 48 continuation epochs, then 24 smaller-batch refinement epochs.
The short-label data revision transferred a full BAT checkpoint into a fresh run,
configured for 20 epochs and early-stopped after 13; its frozen best is epoch 3.
Typical epochs took below one second in the first run and about one second in
refinement, under `caffeinate -i`. Inference exports never initialize training.

The natural test consists of `scripts/test.bat`, `listprocesses.bat` and
`scripts/test-documentation.bat` from three held-out families. Natural validation
has four related code launchers in one family; these are deliberately reported
as small, uneven source evidence rather than independent projects. The selected
baseline prioritizes usable variables, loops and ordinary label calls, retaining
conditional-tail and quote-boundary failures instead of further score chasing.
