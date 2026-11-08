import { finished } from "node:stream/promises";

import type { HighlightRequest, HighlightResult, SemanticSpan } from "@nsh/core";
import { DecodingMode, HtmlEntityDecoder } from "entities/decode";
import { SAXParser, type SaxToken } from "parse5-sax-parser";

export interface HtmlRegion {
  start: number;
  end: number;
  language: "javascript" | "css" | "data";
  context: "block";
}

export interface HtmlGold extends HighlightResult {
  regions: HtmlRegion[];
  modernExclusions: string[];
}

// Explicitly obsolete elements in the current Living Standard. This is a data
// selection policy, not an allowlist of the conforming/custom/foreign vocabulary.
const obsolete = new Set([
  "acronym",
  "applet",
  "basefont",
  "bgsound",
  "big",
  "blink",
  "center",
  "dir",
  "font",
  "frame",
  "frameset",
  "isindex",
  "keygen",
  "listing",
  "marquee",
  "multicol",
  "nextid",
  "nobr",
  "noembed",
  "noframes",
  "param",
  "plaintext",
  "rb",
  "rtc",
  "spacer",
  "strike",
  "tt",
  "xmp",
]);
const javascriptTypes = new Set([
  "",
  "module",
  "text/javascript",
  "application/javascript",
  "text/ecmascript",
  "application/ecmascript",
  "application/x-javascript",
  "text/jscript",
  "text/livescript",
  "text/x-javascript",
  "text/x-ecmascript",
]);
const rawText = new Set([
  "style",
  "script",
  "iframe",
  "noscript",
  "xmp",
  "noembed",
  "noframes",
  "plaintext",
]);

function range(token: SaxToken): [number, number] {
  if (!token.sourceCodeLocation) throw new Error("Missing HTML parser source location");
  return [token.sourceCodeLocation.startOffset, token.sourceCodeLocation.endOffset];
}

/** Offline original-source Gold only. Never imported by an inference runtime. */
export async function labelHtml({ source, documentKind }: HighlightRequest): Promise<HtmlGold> {
  if (documentKind !== "html") throw new Error("Unsupported HTML document kind: " + documentKind);
  if (source.includes("\0")) throw new Error("NUL is outside complete HTML Gold coverage");
  const spans: SemanticSpan[] = [];
  const regions: HtmlRegion[] = [];
  const modernExclusions = new Set<string>();
  const add = (start: number, end: number, tokenType: string, closing = false) => {
    if (start < 0 || end <= start || end > source.length)
      throw new Error("Invalid HTML source range");
    spans.push({ start, end, tokenType, ...(closing ? { modifiers: ["closing"] } : {}) });
  };
  let textMode = "";
  let body: { tag: string; start: number; language: HtmlRegion["language"] } | undefined;

  const tag = (start: number, end: number, closing: boolean): string => {
    const raw = source.slice(start, end);
    const match = /^(<\/?)([^\s/>]+)/u.exec(raw);
    if (!match || Boolean(match[1] === "</") !== closing)
      throw new Error("Invalid HTML tag source");
    const name = match[2]!;
    add(start, start + match[1]!.length, "punctuation");
    add(start + match[1]!.length, start + match[0].length, "tag", closing);
    let cursor = match[0].length;
    for (;;) {
      while (/\s/u.test(raw[cursor] ?? "") && cursor < raw.length) cursor += 1;
      const tail = raw.slice(cursor);
      if (tail === ">" || (!closing && tail === "/>")) {
        add(start + cursor, end, "punctuation");
        break;
      }
      if (closing) throw new Error("Unexpected material in HTML end tag");
      const attribute = /^[^\s"'<>/=]+/u.exec(tail)?.[0];
      if (!attribute) throw new Error("Malformed HTML attribute at " + (start + cursor));
      add(start + cursor, start + cursor + attribute.length, "attribute");
      cursor += attribute.length;
      while (cursor < raw.length && /\s/u.test(raw[cursor]!)) cursor += 1;
      if (raw[cursor] !== "=") continue;
      add(start + cursor, start + cursor + 1, "punctuation");
      cursor += 1;
      while (cursor < raw.length && /\s/u.test(raw[cursor]!)) cursor += 1;
      const begin = cursor;
      const quote = raw[cursor];
      if (quote === '"' || quote === "'") {
        cursor = raw.indexOf(quote, cursor + 1);
        if (cursor < 0) throw new Error("Unterminated HTML attribute string");
        cursor += 1;
      } else {
        while (cursor < raw.length && !/[\s>]/u.test(raw[cursor]!)) cursor += 1;
        if (cursor === begin || /["'<=`]/u.test(raw.slice(begin, cursor))) {
          throw new Error("Malformed unquoted HTML attribute value");
        }
      }
      add(start + begin, start + cursor, "string");
    }
    return name.toLowerCase();
  };

  const text = (start: number, end: number) => {
    const raw = source.slice(start, end);
    if (!raw.trim()) return;
    if (rawText.has(textMode) || raw.includes("<![CDATA[")) {
      add(start, end, "text");
      return;
    }
    let cursor = 0;
    const decoder = new HtmlEntityDecoder(() => {});
    for (let amp = raw.indexOf("&"); amp >= 0; amp = raw.indexOf("&", amp + 1)) {
      decoder.startEntity(DecodingMode.Legacy);
      let length = decoder.write(raw, amp + 1);
      if (length < 0) length = decoder.end();
      if (length < 1) continue;
      if (cursor < amp) add(start + cursor, start + amp, "text");
      add(start + amp, start + amp + length, "entity");
      cursor = amp + length;
      amp = cursor - 1;
    }
    if (cursor < raw.length) add(start + cursor, end, "text");
  };

  const parser = new SAXParser({ sourceCodeLocationInfo: true });
  parser.on("startTag", (token) => {
    if (body) return;
    const [start, end] = range(token);
    const name = tag(start, end, false);
    if (obsolete.has(name)) modernExclusions.add("obsolete-element:" + name);
    const attrs = new Map(token.attrs.map((attribute) => [attribute.name, attribute.value]));
    if (name === "script" && (attrs.has("language") || attrs.has("charset"))) {
      modernExclusions.add("obsolete-script-attribute");
    }
    if ((name === "script" || name === "style") && !token.selfClosing) {
      const type = (attrs.get("type") ?? "").trim().toLowerCase();
      const language =
        name === "style"
          ? type === "" || type === "text/css"
            ? "css"
            : "data"
          : javascriptTypes.has(type)
            ? "javascript"
            : "data";
      body = { tag: name, start: end, language };
    }
    textMode = rawText.has(name) || name === "title" || name === "textarea" ? name : "";
  });
  parser.on("endTag", (token) => {
    const [start, end] = range(token);
    if (body) {
      if (token.tagName.toLowerCase() !== body.tag) return;
      if (start > body.start) {
        add(body.start, start, "embedded-" + body.language);
        regions.push({ start: body.start, end: start, language: body.language, context: "block" });
      }
      body = undefined;
    }
    tag(start, end, true);
    textMode = "";
  });
  parser.on("text", (token) => {
    if (!body) text(...range(token));
  });
  parser.on("comment", (token) => {
    if (body) return;
    const [start, end] = range(token);
    const raw = source.slice(start, end);
    if (!raw.startsWith("<!--") || !raw.endsWith("-->")) throw new Error("Malformed HTML comment");
    add(start, end, "comment");
  });
  parser.on("doctype", (token) => {
    if (body) return;
    const [start, end] = range(token);
    if (!/^<!doctype\s+html\s*>$/iu.test(source.slice(start, end)))
      modernExclusions.add("legacy-doctype");
    add(start, end, "keyword");
  });
  const completion = finished(parser);
  try {
    parser.end(source);
    await completion;
  } catch (error) {
    parser.destroy();
    await completion.catch(() => {});
    throw error;
  }
  if (body) throw new Error("Unclosed HTML script/style body");
  spans.sort((a, b) => a.start - b.start);
  let end = 0;
  for (const span of spans) {
    if (span.start < end || source.slice(end, span.start).trim())
      throw new Error("Incomplete HTML Gold coverage at " + end);
    end = span.end;
  }
  if (source.slice(end).trim()) throw new Error("Unlabeled HTML source suffix at " + end);
  return {
    offsetEncoding: "utf-16",
    spans,
    regions,
    modernExclusions: [...modernExclusions].sort(),
  };
}
