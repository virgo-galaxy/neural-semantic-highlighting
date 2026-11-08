import type { HighlightResult, SemanticSpan } from "@nsh/core";
import * as ts from "typescript";

import { labelCss } from "../../css/labeling/label.js";
import { labelTypeScript } from "../../typescript/labeling/label.js";
import type { HtmlGold } from "./label.js";

/** Offline evaluation reference; never used to choose inference regions. */
export function composeHtmlGold(source: string, base: HtmlGold): HighlightResult {
  const spans: SemanticSpan[] = [];
  for (const span of base.spans) {
    const css = span.tokenType === "embedded-css";
    const javascript = span.tokenType === "embedded-javascript";
    if (!css && !javascript) {
      spans.push(span);
      continue;
    }
    const content = source.slice(span.start, span.end);
    if (javascript) {
      const diagnostics =
        ts.transpileModule(content, {
          fileName: "embedded.js",
          reportDiagnostics: true,
          compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
        }).diagnostics ?? [];
      if (diagnostics.some((item) => item.category === ts.DiagnosticCategory.Error))
        throw new Error("Embedded JavaScript syntax has no complete evaluation Gold");
    }
    const child = css
      ? labelCss({ source: content, documentKind: "css" })
      : labelTypeScript({ source: content, documentKind: "javascript" });
    if (child.offsetEncoding !== "utf-16")
      throw new Error("Embedded Gold must use original UTF-16 positions");
    let end = 0;
    for (const item of child.spans) {
      if (item.start < end || content.slice(end, item.start).trim() || item.end > content.length)
        throw new Error("Incomplete or overlapping embedded Gold");
      spans.push({ ...item, start: span.start + item.start, end: span.start + item.end });
      end = item.end;
    }
    if (content.slice(end).trim()) throw new Error("Unlabeled embedded Gold tail");
  }
  return { offsetEncoding: "utf-16", spans };
}
