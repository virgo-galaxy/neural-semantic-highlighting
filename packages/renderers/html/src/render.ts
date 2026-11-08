import type { HighlightResult, OffsetEncoding } from "@nsh/core";

export interface RenderToHtmlOptions {
  source: string;
  documentKind: string;
  result: HighlightResult;
}

export function renderCodeToHtml({ source, result }: RenderToHtmlOptions): string {
  const spans = [...result.spans].sort(
    (left, right) => left.start - right.start || left.end - right.end,
  );

  const resolveOffset = createUtf16OffsetResolver(source, result.offsetEncoding);

  const parts: string[] = [];
  let cursor = 0;

  for (const span of spans) {
    const start = resolveOffset(span.start);
    const end = resolveOffset(span.end);

    if (start < cursor) {
      throw new Error("Semantic spans must not overlap.");
    }

    if (end < start) {
      throw new Error("Semantic span end must not precede start.");
    }

    if (start > cursor) {
      parts.push(escapeHtml(source.slice(cursor, start)));
    }

    const modifiers =
      span.modifiers && span.modifiers.length > 0
        ? ` data-modifiers="${escapeAttribute(span.modifiers.join(" "))}"`
        : "";

    parts.push(
      `<span class="nsh-token" data-token-type="${escapeAttribute(
        span.tokenType,
      )}"${modifiers}>${escapeHtml(source.slice(start, end))}</span>`,
    );

    cursor = end;
  }

  if (cursor < source.length) {
    parts.push(escapeHtml(source.slice(cursor)));
  }

  return parts.join("");
}

export function renderToHtml(options: RenderToHtmlOptions): string {
  return `<pre class="nsh" data-language="${escapeAttribute(options.documentKind)}"><code>${renderCodeToHtml(options)}</code></pre>`;
}

function createUtf16OffsetResolver(
  source: string,
  encoding: OffsetEncoding,
): (offset: number) => number {
  if (encoding === "utf-16") {
    return (offset) => {
      if (offset < 0 || offset > source.length) {
        throw new Error(`UTF-16 offset ${offset} is out of bounds.`);
      }

      return offset;
    };
  }

  const offsets = new Map<number, number>([[0, 0]]);

  let encodedOffset = 0;
  let utf16Offset = 0;

  for (const character of source) {
    encodedOffset += encoding === "utf-8" ? new TextEncoder().encode(character).length : 1;

    utf16Offset += character.length;
    offsets.set(encodedOffset, utf16Offset);
  }

  return (offset) => {
    const resolved = offsets.get(offset);

    if (resolved === undefined) {
      throw new Error(
        `${encoding.toUpperCase()} offset ${offset} does not align with a character boundary.`,
      );
    }

    return resolved;
  };
}

function escapeHtml(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function escapeAttribute(value: string): string {
  return escapeHtml(value).replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}
