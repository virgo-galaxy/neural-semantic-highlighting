import { contentTypes, documentKindForFilename, getContentType } from "@nsh/highlighter/catalog";

import assemblyIcon from "@/assets/document-kinds/assembly.svg";
import awkIcon from "@/assets/document-kinds/awk.svg";
import bashIcon from "@/assets/document-kinds/bash.svg";
import batIcon from "@/assets/document-kinds/bat.svg";
import cIcon from "@/assets/document-kinds/c.svg";
import cppIcon from "@/assets/document-kinds/cpp.svg";
import csharpIcon from "@/assets/document-kinds/csharp.svg";
import cssIcon from "@/assets/document-kinds/css.svg";
import dartIcon from "@/assets/document-kinds/dart.svg";
import diffIcon from "@/assets/document-kinds/diff.svg";
import dockerIcon from "@/assets/document-kinds/docker.svg";
import dotenvIcon from "@/assets/document-kinds/dotenv.svg";
import flutterIcon from "@/assets/document-kinds/flutter.svg";
import goIcon from "@/assets/document-kinds/go.svg";
import graphqlIcon from "@/assets/document-kinds/graphql.svg";
import htmlIcon from "@/assets/document-kinds/html.svg";
import iniIcon from "@/assets/document-kinds/ini.svg";
import javaIcon from "@/assets/document-kinds/java.svg";
import javascriptIcon from "@/assets/document-kinds/javascript.svg";
import jsonIcon from "@/assets/document-kinds/json.svg";
import kotlinIcon from "@/assets/document-kinds/kotlin.svg";
import lessIcon from "@/assets/document-kinds/less.svg";
import luaIcon from "@/assets/document-kinds/lua.svg";
import makefileIcon from "@/assets/document-kinds/makefile.svg";
import markdownIcon from "@/assets/document-kinds/markdown.svg";
import perlIcon from "@/assets/document-kinds/perl.svg";
import phpIcon from "@/assets/document-kinds/php.svg";
import powershellIcon from "@/assets/document-kinds/powershell.svg";
import protobufIcon from "@/assets/document-kinds/protobuf.svg";
import pythonIcon from "@/assets/document-kinds/python.svg";
import rIcon from "@/assets/document-kinds/r.svg";
import rubyIcon from "@/assets/document-kinds/ruby.svg";
import rustIcon from "@/assets/document-kinds/rust.svg";
import scalaIcon from "@/assets/document-kinds/scala.svg";
import scssIcon from "@/assets/document-kinds/scss.svg";
import sqlIcon from "@/assets/document-kinds/sql.svg";
import svelteIcon from "@/assets/document-kinds/svelte.svg";
import svgIcon from "@/assets/document-kinds/svg.svg";
import swiftIcon from "@/assets/document-kinds/swift.svg";
import tomlIcon from "@/assets/document-kinds/toml.svg";
import typescriptIcon from "@/assets/document-kinds/typescript.svg";
import vueIcon from "@/assets/document-kinds/vue.svg";
import xmlIcon from "@/assets/document-kinds/xml.svg";
import yamlIcon from "@/assets/document-kinds/yaml.svg";
import zigIcon from "@/assets/document-kinds/zig.svg";
import type {
  HighlighterContentType,
  HighlighterExample,
} from "@/views/highlighter/examples/types";

const icons: Readonly<Record<string, string>> = {
  typescript: typescriptIcon,
  javascript: javascriptIcon,
  go: goIcon,
  css: cssIcon,
  scss: scssIcon,
  less: lessIcon,
  html: htmlIcon,
  vue: vueIcon,
  python: pythonIcon,
  bash: bashIcon,
  perl: perlIcon,
  awk: awkIcon,
  sql: sqlIcon,
  powershell: powershellIcon,
  bat: batIcon,
  assembly: assemblyIcon,
  java: javaIcon,
  csharp: csharpIcon,
  c: cIcon,
  cpp: cppIcon,
  php: phpIcon,
  svelte: svelteIcon,
  rust: rustIcon,
  zig: zigIcon,
  dart: dartIcon,
  flutter: flutterIcon,
  swift: swiftIcon,
  kotlin: kotlinIcon,
  r: rIcon,
  scala: scalaIcon,
  ruby: rubyIcon,
  lua: luaIcon,
  json: jsonIcon,
  jsonc: jsonIcon,
  yaml: yamlIcon,
  toml: tomlIcon,
  ini: iniIcon,
  dotenv: dotenvIcon,
  xml: xmlIcon,
  svg: svgIcon,
  markdown: markdownIcon,
  dockerfile: dockerIcon,
  makefile: makefileIcon,
  graphql: graphqlIcon,
  protobuf: protobufIcon,
  diff: diffIcon,
  jsx: javascriptIcon,
  tsx: typescriptIcon,
};

const sources = import.meta.glob(["./code/*/*", "./formats/*/*", "./formats/ini/.editorconfig"], {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

function createExample(path: string, source: string): HighlighterExample {
  const match = /^\.\/(code|formats)\/([^/]+)\/([^/]+)$/u.exec(path);
  if (!match) throw new Error(`Invalid highlighter example path: ${path}`);
  const [, category, contentTypeId, filename] = match;
  const entry = getContentType(contentTypeId);
  if (!entry || entry.id !== contentTypeId || entry.category !== category)
    throw new Error(`Example category does not match catalog: ${path}`);
  return {
    // Keep stable IDs so moving examples does not change reference/selection identity.
    id: `${contentTypeId}/${filename}`,
    contentTypeId,
    filename,
    documentKind: documentKindForFilename(filename, contentTypeId)!,
    source,
  };
}

export const highlighterExamples: readonly HighlighterExample[] = Object.entries(sources)
  .sort(([left], [right]) => left.localeCompare(right))
  .map(([path, source]) => createExample(path, source));

const availableIds = new Set(highlighterExamples.map((example) => example.contentTypeId));

export const highlighterContentTypes: readonly HighlighterContentType[] = contentTypes
  .filter((entry) => availableIds.has(entry.id))
  .map((entry) => ({
    id: entry.id,
    label: entry.label,
    category: entry.category,
    icon: icons[entry.id],
  }));

export function examplesForContentType(contentTypeId: string): readonly HighlighterExample[] {
  return highlighterExamples.filter((example) => example.contentTypeId === contentTypeId);
}
