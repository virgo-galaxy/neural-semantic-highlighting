# Assembly baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic type to match.
Role macro F1 averages represented roles; modifier-aware results are separate in JSON.
Natural source and original focused tasks are reported separately.

| Evidence                          | Documents | Exact-span F1 | Role macro F1 |
| --------------------------------- | --------: | ------------: | ------------: |
| Adaptive natural validation (CPU) |        10 |        95.83% |        89.87% |
| Adaptive focus validation (CPU)   |       288 |        95.82% |        75.19% |
| First natural test (MPS)          |         5 |        98.63% |        87.36% |
| First focus test (MPS)            |       192 |        98.03% |        98.11% |

Selected full checkpoint: `artifacts/assembly/context512-20261109-01/candidates/epoch-0015.pt`.
The run's best natural fixed-validation role macro F1 is 0.9175.
Candidate review included adaptive real-source inference, Golden and rendered
examples before the first independent test. Test results were never used for
further tuning; future evaluation on this archived test is a known-test comparison.
Fixed validation and adaptive inference use different cuts, without Gold at runtime.

## Data and lineage

Snapshot: `0d83136d5c67ccefdefd924c4b249ead15df98a9b600936f14ec46644fa529d5`.
2,657 input records, 0 exact duplicates
merged within families and 192 cross-family copies excluded;
2,465 records / 2,429 distinct source texts retained.
Source/task families split before windows with exact, lexical and normalized-copy
auditing. Frozen assignments are committed; Golden and Playground are excluded.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |           50 |       1920 |    2154 |
| validation |           10 |        288 |     318 |
| test       |            5 |        192 |     221 |

20 independently marked visible Golden probes remain development evidence;
6 are fully exact including modifiers. They are not an independent corpus score.

| Separately authored display probe | Exact-span F1 |
| --------------------------------- | ------------: |
| aarch64.S                         |       100.00% |
| att.s                             |        94.87% |
| intel.s                           |        96.43% |
| macros.asm                        |        89.29% |
| masm.asm                          |        94.87% |
| nasm.asm                          |        96.08% |

Display probes are development diagnostics, not held-out test evidence.

Small source-family holdouts from bounded upstream captures do not certify every
project, dialect, module or execution environment. Read KNOWN_ISSUES.md alongside
the raw reports. Original sources, complete licenses, locks and Gold remain in
the external dataset; all resumable checkpoints remain under artifacts.

## Profile evidence

| First-test profile | Natural docs | Natural F1 | Focus docs | Focus F1 |
| ------------------ | -----------: | ---------: | ---------: | -------: |
| nasm               |            2 |     99.01% |         48 |   96.94% |
| gas                |            1 |     98.49% |         48 |   97.47% |
| masm               |            1 |     97.45% |         48 |   96.60% |
| aarch64            |            1 |     99.57% |         48 |  100.00% |

The selected checkpoint maximizes mean per-profile natural fixed-validation role
macro F1 (0.9175), rather than the pooled document score. Adaptive CPU validation
uses different predicted cuts. The six separately authored displayed examples
were checked with the actual renderer/theme before the first independent MPS test.
The GNU Intel-mode example is development evidence; the natural GNU profile is
AT&T source. Vector/definition modifiers are scored separately from role ranges.

## Source and training protocol

The bounded original-byte capture contains 16 NASM files from FFmpeg 7.1.1,
16 MASM files from .NET runtime 10.0 and 20 GNU x86-64 / 13 AArch64 files from
musl 1.2.5. Git revisions/blobs and the official musl archive/member SHA-256 values
are pinned. Full original source licenses, SHA-256 locks and source bytes remain
external. No assembler, emulator, Windows/x86 environment, build or source code
was installed or executed. Offline Gold uses the pinned display grammar only.

The 2,592 original profile-addressed tasks share related family IDs across syntax
styles. Their second revision keeps MASM END after data/conditional blocks; the
first source/Gold/prepared revision is preserved. All 71 families were frozen
before training. Related templates and cross-architecture routines stay together.
Shared raw text under profile aliases is coverage, not independent source evidence.
Golden and Playground sources are excluded from capture.

Architecture is unchanged: four Transformer layers, width 128, four heads, FF512,
512-byte context and 893,711 parameters. Initialization uses the complete Go
checkpoint `artifacts/go/context512-20260913-074648-569634/best.pt`.
A one-epoch smoke reload/inference check preceded 3 measured and 16 continuation
epochs, typically 3–4 seconds each under `caffeinate -i`. Full optimizer/RNG/data
checkpoints remain in `artifacts/assembly/context512-20261109-01`; the selected
float32 artifact is inference-only and preserves the frozen candidate weights.

The first natural test's five files are a small, uneven holdout; per-profile
counts must accompany its pooled 98.63% F1. In particular, high natural-source F1
does not remove the measured macro, Unicode, comment and modifier failures in
KNOWN_ISSUES.md. No tuning followed inspection of this first test.
