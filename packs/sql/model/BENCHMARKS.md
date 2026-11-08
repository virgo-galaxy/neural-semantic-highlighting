# SQL baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic type to match.
Macro F1 averages represented roles; modifiers are reported separately in JSON.

| Evidence                          | Documents | Exact-span F1 | Role macro F1 |
| --------------------------------- | --------: | ------------: | ------------: |
| Adaptive natural validation (CPU) |         6 |        88.48% |        78.58% |
| Adaptive focus validation (CPU)   |       278 |        96.39% |        81.80% |
| First natural test (MPS)          |         7 |        88.41% |        76.08% |
| First focus test (MPS)            |       248 |        97.48% |        96.51% |

| First-test profile | Natural docs | Natural F1 | Focus docs | Focus F1 |
| ------------------ | -----------: | ---------: | ---------: | -------: |
| postgres           |            1 |     93.74% |        104 |   96.51% |
| mysql              |            2 |     78.62% |         48 |   99.92% |
| oracle             |            4 |     88.37% |         96 |   96.91% |

## Selection, data and measured scope

Selected checkpoint: `artifacts/sql/context512-literals-refine-20261108-01/candidates/epoch-0011.pt`.
It is the run's best mean per-profile natural fixed-validation role macro F1
(0.7225). Adaptive validation uses different predicted cuts and is reported above.
The candidate was frozen after actual query/routine, Golden and rendered review;
the independent test was read once afterwards and never used to tune this model.

The bounded source capture contains 58 original PostgreSQL 18 tutorial, MySQL
8.4 sys-schema and Oracle sample-schema scripts. Individual pinned revisions,
Git blobs, original licenses and SHA-256 locks remain with the external data.
Offline pinned lexer/local-role Gold never executes input or needs a database.
Original common/dialect tasks (1,680 profile-addressed records) and a later
960-record literal/cast supplement stay separate from natural-source scoring.
Shared text repeated under profiles is coverage, not independent source evidence.
All 88 family assignments are frozen before windows; 102 exact duplicate records
merge and four cross-family copies are excluded. Golden and display probes are
not collected. The retained data includes 1,756 distinct source texts.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| Train      |           41 |       1852 |    2220 |
| Validation |            6 |        278 |     363 |
| Test       |            7 |        248 |     328 |

Architecture: four layers, width 128, four heads, FF512, 512-byte context;
893,969 parameters. Full Go checkpoint transfer took 3 measured + 24 continuation
epochs, followed by full SQL weights-only transfer on the literal revision
(12 epochs, early stopped), then 12 lower-learning-rate refinement epochs.
Typical epochs took 5–7 seconds under `caffeinate -i`; all resumable runs remain.
There was no training from an inference export and no database environment install.

Four independently authored rendered display examples have F1 of 97.06% (query),
96.15% (MySQL), 80.00% (PostgreSQL), and 80.00% (Oracle). These are development
probes, not additional held-out tests. Eight of fourteen visible Golden probes
are fully exact including modifiers. Ordinary queries/routines are stronger;
mixed dollar/q-quote bodies and client commands retain measured boundary failures.
See KNOWN_ISSUES.md and raw reports; pooled results do not certify every dialect.
