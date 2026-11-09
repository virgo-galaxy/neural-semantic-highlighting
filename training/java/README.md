# Java training

Reuse the established shared four-layer byte Transformer and pack commands. Data
lives under `~/Datasets/neural-semantic-highlighting/java`; full resumable runs live
under ignored `artifacts/java`. Preserve every existing source revision, run and
selected model. The JDK is an offline Gold dependency, never a frontend dependency.

The pinned local OpenJDK 22.0.1 scans and parses original Java source with annotation
processing disabled. No dependencies, Maven/Gradle project or collected source is
built or executed. `NSH_JAVA_HOME` selects that exact JDK on another machine.

```sh
make test-labeling-java
make test-training-data-shared
make dataset-java
make train-java-smoke JAVA_DEVICE=mps JAVA_RUN=artifacts/java/smoke-new
caffeinate -i make train-java JAVA_DEVICE=mps JAVA_EPOCHS=3 \
  JAVA_RUN=artifacts/java/new-run \
  JAVA_INIT_FROM=artifacts/go/context512-20260913-074648-569634/best.pt
caffeinate -i make continue-java JAVA_DEVICE=mps JAVA_EPOCHS=3 \
  JAVA_CHECKPOINT=artifacts/java/new-run/last.pt
```

Freeze the first prepared source-family assignments in `dataset/split-groups.json`
before training. A source/teacher change creates a new immutable dataset/run;
initialization is explicit weights-only transfer from a compatible full checkpoint.
Only resume `last.pt` in its original run. Never initialize/resume from
`packs/*/model/model.pt`. Keep the current PyTorch environment intact.

Start with smoke and three measured epochs. Use actual epoch timings and natural
validation failures to choose bounded continuations. `status.json`, `run.json`,
`epochs/*.json`, `best.pt` and `last.pt` expose progress and preserve optimizer/RNG.
Inspect independent Golden and real displayed Java before freezing a candidate.
Only then inspect its held-out adaptive test once, document limits, and export.

```sh
make evaluate-java JAVA_CHECKPOINT=artifacts/java/new-run/best.pt
make challenge-java JAVA_CHECKPOINT=artifacts/java/new-run/best.pt
make evaluate-java JAVA_CHECKPOINT=artifacts/java/new-run/frozen.pt JAVA_EVAL_SPLIT=test
make export-java-model JAVA_CHECKPOINT=artifacts/java/new-run/frozen.pt JAVA_TEST_REPORT=path/to/test.json
```

Browser export uses the same float32 weights through the existing
[ONNX workflow](../browser/README.md), with head-level and rendered-span parity.
