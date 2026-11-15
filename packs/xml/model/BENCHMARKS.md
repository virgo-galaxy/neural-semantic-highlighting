# XML / SVG baseline evaluation

Exact-span F1 requires matching original UTF-16 start, end and role. Role macro F1
averages represented roles; closing modifiers are separate. This measures
independent XML/source-local Gold, not XML/SVG schema validity, stylesheet
execution, application correctness, rendering or every possible vocabulary.

| Evidence   | Profile | Stream  | Documents | Exact-span F1 | Role macro F1 |
| ---------- | ------- | ------- | --------: | ------------: | ------------: |
| Validation | xml     | natural |         6 |        95.54% |        60.33% |
| Validation | xml     | focus   |       144 |        99.24% |        96.85% |
| Validation | svg     | natural |         6 |       100.00% |       100.00% |
| Validation | svg     | focus   |       144 |        99.65% |        96.78% |
| First test | xml     | natural |         7 |        85.87% |        81.28% |
| First test | xml     | focus   |       144 |        99.29% |        96.98% |
| First test | svg     | natural |         6 |       100.00% |       100.00% |
| First test | svg     | focus   |       144 |        99.80% |        97.63% |

Natural test aggregate: **92.20%** across
13 real files. Focus and combined-corpus scores
must not be presented as real-code accuracy. Small family holdouts from bounded
captures do not certify an entire language ecosystem or dependency environment.

## Data and frozen selection

128 Git-pinned original files come from MSBuild, Now in Android, VS Code, Devicon.
Original root licenses/notices, Git blob hashes and source bytes remain preserved.
The original curriculum has 60 families / 2880 variants.
40 original tree families and a bounded 20-family mixed extension cover declarations, processing instructions, DTDs, multiline CDATA, escaped text and SVG attributes. One source ID/family key groups XML/SVG counterparts before splitting. An audit found and corrected kind-specific IDs in the six-epoch exploratory run; those weights are not used for final training or selection. All exploratory snapshots/checkpoints remain preserved. Natural holdouts remain fixed, and the final run starts from the complete HTML checkpoint. No model predictions or source contents inform the size/hash allocation of natural holdouts.
Golden, tests and displayed source never enter collection roots. Corpus/Gold /
prepared revisions remain immutable; exact and cross-family copies are audited
before windowing, and 105 source-family assignments are frozen before training.

Prepared snapshot: `8a7196c3f20c715d8db0471dde4f5ba83ad03fb75c64d5df83aa10c5f72de8b5`. 3008 Gold inputs,
7 exact duplicates merged,
37 cross-family copy documents excluded,
2964 retained. Final Gold accepts 3008 files and
quarantines 0; rejected originals remain retained, never rewritten.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |           61 |       2302 |    5262 |
| validation |           12 |        288 |     711 |
| test       |           13 |        288 |     689 |

Full candidate: `artifacts/xml/context512-refine-20261116-01/candidates/epoch-0003.pt`, epoch 3.
SHA-256: `796002fbb207a2258755f62bce864856d22799a2a7823d0e6863a1bdc2eacf12`. Fixed mean per-profile natural validation
role macro F1 (0.8370) selects within its run.
Review precedes freeze and the first adaptive test; no training follows that test.
Source, locks, licenses, every snapshot and full optimizer/RNG experiment remain
under ~/Datasets/neural-semantic-highlighting/xml and artifacts/xml, outside the
committed inference bundle.

## Environment and short training

Existing Python 3.12.2, PyTorch 2.14.0 and MPS train
**893,324 parameters**: four layers, width 128, four heads, FFN 512, and **512 original
UTF-8 bytes** of context. Smoke precedes short three-epoch phases, initialized from
the compatible full `artifacts/html/context512-fragments-20261108-01/best.pt`. All 15 non-smoke epochs, including six discarded exploratory epochs, take
135.6 seconds; exact invocations, resumptions and timings remain in
reports/experiments.json. Inference .pt/ONNX never initialize or resume training.

No language SDK/interpreter or global dependency is installed. Offline tooling:
Existing CPython 3.12 Expat raw-event and namespace-aware validation with binary/source hashes; no downloads, SDKs or packages. Fixed revisions, original licenses/blob hashes, compiler and binary
provenance are retained. Collected source/dependencies never execute. Grammar
acceptance is not compiler validity. Parser errors, original coverage and Unicode
boundary failures quarantine input. Original CRLF and Unicode text remain unchanged.

## Real and independently visible review

Sixteen authored displays aggregate **98.97%**.
Ten actual natural validation sources were inspected before freeze; F1 ranges
90.49%–100.00%.
These are visible development diagnostics, not additional unseen test evidence.
Long upstream diagnostic excerpts are bounded in committed reports.

| Display               | Exact-span F1 |
| --------------------- | ------------: |
| svg/accessible.svg    |       100.00% |
| svg/animation.svg     |       100.00% |
| svg/cdata.svg         |       100.00% |
| svg/filters.svg       |       100.00% |
| svg/gradients.svg     |       100.00% |
| svg/hello.svg         |       100.00% |
| svg/mask.svg          |       100.00% |
| svg/symbols.svg       |       100.00% |
| xml/catalog.xsl       |       100.00% |
| xml/cdata.xml         |        78.26% |
| xml/feed.xml          |        97.48% |
| xml/hello.xml         |       100.00% |
| xml/namespaces.xml    |       100.00% |
| xml/pom.xml           |       100.00% |
| xml/preferences.plist |        97.30% |
| xml/schema.xsd        |       100.00% |

The teacher passes 48 separately hand-marked Golden cases and
14 focused tests. Neural spans, roles and modifiers are entirely
exact in **37/48** Golden cases. All sixteen
examples pass existing Expat validation and complete original coverage; no SDK/compiler
execution, dependency compatibility or package API validity is claimed.

Natural XML test comment and string exact-span F1 are only 51.28% (15 reference comment spans) and 70.93% (69 string spans), so the aggregate must not hide difficult comment/quoted-content boundaries. The instruction-plus-nested-code CDATA display remains weak (xml/cdata.xml 78.26% exact-span F1): a processing instruction can split into keyword fragments, quoted markup inside CDATA can receive tag/text roles, and escaped closing-tag text can merge entity boundaries. Atom text/whitespace and public-doctype boundaries also remain approximate (feed.xml 97.48%, preferences.plist 97.30%). All eight authored SVG displays reach 100%, which is visible development evidence rather than unseen generalization. Long strings/comments/CDATA and closing modifiers across 512 bytes remain approximate. UTF-8 XML 1.0 is the bounded profile; no XML 1.1, custom entity expansion, DTD/schema validation, SVGZ, SVG path/CSS/JS parsing, template syntax, automatic detection or runtime parser/spelling repair is provided. No runtime parser, regular expression or source-spelling
repair masks prediction errors. Browser/native parity and original-text checks
establish consistent execution rather than perfect semantics. This is a bounded
usable baseline; tuning stops after its freeze and first test.
