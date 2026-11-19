# Svelte baseline evaluation

Exact-span F1 requires original UTF-16 start, end and role to match. Role macro
F1 averages represented roles. Closing modifiers are evaluated separately.
**Base template/region accuracy is distinct from composed JS/TS/style accuracy.**
Natural upstream components, original focus tasks and visible development examples
are separate evidence. Do not use the combined score as natural-code accuracy.

| Base template / region evidence | Documents | Exact-span F1 | Role macro F1 |
| ------------------------------- | --------: | ------------: | ------------: |
| Natural validation              |        10 |        92.06% |        71.50% |
| Focus validation                |        96 |        98.50% |        95.48% |
| First natural test              |         9 |        88.47% |        58.49% |
| First focus test                |        92 |        97.37% |        91.38% |

The full test stream combines 101 documents
at 95.49%, but the natural holdout is only
9 files and scores 88.47%.
It is a small, bounded baseline and does not certify every real application.

## Selection and experiments

Frozen full checkpoint: `artifacts/svelte/context512-boundaries-20261110-01/candidates/epoch-0007.pt`, epoch 7 of the boundary run.
Its fixed natural validation role macro F1 is 0.7410.
Later epochs were retained in the run but did not improve that selection metric.
Real validation source, 20 independent Golden and eight authored components were
reviewed before the first adaptive test. No training followed that test. These
results are now known evidence for any future revision.

The model has **894,614 parameters**, 512 UTF-8 bytes of context, width 128,
four attention heads and four layers. Initialization uses the complete Vue
`artifacts/vue/context512-compact-20261108-01/best.pt` checkpoint (epoch 35), never
an inference artifact. A smoke check precedes 3 + 6 + 6 short initial epochs.
A separate boundary revision transfers the full initial epoch-15 checkpoint and
runs 6 + 3 short epochs, selecting epoch 7. Optimizers are fresh on transfer;
continuation retains full optimizer/RNG state. Per-epoch measured timings and
full initialization provenance are retained in `reports/experiments.json` and the
ignored runs; epochs typically took about 5–8 seconds on this MPS host.

The revision addresses visible fragmented directive boundaries, wrong script/style
regions and template-like text inside scripts. Attribute keys/equals/whole values
now use one consistent convention. It adds 480 original tasks across 20 intact
families. All 140 old assignments are preserved and extended to 160 before training.

## Source and split audit

Snapshot: `15b208c34781c4ef96959a4f9e3b44d0874c0efc1b24e14914f5f835b1a7223e`. 1,344 input records,
215 exact duplicate records merged, 93
cross-family copy documents excluded, 1,036 retained documents.
Exact, lexical and normalized copies are audited before windowing; exclusion
rules are unchanged. Data and complete licenses remain external under
`~/Datasets/neural-semantic-highlighting/svelte`.

Natural capture pins 64 components each from Bits UI (legacy), LayerChart and
Flowbite Svelte (modern); exact commits, Git blobs and licenses are in
`dataset/upstreams.json` and external source locks. The original 672 focused tasks
and 480 boundary tasks stay grouped by source family. All 1,344 captured records
passed offline Gold coverage; zero were quarantined in this bounded capture.
This does not imply arbitrary source will parse. Unknown/malformed syntax fails closed.
Golden and Playground sources are excluded from collection.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |           77 |        752 |    1743 |
| validation |           10 |         96 |     191 |
| test       |            9 |         92 |     186 |

## Visible composed component review

Gold uses the official Svelte parse-only bundle and independent existing TS/CSS
teachers. Runtime uses only model-predicted regions; no teacher cuts are passed to
inference. All eight authored components have supported child Gold (zero skipped).
Aggregate composed exact-span F1 is **97.53%**.
This is development evidence, not an unseen whole-component test.

| Component               | Composed exact-span F1 |
| ----------------------- | ---------------------: |
| async-content.svelte    |                100.00% |
| control-flow.svelte     |                 99.05% |
| counter.svelte          |                 95.35% |
| directives.svelte       |                 96.89% |
| legacy-component.svelte |                 97.01% |
| module-less.svelte      |                 96.84% |
| snippets.svelte         |                 98.25% |
| typed-scss.svelte       |                 96.77% |

The neural model exactly matches every span/role/modifier in 8/20 visible Golden
cases; the offline teacher independently passes all 20 marked cases. Ten natural
validation components were inspected directly; their base scores range from
83.15% to 100.00%.
Residual snippet/key bindings, entity/text boundaries, long script fragmentation
and JS/TS or style-language confusion remain in the recorded reports and
[known issues](KNOWN_ISSUES.md). Rendering preserves source text independently of
role accuracy. Browser/native parity is a consistency check, not a quality claim.
