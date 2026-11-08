# Vue benchmark

## Protocol

Exact spans match original UTF-16 start/end and semantic type; modifier-aware
scoring additionally matches the complete modifier set. Macro F1 averages roles
with any Gold/predicted support. Unsupported predicted roles score zero; missing
roles establish no accuracy. Report natural source and focus grammar separately.

Fixed-window training validation reassembles full documents without Gold cuts.
Selection averages natural macro F1 across Vue 2, Vue 3 and Vue 3.2. Independent
adaptive inference uses only predicted cuts. Actual composed evaluation sends only
neural Vue regions to the existing JS/TS/JSX/TSX and CSS/SCSS/Less models. It never
uses Gold cuts or parses source at runtime.

| Profile | Natural validation base / composed F1 | Natural test base / composed F1 |
| ------- | ------------------------------------: | ------------------------------: |
| Vue 2   |         97.72% / 97.57% (3 documents) |   97.48% / 96.37% (5 documents) |
| Vue 3   |         96.19% / 96.94% (3 documents) |   97.80% / 97.86% (4 documents) |
| Vue 3.2 |          93.22% / 96.83% (1 document) |    97.67% / 96.18% (1 document) |

Base natural test has 630 Gold spans; composed has 1,291 (Vue 2: 572, Vue 3: 654,
Vue 3.2: 65). No final validation/test document is excluded from composed Gold.
Typed exact-region natural test F1 is 67.86% (19 TP, 10 FP, 8 FN). There are nine
JS bodies, one TS body and 17 interpolations; no real test style/JSX/TSX/data bodies.
Styling and render-function integration therefore rely on separate focus/Golden
and demonstration evidence, plus existing child-model evaluation. They must not
be inferred from the natural test aggregate. Validation has only one CSS body.

JS/TS body classes can be confused while both select the same underlying code
model. Splitting regions or including markup is still a real failure, not a
harmless type rename. Typed character coverage and exact regions are reported
separately. Base/composed metrics are different scopes, not direct improvements.

The original family holdout has 96 focus test documents, base F1 95.18%, composed
97.01%. Visible independently authored Golden probes have six exact cases out
of nine; raw mismatches are preserved. Playground examples were authored outside
collection roots and are development observations, not a new independent test.

## Offline references and isolation

The base teacher uses pinned `vue-eslint-parser` and TypeScript parser locations.
The composed teacher reuses script/style labelers, with official TypeScript AST
punctuation leaves completing omitted operators such as `!` and `...`. JSX text
remains intentionally neutral. It never assigns guessed roles to arbitrary gaps.
Mustache wrappers are fixed and projected to original coordinates. Unsupported
reference syntax is explicitly counted; none is excluded in final reports.

Prepared snapshot:
`29c6af2a7842f582322911aab1b99f076f2704f6e73565e1d5cd452884d0b848`.
Manifest SHA-256:
`19dc1f859c3de80a7d4445ef62a92a664cd4f7b766c5bf089b9387b067eed5e5`.
The archived manifest/checksums and group map bind the exact split.

Sources reuse local Vite/TanStack files and selected official Vuex 3, Vuex 4 and
Vue-3.2-era Pinia components. Pinned commits/selections live in
`../dataset/git-sources.json`; only 44 official SFCs and three root license files
are fetched, with Git blob and SHA-256 checks. Existing local files bring the real
input count to 61. Curriculum v4 contributes 736 original grammar documents across
three profiles, mixing source order, compact/pretty layouts, short/long bodies,
typed setup, versioned directives and code languages. No source is executed.

All 797 inputs receive complete base Gold. There are 795 unique documents after
two exact duplicates merge; two unrelated cross-group shape copies are excluded.
Related version siblings share explicit directory-family identities before
splitting. The retained 793 documents split as follows:

| Split      | Natural documents / windows | Focus documents / windows |
| ---------- | --------------------------: | ------------------------: |
| Train      |                    40 / 168 |                 544 / 999 |
| Validation |                      7 / 16 |                  96 / 139 |
| Test       |                     10 / 17 |                  96 / 134 |

`../dataset/split-groups.json` freezes the first trained source-family assignments.
Every overlapping family keeps its original split across curriculum revisions;
previously inspected validation files cannot become test files. New experiments
start from the complete HTML checkpoint and preserve all earlier state. Class
weights count unique train labels; padding and UTF-8 continuation bytes are masked.
Every profile/stream retains independent groups, though actual natural sample
counts remain small. Synthetic repetition is never counted as new natural data.

## Reproduce

```bash
make evaluate-vue VUE_CHECKPOINT=artifacts/vue/context512-compact-20261108-01/best.pt VUE_DEVICE=mps
make evaluate-vue-composed VUE_CHECKPOINT=artifacts/vue/context512-compact-20261108-01/best.pt VUE_DEVICE=mps
make challenge-vue VUE_CHECKPOINT=artifacts/vue/context512-compact-20261108-01/best.pt VUE_DEVICE=cpu
```

Use the original full checkpoint and frozen external snapshot for checkpoint-bound
reports. Final base/composed test were each first run only after freezing this
candidate, on MPS. Archived validation/Golden use the explicitly recorded backend.
Reported evaluator times include setup and are not browser throughput claims.
Report hashes bind the source checkpoint; the inference-export hash is separate.
