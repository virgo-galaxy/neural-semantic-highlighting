import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const dist = new URL("../dist/", import.meta.url);
mkdirSync(dist, { recursive: true });
for (const name of ["ort-wasm-simd-threaded.wasm", "ort-wasm-simd-threaded.mjs"]) {
  copyFileSync(require.resolve(`onnxruntime-web/${name}`), new URL(name, dist));
}
copyFileSync(
  new URL("../vendor/ONNX-RUNTIME-LICENSE.txt", import.meta.url),
  new URL("ONNX-RUNTIME-LICENSE.txt", dist),
);
