/** Offline YAML CST supervision; never loads application schemas or executes source. */
import { createRequire } from "node:module";
import readline from "node:readline";
const Y = createRequire(import.meta.url)(process.argv[2]);
const punctuation = new Set([
  "doc-start",
  "doc-end",
  "seq-item-ind",
  "map-key-ind",
  "explicit-key-ind",
  "map-value-ind",
  "flow-map-start",
  "flow-map-end",
  "flow-seq-start",
  "flow-seq-end",
  "comma",
  "block-scalar-header",
]);
export function label(source, documentKind) {
  if (typeof source !== "string" || documentKind !== "yaml" || source.includes("\0"))
    throw Error("Expected original YAML source");
  const documents = Y.parseAllDocuments(source, {
    keepSourceTokens: true,
    prettyErrors: false,
    strict: true,
    uniqueKeys: false,
    version: "1.2",
    schema: "core",
    merge: false,
  });
  const roles = new Map();
  const features = new Set();
  for (const doc of documents) {
    if (doc.errors.length)
      throw Error(
        "Invalid YAML syntax: " + doc.errors.map((e) => e.code + "@" + e.pos[0]).join(","),
      );
    if (doc.warnings.some((w) => w.code !== "TAG_RESOLVE_FAILED"))
      throw Error("Unsupported YAML directive/tag warning");
    function visit(node, key = false) {
      if (!node) return;
      if (Y.isScalar(node)) {
        const token = node.srcToken;
        if (token?.type === "block-scalar") roles.set(token.offset, key ? "property" : "string");
        else if (token) {
          const role = key
            ? "property"
            : node.type !== "PLAIN"
              ? "string"
              : typeof node.value === "number" || typeof node.value === "bigint"
                ? "number"
                : typeof node.value === "boolean" || node.value === null
                  ? "keyword"
                  : "string";
          roles.set(token.offset, role);
        }
      } else if (Y.isMap(node)) {
        features.add("mappings");
        for (const pair of node.items) {
          visit(pair.key, true);
          visit(pair.value);
        }
      } else if (Y.isSeq(node)) {
        features.add("sequences");
        for (const item of node.items) visit(item);
      }
      // Alias nodes remain references; do not resolve or expand them.
    }
    visit(doc.contents);
  }
  if (documents.length > 1) features.add("multi-document");
  const spans = [];
  function add(start, text, tokenType, declaration = false) {
    if (!text.length) return;
    if (source.slice(start, start + text.length) !== text)
      throw Error("CST range does not match original YAML bytes");
    const span = { start, end: start + text.length, tokenType };
    if (declaration) span.modifiers = ["declaration"];
    spans.push(span);
    if (tokenType === "comment") features.add("comments");
    if (tokenType === "string") features.add("strings");
    if (tokenType === "number") features.add("numbers");
    if (tokenType === "keyword") features.add("keywords");
  }
  function walk(token) {
    if (!token || typeof token !== "object") return;
    if (Array.isArray(token)) {
      for (const t of token) walk(t);
      return;
    }
    if (token.type === "error") throw Error("YAML CST recovery token");
    if (token.type === "block-scalar") {
      features.add("block-strings");
      walk(token.props);
      const start = Math.max(token.offset, ...token.props.map((p) => p.offset + p.source.length));
      add(start, token.source, roles.get(token.offset) ?? "string");
      return;
    }
    if (typeof token.source === "string" && Number.isInteger(token.offset)) {
      const { type, offset, source: text } = token;
      if (type === "space" || type === "newline") {
        if (/[^ \t\r\n]/u.test(text)) throw Error("Unsupported YAML whitespace");
      } else if (type === "comment") add(offset, text, "comment");
      else if (type === "byte-order-mark") add(offset, text, "punctuation");
      else if (type === "anchor") {
        add(offset, text, "label", true);
        features.add("anchors");
      } else if (type === "alias") {
        add(offset, text, "label");
        features.add("aliases");
      } else if (type === "tag") {
        add(offset, text, "decorator");
        features.add("tags");
      } else if (type === "directive") {
        add(offset, text, "keyword");
        features.add("directives");
      } else if (punctuation.has(type)) add(offset, text, "punctuation");
      else if (["scalar", "single-quoted-scalar", "double-quoted-scalar"].includes(type)) {
        const role = roles.get(offset);
        if (!role) throw Error("YAML scalar has no independently composed role");
        add(offset, text, role);
      } else throw Error("Unmapped YAML CST token " + type);
      walk(token.end);
      return;
    }
    for (const value of Object.values(token)) if (typeof value === "object") walk(value);
  }
  for (const token of new Y.Parser().parse(source)) walk(token);
  spans.sort((a, b) => a.start - b.start);
  let end = 0;
  for (const span of spans) {
    if (span.start < end || /[^ \t\r\n]/u.test(source.slice(end, span.start)))
      throw Error("Incomplete/overlapping original YAML coverage");
    end = span.end;
  }
  if (/[^ \t\r\n]/u.test(source.slice(end))) throw Error("Incomplete original YAML suffix");
  if (source.includes("\r\n")) features.add("crlf");
  if (/[^\x00-\x7F]/u.test(source)) features.add("unicode");
  return { offsetEncoding: "utf-16", spans, features: [...features].sort() };
}
const lines = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of lines) {
  try {
    const request = JSON.parse(line);
    process.stdout.write(
      JSON.stringify({ result: label(request.source, request.documentKind) }) + "\n",
    );
  } catch (error) {
    process.stdout.write(JSON.stringify({ error: String(error.message) }) + "\n");
  }
}
