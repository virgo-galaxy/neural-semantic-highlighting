import type { HighlightResult, SemanticSpan } from "@nsh/core";
import * as ts from "typescript";

import { labelCss } from "../../css/labeling/label.js";
import { labelTypeScript } from "../../typescript/labeling/label.js";
import { EXPRESSION_PREFIX, EXPRESSION_SUFFIX } from "../runtime/composite.js";
import type { VueGold } from "./label.js";

/** Independent offline reference composition; never supplies inference regions. */
export function composeVueGold(source: string, base: VueGold): HighlightResult {
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
        throw new Error("Unsupported embedded Vue reference syntax");
    }
    const result = css
      ? labelCss({ source: content, documentKind: kind })
      : labelTypeScript({ source: content, documentKind: kind });
    let end = 0;
    for (const item of result.spans) {
      if (item.start < end || content.slice(end, item.start).trim() || item.end > content.length)
        throw new Error("Incomplete or overlapping Vue child Gold");
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
    if (content.slice(end).trim()) throw new Error("Unlabeled Vue child reference tail");
  }
  return { offsetEncoding: "utf-16", spans };
}
