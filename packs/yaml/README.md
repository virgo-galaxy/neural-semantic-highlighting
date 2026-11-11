# YAML pack

One YAML entry for .yaml/.yml source, including common Kubernetes, Compose,
Prometheus and CI configurations. Mappings/sequences, plain/quoted/block scalars,
anchors/aliases, tags, directives and multiple documents use source-local roles.
No application schema, template renderer, YAML loader execution or alias expansion
is implied. Frontend/Playground use the existing browser Worker without Python.

See [semantics](SEMANTICS.md), [dataset](dataset/README.md), [Golden](fixtures/README.md),
[training](../../training/yaml/README.md) and [consumer usage](../../README.md).
Keep the established external data paths, immutable revisions, full training
checkpoints and short English stage commits. Preserve prior data and models.
