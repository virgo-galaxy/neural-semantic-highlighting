import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import type { HighlightResult, PackManifest, PackSchema, SemanticSpan } from "@nsh/core";
import { createLocalProcessPack } from "@nsh/local";

import { composeHtmlGold } from "../../packs/html/labeling/embedded.js";
import type { HtmlGold } from "../../packs/html/labeling/label.js";
import { createCompositeHtmlPack } from "../../packs/html/runtime/composite.js";

const repository = fileURLToPath(new URL("../../", import.meta.url));
const python = join(repository, ".venv/bin/python");
const hash = (raw: Uint8Array | string) => createHash("sha256").update(raw).digest("hex");
const fileHash = async (path: string) => hash(await readFile(path));
const run = promisify(execFile);

class Metrics {
  documents = 0;
  counts = new Map<string, { tp: number; fp: number; fn: number }>();
  modifiers = { tp: 0, fp: 0, fn: 0 };
  constructor(schema: PackSchema) {
    for (const role of schema.tokenTypes) this.counts.set(role.id, { tp: 0, fp: 0, fn: 0 });
  }
  add(gold: HighlightResult, predicted: HighlightResult) {
    const key = (s: SemanticSpan, mods = false) =>
      JSON.stringify([
        s.start,
        s.end,
        s.tokenType,
        ...(mods ? [[...(s.modifiers ?? [])].sort()] : []),
      ]);
    const expected = new Set(gold.spans.map((s) => key(s))),
      actual = new Set(predicted.spans.map((s) => key(s)));
    for (const s of gold.spans) {
      const counts = this.counts.get(s.tokenType);
      if (!counts) throw new Error("Unknown public Gold role " + s.tokenType);
      counts[actual.has(key(s)) ? "tp" : "fn"] += 1;
    }
    for (const s of predicted.spans)
      if (!expected.has(key(s))) {
        const counts = this.counts.get(s.tokenType);
        if (!counts) throw new Error("Unknown public predicted role " + s.tokenType);
        counts.fp += 1;
      }
    const expectedM = new Set(gold.spans.map((s) => key(s, true))),
      actualM = new Set(predicted.spans.map((s) => key(s, true)));
    for (const k of expectedM) this.modifiers[actualM.has(k) ? "tp" : "fn"] += 1;
    for (const k of actualM) if (!expectedM.has(k)) this.modifiers.fp += 1;
    this.documents += 1;
  }
  report() {
    const total = { tp: 0, fp: 0, fn: 0 };
    const scores = [...this.counts].map(([role, c]) => {
      total.tp += c.tp;
      total.fp += c.fp;
      total.fn += c.fn;
      return [role, prf(c)] as const;
    });
    const represented = scores.filter(([, c]) => c.tp + c.fp + c.fn > 0);
    return {
      documents: this.documents,
      exactSpan: prf(total),
      exactSpanMacroF1: represented.length
        ? represented.reduce((v, [, c]) => v + c.f1, 0) / represented.length
        : 0,
      exactSpanIncludingModifiers: prf(this.modifiers),
      byTokenType: Object.fromEntries(scores),
    };
  }
}
function prf({ tp, fp, fn }: { tp: number; fp: number; fn: number }) {
  return {
    precision: tp + fp ? tp / (tp + fp) : 0,
    recall: tp + fn ? tp / (tp + fn) : 0,
    f1: 2 * tp + fp + fn ? (2 * tp) / (2 * tp + fp + fn) : 0,
    tp,
    fp,
    fn,
    support: tp + fn,
  };
}

async function main() {
  const args = process.argv.slice(2);
  const option = (name: string) => {
    const i = args.indexOf(name);
    return i < 0 ? undefined : args[i + 1];
  };
  if (!option("--checkpoint")) throw new Error("Set --checkpoint to a reviewed HTML candidate");
  const original = resolve(option("--checkpoint")!);
  const split = option("--split") ?? "validation",
    device = option("--device") ?? "auto";
  if (!["validation", "test"].includes(split) || !["auto", "cpu", "mps", "cuda"].includes(device))
    throw new Error("Invalid split/device");
  const stamp = new Date().toISOString().replace(/[:.]/gu, "-");
  const output = resolve(
    option("--output") ?? join(dirname(original), `${split}-composed-${stamp}.json`),
  );
  const raw = await readFile(original),
    checkpointHash = hash(raw);
  const cache = join(dirname(output), ".eval-checkpoints");
  await mkdir(cache, { recursive: true });
  const frozen = join(cache, checkpointHash + ".pt");
  try {
    await writeFile(frozen, raw, { flag: "wx" });
  } catch (e) {
    if ((e as NodeJS.ErrnoException).code !== "EEXIST") throw e;
  }
  if ((await fileHash(frozen)) !== checkpointHash)
    throw new Error("Frozen checkpoint cache was modified");
  const metadataCode =
    'import json,sys; from training.html.checkpoints import load_model_artifact; p=load_model_artifact(__import__("pathlib").Path(sys.argv[1])); print(json.dumps({k:p[k] for k in ("epoch","dataset","modelConfig","trainingConfig")}))';
  const meta = JSON.parse(
    (await run(python, ["-c", metadataCode, frozen], { cwd: repository })).stdout,
  ) as {
    epoch: number;
    dataset: { path: string; snapshot: string; manifestHash: string };
    modelConfig: unknown;
    trainingConfig: { smoke?: boolean };
  };
  const snapshot = resolve(option("--snapshot") ?? meta.dataset.path);
  if ((await fileHash(join(snapshot, "manifest.json"))) !== meta.dataset.manifestHash)
    throw new Error("Checkpoint dataset mismatch");
  const manifest = JSON.parse(await readFile(join(snapshot, "manifest.json"), "utf8")) as {
    snapshot: string;
    checksums: Record<string, string>;
  };
  if (
    manifest.snapshot !== meta.dataset.snapshot ||
    (await fileHash(join(snapshot, split, "documents.jsonl"))) !==
      manifest.checksums[split + "/documents.jsonl"]
  )
    throw new Error("Document checksum mismatch");
  const schema = JSON.parse(
    await readFile(join(repository, "packs/html/schema.json"), "utf8"),
  ) as PackSchema;
  const packManifest = async (name: string) =>
    JSON.parse(
      await readFile(join(repository, `packs/${name}/manifest.json`), "utf8"),
    ) as PackManifest;
  const typescript = createLocalProcessPack({
    manifest: await packManifest("typescript"),
    command: python,
    cwd: repository,
    args: [
      "-c",
      'import sys; from packs.typescript.runtime.local import TypeScriptLocalPack,run_stdio,select_device; run_stdio(TypeScriptLocalPack(device=select_device() if sys.argv[1]=="auto" else __import__("torch").device(sys.argv[1])))',
      device,
    ],
  });
  const css = createLocalProcessPack({
    manifest: await packManifest("css"),
    command: python,
    cwd: repository,
    args: ["-m", "packs.css.runtime.local", "--stdio", "--device", device],
  });
  const html = createLocalProcessPack({
    manifest: await packManifest("html"),
    command: python,
    cwd: repository,
    args: ["-m", "packs.html.runtime.local", "--stdio", "--checkpoint", frozen, "--device", device],
  });
  const composed = createCompositeHtmlPack({
    base: html,
    highlightEmbedded: (request) =>
      (request.documentKind === "css" ? css : typescript).highlight(request),
  });
  const childModels = {
    typescript: await fileHash(join(repository, "packs/typescript/model/model.pt")),
    css: await fileHash(join(repository, "packs/css/model/model.pt")),
  };
  const streams = { natural: new Metrics(schema), focus: new Metrics(schema) };
  const features = new Map<string, Metrics>();
  const excluded: { id: string; path: string; stream: string; reason: string }[] = [];
  const docs = (await readFile(join(snapshot, split, "documents.jsonl"), "utf8"))
    .trim()
    .split("\n")
    .map(
      (line) =>
        JSON.parse(line) as {
          id: string;
          path: string;
          source: string;
          contentHash: string;
          result: HtmlGold;
          features: string[];
          stream: "natural" | "focus";
        },
    );
  const started = performance.now();
  try {
    for (const [i, doc] of docs.entries()) {
      if (hash(doc.source) !== doc.contentHash) throw new Error("Captured source changed");
      let gold: HighlightResult;
      try {
        gold = composeHtmlGold(doc.source, doc.result);
      } catch (e) {
        excluded.push({
          id: doc.id,
          path: doc.path,
          stream: doc.stream,
          reason: e instanceof Error ? e.message : String(e),
        });
        continue;
      }
      const predicted = await composed.highlight({ source: doc.source, documentKind: "html" });
      streams[doc.stream].add(gold, predicted);
      for (const feature of doc.features ?? []) {
        if (!features.has(feature)) features.set(feature, new Metrics(schema));
        features.get(feature)!.add(gold, predicted);
      }
      if (i === 0 || (i + 1) % 10 === 0 || i === docs.length - 1)
        console.log(`Composed ${split}: ${i + 1}/${docs.length}`);
    }
  } finally {
    await Promise.all([html.close(), css.close(), typescript.close()]);
  }
  if (
    (await fileHash(join(repository, "packs/typescript/model/model.pt"))) !==
      childModels.typescript ||
    (await fileHash(join(repository, "packs/css/model/model.pt"))) !== childModels.css
  )
    throw new Error("A child model changed during evaluation");
  const provenanceFiles = [
    "packs/html/labeling/embedded.ts",
    "packs/html/labeling/label.ts",
    "packs/html/runtime/composite.ts",
    "packs/css/labeling/label.ts",
    "packs/typescript/labeling/label.ts",
    "pnpm-lock.yaml",
  ];
  const report = {
    scope: "composed-markup-plus-javascript-and-css-bodies",
    split,
    inference: "neural-predicted-regions-and-neural-child-packs",
    checkpointHash,
    checkpointEpoch: meta.epoch,
    modelConfig: meta.modelConfig,
    smokeCheckpoint: !!meta.trainingConfig.smoke,
    dataset: { snapshot: meta.dataset.snapshot, manifestHash: meta.dataset.manifestHash },
    childModels,
    device,
    streams: { natural: streams.natural.report(), focus: streams.focus.report() },
    features: Object.fromEntries([...features].map(([key, value]) => [key, value.report()])),
    attemptedDocuments: docs.length,
    excludedGoldDocuments: excluded,
    seconds: (performance.now() - started) / 1000,
    provenance: Object.fromEntries(
      await Promise.all(
        provenanceFiles.map(async (name) => [name, await fileHash(join(repository, name))]),
      ),
    ),
  };
  await writeFile(output, JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
  console.log(
    JSON.stringify(
      {
        natural: report.streams.natural.exactSpan,
        focus: report.streams.focus.exactSpan,
        excluded: excluded.length,
        output,
      },
      null,
      2,
    ),
  );
}

main().catch((e: unknown) => {
  console.error(e);
  process.exitCode = 1;
});
