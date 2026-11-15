/** Offline dotenv ranges. parse() validates values without loading process.env. */
import { createRequire } from "node:module";
import readline from "node:readline";
const D = createRequire(import.meta.url)(process.argv[2]);
export function label(source, documentKind) {
  if (
    typeof source !== "string" ||
    documentKind !== "dotenv" ||
    /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/u.test(source) ||
    /\r(?!\n)/u.test(source)
  )
    throw Error("Expected supported original dotenv source");
  const spans = [],
    features = new Set(),
    expected = Object.create(null);
  let at = 0;
  const add = (start, end, tokenType, declaration = false) => {
    if (end > start) {
      const s = { start, end, tokenType };
      if (declaration) s.modifiers = ["declaration"];
      spans.push(s);
    }
  };
  const blank = (c) => c === " " || c === "\t";
  const newline = (c) => c === "\r" || c === "\n";
  function comment() {
    const start = at;
    while (at < source.length && !newline(source[at])) at++;
    add(start, at, "comment");
    features.add("comments");
  }
  if (source.startsWith("\ufeff")) {
    add(0, 1, "punctuation");
    at = 1;
    features.add("bom");
  }
  while (at < source.length) {
    while (at < source.length && (blank(source[at]) || newline(source[at]))) at++;
    if (at >= source.length) break;
    if (source[at] === "#") {
      comment();
      continue;
    }
    const prefix = /^export[ \t]+(?=[A-Za-z_][A-Za-z0-9_]*[ \t]*=)/u.exec(source.slice(at));
    if (prefix) {
      add(at, at + 6, "keyword");
      features.add("exports");
      at += prefix[0].length;
    }
    const key = /^[A-Za-z_][A-Za-z0-9_]*/u.exec(source.slice(at));
    if (!key) throw Error("Unsupported dotenv binding name");
    const name = key[0];
    add(at, at + name.length, "variable", true);
    features.add("bindings");
    at += name.length;
    while (blank(source[at])) at++;
    if (source[at] !== "=") throw Error("Expected equals dotenv assignment");
    add(at, at + 1, "punctuation");
    at++;
    while (blank(source[at])) at++;
    const start = at;
    let end = at,
      decoded = "";
    if (["'", '"', "`"].includes(source[at])) {
      const quote = source[at++];
      features.add("quoted-values");
      let closed = false;
      while (at < source.length) {
        if (source[at] === "\\" && source[at + 1] === quote) {
          at += 2;
          continue;
        }
        if (source[at] === quote) {
          at++;
          closed = true;
          break;
        }
        at++;
      }
      if (!closed) throw Error("Unterminated dotenv quote");
      end = at;
      decoded = source.slice(start + 1, end - 1).replace(/\r\n/g, "\n");
      if (quote === '"') decoded = decoded.replace(/\\n/g, "\n").replace(/\\r/g, "\r");
      if (source.slice(start, end).includes("\n")) features.add("multiline-strings");
      while (blank(source[at])) at++;
      if (at < source.length && !newline(source[at]) && source[at] !== "#")
        throw Error("Unexpected text after dotenv quoted value");
    } else {
      while (at < source.length && !newline(source[at]) && source[at] !== "#") at++;
      end = at;
      while (end > start && blank(source[end - 1])) end--;
      decoded = source.slice(start, end);
    }
    if (end > start) {
      add(start, end, "string");
      features.add("strings");
    } else features.add("empty-values");
    expected[name] = decoded;
    if (source[at] === "#") comment();
  }
  const parsed = D.parse(source);
  const keys = Object.keys(parsed).sort();
  if (
    JSON.stringify(keys) !== JSON.stringify(Object.keys(expected).sort()) ||
    keys.some((k) => parsed[k] !== expected[k])
  )
    throw Error("Original dotenv ranges disagree with independent parser values");
  let end = 0;
  for (const span of spans) {
    if (span.start < end || /[^ \t\r\n]/u.test(source.slice(end, span.start)))
      throw Error("Incomplete/overlapping dotenv coverage");
    end = span.end;
  }
  if (/[^ \t\r\n]/u.test(source.slice(end))) throw Error("Incomplete dotenv suffix");
  if (source.includes("\r\n")) features.add("crlf");
  if (/[^\x00-\x7f]/u.test(source)) features.add("unicode");
  return { offsetEncoding: "utf-16", spans, features: [...features].sort() };
}
for await (const line of readline.createInterface({ input: process.stdin, crlfDelay: Infinity })) {
  try {
    const r = JSON.parse(line);
    process.stdout.write(JSON.stringify({ result: label(r.source, r.documentKind) }) + "\n");
  } catch (e) {
    process.stdout.write(JSON.stringify({ error: String(e.message) }) + "\n");
  }
}
