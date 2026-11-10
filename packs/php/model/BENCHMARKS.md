# PHP baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match.
Role macro F1 averages represented roles; declaration modifiers are separate.
The table measures **base PHP syntax plus opaque predicted HTML regions**, not
full composed PHP/HTML/JS/CSS accuracy. Source-local grammar labels do not perform
project type checking, PHP execution, dependency resolution or framework semantics.
Natural source, focus tasks and visible development probes are distinct evidence.

| Base PHP/region evidence | Documents | Exact-span F1 | Role macro F1 |
| ------------------------ | --------: | ------------: | ------------: |
| Natural validation       |        21 |        95.49% |        88.05% |
| Focus validation         |       165 |        92.72% |        68.95% |
| First natural test       |        21 |        94.05% |        89.27% |
| First focus test         |       144 |        93.85% |        80.47% |

Frozen complete checkpoint: `artifacts/php/context512-mixed-20261110-01/candidates/epoch-0001.pt`, epoch 1.
Within the final experiment, natural fixed-validation role macro F1
(0.9092) selects the candidate. Real validation source,
independent Golden and display/template probes were inspected before first adaptive
test. No training followed that test. Its data is now known evidence for future work.

## Source and split protocol

Final immutable snapshot: `981eba377acc9f6ebebf3f5815fbba8f70102ea5421fd180b2558ec156452b9e`.
1,835 input records; 14 exact duplicate records merged;
20 cross-family copy documents excluded; 1,801 retained.
Exact, lexical and normalized copies are audited before intact source/task-family
allocation and windowing. All 262 original family assignments are preserved and
extended to 274 before the mixed revision trains. Golden and Playground never
enter collection roots.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          165 |       1285 |    2548 |
| validation |           21 |        165 |     312 |
| test       |           21 |        144 |     291 |

Capture pins 65 Symfony HttpFoundation 7.2.6, 85 Laravel 12.8.1, 50 Monolog 3.9.0
and 30 Guzzle 7.9.3 source files. Exact commits and per-file Git blobs remain in
`upstreams.json`; original bytes, complete licenses and locks stay external.
Three captured Laravel Blade templates outside the PHP grammar are quarantined;
Blade support is not claimed. Invalid source never receives a fallback valid label.

Original focused data has 1,320 syntax/template tasks across 55 families. The
initial 53-family source revision is retained; template variants were made
structurally independent and extended before any training/frozen split. A final
288-task/12-family revision improves mixed assets, heredocs, properties and enums.
Its copy audit retains the same 20 natural cross-family exclusions and every prior
split assignment. All corpora, Gold, prepared versions and experiments remain.

## No PHP environment installation

No PHP interpreter, SDK, Composer, web server or global package is installed.
Pinned official Tree-sitter 0.25.10 / PHP grammar 0.24.1 sources build with the
already available native compiler into ignored project cache. Separate grammar
entry points handle tagged documents and tagless code without changing source.
Source/compiler/library identities accompany Gold. Captured PHP, includes,
autoloaders and applications never execute. Modern accepted PHP 8 syntax does
not certify every newer feature or framework DSL.

## Visible development review

Ten natural validation files across source lengths/upstreams, eight separately
authored display sources and manually marked Golden cases guide development.
Their visible scores are not another held-out test.

| Base PHP/region probe | Exact-span F1 |
| --------------------- | ------------: |
| closures.php          |        91.80% |
| collections.php       |        92.44% |
| embedded.phtml        |        55.56% |
| enums.php             |        95.74% |
| hello.php             |        97.37% |
| heredoc.php           |        90.91% |
| records.php           |        94.83% |
| template.phtml        |        93.94% |

Neural Golden matches every boundary, role and modifier exactly in 5/23
cases; the offline teacher separately passes all 23 marked cases. Full source,
missing/unexpected spans and modifier diagnostics remain in `reports/`.

## Composed template evidence

The existing HTML/JS/CSS models run only inside **PHP-predicted regions**.
No source tag scanner, runtime parser, execution or Gold cuts choose inference
regions. The independent offline diagnostic uses actual PHP/HTML/JS/CSS Gold
for the following two visible templates and preserves original child offsets.

| Visible full PHP/HTML/JS/CSS probe | Composed exact-span F1 |
| ---------------------------------- | ---------------------: |
| embedded.phtml                     |                 87.69% |
| template.phtml                     |                 95.50% |

These two development probes do not establish an unseen whole-template score.
Child Gold/source hashes, full expected/actual spans and scope are retained in
`reports/composed-templates.json`. Incorrect base regions and incomplete fragments
remain composition limits. PHP embedded in HTML attributes/JS strings, Blade/Twig
and arbitrary template languages are not certified.

## Training and runtime

Unchanged four-layer byte Transformer: 895,130 parameters, width 128,
four heads, FFN 512 and context 512 original UTF-8 bytes. First training starts
with weights-only transfer from the complete selected C++ checkpoint in
`artifacts/cpp`, using fresh optimizer/RNG state and PHP labels. Three initial plus
six continuation epochs select first-run epoch 9. The mixed-data experiment
initializes from that complete epoch-9 candidate and runs three epochs at learning
rate 0.0001. Timing, full optimizer/RNG state, code/data identity and invocation
records remain under `artifacts/php`. Inference-only `.pt`/ONNX are never used
for transfer or resumption.

Base adaptive inference uses predicted boundaries, original text and learned
weights only. Long code uses multiple windows; comments/literals/distant bindings
remain bounded-context limits. Browser composition fetches existing HTML/JS/CSS
weights lazily and requires no Python/PHP backend. Numerical export and actual
browser parity are separate consistency checks, not new accuracy measurements.
