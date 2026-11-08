import type { HighlightRequest, HighlightResult, SemanticPack, SemanticSpan } from "@nsh/core";

export interface HtmlCompositionOptions {
  base: SemanticPack;
  highlightEmbedded(request: HighlightRequest): Promise<HighlightResult>;
}

function validate(source: string, result: HighlightResult): void {
  if (result.offsetEncoding !== "utf-16")
    throw new Error("HTML composition requires UTF-16 model offsets");
  const boundaries = new Set<number>([0]);
  let unit = 0;
  for (const character of source) {
    unit += character.length;
    boundaries.add(unit);
  }
  let end = 0;
  for (const span of result.spans) {
    if (
      !Number.isInteger(span.start) ||
      !Number.isInteger(span.end) ||
      span.start < end ||
      span.end <= span.start ||
      !boundaries.has(span.start) ||
      !boundaries.has(span.end)
    ) {
      throw new Error("Invalid or overlapping model spans in HTML composition");
    }
    end = span.end;
  }
}

/** Compose existing neural packs only inside regions predicted by the HTML model.
 * No source parsing, tag scanning, entities decoding, execution or Gold cuts.
 * The callback can use any runtime/transport implementing the existing contract.
 */
export function createCompositeHtmlPack({
  base,
  highlightEmbedded,
}: HtmlCompositionOptions): SemanticPack {
  return {
    manifest: base.manifest,
    async highlight(request) {
      if (request.documentKind !== "html")
        throw new Error("Unsupported HTML document kind: " + request.documentKind);
      const result = await base.highlight(request);
      validate(request.source, result);
      const spans: SemanticSpan[] = [];
      for (const span of result.spans) {
        const documentKind =
          span.tokenType === "embedded-javascript"
            ? "javascript"
            : span.tokenType === "embedded-css"
              ? "css"
              : undefined;
        if (!documentKind) {
          spans.push(span);
          continue;
        }
        const source = request.source.slice(span.start, span.end);
        const child = await highlightEmbedded({ source, documentKind });
        validate(source, child);
        for (const item of child.spans) {
          spans.push({ ...item, start: span.start + item.start, end: span.start + item.end });
        }
      }
      return { offsetEncoding: "utf-16", spans };
    },
  };
}
