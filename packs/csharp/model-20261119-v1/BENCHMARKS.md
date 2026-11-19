# C# baseline evaluation

Exact-span F1 requires original UTF-16 token start, end and semantic role to match.
Role macro F1 averages represented roles; declaration-modifier results are separate.
These scores use the documented source-local grammar contract, not a Roslyn type
checker. Natural code, focus tasks and visible probes are distinct evidence.

| Evidence                          | Documents | Exact-span F1 | Role macro F1 |
| --------------------------------- | --------: | ------------: | ------------: |
| Adaptive natural validation (MPS) |        24 |        95.76% |        83.14% |
| Adaptive focus validation (MPS)   |       152 |        97.94% |        96.38% |
| First natural test (MPS)          |        24 |        94.64% |        87.58% |
| First focus test (MPS)            |       152 |        89.04% |        78.46% |

Selected complete checkpoint: `artifacts/csharp/context512-mixed-20261109-01/candidates/epoch-0003.pt`. Mixed revision epoch 3
maximized natural fixed-validation role macro F1
(0.8005). That selection used validation and
real displayed code before first test inspection; no training followed the first
test. Archived test files are known for future comparisons, not another unseen test.

The first experiment ran 3 initial + 6 continuation epochs. Its best complete
candidate was epoch 6. A new mixed-data experiment started with explicit weights-only
transfer from that full candidate and ran 3 epochs at learning rate 0.0001. The
original experiment, optimizer/RNG state, old datasets and all candidates remain.
No inference-only `.pt` or ONNX export was used for initialization/resumption.

## Data and source protocol

Final immutable snapshot: `fae08849d8cfc1961e902a8dc2d7be70aa3a98b6c7e4404efc5bcd8f8f6406a1`.
1,811 accepted input records, 0 exact duplicate records merged,
2 cross-family copies excluded; 1,809 records retained.
All 275 original source/task family assignments were preserved and extended to
287 before the mixed revision trained. Exact, lexical and identifier-normalized
copies are excluded before grouped windows, including BOM-only variants.
Golden and Playground are outside every collection root.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          177 |       1280 |    2655 |
| validation |           24 |        152 |     318 |
| test       |           24 |        152 |     294 |

The bounded original source capture contains 130 .NET runtime 9.0 files at
`9d5a6a9aa463d6d10b0b0ba6d5982cc82f363dc3`, 70 Newtonsoft.Json 13.0.3 files at
`0a2e291c0d9c0c7675d445703e51750363a549ef`, and 35 Dapper 2.1.66 files at
`bd4f75b512de3e00f2c2631d5309961a1ecfea23`. Complete original licenses, source
bytes and revision/blob/hash locks stay external. Eight captured files outside
the pinned grammar were quarantined; their exact source/error records are retained.
They were not relabeled with an approximate fallback to inflate coverage.

Focused data contains 1,200 original grammar tasks and 384 mixed tasks with varied
indentation/string contexts. Renamed/literal/layout variants keep one task family.
Pretraining source/Gold/prepared revisions remain immutable, including explicit
handling of original UTF-8 BOM and a supported basic-list-pattern task revision.

Tree-sitter 0.25.10 and C# grammar 0.23.5 are pinned to official source blobs. The
host's existing Apple Clang builds only their offline parse library into ignored
project cache. No .NET SDK, Mono, CLR, Roslyn, global Python/Node package, NuGet
resolution or project environment was installed. Collected C# code is never
compiled, loaded, reflected on or executed. Compiler/source/library identities are
stored with Gold; no parser is shipped in the consumer package.

## Visible source review

Ten natural validation files spanning source lengths and upstreams were inspected
alongside eight independently authored display examples and 22 marked Golden probes.
These are development diagnostics, not a second corpus test score.

| Separately authored display probe | Exact-span F1 |
| --------------------------------- | ------------: |
| AsyncStream.cs                    |       100.00% |
| Collections.cs                    |        97.62% |
| GenericStore.cs                   |        97.75% |
| Hello.cs                          |       100.00% |
| Options.cs                        |        94.34% |
| Queries.cs                        |        96.10% |
| Records.cs                        |        83.12% |
| StringTemplates.cs                |       100.00% |

6 of 22 small Golden probes are exact including declaration modifiers. Others
retain explicit role/range/flag differences in `reports/golden.json`. This strict
small-probe count is not the percentage of correct files in the corpus and does
not hide failures behind the pooled score. Complex property patterns/record names
remain weaker than ordinary classes, async, generic and string examples; see
KNOWN_ISSUES.md with the raw reports.

## Architecture and bounded budget

Four Transformer layers, width 128, four heads, FF512, 512-byte context,
894,743 parameters. The first C# experiment initialized from the full Java
checkpoint `artifacts/java/context512-mixed-20261109-01/candidates/epoch-0001.pt`.
A smoke save/reload/inference check preceded 3 + 6 ordinary epochs and 3 lower-rate
mixed epochs. Epochs took roughly 14–20 seconds on MPS under `caffeinate -i`.
This remains the same small architecture, without a long training campaign.

Float32 native inference and ONNX exports preserve the selected weights. They are
not resumable checkpoints. Datasets, parser source/build cache and full training
runs remain external/ignored. All prior language models are preserved unchanged.
