import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { parseArgs } from "node:util";

const { values } = parseArgs({
  options: {
    destination: { type: "string", default: "artifacts/browser/models" },
    models: { type: "string" },
  },
});
const source = resolve("packages/models/dist/assets");
const destination = resolve(values.destination);
const catalog = JSON.parse(readFileSync(resolve(source, "manifest.json"), "utf8"));
if (catalog.format !== "nsh-model-assets-v1") throw new Error("Unsupported model asset catalog");
const selected = new Map();
function collect(id) {
  if (selected.has(id)) return;
  const model = catalog.models.find((entry) => entry.id === id);
  if (!model) throw new Error(`Unknown model ID: ${id}`);
  selected.set(id, model);
  for (const child of model.dependencies) collect(child);
}
for (const id of values.models === undefined
  ? catalog.models.map((entry) => entry.id)
  : values.models.split(","))
  collect(id.trim());
for (const model of selected.values()) {
  for (const [path, digest] of [
    [model.path, model.sha256],
    [model.metadata.path, model.metadata.sha256],
  ]) {
    const file = resolve(source, path);
    if (createHash("sha256").update(readFileSync(file)).digest("hex") !== digest)
      throw new Error(`Model asset integrity mismatch: ${path}`);
    const output = resolve(destination, path);
    mkdirSync(dirname(output), { recursive: true });
    copyFileSync(file, output);
  }
}
// Keep older content-addressed files in place so existing clients remain usable.
mkdirSync(destination, { recursive: true });
writeFileSync(
  resolve(destination, "manifest.json"),
  JSON.stringify({ format: catalog.format, models: [...selected.values()] }, null, 2) + "\n",
);
console.log(
  `Exported ${selected.size} models and their pinned metadata; existing revisions retained.`,
);
