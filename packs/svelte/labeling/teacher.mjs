// Offline only: no compile(), evaluation, imports or preprocessor execution.
import { createRequire } from "node:module";
import { createInterface } from "node:readline";
import { HtmlEntityDecoder, DecodingMode } from "entities/decode";
const require = createRequire(import.meta.url);
const compiler = require("../../../artifacts/tools/svelte-gold/svelte-5.38.0/compiler/index.js");

export async function label(source) {
  // The official preprocessor locates style bodies. Equal UTF-16 length masking
  // lets the template parser accept SCSS/Less without loading any preprocessor.
  const masked = await compiler.preprocess(source, {
    style: ({ content }) => ({ code: content.replace(/[^\r\n]/g, " ") }),
  });
  if (masked.code.length !== source.length)
    throw Error("Style masking changed original coordinates");
  const root = compiler.parse(masked.code.replace(/^\uFEFF/u, " "), { modern: true });
  const spans = [],
    features = new Set();
  const add = (start, end, tokenType, closing = false) => {
    if (end > start && source.slice(start, end).trim())
      spans.push({ start, end, tokenType, ...(closing ? { modifiers: ["closing"] } : {}) });
  };
  if (source.startsWith("\ufeff")) spans.push({ start: 0, end: 1, tokenType: "punctuation" });
  const expression = (n) => {
    if (n) {
      add(n.start, n.end, "embedded-expression");
      features.add("expressions");
    }
  };
  const text = (start, end) => {
    const raw = source.slice(start, end);
    let cursor = 0;
    const decoder = new HtmlEntityDecoder(() => {});
    for (let amp = raw.indexOf("&"); amp >= 0; amp = raw.indexOf("&", amp + 1)) {
      decoder.startEntity(DecodingMode.Legacy);
      let length = decoder.write(raw, amp + 1);
      if (length < 0) length = decoder.end();
      if (length < 1) continue;
      add(start + cursor, start + amp, "text");
      add(start + amp, start + amp + length, "entity");
      cursor = amp + length;
      amp = cursor - 1;
      features.add("entities");
    }
    add(start + cursor, end, "text");
  };
  const tag = (node) => {
    const name = node.name ?? (node.type === "Script" ? "script" : "style");
    const start = node.start;
    if (source[start] !== "<" || source.slice(start + 1, start + 1 + name.length) !== name)
      throw Error("Invalid original tag");
    add(start, start + 1, "punctuation");
    add(start + 1, start + 1 + name.length, "tag");
    let cursor = start + 1 + name.length;
    let attributes = [...(node.attributes ?? [])];
    if (node.type === "SvelteComponent" || node.type === "SvelteElement") {
      const target = node.expression ?? node.tag;
      const at = source.indexOf("this", cursor);
      if (!target || at < cursor || at >= target.start)
        throw Error("Missing dynamic element target");
      let hi = target.end;
      while (/\s/u.test(source[hi] ?? "") && hi < node.end) hi++;
      if (!["}", '"', "'"].includes(source[hi])) throw Error("Unterminated dynamic element target");
      attributes.push({ type: "Attribute", start: at, end: hi + 1 });
      attributes.sort((a, b) => a.start - b.start);
    }
    for (const a of attributes) {
      if (source.slice(cursor, a.start).trim()) throw Error("Unmapped tag gap");
      const raw = source.slice(a.start, a.end);
      if (a.type !== "Attribute") features.add("directives");
      if (raw.startsWith("{")) {
        add(a.start, a.end, "attribute");
        features.add("directives");
      } else {
        const match = /^([^\s=]+)/u.exec(raw);
        if (!match) throw Error("Missing attribute name");
        add(a.start, a.start + match[0].length, "attribute");
        const rest = raw.slice(match[0].length),
          eq = rest.indexOf("=");
        if (eq >= 0) {
          const at = a.start + match[0].length + eq;
          add(at, at + 1, "punctuation");
          const offset = source.slice(at + 1, a.end).search(/\S/u);
          if (offset >= 0) add(at + 1 + offset, a.end, "string");
        } else if (rest.trim()) throw Error("Unmapped attribute suffix");
      }
      cursor = a.end;
    }
    const tail = /^\s*(\/?>)/u.exec(source.slice(cursor, node.end));
    if (!tail) throw Error("Unterminated start tag");
    const openEnd = cursor + tail[0].length;
    add(openEnd - tail[1].length, openEnd, "punctuation");
    const closeStart = source.lastIndexOf("</" + name, node.end);
    let close = null;
    if (closeStart >= openEnd && /^<\/[^\s>]+\s*>$/u.test(source.slice(closeStart, node.end))) {
      close = closeStart;
      add(close, close + 2, "punctuation");
      add(close + 2, close + 2 + name.length, "tag", true);
      add(node.end - 1, node.end, "punctuation");
    }
    return { openEnd, close };
  };
  const fillHeader = (start, end) => {
    const inside = spans
      .filter((s) => s.start >= start && s.end <= end)
      .sort((a, b) => a.start - b.start);
    let cursor = start;
    const fill = (lo, hi) => {
      const raw = source.slice(lo, hi);
      const pattern =
        /\s+|[#:/@](?:else|if|each|await|key|snippet|then|catch|html|render|debug|const|attach)\b|[A-Za-z_$][\w$]*|\d+(?:\.\d+)?|(?:\.{3}|=>|\?\?|\?\.|===|!==|&&|\|\|)|[^\s]/gu;
      for (const m of raw.matchAll(pattern)) {
        const t = m[0];
        if (!t.trim()) continue;
        const role =
          (/^[#:/@]/u.test(t) && t.length > 1) ||
          ["as", "then", "catch", "else", "if", "const"].includes(t)
            ? "keyword"
            : /^[A-Za-z_$]/u.test(t)
              ? "variable"
              : /^\d/u.test(t)
                ? "number"
                : "{}()[],;".includes(t)
                  ? "punctuation"
                  : "operator";
        add(lo + m.index, lo + m.index + t.length, role);
      }
    };
    for (const span of inside) {
      if (cursor < span.start) fill(cursor, span.start);
      cursor = Math.max(cursor, span.end);
    }
    if (cursor < end) fill(cursor, end);
  };
  const fragment = (f) => {
    for (const n of f?.nodes ?? []) visit(n);
  };
  const visit = (node) => {
    if (node.type === "Text") {
      text(node.start, node.end);
      return;
    }
    if (node.type === "Comment") {
      add(node.start, node.end, "comment");
      return;
    }
    if (node.name && source[node.start] === "<") {
      tag(node);
      fragment(node.fragment);
      return;
    }
    if (node.type === "ExpressionTag") {
      add(node.start, node.start + 1, "punctuation");
      expression(node.expression);
      add(node.end - 1, node.end, "punctuation");
      return;
    }
    if (node.type.endsWith("Block") || node.type.endsWith("Tag")) {
      features.add("blocks");
      if (node.type === "SnippetBlock") {
        features.add("snippets");
      } else if (node.type === "ConstTag") {
        expression(node.declaration?.declarations?.[0]?.init);
      } else {
        expression(node.test);
        expression(node.expression);
        expression(node.key);
      }
      for (const value of Object.values(node)) if (value?.type === "Fragment") fragment(value);
      fillHeader(node.start, node.end);
      return;
    }
    throw Error("Unmapped Svelte node: " + node.type);
  };
  for (const block of [root.instance, root.module, root.css])
    if (block) {
      const { openEnd, close } = tag(block);
      if (close === null) throw Error("Unclosed code block");
      const lang = block.attributes?.find((a) => a.name === "lang")?.value?.[0]?.data ?? "";
      const language =
        block.type === "Script"
          ? {
              "": "javascript",
              js: "javascript",
              javascript: "javascript",
              ts: "typescript",
              typescript: "typescript",
            }[lang]
          : { "": "css", css: "css", scss: "scss", less: "less" }[lang];
      const type = "embedded-" + (language ?? "data");
      add(openEnd, close, type);
      features.add(type);
      if (block.context === "module") features.add("module-script");
    }
  // svelte:options is represented separately by the modern parser.
  if (root.options) visit({ ...root.options, type: "SvelteOptions", name: "svelte:options" });
  fragment(root.fragment);
  spans.sort((a, b) => a.start - b.start);
  let end = 0;
  const boundaries = new Set([0]);
  let unit = 0;
  for (const c of source) {
    unit += c.length;
    boundaries.add(unit);
  }
  for (const s of spans) {
    if (
      s.start < end ||
      source.slice(end, s.start).trim() ||
      !boundaries.has(s.start) ||
      !boundaries.has(s.end)
    )
      throw Error("Incomplete/overlapping Svelte Gold at " + end);
    end = s.end;
  }
  if (source.slice(end).trim()) throw Error("Incomplete Svelte suffix at " + end);
  if (source.includes("\r\n")) features.add("crlf");
  if (/[^\x00-\x7f]/u.test(source)) features.add("unicode");
  const joined = [];
  for (const s of spans) {
    const prev = joined.at(-1);
    if (
      prev &&
      ["string", "text", "comment"].includes(s.tokenType) &&
      prev.tokenType === s.tokenType &&
      prev.end === s.start
    )
      prev.end = s.end;
    else joined.push(s);
  }
  return { offsetEncoding: "utf-16", spans: joined, features: [...features].sort() };
}
for await (const line of createInterface({ input: process.stdin, crlfDelay: Infinity })) {
  try {
    console.log(JSON.stringify(await label(JSON.parse(line).source)));
  } catch (e) {
    console.log(JSON.stringify({ error: e.message }));
  }
}
