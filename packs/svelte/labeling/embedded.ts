import type { HighlightResult, SemanticSpan } from "@nsh/core";
import * as ts from "typescript";

import { labelCss } from "../../css/labeling/label.js";
import { labelTypeScript } from "../../typescript/labeling/label.js";
import { EXPRESSION_PREFIX, EXPRESSION_SUFFIX } from "../runtime/composite.js";

function scriptReference(content: string, kind: string) {
  const base = labelTypeScript({ source: content, documentKind: kind });
  const scriptKind =
    kind === "tsx"
      ? ts.ScriptKind.TSX
      : kind === "jsx"
        ? ts.ScriptKind.JSX
        : kind === "javascript"
          ? ts.ScriptKind.JS
          : ts.ScriptKind.TS;
  const file = ts.createSourceFile("reference", content, ts.ScriptTarget.Latest, true, scriptKind);
  const spans = [...base.spans],
    neutral: [number, number][] = [];
  const punctuation = new Set([
    ts.SyntaxKind.OpenBraceToken,
    ts.SyntaxKind.CloseBraceToken,
    ts.SyntaxKind.OpenParenToken,
    ts.SyntaxKind.CloseParenToken,
    ts.SyntaxKind.OpenBracketToken,
    ts.SyntaxKind.CloseBracketToken,
    ts.SyntaxKind.DotToken,
    ts.SyntaxKind.CommaToken,
    ts.SyntaxKind.SemicolonToken,
    ts.SyntaxKind.ColonToken,
    ts.SyntaxKind.QuestionToken,
    ts.SyntaxKind.AtToken,
  ]);
  const visit = (node: ts.Node) => {
    if (ts.isJsxText(node)) {
      neutral.push([node.pos, node.end]);
      return;
    }
    const children = node.getChildren(file);
    if (children.length) {
      for (const child of children) visit(child);
      return;
    }
    if (node.kind < ts.SyntaxKind.FirstPunctuation || node.kind > ts.SyntaxKind.LastPunctuation)
      return;
    const start = node.getStart(file),
      end = node.end;
    if (start >= end || spans.some((span) => span.start < end && span.end > start)) return;
    // Fill only official compiler punctuation leaves, never guessed identifiers.
    spans.push({ start, end, tokenType: punctuation.has(node.kind) ? "punctuation" : "operator" });
  };
  visit(file);
  spans.sort((a, b) => a.start - b.start);
  const neutralGap = (a: number, b: number) => {
    for (let index = a; index < b; index++)
      if (content[index]!.trim() && !neutral.some(([lo, hi]) => lo <= index && index < hi))
        return false;
    return true;
  };
  return { result: { ...base, spans }, neutralGap };
}

/** Independent offline reference composition; never supplies inference regions. */
export function composeSvelteGold(source: string, base: HighlightResult): HighlightResult {
  const spans: SemanticSpan[] = [];
  for (const span of base.spans) {
    const language = span.tokenType.slice("embedded-".length);
    if (!span.tokenType.startsWith("embedded-") || language === "data") {
      spans.push(span);
      continue;
    }
    const expression = language === "expression";
    const prefix = expression ? EXPRESSION_PREFIX : "",
      suffix = expression ? EXPRESSION_SUFFIX : "";
    const raw = source.slice(span.start, span.end),
      content = prefix + raw + suffix;
    const kind = expression ? "typescript" : language;
    const css = ["css", "scss", "less"].includes(kind);
    if (!css) {
      const extension = kind === "javascript" ? "js" : kind === "typescript" ? "ts" : kind;
      const diagnostics =
        ts.transpileModule(content, {
          fileName: "embedded." + extension,
          reportDiagnostics: true,
          compilerOptions: {
            target: ts.ScriptTarget.ES2022,
            module: ts.ModuleKind.ESNext,
            jsx: ts.JsxEmit.Preserve,
          },
        }).diagnostics ?? [];
      if (diagnostics.some((d) => d.category === ts.DiagnosticCategory.Error))
        throw new Error("Unsupported embedded Svelte reference syntax");
    }
    const script = css ? undefined : scriptReference(content, kind);
    const result = css ? labelCss({ source: content, documentKind: kind }) : script!.result;
    const permittedGap = (a: number, b: number) =>
      !content.slice(a, b).trim() || Boolean(script?.neutralGap(a, b));
    let end = 0;
    for (const item of result.spans) {
      if (item.start < end || !permittedGap(end, item.start) || item.end > content.length)
        throw new Error("Incomplete or overlapping Svelte child Gold");
      end = item.end;
      const a = Math.max(item.start, prefix.length),
        b = Math.min(item.end, prefix.length + raw.length);
      if (a < b)
        spans.push({
          ...item,
          start: span.start + a - prefix.length,
          end: span.start + b - prefix.length,
        });
    }
    if (!permittedGap(end, content.length))
      throw new Error("Unlabeled Svelte child reference tail");
  }
  return { offsetEncoding: "utf-16", spans };
}
