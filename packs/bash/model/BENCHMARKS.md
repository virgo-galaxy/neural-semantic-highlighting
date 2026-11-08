# Shell baseline evaluation

Exact spans match UTF-16 start, end and role. Modifier-aware F1 additionally
requires the complete modifier set. Macro F1 averages roles with Gold or predicted
support. Natural source and original focused grammar remain separate; zero or low
support does not establish broad accuracy.

| Profile | Natural validation F1 | Natural test docs | Natural test F1 | Natural test macro F1 | Focus test F1 |
| ------- | --------------------: | ----------------: | --------------: | --------------------: | ------------: |
| POSIX   |                77.86% |                 1 |          89.33% |                89.56% |        99.88% |
| Bash    |                89.53% |                 5 |          93.28% |                92.38% |        99.94% |
| Zsh     |                87.03% |                 1 |          71.55% |                73.74% |        99.94% |
| Csh     |                81.95% |                 4 |          87.43% |                90.08% |        95.90% |

All reported rows use actual predicted-adaptive MPS inference with no Gold cursor
cuts or runtime lexer/parser. Pooled natural test F1/macro are 84.20%/85.17%;
focused test F1/macro are 98.99%/95.61%. Each profile has 80 focused test documents.
Do not present the large focused sample as independent real-project coverage.
The lone POSIX/Zsh natural test files especially limit generalization claims.

The frozen candidate was selected using mean per-profile natural fixed-validation
role macro F1 (0.855868), followed by real-source, independent Golden and display
inspection. Training fixed windows are reassembled before whole-document scoring;
those cuts do not consult Gold. Runtime uses predicted adaptive cuts. The first
independent test took about 2.04 seconds inside the evaluator, not a steady-state
latency benchmark. No subsequent tuning used that test.

## Data and revisions

The bounded natural corpus captures 88 original files from GNU Bash 5.3, Zsh 5.9
and Tcsh 6.24.16, with pinned revisions/archive hashes and original source/license
bytes. It does not install or execute those shells. Original curriculum, short
fragments, mixed tasks, loop-entry fragments and collection tasks add 3,136 files.
Pygments 2.21.0 is pinned as an isolated offline-only lexer asset; a source-local
adapter defines command, binding and expansion roles. It is not an execution
validator or a complete shell interpreter.

All 3,224 captured documents receive coordinate/coverage-valid Gold. After 241
exact duplicate records are merged within profiles, 2,983 profile-addressed
documents remain, representing 2,956 distinct source texts. Related profile
aliases remain in one source family; they are not independent programs. Exact,
lexical and identifier-normalized cross-family copies are checked before windows.
No retained document crosses its frozen family split.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| Train      |           65 |      2,065 |   2,557 |
| Validation |           12 |        510 |     575 |
| Test       |           11 |        320 |     375 |

Existing family assignments never move when adding data. Coverage gates require
loops, conditionals and source-leading loops in at least three training families
per profile, plus arrays for Bash/Zsh/Csh. This prevents holding out an entire
common syntax along with a synthetic task. Csh's single large natural training
completion program remains intact; focused tasks provide additional basic syntax
coverage, without being counted as independent natural projects.

The four preserved experiments completed 27, 12, 16 and 20 epochs with explicit
weights-only transfer for new snapshots/protocols. Actual epochs were roughly
6–10 seconds. The initial run included a 3-epoch measurement before continuation.
Smoke checks verified full checkpoint reload and pure-neural document inference.
The final selected epoch is 16 of the coverage run, not a claim that all those
epochs belong to one unchanged dataset or optimizer state.

Earlier reports used different string canonicalization or coarser Csh quoted
variable labels. They are retained as experiments and are not directly comparable
to this final protocol. Shared quoted syntax now has common variable/string
ranges, while source profiles retain their own corpus identities.

Twelve independently marked, visible Golden probes are excluded from collection.
Nine are entirely exact including modifiers. Remaining development failures are
preserved in `reports/golden-probes.json`. Four separately authored display
snippets were rendered with the real HTML renderer and base theme before testing;
those are development checks, not a corpus benchmark.

```sh
make evaluate-bash BASH_CHECKPOINT=artifacts/bash/context512-coverage-20261108-01/candidates/epoch-0016.pt
make challenge-bash BASH_CHECKPOINT=artifacts/bash/context512-coverage-20261108-01/candidates/epoch-0016.pt
```

Full checkpoint/snapshot/code hashes and the first independent test are archived
with the inference bundle. Future measurements on this same test are known-test
comparisons, not new unseen evidence.
