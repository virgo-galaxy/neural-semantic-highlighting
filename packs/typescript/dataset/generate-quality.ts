import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import ts from "typescript";

import { labelTypeScript } from "../labeling/label.js";

const contexts: Record<string, (literal: string, n: number) => string> = {
  declaration: (r, n) => `const rule${n} = ${r};\nexport const active${n} = true;`,
  predicate: (r, n) =>
    `export function accepts${n}(input: string) {\n  return ${r}.test(input);\n}`,
  object: (r, n) => `export const policy${n} = { name: "entry", pattern: ${r}, enabled: true };`,
  array: (r, n) => `export const filters${n} = [${r}, /[Q-Z]+/u];`,
  callback: (r, n) =>
    `export const select${n} = (values: string[]) => values.filter(value => ${r}.test(value));`,
  class: (r, n) =>
    `export class Validator${n} { readonly pattern = ${r}; check(value: string) { return this.pattern.test(value); } }`,
  replacement: (r, n) =>
    `export function clean${n}(value: string) { return value.replace(${r}, "_"); }`,
  matching: (r, n) =>
    `export function parts${n}(value: string) { return value.match(${r}) ?? []; }`,
  splitting: (r, n) => `export const split${n} = (value: string) => value.split(${r});`,
  conditional: (r, n) =>
    `export function inspect${n}(value: string) { if (${r}.test(value)) { return value; } return ""; }`,
  grouping: (r, n) => `export const grouped${n} = (${r});\nexport const count${n} = 3;`,
  factory: (r, n) =>
    `export function create${n}() { return { pattern: ${r}, message: "invalid" }; }`,
  argument: (r, n) =>
    `function configure${n}(rule: RegExp) { return rule; }\nexport const configured${n} = configure${n}(${r});`,
  comments: (r, n) =>
    `// A literal boundary next to a real line comment\nexport const checked${n} = ${r}; // retain the following statement\nexport const ready${n} = false;`,
  ternary: (r, n) => `export const choose${n} = (strict: boolean) => strict ? ${r} : /[RST]+/;`,
  jsx: (r, n) =>
    `export function Badge${n}({ value }: { value: string }) { return <span data-valid={${r}.test(value)}>{value}</span>; }`,
  loop: (r, n) =>
    `export function scan${n}(values: string[]) { for (const value of values) { if (${r}.test(value)) return value; } return undefined; }`,
  async: (r, n) =>
    `export async function fetch${n}(value: string) { const rule = ${r}; return Promise.resolve(rule.test(value)); }`,
  computed: (r, n) => `export const rules${n}: Record<string, RegExp> = { ["entry"]: ${r} };`,
  assertion: (r, n) =>
    `export function assert${n}(value: string): asserts value is string { if (!${r}.test(value)) throw new Error("invalid"); }`,
};
Object.assign(contexts, {
  typedLet: (r: string, n: number) => `let matcher${n}: RegExp = ${r};\nexport { matcher${n} };`,
  typedConst: (r: string, n: number) => `export const matcher${n}: RegExp = ${r};`,
  variable: (r: string, n: number) =>
    `var matcher${n} = ${r};\nexport const found${n} = matcher${n}.test("input");`,
  assignment: (r: string, n: number) =>
    `let matcher${n}: RegExp;\nmatcher${n} = ${r};\nexport { matcher${n} };`,
  prefix: (r: string, n: number) => `export const matcher${n} = !${r}.test("input");`,
  destructure: (r: string, n: number) => `export const [matcher${n}] = [${r}];`,
  multiline: (r: string, n: number) => `export const matcher${n}: RegExp =\n  ${r}\n;`,
  bareLet: (r: string, n: number) => `let probe${n}: RegExp = ${r};`,
  bareConst: (r: string, n: number) => `const probe${n} = ${r};`,
  bareVar: (r: string, n: number) => `var probe${n} = ${r};`,
  shortExport: (r: string) => `export default ${r};`,
  shortCallback: (r: string, n: number) => `export const fn${n} = () => ${r};`,
  inline: (r: string, n: number) => `export const matcher${n} = ${r} /* original note */;`,
});
Object.assign(contexts, {
  leadingNote: (r: string, n: number) => `const rule${n} = /* chosen pattern */ ${r};`,
  expressionMap: (r: string, n: number) => `export const view${n} = <code>{${r}.source}</code>;`,
});
const bodies = [
  "[B-H]+",
  "[5-8]{2,5}",
  "\\s{1,3}",
  "\\p{Letter}{2,6}",
  "[^:;]+",
  "(?:north|south)",
  "^entry_[A-Z]+$",
  "[A-F0-9]{4,8}",
  "\\bitem\\b",
  "x(?=yz)",
  "q(?!rs)",
  "(?<part>[A-J]+)",
  "[\\[\\]{}]+",
  "\\/assets\\/",
  "a.*?z",
  "(?:uv){2,4}",
  "[\\t\\r\\n]+",
  "\\d{3}[-:]\\d{2}",
  "[!@#$%]+",
  "[a-z]+(?:_[a-z]+)*",
  "^\\S+@\\S+\\.[a-z]+$",
  "\\\\[nrt]",
  "\\u{1F680}",
  "[\\s\\S]{0,12}",
  "(?<=cedar)leaf",
  "(?<!copper)coin",
  "(ink)\\1",
  "(?<tone>bell)\\k<tone>",
  "(?:uv(w|x)+){1,3}",
  "oak|pine|fir",
  "^cedar$",
  "cedar(?=$|[.:])",
  "\\Bxy\\B",
  "[^\\w\\s]",
  "[a\\-c]",
  "[\\]\\[]",
  "[{}()]",
  "(?:)",
  "(?=ab)ab",
  "(?!zz)[a-z]+",
  "(?:(?<=x)y|z)",
  "^(?<left>[A-F]+):\\k<left>$",
  "([MN])(?:op)\\1",
  "\\x41+",
  "\\0[1-7]",
  "[A-Z]{2,}(?:-[0-9]+)?",
  "(?:ab|cd){2,5}?",
  "[\\p{Letter}&&\\p{ASCII}]",
  "[^/]+\\/[^/]+",
  "a(?<!b)c",
  "[a-z]*?(?=;|$)",
  "(ab)(cd)\\2\\1",
  "(?<word>[a-z]+)-\\k<word>",
  "(?:a|b(?:c|d))+$",
  "(?<=\\d{2})[A-Z]+",
  "[^\\[\\]\\\\]+",
  "[\\-\\^]+",
  "\\u0041+",
];
const digest = (value: string) => createHash("sha256").update(value).digest("hex");
const directory = join(
  process.env.NSH_DATASET_ROOT ?? join(homedir(), "Datasets", "neural-semantic-highlighting"),
  "typescript",
  "quality-regexp-20261119-10",
);
await mkdir(directory, { recursive: true });
const records = [];
const folds: Record<string, string> = {};
for (const [index, [family, render]] of Object.entries(contexts).entries()) {
  const split = ["replacement", "loop", "shortExport"].includes(family)
    ? "validation"
    : ["splitting", "computed", "shortCallback"].includes(family)
      ? "test"
      : "train";
  folds[family] = split;
  for (let variant = 0; variant < 96; variant++) {
    const words =
      split === "train"
        ? ["cedar", "copper", "falcon", "ember"]
        : split === "validation"
          ? ["birch", "silver", "heron", "breeze"]
          : ["spruce", "bronze", "otter", "ripple"];
    const word = words[variant % words.length]!;
    const body =
      variant < 24 && variant % 3 === 0
        ? word
        : variant >= 24 || variant % 3 === 1
          ? bodies[(variant + index * 5) % bodies.length]!
          : word[0]! + ["+", "*", "?", "{3,7}"][Math.floor(variant / 3) % 4]!;
    let flags = ["", "g", "i", "m", "s", "y", "d", "u", "gi", "gm", "su", "giu"][
      (variant + index * 7 + Math.floor(variant / 24) * 5) % 12
    ]!;
    if (body.includes("&&")) flags = "v";
    else if ((body.includes("\\p{") || body.includes("\\u{")) && !flags.includes("u")) flags += "u";
    const n = 1000 + index * 100 + variant;
    const literal = `/${body}/${flags}`;
    const negative = `\nexport const ratio${n} = (48 + ${variant}) / 6 / 2;\nexport const note${n} = "quoted ${literal.replaceAll("\\", "\\\\")}"; // a / b / c is comment text\n`;
    let source = render(literal, n) + (variant % 4 === 0 ? negative : "\n");
    if (variant % 7 === 0) source = source.replaceAll("\n", "\r\n");
    if (variant % 3 === 0) source = source.replace(/;(\s*)$/, "$1");
    if (variant % 2 === 0) source = source.trimEnd();
    const javascriptFamilies = new Set([
      "declaration",
      "object",
      "array",
      "grouping",
      "comments",
      "factory",
    ]);
    const documentKind = ["jsx", "expressionMap"].includes(family)
      ? "tsx"
      : javascriptFamilies.has(family) && variant % 2 === 0
        ? "javascript"
        : "typescript";
    const parsed = ts.createSourceFile(
      "source.tsx",
      source,
      ts.ScriptTarget.Latest,
      true,
      documentKind === "tsx"
        ? ts.ScriptKind.TSX
        : documentKind === "javascript"
          ? ts.ScriptKind.JS
          : ts.ScriptKind.TS,
    );
    const diagnostics = (parsed as ts.SourceFile & { parseDiagnostics: readonly ts.Diagnostic[] })
      .parseDiagnostics;
    if (diagnostics.length) throw new Error(`Invalid authored focus source: ${family}/${variant}`);
    const validateRegex = (node: ts.Node): void => {
      if (ts.isRegularExpressionLiteral(node)) {
        const closing = node.text.lastIndexOf("/");
        // Compile only the authored literal; never match text or execute source.
        new RegExp(node.text.slice(1, closing), node.text.slice(closing + 1));
      }
      ts.forEachChild(node, validateRegex);
    };
    validateRegex(parsed);
    records.push({
      repository: "original-quality-curriculum",
      path: `${family}/${variant}.${documentKind === "tsx" ? "tsx" : documentKind === "javascript" ? "js" : "ts"}`,
      sourceGroup: family,
      split,
      documentKind,
      source,
      contentHash: digest(source),
      result: labelTypeScript({ source, documentKind }),
    });
  }
}
const negatives: Record<string, (n: number) => string> = {
  division: (n) =>
    `const left${n} = 84; const right${n} = 7; export const quotient${n} = left${n} / right${n};`,
  chain: (n) => `export const ratio${n} = (90 + ${n}) / 3 / 5;`,
  compound: (n) => `let amount${n} = 96; amount${n} /= 4; export { amount${n} };`,
  string: (n) => `export const message${n} = "literal /[ABC]+/gi remains text";`,
  template: (n) => "export const message" + n + " = `a / b; /[GH]+/g is template text`;",
  comment: (n) => `// a / b and /[JK]+/u are only comment text\nexport const entry${n} = 1;`,
  blockComment: (n) =>
    `/* /[MN]+/g and path/to/file are only comment text */\nexport const entry${n} = 2;`,
  jsx: (n) => `export const Item${n} = () => <section><span>ready</span></section>;`,
  jsxAttribute: (n) => `export const Item${n} = () => <a href="/docs/intro">Docs</a>;`,
  jsxExpression: (n) =>
    `export const Item${n} = ({ count }: { count: number }) => <span>{count / 2}</span>;`,
  imports: (n) => `import value${n} from "./path/to/module"; export { value${n} };`,
  returnDivision: (n) => `export function calculate${n}(value: number) { return value / 12; }`,
};
Object.assign(negatives, {
  taggedTemplate: (n: number) =>
    `const note${n} = String.raw` + "`quoted /[WY]+/g and path/to/end`" + `; export { note${n} };`,
  markupTemplate: (n: number) =>
    `const note${n} = ` +
    "`<section>ratio = total / width; /[DE]+/u</section>`" +
    `; export { note${n} };`,
  multipleComment: (n: number) =>
    `/* Example literals: /[WX]/u, /[YZ]/gi, /value/. */ const count${n} = 3; export { count${n} };`,
  jsxRatioProp: (n: number) =>
    `export const Item${n} = ({ size }: { size: number }) => <meter value={size / 4} />;`,
  jsxAddressText: (n: number) =>
    `export const Item${n} = () => <small>https://sample.test/guide/start</small>;`,
  bareDivision: (n: number) => `const ratio${n} = total${n} / width${n};`,
  commentTail: (n: number) => `const entry${n} = 4; /* documentation /[AB]/g appears here */`,
});
for (const [index, [family, render]] of Object.entries(negatives).entries()) {
  const split = ["chain", "jsxAttribute"].includes(family)
    ? "validation"
    : ["template", "returnDivision"].includes(family)
      ? "test"
      : "train";
  folds[`negative-${family}`] = split;
  for (let variant = 0; variant < 48; variant++) {
    let source = render(2000 + index * 100 + variant) + "\n";
    if (variant % 3 === 0) source = source.replace(/;(\s*)$/, "$1");
    if (variant % 2 === 0) source = source.trimEnd();
    const documentKind = family.startsWith("jsx") ? "tsx" : "typescript";
    const result = labelTypeScript({ source, documentKind });
    if (result.spans.some((span) => span.tokenType === "regexp"))
      throw new Error("Negative curriculum unexpectedly contains a regexp");
    records.push({
      repository: "original-quality-curriculum",
      path: `negative-${family}/${variant}.${documentKind === "tsx" ? "tsx" : "ts"}`,
      sourceGroup: `negative-${family}`,
      split,
      documentKind,
      source,
      contentHash: digest(source),
      result,
    });
  }
}
const seen = new Map<string, { split: string; sourceGroup: string }>();
const unique = records.filter((record) => {
  const previous = seen.get(record.contentHash);
  if (previous) {
    if (previous.split !== record.split || previous.sourceGroup !== record.sourceGroup)
      throw new Error("Source copy crosses curriculum families");
    return false;
  }
  seen.set(record.contentHash, { split: record.split, sourceGroup: record.sourceGroup });
  return true;
});
const raw = JSON.stringify(unique, null, 2) + "\n";
const output = join(directory, "focus.json");
try {
  if ((await readFile(output, "utf8")) !== raw)
    throw new Error("Preserve original quality curriculum");
} catch (error) {
  if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  await writeFile(output, raw);
}
const protocol = {
  format: "nsh-typescript-quality-focus-v1",
  folds,
  records: unique.length,
  duplicateVariantsRemoved: records.length - unique.length,
  nodeVersion: process.version,
  sha256: digest(raw),
  generatorSha256: digest(await readFile(new URL(import.meta.url), "utf8")),
  teacherSha256: digest(await readFile(new URL("../labeling/label.ts", import.meta.url), "utf8")),
  typescriptVersion: ts.version,
  purpose:
    "Original grammar/context families; no Golden, Playground or challenge source copies; natural replay remains separate",
};
const manifestPath = join(directory, "manifest.json");
const manifestRaw = JSON.stringify(protocol, null, 2) + "\n";
try {
  if ((await readFile(manifestPath, "utf8")) !== manifestRaw)
    throw new Error("Preserve original curriculum manifest");
} catch (error) {
  if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  await writeFile(manifestPath, manifestRaw);
}
console.log(
  JSON.stringify({
    records: unique.length,
    duplicateVariantsRemoved: records.length - unique.length,
    nodeVersion: process.version,
    directory,
    folds,
  }),
);
