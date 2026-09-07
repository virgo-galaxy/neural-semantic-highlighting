import { readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import type { SemanticSpan } from "@/core/result.js";

interface LabeledSample {
  repository: string;
  path: string;
  documentKind: string;
  source: string;
  result: {
    offsetEncoding: string;
    spans: SemanticSpan[];
  };
}

const datasetRoot =
  process.env.NSH_DATASET_ROOT ?? join(homedir(), "Datasets", "neural-semantic-highlighting");

const typescriptDatasetRoot = join(datasetRoot, "typescript");

const inputPath = join(typescriptDatasetRoot, "labeled-sample.json");

const outputPath = join(typescriptDatasetRoot, "review-sample.txt");

const samplesPerRepository = 2;
const maxSpansPerFile = 80;

function getLineAndColumn(source: string, offset: number): readonly [number, number] {
  const before = source.slice(0, offset);

  const line = before.split("\n").length;
  const lastNewline = before.lastIndexOf("\n");

  const column = lastNewline === -1 ? offset + 1 : offset - lastNewline;

  return [line, column];
}

function selectSpans(spans: readonly SemanticSpan[]): readonly SemanticSpan[] {
  if (spans.length <= maxSpansPerFile) {
    return spans;
  }

  return Array.from({ length: maxSpansPerFile }, (_, index) => {
    const spanIndex = Math.round((index * (spans.length - 1)) / (maxSpansPerFile - 1));

    return spans[spanIndex];
  }).filter((span): span is SemanticSpan => span !== undefined);
}

const labeled = JSON.parse(await readFile(inputPath, "utf8")) as LabeledSample[];

const byRepository = new Map<string, LabeledSample[]>();

for (const sample of labeled) {
  const entries = byRepository.get(sample.repository) ?? [];

  entries.push(sample);

  byRepository.set(sample.repository, entries);
}

const selected: LabeledSample[] = [];

for (const repository of [...byRepository.keys()].sort()) {
  const entries = byRepository.get(repository);

  if (!entries) {
    continue;
  }

  selected.push(
    ...[...entries]
      .sort((left, right) => left.path.localeCompare(right.path))
      .slice(0, samplesPerRepository),
  );
}

const lines: string[] = [];

lines.push("Neural Semantic Highlighting");
lines.push("TypeScript Real-World Label Review");
lines.push("");
lines.push(`Files: ${selected.length}`);
lines.push("");

for (const sample of selected) {
  lines.push("=".repeat(100));
  lines.push(`${sample.repository}/${sample.path}`);
  lines.push(`Document kind: ${sample.documentKind}`);
  lines.push(`Spans: ${sample.result.spans.length} total`);
  lines.push("");

  for (const span of selectSpans(sample.result.spans)) {
    const [line, column] = getLineAndColumn(sample.source, span.start);

    const text = sample.source.slice(span.start, span.end);

    const modifiers =
      span.modifiers && span.modifiers.length > 0 ? ` [${span.modifiers.join(", ")}]` : "";

    lines.push(`L${line}:C${column}  ${JSON.stringify(text)}  ->  ${span.tokenType}${modifiers}`);
  }

  lines.push("");
}

await writeFile(outputPath, `${lines.join("\n")}\n`, "utf8");

console.log(`Reviewed ${selected.length} files.`);
console.log(`Written to ${outputPath}`);
