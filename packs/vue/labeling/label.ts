import type { HighlightRequest, HighlightResult, SemanticSpan } from "@nsh/core";
import { DecodingMode, HtmlEntityDecoder } from "entities/decode";
import { parser as scriptParser } from "typescript-eslint";
import { type AST, parseForESLint } from "vue-eslint-parser";

export const scriptKinds = ["javascript", "typescript", "jsx", "tsx"] as const;
export const styleKinds = ["css", "scss", "less"] as const;
export type VueLanguage =
  (typeof scriptKinds)[number] | (typeof styleKinds)[number] | "data" | "expression";
export interface VueRegion {
  start: number;
  end: number;
  language: VueLanguage;
  context: "block" | "expression";
}
export interface VueGold extends HighlightResult {
  regions: VueRegion[];
  features: string[];
}

/** Offline source-location Gold. No compiler/parser is imported by inference. */
export function labelVue({ source, documentKind }: HighlightRequest): VueGold {
  if (documentKind !== "vue" || source.includes("\0"))
    throw new Error("Expected original Vue SFC source");
  const parsed = parseForESLint(source, {
    sourceType: "module",
    ecmaVersion: "latest",
    range: true,
    loc: true,
    parser: scriptParser,
    ecmaFeatures: { jsx: true },
    vueFeatures: { filter: true, interpolationAsNonHTML: true, styleCSSVariableInjection: false },
  });
  const document = parsed.services?.getDocumentFragment();
  // SFC templates allow self-closing non-void elements/components. The parser
  // also exposes the stricter HTML warning; it is not a Vue syntax failure.
  const errors = [...(document?.errors ?? []), ...(parsed.ast.templateBody?.errors ?? [])].filter(
    (error) => error.code !== "non-void-html-element-start-tag-with-trailing-solidus",
  );
  if (!document || errors.length)
    throw new Error(
      "Vue source has parser errors: " + errors.map((error) => error.message).join("; "),
    );
  const spans: SemanticSpan[] = [],
    regions: VueRegion[] = [];
  const features = new Set<string>();
  const add = (start: number, end: number, tokenType: string, closing = false) => {
    if (start < 0 || end <= start || end > source.length)
      throw new Error("Invalid Vue source range");
    spans.push({ start, end, tokenType, ...(closing ? { modifiers: ["closing"] } : {}) });
  };
  const text = (start: number, end: number) => {
    const raw = source.slice(start, end);
    if (!raw.trim()) return;
    let cursor = 0;
    const decoder = new HtmlEntityDecoder(() => {});
    for (let amp = raw.indexOf("&"); amp >= 0; amp = raw.indexOf("&", amp + 1)) {
      decoder.startEntity(DecodingMode.Legacy);
      let length = decoder.write(raw, amp + 1);
      if (length < 0) length = decoder.end();
      if (length < 1) continue;
      if (cursor < amp) add(start + cursor, start + amp, "text");
      add(start + amp, start + amp + length, "entity");
      features.add("entities");
      cursor = amp + length;
      amp = cursor - 1;
    }
    if (cursor < raw.length) add(start + cursor, end, "text");
  };
  const tag = (node: AST.VStartTag | AST.VEndTag, closing: boolean) => {
    const [start, end] = node.range;
    const prefix = closing ? "</" : "<";
    if (!source.startsWith(prefix, start)) throw new Error("Invalid Vue tag delimiter");
    const name = /^[^\s/>]+/u.exec(source.slice(start + prefix.length, end))?.[0];
    if (!name) throw new Error("Missing Vue tag name");
    add(start, start + prefix.length, "punctuation");
    add(start + prefix.length, start + prefix.length + name.length, "tag", closing);
    if (node.type === "VStartTag") {
      for (const attribute of node.attributes) {
        const [lo, hi] = attribute.key.range;
        add(lo, hi, "attribute");
        if (attribute.directive) {
          features.add("directives");
          const raw = source.slice(lo, hi);
          if (/\[.*\]/u.test(raw)) features.add("dynamic-arguments");
          if (/\.sync(?:\.|$)|\.native(?:\.|$)/u.test(raw)) features.add("vue2-directives");
          if (/^(?:#|v-slot)/u.test(raw)) features.add("slots");
          if (/^v-model:/u.test(raw)) features.add("vue3-v-model");
        }
        if (attribute.value) {
          const [a, b] = attribute.value.range;
          const gap = source.slice(hi, a),
            equals = gap.indexOf("=");
          if (equals < 0 || gap.slice(0, equals).trim() || gap.slice(equals + 1).trim())
            throw new Error("Invalid Vue attribute association");
          add(hi + equals, hi + equals + 1, "punctuation");
          add(a, b, "string");
        }
      }
    }
    const delimiter = !closing && source.slice(start, end).endsWith("/>") ? "/>" : ">";
    if (!source.slice(start, end).endsWith(delimiter)) throw new Error("Unterminated Vue tag");
    add(end - delimiter.length, end, "punctuation");
  };
  const attribute = (node: AST.VElement, name: string) =>
    node.startTag.attributes.find(
      (a): a is AST.VAttribute => !a.directive && a.key.name.toLowerCase() === name,
    );
  const region = (
    start: number,
    end: number,
    language: VueLanguage,
    context: VueRegion["context"] = "block",
  ) => {
    if (end <= start) return;
    add(start, end, "embedded-" + language);
    regions.push({ start, end, language, context });
    features.add("embedded-" + language);
  };
  const visit = (node: AST.VElement | AST.VText | AST.VExpressionContainer, root = false) => {
    if (node.type === "VText") {
      text(...node.range);
      return;
    }
    if (node.type === "VExpressionContainer") {
      const [a, b] = node.range;
      if (!source.startsWith("{{", a) || source.slice(b - 2, b) !== "}}")
        throw new Error("Unknown Vue interpolation delimiters");
      add(a, a + 2, "punctuation");
      region(a + 2, b - 2, "expression", "expression");
      add(b - 2, b, "punctuation");
      if (node.expression?.type === "VFilterSequenceExpression") features.add("filter-pipes");
      return;
    }
    tag(node.startTag, false);
    const lang = attribute(node, "lang")?.value?.value.toLowerCase() ?? "";
    const name = node.name.toLowerCase();
    const opaque =
      name === "script" ||
      name === "style" ||
      (root && name !== "template") ||
      (root && lang && lang !== "html");
    if (opaque && !node.startTag.selfClosing) {
      if (!node.endTag) throw new Error("Unclosed Vue block");
      const aliases: Record<string, VueLanguage> =
        name === "script"
          ? {
              "": "javascript",
              js: "javascript",
              javascript: "javascript",
              ts: "typescript",
              typescript: "typescript",
              jsx: "jsx",
              tsx: "tsx",
            }
          : name === "style"
            ? { "": "css", css: "css", scss: "scss", less: "less" }
            : {};
      region(node.startTag.range[1], node.endTag.range[0], aliases[lang] ?? "data");
      if (attribute(node, "setup")) features.add("script-setup");
      if (attribute(node, "scoped")) features.add("scoped-style");
      if (attribute(node, "module")) features.add("module-style");
    } else for (const child of node.children) visit(child);
    if (node.endTag) tag(node.endTag, true);
  };
  for (const child of document.children) visit(child, true);
  for (const comment of document.comments) {
    const [a, b] = comment.range;
    if (regions.some((r) => a >= r.start && b <= r.end)) continue;
    if (!source.startsWith("<!--", a) || source.slice(b - 3, b) !== "-->")
      throw new Error("Malformed Vue comment");
    add(a, b, "comment");
  }
  spans.sort((a, b) => a.start - b.start);
  regions.sort((a, b) => a.start - b.start);
  let end = 0;
  for (const span of spans) {
    if (span.start < end || source.slice(end, span.start).trim())
      throw new Error("Incomplete Vue Gold at " + end);
    end = span.end;
  }
  if (source.slice(end).trim()) throw new Error("Incomplete Vue Gold suffix");
  if (source.includes("\r\n")) features.add("crlf");
  return { offsetEncoding: "utf-16", spans, regions, features: [...features].sort() };
}
