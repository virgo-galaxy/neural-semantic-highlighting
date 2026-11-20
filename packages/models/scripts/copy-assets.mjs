import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";

const root = new URL("../../../", import.meta.url);
const modelAssets = JSON.parse(
  readFileSync(new URL("../src/asset-catalog.json", import.meta.url), "utf8"),
);
const output = new URL("../dist/assets/", import.meta.url);
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
mkdirSync(output, { recursive: true });
for (const asset of modelAssets) {
  const folder = new URL(`v1/${asset.id}/`, output);
  mkdirSync(folder, { recursive: true });
  for (const [filename, destination, digest] of [
    ["model.onnx", asset.path, asset.sha256],
    ["model.json", asset.metadata.path, asset.metadata.sha256],
  ]) {
    const source = new URL(`packs/${asset.id}/browser/${filename}`, root);
    const bytes = readFileSync(source);
    if (hash(bytes) !== digest)
      throw new Error(`Regenerate browser descriptors: ${asset.id}/${filename}`);
    if (filename === "model.onnx" && bytes.length !== asset.bytes)
      throw new Error(`Model size mismatch: ${asset.id}`);
    copyFileSync(source, new URL(destination, output));
  }
}
writeFileSync(
  new URL("manifest.json", output),
  JSON.stringify({ format: "nsh-model-assets-v1", models: modelAssets }, null, 2) + "\n",
);
