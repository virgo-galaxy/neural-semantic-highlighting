import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import type { HighlightRequest, PackManifest, SemanticPack } from "@nsh/core";
import { createCompositeHtmlPack } from "@nsh/core/composition/html";
import { createCompositeVuePack } from "@nsh/core/composition/vue";
import { createLocalProcessPack, type LocalProcessPack } from "@nsh/local";

const root = process.cwd();
const ids = [
  "typescript",
  "go",
  "css",
  "html",
  "vue",
  "python",
  "bash",
  "perl",
  "awk",
  "sql",
  "powershell",
  "bat",
  "assembly",
  "java",
  "csharp",
];
const manifests = ids.map(
  (id) => JSON.parse(readFileSync(`packs/${id}/manifest.json`, "utf8")) as PackManifest,
);
const models = new Map<string, LocalProcessPack>();
const packs = new Map<string, SemanticPack>();
function getPack(kind: string): SemanticPack {
  const manifest = manifests.find((item) => item.documentKinds.some((entry) => entry.id === kind));
  if (!manifest) throw new Error(`Unsupported reference kind: ${kind}`);
  const cached = packs.get(manifest.id);
  if (cached) return cached;
  const base = createLocalProcessPack({
    manifest,
    command: resolve(root, ".venv/bin/python"),
    args: ["-m", "training.browser.reference_provider", "--pack", manifest.id],
    cwd: root,
    env: { PYTHONPATH: resolve(root, "artifacts/tools/browser-export") + ":" + root },
  });
  models.set(manifest.id, base);
  const highlightEmbedded = (request: HighlightRequest) =>
    getPack(request.documentKind).highlight(request);
  const pack =
    manifest.id === "html"
      ? createCompositeHtmlPack({ base, highlightEmbedded })
      : manifest.id === "vue"
        ? createCompositeVuePack({ base, highlightEmbedded })
        : base;
  packs.set(manifest.id, pack);
  return pack;
}
const suffixes = manifests
  .flatMap((manifest) =>
    manifest.documentKinds.flatMap((kind) =>
      kind.extensions.map((extension) => ({ extension, kind: kind.id })),
    ),
  )
  .sort((a, b) => b.extension.length - a.extension.length);
const cases = [];
const folder = resolve(root, "apps/playground/src/views/highlighter/examples");
for (const entry of readdirSync(folder, { withFileTypes: true }).filter((entry) =>
  entry.isDirectory(),
)) {
  for (const filename of readdirSync(resolve(folder, entry.name))) {
    const source = readFileSync(resolve(folder, entry.name, filename), "utf8");
    const kind = suffixes.find((item) => filename.endsWith(item.extension))?.kind;
    if (!kind) throw new Error(`Unknown example suffix: ${filename}`);
    const result = await getPack(kind).highlight({ source, documentKind: kind });
    cases.push({ filename: entry.name + "/" + filename, source, documentKind: kind, result });
  }
  await Promise.all([...models.values()].map((model) => model.close()));
  models.clear();
  packs.clear();
}
for (const source of [
  "",
  "\r\n",
  'const title = "星空 🌌";\r\nconsole.log(title);\r\n',
  'const message = "🌌";\n'.repeat(90) + "export const end = 42;\n",
]) {
  cases.push({
    filename: "edge/" + cases.length + ".ts",
    source,
    documentKind: "typescript",
    result: await getPack("typescript").highlight({ source, documentKind: "typescript" }),
  });
}
await Promise.all([...models.values()].map((model) => model.close()));
writeFileSync(
  "artifacts/browser/reference.json",
  JSON.stringify({ reference: "selected PyTorch CPU + existing composition", cases }, null, 2) +
    "\n",
);
console.log(cases.length, "native-reference cases");
