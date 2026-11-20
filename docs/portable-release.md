# Portable release metadata

Current repository files and distributed models must not embed a developer's
home directory or macOS temporary-directory identity. Repository paths are
relative; external data references use
`~/Datasets/neural-semantic-highlighting/<model-name>/`. A reader expands `~`
when accessing an explicitly chosen local dataset.

The selected models are not retrained or quantized for this cleanup. Native
PyTorch artifact metadata is rewritten through the serializer and reloaded;
all tensor bytes are compared. ONNX exporter debug properties and doc strings
are removed through protobuf, with all non-annotation fields verified unchanged.
CPU ONNX Runtime predictions before/after cleanup must match exactly at 1, 2, 7,
31, 64, 127, 511 and 512 input bytes for every rewritten ONNX artifact.

[Verification](portable-release-verification.json) records the 65 rewritten
native artifacts and 66 browser artifacts, including current selected bundles
and archived bundles that remain in the current checkout. Two native artifacts
already contained no local paths and retain their original files. Metrics and
selection results are retained. File-integrity links, browser descriptors and
model hashes are updated for the sanitized containers. Historical training
checkpoint identities continue to identify the original training evidence.
An archived TypeScript export retains its historical source digest rather than
claiming it was generated from today's selected native model.

## Check current files

```bash
pnpm check:portable
# Equivalent, with no exporter dependencies needed:
python3 -m training.sanitize_release
```

The check includes tracked files and new, non-ignored project files. It excludes
Git internals, local virtual environments, installed dependencies, generated
build output and training caches. These local-only directories may legitimately
contain working machine paths; they are not distribution artifacts. The project
check does not claim to audit every possible secret or inspect Git history.

## Maintenance

The native and ONNX exporters sanitize future release metadata automatically.
To clean an older current checkout, use the existing Python/PyTorch and browser
export tools, with an unused backup directory outside the repository:

```bash
PYTHONPATH=artifacts/tools/browser-export:. \
  .venv/bin/python -m training.sanitize_release --apply \
  --backup-dir /tmp/nsh-release-originals \
  --report docs/portable-release-verification.json
```

Original changed files are retained in that external backup. The command does
not change external datasets, resumable checkpoints under `artifacts`, or Git
history. It refuses a backup directory inside the repository. Backups are local
originals and are not release assets.

Afterward regenerate descriptors with `training/browser/generate_descriptors.py`,
format them, rebuild browser packages and verify browser/native comparisons.
This keeps the hashes used by the browser's integrity check synchronized.
