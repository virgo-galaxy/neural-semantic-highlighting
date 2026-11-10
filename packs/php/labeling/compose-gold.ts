/** Offline PHP template diagnostics; no consumer runtime imports this module. */
import type { HighlightResult, SemanticSpan } from "@nsh/core";

import { composeHtmlGold } from "../../html/labeling/embedded.js";
import { labelHtml } from "../../html/labeling/label.js";

export async function composePhpGold(
  source: string,
  base: HighlightResult,
): Promise<HighlightResult> {
  const spans: SemanticSpan[] = [];
  for (const span of base.spans) {
    if (span.tokenType !== "embedded-html") {
      spans.push(span);
      continue;
    }
    const raw = source.slice(span.start, span.end);
    const htmlGold = await labelHtml({ source: raw, documentKind: "html" });
    const child = composeHtmlGold(raw, htmlGold);
    for (const token of child.spans) {
      const region = htmlGold.regions.find(
        (item) => token.start >= item.start && token.end <= item.end,
      );
      const documentKind =
        region?.language === "css" || region?.language === "javascript" ? region.language : "html";
      spans.push({
        ...token,
        start: span.start + token.start,
        end: span.start + token.end,
        documentKind: token.documentKind ?? documentKind,
      });
    }
  }
  return { offsetEncoding: "utf-16", spans };
}
