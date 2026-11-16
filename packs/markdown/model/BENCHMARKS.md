# Markdown optimization evaluation

The metric is unchanged: an exact match of original UTF-16 start, end and role.
No prose roles, whitespace rules or reference spans were removed. Modifiers are
reported separately. Base Markdown quality does not establish child-language
semantic accuracy or Markdown document rendering.

| Evidence                         | Documents | Exact-span F1 | Role macro F1 | F1 including modifiers |
| -------------------------------- | --------: | ------------: | ------------: | ---------------------: |
| Validation, real                 |        23 |        92.29% |        91.24% |                 91.86% |
| First new independent test, real |        20 |        95.10% |        93.80% |                 94.97% |
| Exposed v1 regression, real      |        14 |        95.99% |        93.74% |                 95.94% |
| All test, real                   |        34 |        95.44% |        93.89% |                 95.34% |
| Test, authored focus             |       120 |        99.64% |        99.53% |                 99.50% |

The **20-file first new independent test (95.10%)** is the
primary result. The 14 v1 files are exposed regression evidence, separately
reported: **77.24% → 95.99%** on the same original documents
and Gold. Combined/focus scores are not a substitute for real-source accuracy.

## Frozen data and selection

The same five Git-pinned public projects provide 272 captured original files.
One unsupported Liquid document remains quarantined. The bounded extension uses
existing clones/revisions and licenses; no repository rebuild or SDK installation
occurs. The natural splits are **200 / 23 / 34**; test contains 20 new independent
and 14 exposed legacy documents. Authored splits are **1464 / 144 / 120**.
The 192 new train-only multiline fence tasks have eight structural families and
never read Golden, displays or held-out source. Exact/structural copy auditing,
all old assignments, snapshots and captured bytes remain preserved.
The exact frozen source configuration is retained in `reports/sources.json`.

[Protocol](reports/optimization-protocol.json) reserves complete new families
before training. [Cohorts](reports/optimization-cohorts.json) keep legacy and fresh
metrics separate. Validation and all test records stay byte-for-byte unchanged
after the train-only fence extension. Prepared snapshot:
`55885990c801a91c3b328e1b00fb91668bd6eb4e83e8b0f62330391498754f26`; manifest hash `e1b2447a5d435c48089135f69a46461ac8fb2ceb400f04d059128cae2a360352`.

The matched three-epoch kernel-three residual does not improve the control and
is not selected. Nine real-source control epochs are followed by three short
fence-refinement epochs. Selected fence epoch three passes the seven-of-seven
visible region/info gate and has the higher adaptive validation score among
passing fence candidates. Control epoch nine has slightly higher validation but
still splits two visible bodies, so it is not selected. All three experiment
runs total **15 epochs / 519.3 seconds**; this includes the unselected
three-epoch architectural control. Earlier v1 training remains archived.

The backbone stays at **894,227 neural parameters**, four layers, width 128,
four heads, FFN 512, context **512 original UTF-8 bytes**. Full training checkpoint:
`artifacts/markdown/optimization-20261116/calibrated-fences-e3.pt`, SHA-256 `6b6d7d4447172dc9c7aeafebe4ee08b1b89d16b4685cbc8635410d3a8b264401`.
The joint BIO/role transition probabilities fit **natural training Gold only**;
one fixed 12-pair grid selects type/transition weights **0.5 / 0.5** on natural
validation (minimum F1 across fresh/legacy/all). Frozen calibration evidence is
[retained](reports/decoder-calibration.json). It uses neural logits and learned
transition scores; there is no runtime parser, regex, spelling repair or source
language guessing. Modifier policies and the semantic contract are unchanged.

[Selection](reports/selection.json) freezes the candidate before its first new
independent test. No training follows that test. Full optimizer/RNG checkpoints,
all trials and old formal models remain preserved. Native export binds the exact
checkpoint and calibrated decoder to the test report; browser export retains the
same parameters and requires numeric/full-document parity.

## Actual display and edge-case review

Eight unchanged displays aggregate **95.65%**;
`code.md` and `mixed.md` are exact at base-span level. All **7/7** expected
fence-body/info ranges match, versus 5/7 in v1. The Python opening import and
unknown-language opening paragraph are now included. This is visible development
evidence, separate from independent test accuracy. Ten actual natural validation
files were reviewed before freeze; their F1 ranges from
89.39% to
100.00%.

The unchanged 48 hand-marked Golden probes remain deliberately strict: **21/48**
whole cases match including modifiers; aggregate base-span F1 is
**74.48%**. Their rare syntax,
CRLF/frontmatter and nested modifier errors remain documented, not relabeled.
The offline teacher still passes all 48 marked cases and 14 unit tests.

Fresh independent embedded-code body F1 remains **78.57%** on
25 reference spans, despite the much stronger overall score;
composition cannot fix a wrong model-predicted body. Full per-role counts are in
[test metrics](reports/test-metrics.json). Browser/native parity proves consistent
inference, not semantic perfection. See [known issues](KNOWN_ISSUES.md).
