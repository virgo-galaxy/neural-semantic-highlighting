import type { HighlightRequest, SemanticPack } from "../pack.js";
import type { HighlightResult, SemanticSpan } from "../result.js";

function validate(source: string, result: HighlightResult): void {
  if (result.offsetEncoding !== "utf-16")
    throw new Error("Markdown composition requires UTF-16 offsets");
  const boundaries = new Set([0]);
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
      throw new Error("Invalid Markdown base/child offsets");
    }
    end = span.end;
  }
}

/** Reuse registered packs inside predicted code bodies. Only an explicit,
 * model-delimited info word selects a child: no fence/source parser or guessing.
 */
export function createCompositeMarkdownPack(options: {
  base: SemanticPack;
  resolveLanguage(name: string): string | undefined;
  highlightEmbedded(request: HighlightRequest): Promise<HighlightResult>;
}): SemanticPack {
  return {
    manifest: options.base.manifest,
    async highlight(request) {
      if (request.documentKind !== "markdown")
        throw new Error("Unsupported Markdown document kind");
      const result = await options.base.highlight(request);
      validate(request.source, result);
      const spans: SemanticSpan[] = [];
      let language: string | undefined;
      for (const span of result.spans) {
        if (span.tokenType === "code-fence") language = undefined;
        if (span.tokenType === "code-language") {
          language = options.resolveLanguage(request.source.slice(span.start, span.end).trim());
        }
        if (span.tokenType !== "embedded-code") {
          spans.push(span);
          continue;
        }
        const documentKind = language;
        language = undefined;
        if (!documentKind || documentKind === "markdown") {
          spans.push({ ...span, tokenType: "code" });
          continue;
        }
        const source = request.source.slice(span.start, span.end);
        const child = await options.highlightEmbedded({ source, documentKind });
        validate(source, child);
        for (const item of child.spans)
          spans.push({
            ...item,
            start: span.start + item.start,
            end: span.start + item.end,
            documentKind: item.documentKind ?? documentKind,
          });
      }
      return { offsetEncoding: "utf-16", spans };
    },
  };
}
