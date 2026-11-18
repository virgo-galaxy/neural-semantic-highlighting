# GraphQL training

Use the shared four-layer width-128, four-head, FFN-512 byte Transformer with
512-byte context. Start from a compatible full `artifacts` training checkpoint;
never use `packs/*/model/model.pt` for training initialization or continuation.
Natural sources are fully presented each epoch and bounded original focus
windows rotate separately. Preserve old datasets, experiments and model bundles.

    make dataset-graphql
    make test-labeling-graphql
    caffeinate -i make train-graphql-smoke GRAPHQL_DEVICE=mps GRAPHQL_LOCAL_KERNEL=5 GRAPHQL_RUN=artifacts/graphql/smoke-20261119-01 GRAPHQL_INIT_FROM=artifacts/makefile/optimization-20261118/contexts-e10-balanced.pt
    caffeinate -i make train-graphql GRAPHQL_DEVICE=mps GRAPHQL_EPOCHS=3 GRAPHQL_LOCAL_KERNEL=5 GRAPHQL_RUN=artifacts/graphql/context512-20261119-01 GRAPHQL_INIT_FROM=artifacts/makefile/optimization-20261118/contexts-e10-balanced.pt
    caffeinate -i make continue-graphql GRAPHQL_DEVICE=mps GRAPHQL_EPOCHS=3 GRAPHQL_CHECKPOINT=artifacts/graphql/context512-20261119-01/last.pt

Record actual epoch time and inspect real natural validation and visible probes
at short stages. Freeze a complete candidate and validation-only decision before
first independent adaptive test. No training or decoder selection uses that test.
Keep focus, natural, visible and Golden scores separate. Export only with matching
held-out evidence and model README/BENCHMARKS/KNOWN_ISSUES. Verify native/ONNX,
full browser parity, independent private-tarball integration and repository checks.

    make evaluate-graphql GRAPHQL_CHECKPOINT=artifacts/graphql/RUN/candidates/SELECTED.pt
    make challenge-graphql GRAPHQL_CHECKPOINT=artifacts/graphql/RUN/candidates/SELECTED.pt
    make export-graphql-model GRAPHQL_CHECKPOINT=artifacts/graphql/RUN/candidates/SELECTED.pt GRAPHQL_TEST_REPORT=artifacts/graphql/test.json

Inference is standalone neural highlighting. The offline parser is absent from
browser/native runtime; no server, parser/regex fallback, SDK or source execution.
Short English stage commits are retained; publishing is separately authorized.
