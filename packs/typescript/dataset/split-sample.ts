import { readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import type { HighlightResult } from "@/core/result.js";

interface LabeledSample {
  repository: string;
  path: string;
  documentKind: string;
  source: string;
  result: HighlightResult;
}

interface HoldoutEntry {
  repository: string;
  path: string;
  documentKind: string;
  split: "validation" | "test";
}

const datasetRoot =
  process.env.NSH_DATASET_ROOT ?? join(homedir(), "Datasets", "neural-semantic-highlighting");

const typescriptDatasetRoot = join(datasetRoot, "typescript");

const labeledSamplePath = join(typescriptDatasetRoot, "labeled-sample.json");

const trainPath = join(typescriptDatasetRoot, "train.json");
const validationPath = join(typescriptDatasetRoot, "validation.json");
const testPath = join(typescriptDatasetRoot, "test.json");

const holdoutPath = join(process.cwd(), "packs", "typescript", "dataset", "holdout.json");

function key(repository: string, path: string): string {
  return `${repository}:${path}`;
}

const labeled = JSON.parse(await readFile(labeledSamplePath, "utf8")) as LabeledSample[];
const holdout = JSON.parse(await readFile(holdoutPath, "utf8")) as HoldoutEntry[];

const holdoutByKey = new Map<string, HoldoutEntry>();

for (const entry of holdout) {
  const entryKey = key(entry.repository, entry.path);

  if (holdoutByKey.has(entryKey)) {
    throw new Error(`Duplicate holdout entry: ${entryKey}`);
  }

  holdoutByKey.set(entryKey, entry);
}

const train: LabeledSample[] = [];
const validation: LabeledSample[] = [];
const test: LabeledSample[] = [];

const foundHoldoutKeys = new Set<string>();

for (const entry of labeled) {
  const entryKey = key(entry.repository, entry.path);
  const holdoutEntry = holdoutByKey.get(entryKey);

  if (!holdoutEntry) {
    train.push(entry);
    continue;
  }

  if (entry.documentKind !== holdoutEntry.documentKind) {
    throw new Error(
      `${entryKey}: document kind changed from "${holdoutEntry.documentKind}" to "${entry.documentKind}"`,
    );
  }

  foundHoldoutKeys.add(entryKey);

  if (holdoutEntry.split === "validation") {
    validation.push(entry);
  } else {
    test.push(entry);
  }
}

for (const entryKey of holdoutByKey.keys()) {
  if (!foundHoldoutKeys.has(entryKey)) {
    throw new Error(`Frozen holdout entry is missing from the expanded corpus: ${entryKey}`);
  }
}

train.sort((left, right) =>
  key(left.repository, left.path).localeCompare(key(right.repository, right.path)),
);

validation.sort((left, right) =>
  key(left.repository, left.path).localeCompare(key(right.repository, right.path)),
);

test.sort((left, right) =>
  key(left.repository, left.path).localeCompare(key(right.repository, right.path)),
);

await writeFile(trainPath, `${JSON.stringify(train, null, 2)}\n`, "utf8");
await writeFile(validationPath, `${JSON.stringify(validation, null, 2)}\n`, "utf8");
await writeFile(testPath, `${JSON.stringify(test, null, 2)}\n`, "utf8");

console.log("");
console.log("TypeScript Expanded Dataset Split");
console.log("--------------------------------");
console.log(`Train:      ${train.length}`);
console.log(`Validation: ${validation.length}`);
console.log(`Test:       ${test.length}`);
console.log("");
console.log(`Frozen holdout entries: ${holdout.length}`);
console.log(`Written to ${typescriptDatasetRoot}`);
