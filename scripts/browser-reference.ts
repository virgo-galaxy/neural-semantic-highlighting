import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  type HighlightRequest,
  normalizeLanguageId,
  type PackManifest,
  type SemanticPack,
} from "@nsh/core";
import { createCompositeHtmlPack } from "@nsh/core/composition/html";
import { createCompositeMarkdownPack } from "@nsh/core/composition/markdown";
import { createCompositePhpPack } from "@nsh/core/composition/php";
import { createCompositeSveltePack } from "@nsh/core/composition/svelte";
import { createCompositeVuePack } from "@nsh/core/composition/vue";
import { createLocalProcessPack, type LocalProcessPack } from "@nsh/local";

const root = process.cwd();
const ids = [
  "typescript",
  "go",
  "css",
  "html",
  "vue",
  "python",
  "bash",
  "perl",
  "awk",
  "sql",
  "powershell",
  "bat",
  "assembly",
  "java",
  "csharp",
  "c",
  "cpp",
  "php",
  "svelte",
  "rust",
  "zig",
  "dart",
  "swift",
  "kotlin",
  "r",
  "scala",
  "ruby",
  "lua",
  "json",
  "yaml",
  "toml",
  "ini",
  "dotenv",
  "xml",
  "markdown",
  "dockerfile",
  "makefile",
];
const manifests = ids.map(
  (id) => JSON.parse(readFileSync(`packs/${id}/manifest.json`, "utf8")) as PackManifest,
);
const models = new Map<string, LocalProcessPack>();
const packs = new Map<string, SemanticPack>();
function getPack(kind: string): SemanticPack {
  const manifest = manifests.find((item) => item.documentKinds.some((entry) => entry.id === kind));
  if (!manifest) throw new Error(`Unsupported reference kind: ${kind}`);
  const cached = packs.get(manifest.id);
  if (cached) return cached;
  const base = createLocalProcessPack({
    manifest,
    command: resolve(root, ".venv/bin/python"),
    args: ["-m", "training.browser.reference_provider", "--pack", manifest.id],
    cwd: root,
    env: { PYTHONPATH: resolve(root, "artifacts/tools/browser-export") + ":" + root },
  });
  models.set(manifest.id, base);
  const highlightEmbedded = (request: HighlightRequest) =>
    getPack(request.documentKind).highlight(request);
  const pack =
    manifest.id === "markdown"
      ? createCompositeMarkdownPack({
          base,
          highlightEmbedded,
          resolveLanguage: (name) => {
            const kind = normalizeLanguageId(name);
            return kind !== "markdown" &&
              manifests.some((m) => m.documentKinds.some((k) => k.id === kind))
              ? kind
              : undefined;
          },
        })
      : manifest.id === "php"
        ? createCompositePhpPack({ base, highlightEmbedded })
        : manifest.id === "html"
          ? createCompositeHtmlPack({ base, highlightEmbedded })
          : manifest.id === "vue"
            ? createCompositeVuePack({ base, highlightEmbedded })
            : manifest.id === "svelte"
              ? createCompositeSveltePack({ base, highlightEmbedded })
              : base;
  packs.set(manifest.id, pack);
  return pack;
}
const suffixes = manifests
  .flatMap((manifest) =>
    manifest.documentKinds.flatMap((kind) =>
      kind.extensions.map((extension) => ({ extension, kind: kind.id })),
    ),
  )
  .sort((a, b) => b.extension.length - a.extension.length);
const cases = [];
const folder = resolve(root, "apps/playground/src/views/highlighter/examples");
async function appendExamples(directory: string) {
  for (const filename of readdirSync(resolve(folder, directory))) {
    const source = readFileSync(resolve(folder, directory, filename), "utf8");
    const kind =
      directory === "jsonc"
        ? "jsonc"
        : directory === "dockerfile"
          ? "dockerfile"
          : suffixes.find((item) => filename.endsWith(item.extension))?.kind;
    if (!kind) throw new Error(`Unknown example suffix: ${filename}`);
    const result = await getPack(kind).highlight({ source, documentKind: kind });
    cases.push({ filename: directory + "/" + filename, source, documentKind: kind, result });
  }
  await Promise.all([...models.values()].map((model) => model.close()));
  models.clear();
  packs.clear();
}
for (const entry of readdirSync(folder, { withFileTypes: true }).filter(
  (entry) => entry.isDirectory() && entry.name !== "dockerfile" && entry.name !== "makefile",
)) {
  await appendExamples(entry.name);
}
for (const source of [
  "",
  "\r\n",
  'const title = "星空 🌌";\r\nconsole.log(title);\r\n',
  'const message = "🌌";\n'.repeat(90) + "export const end = 42;\n",
]) {
  cases.push({
    filename: "edge/" + cases.length + ".ts",
    source,
    documentKind: "typescript",
    result: await getPack("typescript").highlight({ source, documentKind: "typescript" }),
  });
}
for (const [index, source] of [
  "",
  "\r\n",
  '// 星空 🌌\r\nlet title = "Swift"\r\n',
  'let text = """\n' + "Original 🌌 message. ".repeat(160) + '\n"""\n',
].entries()) {
  cases.push({
    filename: `edge/swift-${index}.swift`,
    source,
    documentKind: "swift",
    result: await getPack("swift").highlight({ source, documentKind: "swift" }),
  });
}
for (const [index, source] of [
  "",
  "\r\n",
  '// 星空 🌌\r\nval title = "Kotlin"\r\n',
  'val text = """\n' + "Original 🌌 message. ".repeat(160) + '\n"""\n',
].entries()) {
  cases.push({
    filename: `edge/kotlin-${index}.kt`,
    source,
    documentKind: "kotlin",
    result: await getPack("kotlin").highlight({ source, documentKind: "kotlin" }),
  });
}
for (const [index, source] of [
  "",
  "\r\n",
  '# 星空 🌌\r\nname <- "R"\r\n',
  'text <- r"---[\n' + "Original 🌌 message. ".repeat(160) + '\n]---"\n',
].entries()) {
  cases.push({
    filename: `edge/r-${index}.R`,
    source,
    documentKind: "r",
    result: await getPack("r").highlight({ source, documentKind: "r" }),
  });
}
for (const [index, source] of [
  "",
  "\r\n",
  '// 星空 🌌\r\nval title = "Scala"\r\n',
  'val text = """\n' + "Original 🌌 message. ".repeat(160) + '\n"""\n',
].entries()) {
  cases.push({
    filename: `edge/scala-${index}.scala`,
    source,
    documentKind: "scala",
    result: await getPack("scala").highlight({ source, documentKind: "scala" }),
  });
}
for (const [index, source] of [
  "",
  "\r\n",
  '# 星空 🌌\r\nname = "Ruby"\r\n',
  "text = <<~CONTENT\n" + "Original 🌌 message. ".repeat(160) + "\nCONTENT\n",
].entries()) {
  cases.push({
    filename: `edge/ruby-${index}.rb`,
    source,
    documentKind: "ruby",
    result: await getPack("ruby").highlight({ source, documentKind: "ruby" }),
  });
}
for (const [index, source] of [
  "",
  "\r\n",
  '-- 星空 🌌\r\nlocal title = "Lua"\r\n',
  "local text = [==[\n" + "Original 🌌 message. ".repeat(160) + "\n]==]\n",
].entries()) {
  cases.push({
    filename: `edge/lua-${index}.lua`,
    source,
    documentKind: "lua",
    result: await getPack("lua").highlight({ source, documentKind: "lua" }),
  });
}
for (const kind of ["json", "jsonc"]) {
  const probes = [
    "",
    "\r\n",
    '{"title":"星空 🌌","active":true}\r\n',
    '{"text":"' + "Original 🌌 data with [] {} : , // literal. ".repeat(90) + '","done":true}\n',
  ];
  if (kind === "jsonc") {
    probes[2] = '// 星空 🌌\r\n{"active":true,}\r\n';
    probes[3] =
      "/* " + "Original 🌌 comment with {} and quotes. ".repeat(90) + ' */\n{"done":true,}\n';
  }
  for (const [index, source] of probes.entries())
    cases.push({
      filename: `edge/${kind}-${index}.${kind}`,
      source,
      documentKind: kind,
      result: await getPack(kind).highlight({ source, documentKind: kind }),
    });
}
for (const [index, source] of [
  "",
  "\r\n",
  '# 星空 🌌\r\nname: "YAML"\r\nready: true\r\n',
  "content: |-\n" +
    "  Original 🌌 literal with # markers, {braces} and quotes.\n".repeat(80) +
    "ready: true\n",
].entries())
  cases.push({
    filename: `edge/yaml-${index}.yaml`,
    source,
    documentKind: "yaml",
    result: await getPack("yaml").highlight({ source, documentKind: "yaml" }),
  });
for (const [index, source] of [
  "",
  "\r\n",
  '# 星空 🌌\r\nname="TOML"\r\nready=true\r\n',
  'text="""\n' +
    "Original 🌌 literal with # markers, {braces} and quotes.\n".repeat(80) +
    '"""\nready=true\n',
].entries())
  cases.push({
    filename: `edge/toml-${index}.toml`,
    source,
    documentKind: "toml",
    result: await getPack("toml").highlight({ source, documentKind: "toml" }),
  });
for (const [index, source] of [
  "",
  "\r\n",
  "\ufeff# 星空 🌌\r\n[设置]\r\n标题=星空\r\nready=true\r\n",
  "[article]\nbody=first line\n" +
    "  Original 🌌 continuation with # markers, {braces} and quotes.\n".repeat(80) +
    "ready=true\n",
].entries())
  cases.push({
    filename: `edge/ini-${index}.ini`,
    source,
    documentKind: "ini",
    result: await getPack("ini").highlight({ source, documentKind: "ini" }),
  });
for (const [index, source] of [
  "",
  "\r\n",
  '\ufeff# 星空 🌌\r\nTITLE="星空 🌌"\r\nexport READY=true\r\n',
  'TEXT="first line\n' +
    "  Original 🌌 value with # markers, {braces} and quotes.\n".repeat(80) +
    'last line"\nREADY=true\n',
].entries())
  cases.push({
    filename: `edge/dotenv-${index}.env`,
    source,
    documentKind: "dotenv",
    result: await getPack("dotenv").highlight({ source, documentKind: "dotenv" }),
  });
for (const kind of ["xml", "svg"]) {
  const rootName = kind === "svg" ? "svg" : "document";
  const probes = [
    "",
    "\r\n",
    "\ufeff<" + rootName + ' title="星空 🌌">原文 &amp; text</' + rootName + ">\r\n",
    "<" +
      rootName +
      ' data-long="' +
      "Original 🌌 value &amp; source. ".repeat(90) +
      '"><![CDATA[' +
      "Original 🌌 CDATA <tag/> & data. ".repeat(90) +
      "]]></" +
      rootName +
      ">\n",
  ];
  for (const [index, source] of probes.entries())
    cases.push({
      filename: `edge/${kind}-${index}.${kind}`,
      source,
      documentKind: kind,
      result: await getPack(kind).highlight({ source, documentKind: kind }),
    });
}
for (const [index, source] of [
  "",
  "\r\n",
  "\ufeff# 星空 🌌\r\n\r\n原文 **粗体** and `code`\r\n",
  "# Long original source\n\n" +
    "Original 🌌 prose with ordinary words. ".repeat(70) +
    "\n\n```unknown-example\n" +
    "Original 🌌 body with [] {} and markers. ".repeat(90) +
    "\n```\n",
].entries()) {
  cases.push({
    filename: `edge/markdown-${index}.md`,
    source,
    documentKind: "markdown",
    result: await getPack("markdown").highlight({ source, documentKind: "markdown" }),
  });
}
await appendExamples("dockerfile");
for (const [index, source] of [
  "",
  "\r\n",
  '\ufeff# 星空 🌌\r\nFROM alpine:3\r\nENV TITLE="你好 🌌"\r\n',
  "FROM alpine:3\nCOPY <<'TEXT' /tmp/source\n" +
    "Original 🌌 source with FROM and RUN words. ".repeat(80) +
    '\nTEXT\nCMD ["cat","/tmp/source"]\n',
].entries()) {
  cases.push({
    filename: `edge/dockerfile-${index}.dockerfile`,
    source,
    documentKind: "dockerfile",
    result: await getPack("dockerfile").highlight({ source, documentKind: "dockerfile" }),
  });
}
{
  const source = "# Container source\n\n```dockerfile\nFROM alpine:3\nRUN echo ready\n```\n";
  cases.push({
    filename: "edge/markdown-dockerfile.md",
    source,
    documentKind: "markdown",
    result: await getPack("markdown").highlight({ source, documentKind: "markdown" }),
  });
}
await appendExamples("makefile");
for (const [index, source] of [
  "",
  "\r\n",
  '\ufeff# 原文 🌌\r\nTITLE = "<script>source only</script> 🌌"\r\nall:\r\n\t@echo "$$HOME $(TITLE)"',
  "define MESSAGE\n" +
    "Original 🌌 body with make targets and $(VALUE). ".repeat(80) +
    "\nendef\nall:\n\t@echo ready\n",
].entries()) {
  cases.push({
    filename: `edge/makefile-${index}.mk`,
    source,
    documentKind: "makefile",
    result: await getPack("makefile").highlight({ source, documentKind: "makefile" }),
  });
}
{
  const source = "# Build source\n\n```makefile\nCC ?= cc\nall:\n\t@echo ready\n```\n";
  cases.push({
    filename: "edge/markdown-makefile.md",
    source,
    documentKind: "markdown",
    result: await getPack("markdown").highlight({ source, documentKind: "markdown" }),
  });
}
await Promise.all([...models.values()].map((model) => model.close()));
if (new Set(cases.map((item) => item.filename)).size !== cases.length) {
  throw new Error("Native-reference filenames must be unique");
}
writeFileSync(
  "artifacts/browser/reference.json",
  JSON.stringify({ reference: "selected PyTorch CPU + existing composition", cases }, null, 2) +
    "\n",
);
console.log(cases.length, "native-reference cases");
