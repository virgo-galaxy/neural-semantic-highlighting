import * as ts from "typescript";

import type { HighlightRequest } from "@/core/pack.js";
import type { HighlightResult, SemanticSpan } from "@/core/result.js";

const operatorKinds = new Set<ts.SyntaxKind>([
  ts.SyntaxKind.EqualsToken,
  ts.SyntaxKind.PlusToken,
  ts.SyntaxKind.MinusToken,
  ts.SyntaxKind.AsteriskToken,
  ts.SyntaxKind.SlashToken,
  ts.SyntaxKind.PercentToken,
  ts.SyntaxKind.PlusPlusToken,
  ts.SyntaxKind.MinusMinusToken,
  ts.SyntaxKind.AmpersandAmpersandToken,
  ts.SyntaxKind.BarBarToken,
  ts.SyntaxKind.QuestionQuestionToken,
  ts.SyntaxKind.EqualsEqualsToken,
  ts.SyntaxKind.EqualsEqualsEqualsToken,
  ts.SyntaxKind.ExclamationEqualsToken,
  ts.SyntaxKind.ExclamationEqualsEqualsToken,
  ts.SyntaxKind.LessThanToken,
  ts.SyntaxKind.GreaterThanToken,
  ts.SyntaxKind.LessThanEqualsToken,
  ts.SyntaxKind.GreaterThanEqualsToken,
]);

const punctuationKinds = new Set<ts.SyntaxKind>([
  ts.SyntaxKind.OpenBraceToken,
  ts.SyntaxKind.CloseBraceToken,
  ts.SyntaxKind.OpenParenToken,
  ts.SyntaxKind.CloseParenToken,
  ts.SyntaxKind.OpenBracketToken,
  ts.SyntaxKind.CloseBracketToken,
  ts.SyntaxKind.DotToken,
  ts.SyntaxKind.CommaToken,
  ts.SyntaxKind.SemicolonToken,
  ts.SyntaxKind.ColonToken,
  ts.SyntaxKind.QuestionToken,
  ts.SyntaxKind.AtToken,
]);

function getScriptKind(documentKind: string): ts.ScriptKind {
  switch (documentKind) {
    case "javascript":
    case "javascript-esm":
    case "javascript-commonjs":
      return ts.ScriptKind.JS;

    case "jsx":
      return ts.ScriptKind.JSX;

    case "tsx":
      return ts.ScriptKind.TSX;

    case "typescript":
    case "typescript-esm":
    case "typescript-commonjs":
    case "typescript-declaration":
    case "typescript-esm-declaration":
    case "typescript-commonjs-declaration":
      return ts.ScriptKind.TS;

    default:
      throw new Error(`Unsupported TypeScript document kind "${documentKind}".`);
  }
}

function classifyLexicalToken(kind: ts.SyntaxKind): string | undefined {
  if (kind >= ts.SyntaxKind.FirstKeyword && kind <= ts.SyntaxKind.LastKeyword) {
    return "keyword";
  }

  switch (kind) {
    case ts.SyntaxKind.NumericLiteral:
    case ts.SyntaxKind.BigIntLiteral:
      return "number";

    case ts.SyntaxKind.StringLiteral:
    case ts.SyntaxKind.NoSubstitutionTemplateLiteral:
      return "string";

    case ts.SyntaxKind.RegularExpressionLiteral:
      return "regexp";

    case ts.SyntaxKind.SingleLineCommentTrivia:
    case ts.SyntaxKind.MultiLineCommentTrivia:
      return "comment";
  }

  if (operatorKinds.has(kind)) {
    return "operator";
  }

  if (punctuationKinds.has(kind)) {
    return "punctuation";
  }

  return undefined;
}

export function labelTypeScript(request: HighlightRequest): HighlightResult {
  const scriptKind = getScriptKind(request.documentKind);

  const languageVariant =
    scriptKind === ts.ScriptKind.JSX || scriptKind === ts.ScriptKind.TSX
      ? ts.LanguageVariant.JSX
      : ts.LanguageVariant.Standard;

  const sourceFile = ts.createSourceFile(
    "source.ts",
    request.source,
    ts.ScriptTarget.Latest,
    true,
    scriptKind,
  );

  const spans: SemanticSpan[] = [];

  const scanner = ts.createScanner(ts.ScriptTarget.Latest, false, languageVariant, request.source);

  for (let kind = scanner.scan(); kind !== ts.SyntaxKind.EndOfFileToken; kind = scanner.scan()) {
    const tokenType = classifyLexicalToken(kind);

    if (!tokenType) {
      continue;
    }

    spans.push({
      start: scanner.getTokenPos(),
      end: scanner.getTextPos(),
      tokenType,
    });
  }

  function visit(node: ts.Node): void {
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name)) {
      const modifiers = ["declaration"];

      if (
        ts.isVariableDeclarationList(node.parent) &&
        (node.parent.flags & ts.NodeFlags.Const) !== 0
      ) {
        modifiers.push("readonly");
      }

      spans.push({
        start: node.name.getStart(sourceFile),
        end: node.name.getEnd(),
        tokenType: "variable",
        modifiers,
      });
    }

    ts.forEachChild(node, visit);
  }

  visit(sourceFile);

  spans.sort((left, right) => left.start - right.start);

  return {
    offsetEncoding: "utf-16",
    spans,
  };
}
