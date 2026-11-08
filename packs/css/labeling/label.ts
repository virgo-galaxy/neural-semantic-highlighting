import { createRequire } from "node:module";

import type { HighlightRequest, HighlightResult, SemanticSpan } from "@nsh/core";
import { getCSSLanguageService, getSCSSLanguageService } from "vscode-css-languageservice";
import { TextDocument } from "vscode-languageserver-textdocument";

// The public language service does not expose lexical spans. These narrow
// adapters bind to the internal scanner/AST of the EXACT locked version.
// They are offline Gold tools only and must never enter the inference runtime.
interface AstNode {
  type: number;
  offset: number;
  length: number;
  parent?: AstNode;
  getText(): string;
  getChildren(): AstNode[];
  accept(visitor: (node: AstNode) => boolean): void;
}

interface Token {
  type: number;
  offset: number;
  len: number;
  text: string;
}

interface Scanner {
  ignoreWhitespace: boolean;
  ignoreComment: boolean;
  inURL: boolean;
  setSource(source: string): void;
  scan(): Token;
}

const require = createRequire(import.meta.url);
const { NodeType: nodes, ParseErrorCollector } =
  require("vscode-css-languageservice/lib/umd/parser/cssNodes.js") as {
    NodeType: Record<string, number>;
    ParseErrorCollector: {
      entries(node: AstNode): { getMessage(): string; getOffset(): number }[];
    };
  };
const { Scanner: CSSScanner, TokenType: tokens } =
  require("vscode-css-languageservice/lib/umd/parser/cssScanner.js") as {
    Scanner: new () => Scanner;
    TokenType: Record<string, number>;
  };
const scssScanner = require("vscode-css-languageservice/lib/umd/parser/scssScanner.js") as {
  SCSSScanner: new () => Scanner;
  VariableName: number;
  InterpolationFunction: number;
};

const services = { css: getCSSLanguageService(), scss: getSCSSLanguageService() };
const numericTokens = new Set(
  [
    "Num",
    "Percentage",
    "Dimension",
    "EMS",
    "EXS",
    "Length",
    "Angle",
    "Time",
    "Freq",
    "Resolution",
    "ContainerQueryLength",
  ].map((name) => tokens[name]),
);
const punctuationTokens = new Set(
  [
    "Colon",
    "SemiColon",
    "CurlyL",
    "CurlyR",
    "ParenthesisL",
    "ParenthesisR",
    "BracketL",
    "BracketR",
    "Comma",
  ].map((name) => tokens[name]),
);

interface Candidate extends SemanticSpan {
  priority: number;
}

/** Construct local-role Gold without compiling Sass, resolving imports, or executing code. */
export function labelCss({ source, documentKind }: HighlightRequest): HighlightResult {
  if (documentKind !== "css" && documentKind !== "scss") {
    throw new Error("Unsupported CSS document kind: " + documentKind);
  }
  if (!source.length) return { offsetEncoding: "utf-16", spans: [] };
  const service = services[documentKind];
  const document = TextDocument.create("file:///source." + documentKind, documentKind, 1, source);
  const ast = service.parseStylesheet(document) as unknown as AstNode;
  const errors = ParseErrorCollector.entries(ast);
  if (errors.length) {
    throw new Error(
      "CSS/SCSS parse error: " +
        errors.map((error) => error.getOffset() + ": " + error.getMessage()).join("; "),
    );
  }
  const candidates: Candidate[] = [];
  const add = (
    start: number,
    end: number,
    tokenType: string,
    priority: number,
    declaration = false,
  ) => {
    if (start < 0 || end <= start || end > source.length) {
      throw new Error("Invalid parser range: " + start + ".." + end);
    }
    candidates.push({
      start,
      end,
      tokenType,
      priority,
      ...(declaration ? { modifiers: ["declaration"] } : {}),
    });
  };
  const scan = documentKind === "scss" ? new scssScanner.SCSSScanner() : new CSSScanner();
  scan.ignoreWhitespace = false;
  scan.ignoreComment = false;
  scan.setSource(source);
  let previous: Token | undefined;
  let urlDepth = 0;
  for (;;) {
    const token = scan.scan();
    if (token.type === tokens.EOF) break;
    if (token.type === tokens.Whitespace) continue;
    if (token.type === tokens.BadString || token.type === tokens.BadEscapedJavaScript) {
      throw new Error("Invalid CSS/SCSS token at " + token.offset);
    }
    const end = token.offset + token.len;
    if (token.type === tokens.Comment || token.type === tokens.SingleLineComment) {
      add(token.offset, end, "comment", 100);
    } else if (token.type === tokens.String || token.type === tokens.UnquotedString) {
      add(token.offset, end, "string", 90);
    } else if (numericTokens.has(token.type)) {
      add(token.offset, end, "number", 20);
    } else if (token.type === tokens.AtKeyword || token.type === tokens.Charset) {
      add(token.offset, end, "keyword", 20);
    } else if (token.type === scssScanner.VariableName) {
      add(token.offset, end, "variable", 20);
    } else if (token.type === scssScanner.InterpolationFunction) {
      add(token.offset, end, "punctuation", 70);
    } else if (punctuationTokens.has(token.type)) {
      add(token.offset, end, "punctuation", 10);
    } else if (token.type === tokens.Ident || token.type === tokens.Hash) {
      add(token.offset, end, "keyword", 10);
    } else {
      add(token.offset, end, "operator", 10);
    }
    if (
      previous &&
      previous.offset + previous.len === token.offset &&
      (previous.text === ">" || previous.text === "<") &&
      token.text === "="
    ) {
      add(previous.offset, end, "operator", 20);
    }
    if (token.type === tokens.ParenthesisL) {
      if (urlDepth || previous?.text.toLowerCase() === "url") {
        urlDepth += 1;
        scan.inURL = true;
      }
    } else if (token.type === tokens.ParenthesisR && urlDepth) {
      urlDepth -= 1;
      scan.inURL = urlDepth > 0;
    }
    previous = token;
  }
  ast.accept((node) => {
    if (!node.length || node.offset < 0) return true;
    const start = node.offset;
    const end = start + node.length;
    const kind = node.type;
    if (kind === nodes.ClassSelector || kind === nodes.SelectorPlaceholder) {
      add(start, end, "class", 30);
    } else if (kind === nodes.IdentifierSelector) {
      add(start, end, "label", 30);
    } else if (kind === nodes.ElementNameSelector) {
      add(start, end, node.getText() === "*" ? "operator" : "tag", 30);
    } else if (kind === nodes.Property) {
      add(start, end, "property", 40, true);
    } else if (kind === nodes.NumericValue || kind === nodes.HexColorValue) {
      add(start, end, "number", 40);
    } else if (kind === nodes.VariableName) {
      const parent = node.parent?.type;
      const parameter = parent === nodes.FunctionParameter;
      add(
        start,
        end,
        parameter ? "parameter" : "variable",
        65,
        parameter || parent === nodes.VariableDeclaration,
      );
    } else if (kind === nodes.Interpolation) {
      add(start, start + 2, "punctuation", 70);
      add(end - 1, end, "punctuation", 70);
    } else if (kind === nodes.PseudoSelector) {
      const name = node.getChildren().find((child) => child.type === nodes.Identifier);
      if (name) add(start, name.offset + name.length, "function", 40);
    } else if (kind === nodes.AttributeSelector) {
      const name = node.getChildren().find((child) => child.type === nodes.Identifier);
      if (name) add(name.offset, name.offset + name.length, "attribute", 40);
    } else if (kind === nodes.Identifier) {
      const parent = node.parent?.type;
      if (
        parent === nodes.Function ||
        parent === nodes.Invocation ||
        parent === nodes.MixinReference ||
        parent === nodes.MixinDeclaration ||
        parent === nodes.FunctionDeclaration
      ) {
        add(
          start,
          end,
          "function",
          50,
          parent === nodes.MixinDeclaration || parent === nodes.FunctionDeclaration,
        );
      } else if (parent === nodes.Module || parent === nodes.NamespacePrefix) {
        add(start, end, "namespace", 50);
      } else if (node.getText().startsWith("--") && parent !== nodes.Property) {
        let ancestor = node.parent;
        while (ancestor && ancestor.type !== nodes.Function) ancestor = ancestor.parent;
        const name = ancestor?.getChildren().find((child) => child.type === nodes.Identifier);
        if (name?.getText() === "var") add(start, end, "variable", 50);
      }
    } else if (kind === nodes.URILiteral) {
      // Raw URLs are payload, not Sass line comments or division operators.
      const text = node.getText();
      const open = text.indexOf("(");
      const close = text.lastIndexOf(")");
      if (open >= 0 && close > open) {
        add(start, start + open, "function", 110);
        let lo = start + open + 1;
        let hi = start + close;
        while (lo < hi && /\s/u.test(source[lo]!)) lo += 1;
        while (hi > lo && /\s/u.test(source[hi - 1]!)) hi -= 1;
        if (hi > lo) add(lo, hi, "string", 110);
      }
    }
    return true;
  });
  // Resolve explicit parser/lexical ranges. Preserve original source bytes and
  // adjacent-token boundaries; only one winning range may own each code unit.
  const owner = new Int32Array(source.length).fill(-1);
  candidates.forEach((candidate, index) => {
    for (let at = candidate.start; at < candidate.end; at += 1) {
      const current = owner[at]!;
      if (current < 0 || candidate.priority >= candidates[current]!.priority) owner[at] = index;
    }
  });
  const spans: SemanticSpan[] = [];
  for (let start = 0; start < owner.length;) {
    const index = owner[start]!;
    let end = start + 1;
    while (end < owner.length && owner[end] === index) end += 1;
    if (index >= 0) {
      const candidate = candidates[index]!;
      spans.push({
        start,
        end,
        tokenType: candidate.tokenType,
        ...(candidate.modifiers ? { modifiers: candidate.modifiers } : {}),
      });
    } else if (source.slice(start, end).trim()) {
      throw new Error("Unlabeled source at " + start);
    }
    start = end;
  }
  return { offsetEncoding: "utf-16", spans };
}
