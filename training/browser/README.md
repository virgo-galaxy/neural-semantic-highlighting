# Browser model export

The browser runtime uses float32 ONNX versions of the selected inference models.
No training, quantization or source grammar is introduced. Existing `.pt` files,
external datasets and training checkpoints are preserved.

`BrowserTransformer` expresses the same pre-norm attention/FFN operations with
exportable tensor operations and the original parameters. It accepts an unpadded
`[1, bytes]` int64 input, from 1 through 512 original UTF-8 bytes, and emits the
three original heads. Padding masks are unnecessary for these unpadded windows.

## Export tools

Use the existing Python/PyTorch training environment. The checked exports used
Python 3.12.2 and PyTorch 2.14.0. Install exporter dependencies into an isolated
local directory, not into the runtime or a frontend consumer:

```bash
.venv/bin/python -m pip install --target artifacts/tools/browser-export \
  --no-compile -r training/browser/requirements-export.txt
```

Export one selected model:

```bash
PYTHONPATH=artifacts/tools/browser-export:. \
  .venv/bin/python -m training.browser.export_model --pack typescript \
  --output artifacts/browser/typescript-candidate
```

The target must not already exist. Inspect the candidate and its verification
before replacing a formal export under `packs/<name>/browser/`. Run separate CLI
processes for separate packs: historical model modules use incompatible bare
imports. **This does not create a resumable training checkpoint.** Continue
training only from full checkpoints in `artifacts/`, as before.

Each export records original `.pt` and ONNX SHA-256 hashes, exporter/graph hashes,
schema, threshold and decoder policy. ONNX checker runs, followed by CPU ORT vs
selected PyTorch comparisons at 1, 2, 7, 31, 64, 127, 511 and 512 bytes. Every
head's maximum absolute error must be below `1e-4`.

Exported ONNX files omit PyTorch debug annotations and source stack traces.
Native release metadata uses repository-relative references and portable
`~/Datasets/neural-semantic-highlighting/<model-name>/` paths. Model tensors,
operators, labels and decoder settings are preserved.

Run `pnpm check:portable` before distributing the repository or packages. It scans
current repository files, including model bytes; it does not inspect Git history.
The maintenance command and verification are documented in
[portable release metadata](../../docs/portable-release.md).

After reviewing/promoting exports, regenerate browser descriptors and format them:

```bash
python3 training/browser/generate_descriptors.py
pnpm exec eslint packages/highlighter/src --fix
pnpm exec prettier --write packages/highlighter/src
pnpm build:packages
```

The build copies reviewed ONNX files into `@nsh/highlighter/dist/models`, and
copies the pinned ONNX Runtime WASM/MJS assets and its MIT notice into
`@nsh/browser/dist`. Consumer packages contain no Python or `.pt` artifacts.

## End-to-end parity

Generate native CPU references for every Playground example, plus empty input,
CRLF, Unicode and long multi-window source:

```bash
pnpm browser:reference
pnpm dev
```

Open this local harness, replacing `<checkout-path>` with the checkout's absolute path:

```text
http://127.0.0.1:3000/@fs/<checkout-path>/scripts/browser-check.html
```

It compares original UTF-16 spans, semantic types and modifiers exactly, including
HTML/Vue composition. The native reference process is a development oracle only;
the browser harness does not use it during inference. References stay under
ignored `artifacts/browser/`.

Also test local tarballs in an independent frontend, build that frontend, then
serve only its static output. This catches packaging and Worker/WASM/model asset
issues that linked workspace imports can hide. Current results and limits are in
[the browser runtime report](../../docs/browser-runtime.md).
