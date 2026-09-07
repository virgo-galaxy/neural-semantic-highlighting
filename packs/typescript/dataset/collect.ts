import { createHash } from "node:crypto";
import { mkdir, readdir, stat, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join, relative } from "node:path";

interface Candidate {
  repository: string;
  path: string;
  documentKind: string;
  size: number;
  hash: string;
}

const datasetRoot =
  process.env.NSH_DATASET_ROOT ?? join(homedir(), "Datasets", "neural-semantic-highlighting");

const repositoriesRoot = join(datasetRoot, "repos");
const outputDirectory = join(datasetRoot, "typescript");
const outputPath = join(outputDirectory, "sample.json");

const samplesPerRepository = 10;

const ignoredDirectories = new Set([
  ".git",
  "node_modules",
  "dist",
  "build",
  "coverage",
  "vendor",
  "generated",
]);

const documentKinds: readonly {
  suffix: string;
  kind: string;
}[] = [
  { suffix: ".d.mts", kind: "typescript-esm-declaration" },
  { suffix: ".d.cts", kind: "typescript-commonjs-declaration" },
  { suffix: ".d.ts", kind: "typescript-declaration" },

  { suffix: ".mts", kind: "typescript-esm" },
  { suffix: ".cts", kind: "typescript-commonjs" },
  { suffix: ".tsx", kind: "tsx" },
  { suffix: ".ts", kind: "typescript" },

  { suffix: ".mjs", kind: "javascript-esm" },
  { suffix: ".cjs", kind: "javascript-commonjs" },
  { suffix: ".jsx", kind: "jsx" },
  { suffix: ".js", kind: "javascript" },
];

function getDocumentKind(path: string): string | undefined {
  for (const entry of documentKinds) {
    if (path.endsWith(entry.suffix)) {
      return entry.kind;
    }
  }

  return undefined;
}

function stableHash(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

async function collectFiles(
  repository: string,
  repositoryRoot: string,
  directory: string,
): Promise<Candidate[]> {
  const candidates: Candidate[] = [];

  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) {
      continue;
    }

    const absolutePath = join(directory, entry.name);

    if (entry.isDirectory()) {
      candidates.push(...(await collectFiles(repository, repositoryRoot, absolutePath)));
      continue;
    }

    if (!entry.isFile()) {
      continue;
    }

    const documentKind = getDocumentKind(entry.name);

    if (!documentKind) {
      continue;
    }

    const metadata = await stat(absolutePath);

    if (metadata.size < 200 || metadata.size > 50_000) {
      continue;
    }

    const path = relative(repositoryRoot, absolutePath);

    candidates.push({
      repository,
      path,
      documentKind,
      size: metadata.size,
      hash: stableHash(`${repository}:${path}`),
    });
  }

  return candidates;
}

const repositories = (
  await readdir(repositoriesRoot, {
    withFileTypes: true,
  })
)
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();

const sample: Candidate[] = [];

for (const repository of repositories) {
  const repositoryRoot = join(repositoriesRoot, repository);

  const candidates = await collectFiles(repository, repositoryRoot, repositoryRoot);

  candidates.sort((left, right) => left.hash.localeCompare(right.hash));

  const selected = candidates.slice(0, samplesPerRepository);

  sample.push(...selected);

  console.log(`${repository}: ${selected.length}/${candidates.length} files selected`);
}

await mkdir(outputDirectory, {
  recursive: true,
});

await writeFile(outputPath, `${JSON.stringify(sample, null, 2)}\n`, "utf8");

console.log(`\nCollected ${sample.length} files.`);
console.log(`Written to ${outputPath}`);
