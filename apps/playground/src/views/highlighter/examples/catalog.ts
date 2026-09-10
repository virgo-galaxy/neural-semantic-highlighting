import javascriptIcon from "@/assets/document-kinds/javascript.svg";
import typescriptIcon from "@/assets/document-kinds/typescript.svg";
import type { HighlighterExample, HighlighterLanguage } from "@/views/highlighter/examples/types";

const sources = import.meta.glob("./*/*", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

const LANGUAGE_METADATA: Readonly<Record<string, Omit<HighlighterLanguage, "id">>> = {
  javascript: {
    label: "JavaScript",
    icon: javascriptIcon,
  },
  typescript: {
    label: "TypeScript",
    icon: typescriptIcon,
  },
};

const DOCUMENT_KIND_SUFFIXES = [
  [".d.mts", "typescript-esm-declaration"],
  [".d.cts", "typescript-commonjs-declaration"],
  [".d.ts", "typescript-declaration"],
  [".mts", "typescript-esm"],
  [".cts", "typescript-commonjs"],
  [".tsx", "tsx"],
  [".ts", "typescript"],
  [".mjs", "javascript-esm"],
  [".cjs", "javascript-commonjs"],
  [".jsx", "jsx"],
  [".js", "javascript"],
] as const;

function formatLanguageLabel(languageId: string): string {
  return languageId
    .split(/[-_]/u)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function documentKindFor(filename: string, languageId: string): string {
  return DOCUMENT_KIND_SUFFIXES.find(([suffix]) => filename.endsWith(suffix))?.[1] ?? languageId;
}

function createExample(path: string, source: string): HighlighterExample {
  const match = /^\.\/([^/]+)\/([^/]+)$/u.exec(path);

  if (!match) {
    throw new Error(`Invalid highlighter example path: ${path}`);
  }

  const [, languageId, filename] = match;

  if (!languageId || !filename) {
    throw new Error(`Invalid highlighter example path: ${path}`);
  }

  return {
    id: `${languageId}/${filename}`,
    languageId,
    filename,
    documentKind: documentKindFor(filename, languageId),
    source,
  };
}

export const highlighterExamples: readonly HighlighterExample[] = Object.entries(sources)
  .sort(([left], [right]) => left.localeCompare(right))
  .map(([path, source]) => createExample(path, source));

export const highlighterLanguages: readonly HighlighterLanguage[] = Array.from(
  new Set(highlighterExamples.map((example) => example.languageId)),
)
  .sort((left, right) => {
    if (left === "typescript") return -1;
    if (right === "typescript") return 1;
    return left.localeCompare(right);
  })
  .map((id) => ({
    id,
    label: LANGUAGE_METADATA[id]?.label ?? formatLanguageLabel(id),
    icon: LANGUAGE_METADATA[id]?.icon,
  }));

export function examplesForLanguage(languageId: string): readonly HighlighterExample[] {
  return highlighterExamples.filter((example) => example.languageId === languageId);
}
