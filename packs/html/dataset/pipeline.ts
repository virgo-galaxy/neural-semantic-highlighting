import { createHash, randomUUID } from "node:crypto";
import { mkdir, open, readdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, extname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type { PackSchema } from "@nsh/core";

import { type HtmlGold, labelHtml } from "../labeling/label.js";

const repository = fileURLToPath(new URL("../../../", import.meta.url));
const defaultConfig = fileURLToPath(new URL("sources.json", import.meta.url));
const ignored = new Set([
  ".git",
  "node_modules",
  "dist",
  "build",
  "coverage",
  "vendor",
  "generated",
  "fixtures",
  "__fixtures__",
  "__snapshots__",
  "testdata",
  "challenges",
  "model",
]);
const maxFileBytes = 100_000;

interface SourceSpec {
  id: string;
  base: "repository" | "dataset" | "absolute";
  path: string;
  lock?: string;
}

interface SourceRecord {
  repository: string;
  path: string;
  documentKind: "html";
  sourceGroup: string;
  source: string;
  contentHash: string;
  result?: HtmlGold;
  features?: string[];
}

interface CorpusManifest {
  format: string;
  snapshot: string;
  files: number;
  checksums: Record<string, string>;
  [key: string]: unknown;
}

export const sha256 = (value: string | Uint8Array): string =>
  createHash("sha256").update(value).digest("hex");
const json = (value: unknown): string => JSON.stringify(value, null, 2) + "\n";
const jsonl = (values: unknown[]): string =>
  values.map((value) => JSON.stringify(value)).join("\n") + "\n";

async function atomicJson(path: string, value: unknown): Promise<void> {
  const temporary = path + "." + randomUUID() + ".tmp";
  try {
    await writeFile(temporary, json(value), { flag: "wx" });
    await rename(temporary, path);
  } finally {
    await rm(temporary, { force: true });
  }
}

async function locked<T>(root: string, work: () => Promise<T>): Promise<T> {
  await mkdir(root, { recursive: true });
  const lockPath = join(root, ".dataset.lock");
  const lock = await open(lockPath, "wx");
  try {
    await lock.writeFile(json({ pid: process.pid }));
    return await work();
  } finally {
    await lock.close();
    await rm(lockPath);
  }
}

async function verify(folder: string, manifest: CorpusManifest): Promise<void> {
  for (const [name, expected] of Object.entries(manifest.checksums)) {
    if (name !== relative(folder, join(folder, name)) || name.startsWith("..")) {
      throw new Error("Unsafe corpus checksum path");
    }
    if (sha256(await readFile(join(folder, name))) !== expected) {
      throw new Error("Corpus checksum mismatch: " + name);
    }
  }
}

async function publish(
  root: string,
  parent: string,
  snapshot: string,
  files: Record<string, string>,
  fields: Record<string, unknown>,
  pointer: string,
): Promise<CorpusManifest> {
  await mkdir(parent, { recursive: true });
  const target = join(parent, snapshot);
  const staging = join(parent, ".staging-" + randomUUID());
  const checksums = Object.fromEntries(
    Object.entries(files).map(([name, text]) => [name, sha256(text)]),
  );
  const manifest: CorpusManifest = {
    ...fields,
    format: "nsh-html-corpus-v1",
    snapshot,
    files: Number(fields.files),
    checksums,
  };
  await mkdir(staging);
  try {
    for (const [name, text] of Object.entries(files)) await writeFile(join(staging, name), text);
    await writeFile(join(staging, "sample.json"), json(manifest));
    try {
      await rename(staging, target);
    } catch (error) {
      if (!["EEXIST", "ENOTEMPTY"].includes((error as NodeJS.ErrnoException).code ?? ""))
        throw error;
      const existing = JSON.parse(
        await readFile(join(target, "sample.json"), "utf8"),
      ) as CorpusManifest;
      if (json(existing) !== json(manifest))
        throw new Error("Immutable corpus identity collision", { cause: error });
      await verify(target, existing);
    }
    await atomicJson(join(root, pointer), {
      format: "nsh-html-corpus-pointer-v1",
      directory: relative(root, target),
      manifestHash: sha256(json(manifest)),
    });
    return manifest;
  } finally {
    await rm(staging, { recursive: true, force: true });
  }
}

export async function collect(root: string, configPath = defaultConfig): Promise<CorpusManifest> {
  return locked(root, async () => {
    const rawConfig = await readFile(configPath, "utf8");
    const config = JSON.parse(rawConfig) as { format: string; sources: SourceSpec[] };
    if (config.format !== "nsh-html-sources-v1" || !config.sources.length)
      throw new Error("Invalid source configuration");
    const ids = new Set<string>();
    const records: SourceRecord[] = [];
    const sourceLocks: Record<string, unknown> = {};
    const exclusions: { repository: string; path: string; reason: string }[] = [];
    for (const spec of config.sources) {
      if (!/^[a-z0-9][a-z0-9-]*$/u.test(spec.id) || ids.has(spec.id))
        throw new Error("Duplicate/invalid source id");
      ids.add(spec.id);
      if (!["repository", "dataset", "absolute"].includes(spec.base))
        throw new Error("Invalid source base");
      const base =
        spec.base === "repository" ? repository : spec.base === "dataset" ? dirname(root) : "/";
      const folder = resolve(base, spec.path);
      if (spec.base !== "absolute" && relative(base, folder).startsWith("..")) {
        throw new Error("Source path escapes its configured base");
      }
      const lockPath = spec.lock ? resolve(base, spec.lock) : undefined;
      let lockedFiles: Record<string, string> | undefined;
      if (lockPath) {
        const rawLock = await readFile(lockPath);
        const sourceLock = JSON.parse(rawLock.toString("utf8")) as {
          spec: { name: string; version: string };
          files: Record<string, string>;
          integrity: string;
          commit?: string;
          tree?: string;
          upstream?: string;
        };
        lockedFiles = sourceLock.files;
        sourceLocks[spec.id] = {
          manifestHash: sha256(rawLock),
          package: sourceLock.spec.name,
          version: sourceLock.spec.version,
          integrity: sourceLock.integrity,
          commit: sourceLock.commit,
          tree: sourceLock.tree,
          upstream: sourceLock.upstream,
        };
      }
      const walk = async (directory: string): Promise<void> => {
        for (const entry of (await readdir(directory, { withFileTypes: true })).sort((a, b) =>
          a.name.localeCompare(b.name),
        )) {
          const path = join(directory, entry.name);
          if (entry.isDirectory()) {
            if (!ignored.has(entry.name)) await walk(path);
            continue;
          }
          if (!entry.isFile()) continue;
          const suffix = extname(entry.name).toLowerCase();
          if (suffix !== ".html" && suffix !== ".htm") continue;
          const name = relative(folder, path).split("\\").join("/");
          const raw = await readFile(path);
          if (
            lockPath &&
            lockedFiles?.[relative(dirname(lockPath), path).split("\\").join("/")] !== sha256(raw)
          ) {
            throw new Error("Locked style source was modified: " + path);
          }
          if (!raw.length || raw.length > maxFileBytes || /\.min\.html?$/iu.test(entry.name)) {
            exclusions.push({ repository: spec.id, path: name, reason: "empty-large-or-minified" });
            continue;
          }
          const source = new TextDecoder("utf-8", { fatal: true }).decode(raw);
          // TextDecoder removes a leading BOM. Preserve the original source exactly.
          if (Buffer.from(source, "utf8").compare(raw) !== 0) {
            exclusions.push({
              repository: spec.id,
              path: name,
              reason: "source-encoding-roundtrip",
            });
            continue;
          }
          if (!source.trim()) continue;
          records.push({
            repository: spec.id,
            path: name,
            source,
            documentKind: "html",
            sourceGroup: spec.id + ":" + dirname(name),
            contentHash: sha256(raw),
          });
        }
      };
      await walk(folder);
    }
    const sourceText = jsonl(records);
    const policy = { maxFileBytes, ignored: [...ignored].sort() };
    const snapshot = sha256(
      json({
        source: sha256(sourceText),
        config: sha256(rawConfig),
        policy,
        sourceLocks,
        collector: sha256(await readFile(fileURLToPath(import.meta.url))),
      }),
    );
    return publish(
      root,
      join(root, "corpora"),
      snapshot,
      { "sources.jsonl": sourceText, "exclusions.jsonl": jsonl(exclusions) },
      {
        files: records.length,
        config: JSON.parse(rawConfig),
        policy,
        sourceLocks,
        documentKinds: count(records.map((record) => record.documentKind)),
      },
      "current-corpus.json",
    );
  });
}

async function readPointer(
  root: string,
  name: string,
): Promise<{ folder: string; manifest: CorpusManifest }> {
  const pointer = JSON.parse(await readFile(join(root, name), "utf8")) as {
    directory: string;
    manifestHash: string;
  };
  const folder = resolve(root, pointer.directory);
  if (!relative(root, folder) || relative(root, folder).startsWith(".."))
    throw new Error("Invalid corpus pointer");
  const text = await readFile(join(folder, "sample.json"), "utf8");
  if (sha256(text) !== pointer.manifestHash) throw new Error("Corpus manifest hash mismatch");
  const manifest = JSON.parse(text) as CorpusManifest;
  await verify(folder, manifest);
  return { folder, manifest };
}

const count = (values: string[]): Record<string, number> => {
  const totals: Record<string, number> = {};
  for (const value of values) totals[value] = (totals[value] ?? 0) + 1;
  return totals;
};

export function validateRecord(record: SourceRecord, schema: PackSchema): void {
  if (record.documentKind !== "html") throw new Error("Unknown document kind");
  if (sha256(record.source) !== record.contentHash) throw new Error("Source content hash mismatch");
  if (!record.sourceGroup || !record.repository || !record.path)
    throw new Error("Missing source identity");
  if (record.result?.offsetEncoding !== "utf-16") throw new Error("Expected UTF-16 offsets");
  if (!Array.isArray(record.result.modernExclusions) || record.result.modernExclusions.length)
    throw new Error("Obsolete-source policy exclusions must remain in quarantine");
  const expectedRegions = record.result.spans
    .filter((span) => span.tokenType.startsWith("embedded-"))
    .map((span) => ({
      start: span.start,
      end: span.end,
      language: span.tokenType.slice(9),
      context: "block",
    }));
  if (JSON.stringify(record.result.regions) !== JSON.stringify(expectedRegions))
    throw new Error("Embedded region/source span mismatch");
  const types = new Set(schema.tokenTypes.map((type) => type.id));
  const modifiers = new Set(schema.tokenModifiers.map((modifier) => modifier.id));
  const boundaries = new Set<number>([0]);
  let unit = 0;
  for (const character of record.source) {
    unit += character.length;
    boundaries.add(unit);
  }
  let previous = 0;
  for (const span of record.result.spans) {
    if (
      !Number.isInteger(span.start) ||
      !Number.isInteger(span.end) ||
      span.start < previous ||
      span.end <= span.start ||
      !boundaries.has(span.start) ||
      !boundaries.has(span.end)
    ) {
      throw new Error("Invalid or overlapping UTF-16 span");
    }
    if (record.source.slice(previous, span.start).trim()) throw new Error("Unlabeled source gap");
    if (!types.has(span.tokenType)) throw new Error("Unknown token type");
    if (
      new Set(span.modifiers ?? []).size !== (span.modifiers ?? []).length ||
      (span.modifiers ?? []).some((modifier) => !modifiers.has(modifier))
    )
      throw new Error("Invalid modifier");
    previous = span.end;
  }
  if (record.source.slice(previous).trim()) throw new Error("Unlabeled source suffix");
}

export async function label(root: string): Promise<CorpusManifest> {
  return locked(root, async () => {
    const { folder, manifest } = await readPointer(root, "current-corpus.json");
    const schemaText = await readFile(new URL("../model-schema.json", import.meta.url), "utf8");
    const schema = JSON.parse(schemaText) as PackSchema;
    const raw = await readFile(join(folder, "sources.jsonl"), "utf8");
    const records = raw.trim()
      ? raw
          .trim()
          .split("\n")
          .map((line) => JSON.parse(line) as SourceRecord)
      : [];
    const labeled: SourceRecord[] = [];
    const quarantine: { record: SourceRecord; reason: string }[] = [];
    for (const record of records) {
      if (sha256(record.source) !== record.contentHash) throw new Error("Collected source changed");
      try {
        const result = await labelHtml(record);
        if (result.modernExclusions.length)
          throw new Error(
            "Out-of-scope modern-source policy: " + result.modernExclusions.join(", "),
          );
        const features = new Set(result.regions.map((region) => "embedded-" + region.language));
        if (!result.regions.length) features.add("markup-only");
        for (const span of result.spans) {
          const text = record.source.slice(span.start, span.end).toLowerCase();
          if (span.tokenType === "attribute" && text === "style") features.add("style-attribute");
          if (span.tokenType === "attribute" && text.startsWith("on"))
            features.add("event-attribute");
          if (span.tokenType === "tag" && text.includes("-")) features.add("custom-elements");
          if (span.tokenType === "tag" && (text === "svg" || text === "math"))
            features.add("foreign-content");
          if (span.tokenType === "entity") features.add("entities");
        }
        const gold = { ...record, result, features: [...features].sort() };
        validateRecord(gold, schema);
        labeled.push(gold);
      } catch (error) {
        quarantine.push({ record, reason: error instanceof Error ? error.message : String(error) });
      }
    }
    if (!labeled.length) throw new Error("No valid Gold documents");
    const labelerHash = sha256(await readFile(new URL("../labeling/label.ts", import.meta.url)));
    const dependencyLockHash = sha256(await readFile(join(repository, "pnpm-lock.yaml")));
    const identity = {
      corpus: manifest.snapshot,
      labelerHash,
      dependencyLockHash,
      schemaHash: sha256(schemaText),
      semanticContractHash: sha256(await readFile(new URL("../SEMANTICS.md", import.meta.url))),
    };
    return publish(
      root,
      join(root, "gold"),
      sha256(json(identity)),
      { "labeled-sample.jsonl": jsonl(labeled), "quarantine.jsonl": jsonl(quarantine) },
      {
        files: labeled.length,
        quarantine: quarantine.length,
        provenance: identity,
        documentKinds: count(labeled.map((record) => record.documentKind)),
        tokenTypes: count(
          labeled.flatMap((record) => record.result!.spans.map((span) => span.tokenType)),
        ),
        features: count(labeled.flatMap((record) => record.features ?? [])),
      },
      "current-gold.json",
    );
  });
}

export async function validate(root: string): Promise<CorpusManifest> {
  const { folder, manifest } = await readPointer(root, "current-gold.json");
  const schema = JSON.parse(
    await readFile(new URL("../model-schema.json", import.meta.url), "utf8"),
  ) as PackSchema;
  const lines = (await readFile(join(folder, "labeled-sample.jsonl"), "utf8")).trim().split("\n");
  for (const line of lines) validateRecord(JSON.parse(line) as SourceRecord, schema);
  if (lines.length !== manifest.files) throw new Error("Gold document count mismatch");
  return manifest;
}

async function main(): Promise<void> {
  const [command, ...args] = process.argv.slice(2);
  const option = (name: string): string | undefined => {
    const at = args.indexOf(name);
    if (at < 0) return undefined;
    if (!args[at + 1]) throw new Error("Missing option value: " + name);
    return args[at + 1];
  };
  const parent =
    option("--root") ??
    process.env.NSH_DATASET_ROOT ??
    join(homedir(), "Datasets", "neural-semantic-highlighting");
  const root = join(resolve(parent), "html");
  const result =
    command === "collect"
      ? await collect(root, option("--config"))
      : command === "label"
        ? await label(root)
        : command === "validate"
          ? await validate(root)
          : undefined;
  if (!result)
    throw new Error("Usage: pipeline.ts collect|label|validate [--root parent] [--config path]");
  console.log(json({ root, ...result }));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
}
