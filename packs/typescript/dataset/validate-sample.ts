import { readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import type { HighlightResult } from "@/core/result.js";

interface SampleEntry {
  repository: string;
  path: string;
  documentKind: string;
  size: number;
  hash: string;
}

interface LabeledSample {
  repository: string;
  path: string;
  documentKind: string;
  source: string;
  result: HighlightResult;
}

interface PackSchema {
  tokenTypes: readonly {
    id: string;
  }[];
  tokenModifiers: readonly {
    id: string;
  }[];
}

interface DatasetStatistics {
  files: number;
  spans: number;
  sourceCharacters: number;
  documentKinds: Record<string, number>;
  tokenTypes: Record<string, number>;
  modifiers: Record<string, number>;
}

const datasetRoot =
  process.env.NSH_DATASET_ROOT ?? join(homedir(), "Datasets", "neural-semantic-highlighting");

const typescriptDatasetRoot = join(datasetRoot, "typescript");

const samplePath = join(typescriptDatasetRoot, "sample.json");
const labeledSamplePath = join(typescriptDatasetRoot, "labeled-sample.json");
const statisticsPath = join(typescriptDatasetRoot, "statistics.json");

const schemaPath = join(process.cwd(), "packs", "typescript", "schema.json");

function increment(counter: Record<string, number>, key: string): void {
  const current = Object.hasOwn(counter, key) ? counter[key] : 0;

  counter[key] = current + 1;
}

function sampleKey(repository: string, path: string): string {
  return `${repository}:${path}`;
}

const sample = JSON.parse(await readFile(samplePath, "utf8")) as SampleEntry[];

const labeled = JSON.parse(await readFile(labeledSamplePath, "utf8")) as LabeledSample[];

const schema = JSON.parse(await readFile(schemaPath, "utf8")) as PackSchema;

const validTokenTypes = new Set(schema.tokenTypes.map((entry) => entry.id));

const validModifiers = new Set(schema.tokenModifiers.map((entry) => entry.id));

const errors: string[] = [];

const sampleKeys = new Set<string>();

for (const entry of sample) {
  const key = sampleKey(entry.repository, entry.path);

  if (sampleKeys.has(key)) {
    errors.push(`Duplicate sample entry: ${key}`);
  }

  sampleKeys.add(key);
}

const labeledKeys = new Set<string>();

const statistics: DatasetStatistics = {
  files: labeled.length,
  spans: 0,
  sourceCharacters: 0,
  documentKinds: {},
  tokenTypes: {},
  modifiers: {},
};

for (const entry of labeled) {
  const key = sampleKey(entry.repository, entry.path);

  if (labeledKeys.has(key)) {
    errors.push(`Duplicate labeled entry: ${key}`);
  }

  labeledKeys.add(key);

  if (!sampleKeys.has(key)) {
    errors.push(`Labeled entry not found in sample.json: ${key}`);
  }

  statistics.sourceCharacters += entry.source.length;

  increment(statistics.documentKinds, entry.documentKind);

  if (entry.result.offsetEncoding !== "utf-16") {
    errors.push(`${key}: unexpected offset encoding "${entry.result.offsetEncoding}"`);
  }

  if (entry.result.spans.length === 0) {
    errors.push(`${key}: no semantic spans`);
  }

  let previousEnd = 0;

  for (const span of entry.result.spans) {
    statistics.spans += 1;

    increment(statistics.tokenTypes, span.tokenType);

    if (!validTokenTypes.has(span.tokenType)) {
      errors.push(`${key}: unknown token type "${span.tokenType}"`);
    }

    for (const modifier of span.modifiers ?? []) {
      increment(statistics.modifiers, modifier);

      if (!validModifiers.has(modifier)) {
        errors.push(`${key}: unknown modifier "${modifier}"`);
      }
    }

    if (!Number.isInteger(span.start) || !Number.isInteger(span.end)) {
      errors.push(`${key}: non-integer span ${span.start}-${span.end}`);
      continue;
    }

    if (span.start < 0 || span.end > entry.source.length) {
      errors.push(
        `${key}: span out of bounds ${span.start}-${span.end} for source length ${entry.source.length}`,
      );
    }

    if (span.start >= span.end) {
      errors.push(`${key}: empty or reversed span ${span.start}-${span.end}`);
    }

    if (span.start < previousEnd) {
      errors.push(`${key}: overlapping or unsorted span ${span.start}-${span.end}`);
    }

    previousEnd = span.end;
  }
}

for (const key of sampleKeys) {
  if (!labeledKeys.has(key)) {
    errors.push(`Sample entry was not labeled: ${key}`);
  }
}

if (sample.length !== labeled.length) {
  errors.push(`File count mismatch: sample=${sample.length}, labeled=${labeled.length}`);
}

const sortedStatistics: DatasetStatistics = {
  ...statistics,
  documentKinds: Object.fromEntries(
    Object.entries(statistics.documentKinds).sort(([left], [right]) => left.localeCompare(right)),
  ),
  tokenTypes: Object.fromEntries(
    Object.entries(statistics.tokenTypes).sort(([, left], [, right]) => right - left),
  ),
  modifiers: Object.fromEntries(
    Object.entries(statistics.modifiers).sort(([, left], [, right]) => right - left),
  ),
};

await writeFile(statisticsPath, `${JSON.stringify(sortedStatistics, null, 2)}\n`, "utf8");

console.log("");
console.log("TypeScript Dataset Validation");
console.log("-----------------------------");
console.log(`Files:             ${statistics.files}`);
console.log(`Spans:             ${statistics.spans}`);
console.log(`Source characters: ${statistics.sourceCharacters}`);
console.log("");

console.log("Document kinds:");
for (const [kind, count] of Object.entries(sortedStatistics.documentKinds)) {
  console.log(`  ${kind}: ${count}`);
}

console.log("");
console.log("Token types:");
for (const [tokenType, count] of Object.entries(sortedStatistics.tokenTypes)) {
  console.log(`  ${tokenType}: ${count}`);
}

console.log("");
console.log("Modifiers:");
for (const [modifier, count] of Object.entries(sortedStatistics.modifiers)) {
  console.log(`  ${modifier}: ${count}`);
}

console.log("");

if (errors.length > 0) {
  console.error(`Validation failed with ${errors.length} error(s):`);

  for (const error of errors.slice(0, 50)) {
    console.error(`  - ${error}`);
  }

  if (errors.length > 50) {
    console.error(`  ... and ${errors.length - 50} more`);
  }

  process.exitCode = 1;
} else {
  console.log("Validation passed.");
}

console.log(`Statistics written to ${statisticsPath}`);
