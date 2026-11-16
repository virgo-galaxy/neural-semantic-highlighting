/** Native references for independent Markdown-only and selected-child consumers. */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import { type HighlightRequest, normalizeLanguageId, type PackManifest } from "@nsh/core";
import { createCompositeMarkdownPack } from "@nsh/core/composition/markdown";
import { createLocalProcessPack } from "@nsh/local";

const root = process.cwd();
const models = new Map(
  ["markdown", "typescript", "json"].map((id) => {
    const manifest = JSON.parse(readFileSync(`packs/${id}/manifest.json`, "utf8")) as PackManifest;
    const pack = createLocalProcessPack({
      manifest,
      command: resolve(root, ".venv/bin/python"),
      args: ["-m", "training.browser.reference_provider", "--pack", id],
      cwd: root,
      env: { PYTHONPATH: resolve(root, "artifacts/tools/browser-export") + ":" + root },
    });
    return [id, pack] as const;
  }),
);
const cases = (
  JSON.parse(readFileSync("artifacts/browser/reference.json", "utf8")).cases as {
    filename: string;
    source: string;
    documentKind: string;
  }[]
).filter((x) => x.documentKind === "markdown");
if (cases.length !== 12) throw Error("Expected eight Markdown displays and four edge probes");
const reports: Record<string, unknown[]> = {};
try {
  for (const mode of ["only", "composed"]) {
    const selected = [...models].filter(([id]) => id === "markdown" || mode === "composed");
    const resolveLanguage = (name: string) => {
      const kind = normalizeLanguageId(name);
      return kind !== "markdown" &&
        selected.some(([, p]) => p.manifest.documentKinds.some((k) => k.id === kind))
        ? kind
        : undefined;
    };
    const highlightEmbedded = (request: HighlightRequest) => {
      const pack = selected.find(([, p]) =>
        p.manifest.documentKinds.some((k) => k.id === request.documentKind),
      )?.[1];
      if (!pack) throw Error("Unregistered child");
      return pack.highlight(request);
    };
    const pack = createCompositeMarkdownPack({
      base: models.get("markdown")!,
      resolveLanguage,
      highlightEmbedded,
    });
    const outputs = [];
    for (const test of cases)
      outputs.push({
        ...test,
        result: await pack.highlight({ source: test.source, documentKind: "markdown" }),
      });
    reports[mode] = outputs;
  }
  writeFileSync(
    process.argv[2] ?? "artifacts/markdown/consumer-reference.json",
    JSON.stringify(
      {
        reference:
          "Selected PyTorch CPU weights and predicted-region composition; explicit registered children per mode",
        ...reports,
      },
      null,
      2,
    ) + "\n",
  );
  console.log("24 native selected-package Markdown references");
} finally {
  await Promise.all([...models.values()].map((p) => p.close()));
}
