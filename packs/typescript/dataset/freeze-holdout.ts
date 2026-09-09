import { readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

interface LabeledSample {
  repository: string;
  path: string;
  documentKind: string;
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

const validationPath = join(typescriptDatasetRoot, "validation.json");
const testPath = join(typescriptDatasetRoot, "test.json");

const outputPath = join(process.cwd(), "packs", "typescript", "dataset", "holdout.json");

function toHoldout(
  entries: readonly LabeledSample[],
  split: HoldoutEntry["split"],
): HoldoutEntry[] {
  return entries.map((entry) => ({
    repository: entry.repository,
    path: entry.path,
    documentKind: entry.documentKind,
    split,
  }));
}

const validation = JSON.parse(await readFile(validationPath, "utf8")) as LabeledSample[];
const test = JSON.parse(await readFile(testPath, "utf8")) as LabeledSample[];

if (validation.length === 0 || test.length === 0) {
  throw new Error("Existing validation/test splits must be non-empty before freezing the holdout.");
}

const holdout = [...toHoldout(validation, "validation"), ...toHoldout(test, "test")].sort(
  (left, right) => {
    const repositoryOrder = left.repository.localeCompare(right.repository);

    if (repositoryOrder !== 0) {
      return repositoryOrder;
    }

    const pathOrder = left.path.localeCompare(right.path);

    if (pathOrder !== 0) {
      return pathOrder;
    }

    return left.split.localeCompare(right.split);
  },
);

const keys = new Set<string>();

for (const entry of holdout) {
  const key = `${entry.repository}:${entry.path}`;

  if (keys.has(key)) {
    throw new Error(`Duplicate holdout entry: ${key}`);
  }

  keys.add(key);
}

await writeFile(outputPath, `${JSON.stringify(holdout, null, 2)}\n`, "utf8");

console.log("TypeScript Holdout Freeze");
console.log("-------------------------");
console.log(`Validation: ${validation.length}`);
console.log(`Test:       ${test.length}`);
console.log(`Total:      ${holdout.length}`);
console.log(`Written to ${outputPath}`);
