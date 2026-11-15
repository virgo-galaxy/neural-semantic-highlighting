/** Offline original-range TOML supervision. Never executes source or loads a project. */
import { pathToFileURL } from "node:url";
import readline from "node:readline";
const { parseTOML } = await import(pathToFileURL(process.argv[2]).href);
export function label(source, documentKind) {
  if (typeof source !== "string" || documentKind !== "toml" || source.includes("\0"))
    throw Error("Expected original TOML source");
  const ast = parseTOML(source, { tomlVersion: "1.1.0" });
  const roles = new Map(),
    features = new Set();
  function assign(node, role) {
    roles.set(node.range.join(":"), role);
  }
  function key(node, role) {
    if (node.type !== "TOMLKey") throw Error("Unsupported TOML key AST");
    for (const part of node.keys) {
      if (!["TOMLBare", "TOMLQuoted"].includes(part.type)) throw Error("Unsupported key part");
      assign(part, role);
    }
    if (node.keys.length > 1) features.add("dotted-keys");
  }
  function visit(node) {
    switch (node.type) {
      case "Program":
      case "TOMLTopLevelTable":
        for (const child of node.body) visit(child);
        break;
      case "TOMLTable":
        key(node.key, "namespace");
        features.add("tables");
        if (node.kind === "array") features.add("array-tables");
        for (const child of node.body) visit(child);
        break;
      case "TOMLKeyValue":
        key(node.key, "property");
        visit(node.value);
        break;
      case "TOMLArray":
        features.add("arrays");
        for (const child of node.elements) visit(child);
        break;
      case "TOMLInlineTable":
        features.add("inline-tables");
        for (const child of node.body) visit(child);
        break;
      case "TOMLValue": {
        let role;
        if (node.kind === "string") {
          role = "string";
          features.add("strings");
          if (node.multiline) features.add("multiline-strings");
        } else if (node.kind === "boolean") {
          role = "keyword";
          features.add("keywords");
        } else if (
          [
            "integer",
            "float",
            "offset-date-time",
            "local-date-time",
            "local-date",
            "local-time",
          ].includes(node.kind)
        ) {
          role = "number";
          features.add("numbers");
          if (node.kind.includes("date") || node.kind === "local-time") features.add("dates");
        } else throw Error("Unmapped TOML value kind " + node.kind);
        assign(node, role);
        break;
      }
      default:
        throw Error("Unmapped TOML AST " + node.type);
    }
  }
  visit(ast);
  const spans = [];
  for (const token of ast.tokens) {
    const [start, end] = token.range;
    if (source.slice(start, end) !== token.value) throw Error("Changed original TOML token range");
    const tokenType =
      roles.get(token.range.join(":")) ?? (token.type === "Punctuator" ? "punctuation" : null);
    if (!tokenType) throw Error("Unmapped TOML token " + token.type);
    spans.push({ start, end, tokenType });
  }
  for (const comment of ast.comments) {
    const [start, end] = comment.range;
    if (source[start] !== "#") throw Error("Changed TOML comment range");
    spans.push({ start, end, tokenType: "comment" });
    features.add("comments");
  }
  spans.sort((a, b) => a.start - b.start);
  let end = 0;
  for (const span of spans) {
    if (span.start < end || /[^ \t\r\n]/u.test(source.slice(end, span.start)))
      throw Error("Incomplete/overlapping TOML coverage");
    end = span.end;
  }
  if (/[^ \t\r\n]/u.test(source.slice(end))) throw Error("Incomplete TOML suffix");
  if (source.includes("\r\n")) features.add("crlf");
  if (/[^\x00-\x7F]/u.test(source)) features.add("unicode");
  return { offsetEncoding: "utf-16", spans, features: [...features].sort() };
}
for await (const line of readline.createInterface({ input: process.stdin, crlfDelay: Infinity })) {
  try {
    const r = JSON.parse(line);
    process.stdout.write(JSON.stringify({ result: label(r.source, r.documentKind) }) + "\n");
  } catch (error) {
    process.stdout.write(JSON.stringify({ error: String(error.message) }) + "\n");
  }
}
