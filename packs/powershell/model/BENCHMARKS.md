# PowerShell baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic type to match.
Role macro F1 averages represented roles; modifier-aware results are separate in JSON.
Natural source and original focused tasks are reported separately.

| Evidence                          | Documents | Exact-span F1 | Role macro F1 |
| --------------------------------- | --------: | ------------: | ------------: |
| Adaptive natural validation (CPU) |         5 |        82.69% |        79.51% |
| Adaptive focus validation (CPU)   |        86 |        90.79% |        81.48% |
| First natural test (MPS)          |         3 |        90.67% |        86.80% |
| First focus test (MPS)            |        80 |        94.65% |        83.63% |

Selected full checkpoint: `artifacts/powershell/context512-20261108-01/candidates/epoch-0026.pt`.
The run's best natural fixed-validation role macro F1 is 0.8009.
Candidate review included adaptive real-source inference, Golden and rendered
examples before the first independent test. Test results were never used for
further tuning; future evaluation on this archived test is a known-test comparison.
Fixed validation and adaptive inference use different cuts, without Gold at runtime.

## Data and lineage

Snapshot: `d2aebc575f1aa407c2b5d9460f91ea099a638c12c116dc40ff2173b5259286d1`.
1,094 input records, 160 exact duplicates
merged within families and 104 cross-family copies excluded;
830 records / 830 distinct source texts retained.
Source/task families split before windows with exact, lexical and normalized-copy
auditing. Frozen assignments are committed; Golden and Playground are excluded.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |           30 |        626 |     786 |
| validation |            5 |         86 |     105 |
| test       |            3 |         80 |      99 |

12 independently marked visible Golden probes remain development evidence;
5 are fully exact including modifiers. They are not an independent corpus score.

| Separately authored display probe | Exact-span F1 |
| --------------------------------- | ------------: |
| functions.ps1                     |        94.59% |
| here-strings.ps1                  |        88.89% |
| pipeline.ps1                      |        94.12% |
| records.ps1                       |       100.00% |

Display probes are development diagnostics, not held-out test evidence.

Small source-family holdouts from bounded upstream captures do not certify every
project, dialect, module or execution environment. Read KNOWN_ISSUES.md alongside
the raw reports. Original sources, complete licenses, locks and Gold remain in
the external dataset; all resumable checkpoints remain under artifacts.

The natural capture contains 38 scripts, modules and module-data files from
PowerShell 7.6.0 at a pinned official Git revision, with complete original MIT
license and Git blob / SHA-256 source locks. Directory/module families are kept
together. The 1,056 original tasks vary source positions, CRLF and Here-String
bodies without borrowing Golden/display source. All 58 source/task groups were
frozen before training; old rejected/source revisions remain preserved.

A complete SQL training checkpoint initialized the same four-layer, width-128,
four-head, FF512, 512-byte-context network (893,969 parameters). A one-epoch smoke
reload check preceded 3 measured epochs and 24 continuation epochs, usually about
2 seconds each after warmup under `caffeinate -i`. No inference export, native
Windows, pwsh or .NET environment was used. Basic display is usable with controlled
string/name limits; long embedded module bodies remain weaker as documented.

The natural test's three retained files are `PSSysLog.psd1`, `Xml.psm1` and
`setReleaseTag.ps1`, each from a held-out source family. They include one module
data file, one module and one script; this is a small mixed-source baseline.
