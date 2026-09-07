import { mkdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import { labelTypeScript } from "../labeling/label.js";

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
  result: ReturnType<typeof labelTypeScript>;
}

const datasetRoot =
  process.env.NSH_DATASET_ROOT ?? join(homedir(), "Datasets", "neural-semantic-highlighting");

const repositoriesRoot = join(datasetRoot, "repos");
const typescriptDatasetRoot = join(datasetRoot, "typescript");

const samplePath = join(typescriptDatasetRoot, "sample.json");
const outputPath = join(typescriptDatasetRoot, "labeled-sample.json");

const sample = JSON.parse(await readFile(samplePath, "utf8")) as SampleEntry[];

const labeled: LabeledSample[] = [];

for (const entry of sample) {
  const sourcePath = join(repositoriesRoot, entry.repository, entry.path);

  const source = await readFile(sourcePath, "utf8");

  const result = labelTypeScript({
    source,
    documentKind: entry.documentKind,
  });

  labeled.push({
    repository: entry.repository,
    path: entry.path,
    documentKind: entry.documentKind,
    source,
    result,
  });

  console.log(`${entry.repository}/${entry.path}: ${result.spans.length} spans`);
}

await mkdir(typescriptDatasetRoot, {
  recursive: true,
});

await writeFile(outputPath, `${JSON.stringify(labeled, null, 2)}\n`, "utf8");

console.log(`\nLabeled ${labeled.length} files.`);
console.log(`Written to ${outputPath}`);
