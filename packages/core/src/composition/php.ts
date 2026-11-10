import type { HighlightRequest, SemanticPack } from "../pack.js";
import type { HighlightResult, SemanticSpan } from "../result.js";

function validate(source: string, result: HighlightResult): void {
  if (result.offsetEncoding !== "utf-16")
    throw new Error("PHP composition requires UTF-16 offsets");
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
    )
      throw new Error("Invalid or overlapping PHP composition spans");
    end = span.end;
  }
}

/** Only neural PHP region predictions choose child HTML inference.
 * No source tag scanning, runtime parser, PHP execution or Gold boundaries.
 */
export function createCompositePhpPack(options: {
  base: SemanticPack;
  highlightEmbedded(request: HighlightRequest): Promise<HighlightResult>;
}): SemanticPack {
  return {
    manifest: options.base.manifest,
    async highlight(request) {
      if (request.documentKind !== "php") throw new Error("Unsupported PHP document kind");
      const result = await options.base.highlight(request);
      validate(request.source, result);
      const spans: SemanticSpan[] = [];
      for (const span of result.spans) {
        if (span.tokenType !== "embedded-html") {
          spans.push(span);
          continue;
        }
        const source = request.source.slice(span.start, span.end);
        const child = await options.highlightEmbedded({ source, documentKind: "html" });
        validate(source, child);
        for (const token of child.spans) {
          spans.push({
            ...token,
            start: span.start + token.start,
            end: span.start + token.end,
            documentKind: token.documentKind ?? "html",
          });
        }
      }
      return { offsetEncoding: "utf-16", spans };
    },
  };
}
