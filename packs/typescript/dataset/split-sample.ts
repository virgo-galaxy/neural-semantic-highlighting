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

const datasetRoot =
  process.env.NSH_DATASET_ROOT ?? join(homedir(), "Datasets", "neural-semantic-highlighting");

const typescriptDatasetRoot = join(datasetRoot, "typescript");

const samplePath = join(typescriptDatasetRoot, "sample.json");
const labeledSamplePath = join(typescriptDatasetRoot, "labeled-sample.json");

const trainPath = join(typescriptDatasetRoot, "train.json");
const validationPath = join(typescriptDatasetRoot, "validation.json");
const testPath = join(typescriptDatasetRoot, "test.json");

function key(repository: string, path: string): string {
  return `${repository}:${path}`;
}

const sample = JSON.parse(await readFile(samplePath, "utf8")) as SampleEntry[];

const labeled = JSON.parse(await readFile(labeledSamplePath, "utf8")) as LabeledSample[];

const sampleByKey = new Map(sample.map((entry) => [key(entry.repository, entry.path), entry]));

const byRepository = new Map<string, LabeledSample[]>();

for (const entry of labeled) {
  const entries = byRepository.get(entry.repository) ?? [];

  entries.push(entry);

  byRepository.set(entry.repository, entries);
}

const train: LabeledSample[] = [];
const validation: LabeledSample[] = [];
const test: LabeledSample[] = [];

for (const repository of [...byRepository.keys()].sort()) {
  const entries = byRepository.get(repository);

  if (!entries) {
    continue;
  }

  const sorted = [...entries].sort((left, right) => {
    const leftSample = sampleByKey.get(key(left.repository, left.path));
    const rightSample = sampleByKey.get(key(right.repository, right.path));

    if (!leftSample || !rightSample) {
      throw new Error(`Missing sample metadata while splitting repository "${repository}".`);
    }

    return leftSample.hash.localeCompare(rightSample.hash);
  });

  const trainEnd = Math.floor(sorted.length * 0.8);
  const validationEnd = trainEnd + Math.floor(sorted.length * 0.1);

  train.push(...sorted.slice(0, trainEnd));
  validation.push(...sorted.slice(trainEnd, validationEnd));
  test.push(...sorted.slice(validationEnd));

  console.log(
    `${repository}: train=${trainEnd}, validation=${validationEnd - trainEnd}, test=${
      sorted.length - validationEnd
    }`,
  );
}

await writeFile(trainPath, `${JSON.stringify(train, null, 2)}\n`, "utf8");
await writeFile(validationPath, `${JSON.stringify(validation, null, 2)}\n`, "utf8");
await writeFile(testPath, `${JSON.stringify(test, null, 2)}\n`, "utf8");

console.log("");
console.log("TypeScript Dataset Split");
console.log("------------------------");
console.log(`Train:      ${train.length}`);
console.log(`Validation: ${validation.length}`);
console.log(`Test:       ${test.length}`);
console.log("");
console.log(`Written to ${typescriptDatasetRoot}`);
