# Shell Here Document follow-up

Exact-span F1 requires UTF-16 start, end and role to match. Modifier-aware scores
also require the complete modifier set. Natural and original focused source stay
separate; small sample counts do not establish broad dialect/version coverage.

| Profile | Natural validation F1 | Natural test docs | Known natural test F1 | Known natural test macro F1 | Focus test F1 |
| ------- | --------------------: | ----------------: | --------------------: | --------------------------: | ------------: |
| POSIX   |                79.20% |                 1 |                88.32% |                      90.83% |        98.63% |
| Bash    |                90.37% |                 5 |                93.20% |                      92.04% |        98.57% |
| Zsh     |                86.35% |                 1 |                73.76% |                      74.94% |        98.66% |
| Csh     |                83.46% |                 4 |                89.29% |                      90.96% |        95.84% |

Actual predicted-adaptive MPS inference gives pooled natural F1
84.78% and focused F1
98.19%. The original natural/focus test
was already read for the preceding model. These rows are known-test comparisons,
not new unseen evidence. The original 88 real source files and their family
assignments are unchanged; Gold changed only for one natural training file.

## New Here Document evidence

Eight original mixed task families add 576 source files; twelve short structural
families add 864. Delimiter quoting, `<<-`, code-like/variable-first bodies,
function-keyword forms and post-delimiter redirections appear across families.
Profiles share related families before windows and normalized-copy checks.
Sources, scripts and prior snapshots are preserved, including unused revisions.
No full corpus recrawl or architecture change was needed.

The selected candidate was frozen before inspecting three new held-out task
families: query-input, number-lines and repeat-input. Their 216 profile-addressed
documents score 96.76% exact-span F1, versus 58.84% for the previous model on the
same new tasks. These are original focused tasks, not 216 independent real
projects. The 144 Here Document validation tasks score 86.99%, with harder
post-delimiter redirections. See `reports/heredoc-first-holdout.json` and
`reports/heredoc-validation.json` for the separate evidence.

## Selection, data and checks

The two preserved follow-up runs completed 20 and 24 epochs, about 11 seconds per
epoch after warmup, using `caffeinate -i` and explicit weights-only transfer from
full checkpoints. Epoch 20 of the second run maximizes mean per-profile natural
fixed-validation role macro F1 (0.8675), followed by adaptive real-code, Golden
and actual Playground review. Runtime cursors never consult Gold boundaries.

All 4,664 captured files receive coordinate-valid Gold. Duplicate merging retains
4,423 profile-addressed documents representing 3,524 distinct source texts; no
cross-family copies remain in this prepared snapshot. Identical profile aliases
are not independent programs. Existing holdouts never move into training.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| Train      |           65 |      3,145 |   3,637 |
| Validation |           12 |        654 |     719 |
| Test       |           11 |        536 |     591 |

Nineteen independently marked Golden cases remain visible development probes,
excluded from collection. 8 are entirely exact including modifiers. Failures
include short-snippet string-end overruns and existing name/modifier errors;
Golden is not a held-out corpus benchmark. Six actual Playground examples were
checked and rendered through the existing HTML/theme path. The combined Here
Document example gets ordinary, literal and tab-stripped body roles correct,
with a measured two-newline overrun on its first string span.

The previous formal bundle and complete first-test report remain preserved under
`../model-20261108-e16`. Current checkpoint, dataset and code hashes accompany the
new export. Natural Csh training still consists of one intact large completion
program; Zsh and POSIX natural tests each contain only one file.
