# Markdown dataset

External data stays under `~/Datasets/neural-semantic-highlighting/markdown`.
116 original documents reuse existing public Ant Design, TanStack Query, Vite,
Redux Toolkit and TypeScript clones at their already cached Git revisions. Fixed
size/path-hash selection happens before parser/Golden/model review. Captures copy
verified original Git blobs and applicable root licenses into the new dataset;
clones, old corpora and experiments stay untouched. No new repository collection,
SDK, parser package or dependency installation is needed.

40 original structural families have 24 variants each (960 tasks). Related
heading/list/layout and fence variants stay together. Natural component/document
families group by project sections before exact/lexical/structural copy exclusion.
New prose/link/code roles normalize their literal payloads in the shared copy
audit, preserving prior-role behavior. Freeze retained families before training.
Golden and eight display probes never enter collection roots.

The November 17 optimization adds 156 bounded original documents from the same
pinned clones, without changing the teacher or semantic contract. All earlier
family assignments and immutable captures remain intact. After copy exclusion,
the real-source splits contain 200 training, 23 validation and 34 test documents.
The test split includes the 14 exposed v1 regressions and **20 new independent
documents** from entirely reserved families. They must be reported separately.
[optimization-protocol.json](optimization-protocol.json) fixes these families
before training; the 11 new validation documents may guide selection, the new
test cohort may not. Authored curriculum counts remain 1,272 / 144 / 120.

`make dataset-markdown-tools` fingerprints existing parse-only Prettier/remark/GFM,
entity-decoder and Node assets; all remain offline tools. Source, code fences,
HTML, templates, links and front matter never execute. Unknown AST extensions are
quarantined with originals retained. `make dataset-markdown` publishes immutable
corpus/Gold/prepared revisions. Review validation and visible probes before freeze
and the first adaptive held-out test; no training follows that test. Resume only
full artifacts checkpoints, never formal inference weights or browser exports.

A bounded 24-family/576-task mixed extension follows the first six epochs' real
validation review: wrapped English/CJK prose, consecutive inline code, nested
formatting, varied references/autolinks/images and longer metadata blocks.
All 92 earlier family assignments, original tasks, snapshots and experiments
remain preserved. Teacher semantics and copy-audit policy stay unchanged.
