import type { HighlightRequest, SemanticPack } from "../pack.js";
import type { HighlightResult, SemanticSpan } from "../result.js";

export const EXPRESSION_PREFIX = "const __nsh_vue_value = (\n";
export const EXPRESSION_SUFFIX = "\n);";
const languages: Readonly<Record<string, string>> = {
  "embedded-javascript": "javascript",
  "embedded-typescript": "typescript",
  "embedded-jsx": "jsx",
  "embedded-tsx": "tsx",
  "embedded-css": "css",
  "embedded-scss": "scss",
  "embedded-less": "less",
  "embedded-expression": "typescript",
};

function validate(source: string, result: HighlightResult) {
  if (result.offsetEncoding !== "utf-16")
    throw new Error("Vue composition requires UTF-16 model offsets");
  const boundaries = new Set([0]);
  let unit = 0,
    end = 0;
  for (const character of source) {
    unit += character.length;
    boundaries.add(unit);
  }
  for (const span of result.spans) {
    if (
      !Number.isInteger(span.start) ||
      !Number.isInteger(span.end) ||
      span.start < end ||
      span.end <= span.start ||
      !boundaries.has(span.start) ||
      !boundaries.has(span.end)
    )
      throw new Error("Invalid Vue child/base spans");
    end = span.end;
  }
}

/** Neural regions only. Reuses existing code packs without parsing Vue source. */
export function createCompositeVuePack(options: {
  base: SemanticPack;
  highlightEmbedded(request: HighlightRequest): Promise<HighlightResult>;
}): SemanticPack {
  return {
    manifest: options.base.manifest,
    async highlight(request) {
      if (request.documentKind !== "vue") throw new Error("Unsupported Vue document kind");
      const result = await options.base.highlight(request);
      validate(request.source, result);
      const spans: SemanticSpan[] = [];
      for (const span of result.spans) {
        const documentKind = languages[span.tokenType];
        if (!documentKind) {
          spans.push(span);
          continue;
        }
        const raw = request.source.slice(span.start, span.end);
        const expression = span.tokenType === "embedded-expression";
        const prefix = expression ? EXPRESSION_PREFIX : "",
          suffix = expression ? EXPRESSION_SUFFIX : "";
        const source = prefix + raw + suffix;
        const child = await options.highlightEmbedded({ source, documentKind });
        validate(source, child);
        for (const item of child.spans) {
          const start = Math.max(item.start, prefix.length),
            end = Math.min(item.end, prefix.length + raw.length);
          if (start < end)
            spans.push({
              ...item,
              documentKind: item.documentKind ?? documentKind,
              start: span.start + start - prefix.length,
              end: span.start + end - prefix.length,
            });
        }
      }
      return { offsetEncoding: "utf-16", spans };
    },
  };
}
