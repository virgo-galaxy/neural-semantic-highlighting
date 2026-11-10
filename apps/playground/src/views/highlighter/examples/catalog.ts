import assemblyIcon from "@/assets/document-kinds/assembly.svg";
import awkIcon from "@/assets/document-kinds/awk.svg";
import bashIcon from "@/assets/document-kinds/bash.svg";
import batIcon from "@/assets/document-kinds/bat.svg";
import cIcon from "@/assets/document-kinds/c.svg";
import cppIcon from "@/assets/document-kinds/cpp.svg";
import csharpIcon from "@/assets/document-kinds/csharp.svg";
import cssIcon from "@/assets/document-kinds/css.svg";
import goIcon from "@/assets/document-kinds/go.svg";
import htmlIcon from "@/assets/document-kinds/html.svg";
import javaIcon from "@/assets/document-kinds/java.svg";
import javascriptIcon from "@/assets/document-kinds/javascript.svg";
import lessIcon from "@/assets/document-kinds/less.svg";
import perlIcon from "@/assets/document-kinds/perl.svg";
import phpIcon from "@/assets/document-kinds/php.svg";
import powershellIcon from "@/assets/document-kinds/powershell.svg";
import pythonIcon from "@/assets/document-kinds/python.svg";
import scssIcon from "@/assets/document-kinds/scss.svg";
import sqlIcon from "@/assets/document-kinds/sql.svg";
import svelteIcon from "@/assets/document-kinds/svelte.svg";
import typescriptIcon from "@/assets/document-kinds/typescript.svg";
import vueIcon from "@/assets/document-kinds/vue.svg";
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
  vue: {
    label: "Vue",
    icon: vueIcon,
  },
  python: {
    label: "Python",
    icon: pythonIcon,
  },
  bash: {
    label: "Shell",
    icon: bashIcon,
  },
  perl: {
    label: "Perl",
    icon: perlIcon,
  },
  awk: {
    label: "AWK",
    icon: awkIcon,
  },
  sql: { label: "SQL", icon: sqlIcon },
  powershell: { label: "PowerShell", icon: powershellIcon },
  bat: { label: "BAT / CMD", icon: batIcon },
  assembly: { label: "Assembly", icon: assemblyIcon },
  java: { label: "Java", icon: javaIcon },
  csharp: { label: "C#", icon: csharpIcon },
  c: { label: "C", icon: cIcon },
  cpp: { label: "C++", icon: cppIcon },
  php: { label: "PHP", icon: phpIcon },
  svelte: { label: "Svelte", icon: svelteIcon },
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
  [".vue", "vue"],
  [".py", "python"],
  [".pyw", "python"],
  [".pyi", "python"],
  [".sh", "bash"],
  [".bash", "bash"],
  [".zsh", "bash"],
  [".csh", "bash"],
  [".tcsh", "bash"],
  [".pl", "perl"],
  [".pm", "perl"],
  [".t", "perl"],
  [".perl", "perl"],
  [".awk", "awk"],
  [".gawk", "awk"],
  [".sql", "sql"],
  [".psql", "sql"],
  [".pgsql", "sql"],
  [".plsql", "sql"],
  [".ps1", "powershell"],
  [".psm1", "powershell"],
  [".psd1", "powershell"],
  [".bat", "bat"],
  [".cmd", "bat"],
  [".asm", "assembly"],
  [".ASM", "assembly"],
  [".nasm", "assembly"],
  [".masm", "assembly"],
  [".s", "assembly"],
  [".S", "assembly"],
  [".inc", "assembly"],
  [".java", "java"],
  [".cs", "csharp"],
  [".c", "c"],
  [".h", "c"],
  [".cpp", "cpp"],
  [".cc", "cpp"],
  [".cxx", "cpp"],
  [".c++", "cpp"],
  [".C", "cpp"],
  [".hpp", "cpp"],
  [".hh", "cpp"],
  [".hxx", "cpp"],
  [".h++", "cpp"],
  [".ipp", "cpp"],
  [".tpp", "cpp"],
  [".php", "php"],
  [".phtml", "php"],
  [".svelte", "svelte"],
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
