/** Offline supervision only. Scan original ranges; never execute input source. */
import { createRequire } from "node:module";
import readline from "node:readline";
const parser = createRequire(import.meta.url)(process.argv[2]);
const { SyntaxKind: K, ScanError, parseTree, createScanner } = parser;
export function label(source, documentKind) {
  if (typeof source !== "string" || !["json", "jsonc"].includes(documentKind))
    throw Error("Expected original JSON/JSONC source");
  const errors = [];
  const tree = parseTree(source, errors, {
    disallowComments: documentKind === "json",
    allowTrailingComma: documentKind === "jsonc",
    allowEmptyContent: true,
  });
  if (errors.length)
    throw Error(
      "Invalid " +
        documentKind +
        " syntax: " +
        errors.map((e) => e.error + "@" + e.offset).join(","),
    );
  const keys = new Set();
  const features = new Set();
  function visit(node) {
    if (!node) return;
    if (node.type === "property") keys.add(node.children[0].offset);
    if (node.type === "object") features.add("objects");
    if (node.type === "array") features.add("arrays");
    for (const child of node.children ?? []) visit(child);
  }
  visit(tree);
  const spans = [];
  const scanner = createScanner(source, false);
  let end = 0;
  while (true) {
    const kind = scanner.scan();
    if (scanner.getTokenError() !== ScanError.None)
      throw Error("Incomplete or invalid JSON lexical token");
    if (kind === K.EOF) break;
    const start = scanner.getTokenOffset();
    const stop = start + scanner.getTokenLength();
    if (kind === K.Trivia || kind === K.LineBreakTrivia) continue;
    if (start < end || /[^\x20\x09\x0A\x0D]/u.test(source.slice(end, start)))
      throw Error("Incomplete/overlapping original JSON coverage");
    let tokenType;
    if (kind === K.StringLiteral) {
      tokenType = keys.has(start) ? "property" : "string";
      features.add("strings");
    } else if (kind === K.NumericLiteral) {
      tokenType = "number";
      features.add("numbers");
    } else if ([K.NullKeyword, K.TrueKeyword, K.FalseKeyword].includes(kind)) {
      tokenType = "keyword";
      features.add("keywords");
    } else if ([K.LineCommentTrivia, K.BlockCommentTrivia].includes(kind)) {
      if (documentKind !== "jsonc") throw Error("JSON does not allow comments");
      tokenType = "comment";
      features.add("comments");
    } else if (
      [
        K.OpenBraceToken,
        K.CloseBraceToken,
        K.OpenBracketToken,
        K.CloseBracketToken,
        K.ColonToken,
        K.CommaToken,
      ].includes(kind)
    )
      tokenType = "punctuation";
    else throw Error("Unmapped JSON lexical token " + kind);
    spans.push({ start, end: stop, tokenType });
    end = stop;
  }
  if (/[^\x20\x09\x0A\x0D]/u.test(source.slice(end)))
    throw Error("Incomplete original JSON suffix");
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
