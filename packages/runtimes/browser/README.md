# @nsh/browser

Private low-level browser adapter implementing the `SemanticPack` contract.
Applications normally use `@nsh/highlighter` instead.

One reusable module Worker loads selected float32 ONNX models on demand, verifies
SHA-256 integrity, and runs ONNX Runtime Web 1.31.1 with one WASM CPU thread. Model
windows use original UTF-8 bytes and predicted adaptive cursor cuts; decoded spans
use original UTF-16 offsets. No source parser, language SDK or Python dependency
is included. Close the runtime to release its worker, sessions and pending work.

The build includes the WASM/MJS assets and upstream ONNX Runtime MIT notice.
Inference requires HTTPS or localhost, module Workers, Web Crypto and WebAssembly
SIMD. No cross-origin isolation is required. Other execution providers and old
browser fallbacks are not implemented.
