import cssIcon from "@/assets/document-kinds/css.svg";
import goIcon from "@/assets/document-kinds/go.svg";
import htmlIcon from "@/assets/document-kinds/html.svg";
import javascriptIcon from "@/assets/document-kinds/javascript.svg";
import lessIcon from "@/assets/document-kinds/less.svg";
import scssIcon from "@/assets/document-kinds/scss.svg";
import typescriptIcon from "@/assets/document-kinds/typescript.svg";
import type { HighlighterExample, HighlighterLanguage } from "@/views/highlighter/examples/types";

const sources = import.meta.glob("./*/*", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

const LANGUAGE_METADATA: Readonly<Record<string, Omit<HighlighterLanguage, "id">>> = {
  typescript: {
    label: "TypeScript",
    icon: typescriptIcon,
  },
  javascript: {
    label: "JavaScript",
    icon: javascriptIcon,
  },
  go: {
    label: "Go",
    icon: goIcon,
  },
  css: {
    label: "CSS",
    icon: cssIcon,
  },
  scss: {
    label: "SCSS",
    icon: scssIcon,
  },
  less: {
    label: "Less",
    icon: lessIcon,
  },
  html: {
    label: "HTML",
    icon: htmlIcon,
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
  [".css", "css"],
  [".scss", "scss"],
  [".less", "less"],
  [".html", "html"],
  [".htm", "html"],
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

const availableLanguageIds = new Set(highlighterExamples.map((example) => example.languageId));
const metadataLanguageIds = new Set(Object.keys(LANGUAGE_METADATA));

export const highlighterLanguages: readonly HighlighterLanguage[] = [
  ...Object.entries(LANGUAGE_METADATA)
    .filter(([id]) => availableLanguageIds.has(id))
    .map(([id, metadata]) => ({
      id,
      ...metadata,
    })),
  ...Array.from(availableLanguageIds)
    .filter((id) => !metadataLanguageIds.has(id))
    .sort((left, right) => left.localeCompare(right))
    .map((id) => ({
      id,
      label: formatLanguageLabel(id),
    })),
];

export function examplesForLanguage(languageId: string): readonly HighlighterExample[] {
  return highlighterExamples.filter((example) => example.languageId === languageId);
}
