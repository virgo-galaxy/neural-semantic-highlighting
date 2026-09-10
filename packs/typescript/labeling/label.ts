import type { HighlightRequest, HighlightResult, SemanticSpan } from "@nsh/core";
import * as ts from "typescript";

const typeKeywordKinds = new Set<ts.SyntaxKind>([
  ts.SyntaxKind.AnyKeyword,
  ts.SyntaxKind.BigIntKeyword,
  ts.SyntaxKind.BooleanKeyword,
  ts.SyntaxKind.NeverKeyword,
  ts.SyntaxKind.NumberKeyword,
  ts.SyntaxKind.ObjectKeyword,
  ts.SyntaxKind.StringKeyword,
  ts.SyntaxKind.SymbolKeyword,
  ts.SyntaxKind.UnknownKeyword,
  ts.SyntaxKind.VoidKeyword,
  ts.SyntaxKind.UndefinedKeyword,
]);

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
  ts.SyntaxKind.AmpersandToken,
  ts.SyntaxKind.BarToken,
  ts.SyntaxKind.CaretToken,
  ts.SyntaxKind.EqualsGreaterThanToken,
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

function getVirtualFileName(documentKind: string): string {
  switch (documentKind) {
    case "javascript-esm":
      return "/source.mjs";
    case "javascript-commonjs":
      return "/source.cjs";
    case "jsx":
      return "/source.jsx";
    case "typescript-esm":
      return "/source.mts";
    case "typescript-commonjs":
      return "/source.cts";
    case "tsx":
      return "/source.tsx";
    case "typescript-declaration":
      return "/source.d.ts";
    case "typescript-esm-declaration":
      return "/source.d.mts";
    case "typescript-commonjs-declaration":
      return "/source.d.cts";
    case "javascript":
      return "/source.js";
    default:
      return "/source.ts";
  }
}

function classifyLexicalToken(kind: ts.SyntaxKind): string | undefined {
  if (typeKeywordKinds.has(kind)) {
    return "type";
  }

  if (kind >= ts.SyntaxKind.FirstKeyword && kind <= ts.SyntaxKind.LastKeyword) {
    return "keyword";
  }

  switch (kind) {
    case ts.SyntaxKind.NumericLiteral:
    case ts.SyntaxKind.BigIntLiteral:
      return "number";

    case ts.SyntaxKind.StringLiteral:
    case ts.SyntaxKind.NoSubstitutionTemplateLiteral:
    case ts.SyntaxKind.TemplateHead:
    case ts.SyntaxKind.TemplateMiddle:
    case ts.SyntaxKind.TemplateTail:
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

function createSourceFile(
  source: string,
  documentKind: string,
  scriptKind: ts.ScriptKind,
): ts.SourceFile {
  return ts.createSourceFile(
    getVirtualFileName(documentKind),
    source,
    ts.ScriptTarget.Latest,
    true,
    scriptKind,
  );
}

function hasQuestionToken(node: ts.Node): boolean {
  return (
    "questionToken" in node &&
    (node as ts.Node & { questionToken?: ts.QuestionToken }).questionToken !== undefined
  );
}

function getSemanticModifiers(node: ts.Node): string[] {
  const modifiers: string[] = [];
  const nodeModifiers = ts.canHaveModifiers(node) ? ts.getModifiers(node) : undefined;

  for (const modifier of nodeModifiers ?? []) {
    switch (modifier.kind) {
      case ts.SyntaxKind.ReadonlyKeyword:
        modifiers.push("readonly");
        break;
      case ts.SyntaxKind.StaticKeyword:
        modifiers.push("static");
        break;
      case ts.SyntaxKind.AsyncKeyword:
        modifiers.push("async");
        break;
      case ts.SyntaxKind.AbstractKeyword:
        modifiers.push("abstract");
        break;
      case ts.SyntaxKind.PublicKeyword:
        modifiers.push("public");
        break;
      case ts.SyntaxKind.ProtectedKeyword:
        modifiers.push("protected");
        break;
      case ts.SyntaxKind.PrivateKeyword:
        modifiers.push("private");
        break;
    }
  }

  if (hasQuestionToken(node)) {
    modifiers.push("optional");
  }

  return modifiers;
}

function isTypeOnlyImportSpecifier(node: ts.ImportSpecifier): boolean {
  if (node.isTypeOnly) {
    return true;
  }

  let current: ts.Node | undefined = node.parent;

  while (current) {
    if (ts.isImportClause(current)) {
      return current.isTypeOnly;
    }

    if (ts.isImportDeclaration(current)) {
      break;
    }

    current = current.parent;
  }

  return false;
}

function isTypeOnlyExportSpecifier(node: ts.ExportSpecifier): boolean {
  if (node.isTypeOnly) {
    return true;
  }

  let current: ts.Node | undefined = node.parent;

  while (current) {
    if (ts.isExportDeclaration(current)) {
      return current.isTypeOnly;
    }

    current = current.parent;
  }

  return false;
}

function isHandledDeclarationName(node: ts.Identifier): boolean {
  const parent = node.parent;

  return (
    (ts.isClassDeclaration(parent) && parent.name === node) ||
    (ts.isClassExpression(parent) && parent.name === node) ||
    (ts.isInterfaceDeclaration(parent) && parent.name === node) ||
    (ts.isTypeAliasDeclaration(parent) && parent.name === node) ||
    (ts.isModuleDeclaration(parent) && parent.name === node) ||
    (ts.isEnumDeclaration(parent) && parent.name === node) ||
    (ts.isEnumMember(parent) && parent.name === node) ||
    (ts.isFunctionDeclaration(parent) && parent.name === node) ||
    (ts.isFunctionExpression(parent) && parent.name === node) ||
    (ts.isMethodDeclaration(parent) && parent.name === node) ||
    (ts.isMethodSignature(parent) && parent.name === node) ||
    (ts.isPropertyDeclaration(parent) && parent.name === node) ||
    (ts.isPropertySignature(parent) && parent.name === node) ||
    (ts.isPropertyAssignment(parent) && parent.name === node) ||
    (ts.isShorthandPropertyAssignment(parent) && parent.name === node) ||
    (ts.isGetAccessorDeclaration(parent) && parent.name === node) ||
    (ts.isSetAccessorDeclaration(parent) && parent.name === node) ||
    (ts.isParameter(parent) && parent.name === node) ||
    (ts.isVariableDeclaration(parent) && parent.name === node) ||
    (ts.isTypeParameterDeclaration(parent) && parent.name === node) ||
    (ts.isNamespaceImport(parent) && parent.name === node) ||
    (ts.isImportSpecifier(parent) && parent.name === node) ||
    (ts.isBindingElement(parent) && parent.name === node)
  );
}

export function labelTypeScript(request: HighlightRequest): HighlightResult {
  const scriptKind = getScriptKind(request.documentKind);
  const languageVariant =
    scriptKind === ts.ScriptKind.JSX || scriptKind === ts.ScriptKind.TSX
      ? ts.LanguageVariant.JSX
      : ts.LanguageVariant.Standard;

  const sourceFile = createSourceFile(request.source, request.documentKind, scriptKind);

  let spans: SemanticSpan[] = [];

  function overlaps(left: SemanticSpan, right: SemanticSpan): boolean {
    return left.start < right.end && right.start < left.end;
  }

  function addSpan(
    start: number,
    end: number,
    tokenType: string,
    modifiers?: readonly string[],
  ): void {
    if (start < 0 || end <= start) {
      return;
    }

    const span: SemanticSpan = {
      start,
      end,
      tokenType,
      ...(modifiers?.length
        ? {
            modifiers: [...new Set(modifiers)],
          }
        : {}),
    };

    spans = spans.filter((existing) => !overlaps(existing, span));
    spans.push(span);
  }

  function addNodeSpan(node: ts.Node, tokenType: string, modifiers?: readonly string[]): void {
    addSpan(node.getStart(sourceFile), node.getEnd(), tokenType, modifiers);
  }

  function addDeclarationName(
    name: ts.DeclarationName | undefined,
    tokenType: string,
    declaration: ts.Node,
    extraModifiers: readonly string[] = [],
  ): void {
    if (!name || !ts.isIdentifier(name)) {
      return;
    }

    addNodeSpan(name, tokenType, [
      "declaration",
      ...getSemanticModifiers(declaration),
      ...extraModifiers,
    ]);
  }

  function addAngleBrackets<T extends ts.Node>(
    owner: ts.Node,
    nodes: ts.NodeArray<T> | undefined,
  ): void {
    if (!nodes?.length) {
      return;
    }

    const firstStart = nodes[0].getStart(sourceFile);
    const lastEnd = nodes[nodes.length - 1].getEnd();

    let left = firstStart - 1;

    while (left >= owner.getStart(sourceFile) && /\s/.test(request.source[left] ?? "")) {
      left -= 1;
    }

    if (request.source[left] === "<") {
      addSpan(left, left + 1, "punctuation");
    }

    let right = lastEnd;

    while (right < owner.getEnd() && /\s/.test(request.source[right] ?? "")) {
      right += 1;
    }

    if (request.source[right] === ">") {
      addSpan(right, right + 1, "punctuation");
    }
  }

  const jsxTextRanges: Array<{ start: number; end: number }> = [];

  function collectJsxTextRanges(node: ts.Node): void {
    if (ts.isJsxText(node)) {
      jsxTextRanges.push({
        start: node.getFullStart(),
        end: node.getEnd(),
      });
      return;
    }

    ts.forEachChild(node, collectJsxTextRanges);
  }

  collectJsxTextRanges(sourceFile);

  let jsxTextRangeIndex = 0;

  function overlapsJsxText(start: number, end: number): boolean {
    while (
      jsxTextRangeIndex < jsxTextRanges.length &&
      jsxTextRanges[jsxTextRangeIndex]!.end <= start
    ) {
      jsxTextRangeIndex += 1;
    }

    const range = jsxTextRanges[jsxTextRangeIndex];

    return range !== undefined && range.start < end && start < range.end;
  }

  const scanner = ts.createScanner(ts.ScriptTarget.Latest, false, languageVariant, request.source);
  const templateExpressionBraceDepths: number[] = [];

  for (let kind = scanner.scan(); kind !== ts.SyntaxKind.EndOfFileToken; kind = scanner.scan()) {
    const templateDepthIndex = templateExpressionBraceDepths.length - 1;

    if (templateDepthIndex >= 0) {
      if (kind === ts.SyntaxKind.OpenBraceToken) {
        templateExpressionBraceDepths[templateDepthIndex] += 1;
      } else if (kind === ts.SyntaxKind.CloseBraceToken) {
        const braceDepth = templateExpressionBraceDepths[templateDepthIndex];

        if (braceDepth > 0) {
          templateExpressionBraceDepths[templateDepthIndex] = braceDepth - 1;
        } else {
          kind = scanner.reScanTemplateToken(false);

          if (kind === ts.SyntaxKind.TemplateTail) {
            templateExpressionBraceDepths.pop();
          }
        }
      }
    }

    const tokenStart = scanner.getTokenPos();
    const tokenEnd = scanner.getTextPos();
    const tokenType = classifyLexicalToken(kind);

    if (tokenType && !overlapsJsxText(tokenStart, tokenEnd)) {
      addSpan(tokenStart, tokenEnd, tokenType);
    }

    if (kind === ts.SyntaxKind.TemplateHead) {
      templateExpressionBraceDepths.push(0);
    }
  }

  function isJsxTagIdentifier(node: ts.Identifier): boolean {
    let current: ts.Node = node;

    while (
      ts.isPropertyAccessExpression(current.parent) &&
      (current.parent.expression === current || current.parent.name === current)
    ) {
      current = current.parent;
    }

    const parent = current.parent;

    return (
      (ts.isJsxOpeningElement(parent) ||
        ts.isJsxSelfClosingElement(parent) ||
        ts.isJsxClosingElement(parent)) &&
      parent.tagName === current
    );
  }

  function addJsxTagName(node: ts.JsxTagNameExpression): void {
    if (ts.isIdentifier(node)) {
      addNodeSpan(node, "tag");
      return;
    }

    if (ts.isPropertyAccessExpression(node)) {
      if (ts.isIdentifier(node.expression)) {
        addNodeSpan(node.expression, "tag");
      } else if (ts.isPropertyAccessExpression(node.expression)) {
        addJsxTagName(node.expression);
      }

      const dotStart = node.expression.getEnd();
      const dotEnd = node.name.getStart(sourceFile);
      const dotOffset = request.source.indexOf(".", dotStart);

      if (dotOffset >= dotStart && dotOffset < dotEnd) {
        addSpan(dotOffset, dotOffset + 1, "punctuation");
      }

      addNodeSpan(node.name, "tag");
    }
  }

  function getQualifiedTypeTokenType(node: ts.Identifier): string | undefined {
    let current: ts.Node = node;

    while (ts.isQualifiedName(current.parent)) {
      current = current.parent;
    }

    if (!ts.isQualifiedName(current)) {
      return undefined;
    }

    const container = current.parent;

    if (!ts.isTypeReferenceNode(container) && !ts.isExpressionWithTypeArguments(container)) {
      return undefined;
    }

    return current.right === node ? "type" : "namespace";
  }

  function classifyIdentifier(node: ts.Identifier): void {
    const parent = node.parent;

    if (ts.isDecorator(parent) && parent.expression === node) {
      addNodeSpan(node, "decorator");
      return;
    }

    if (isJsxTagIdentifier(node)) {
      addNodeSpan(node, "tag");
      return;
    }

    if (ts.isJsxAttribute(parent) && parent.name === node) {
      addNodeSpan(node, "attribute");
      return;
    }

    if (
      (ts.isPropertyAssignment(parent) || ts.isShorthandPropertyAssignment(parent)) &&
      parent.name === node
    ) {
      addNodeSpan(node, "property", ["declaration"]);
      return;
    }

    if (isHandledDeclarationName(node)) {
      return;
    }

    if (ts.isPropertyAccessExpression(parent) && parent.name === node) {
      if (ts.isCallExpression(parent.parent) && parent.parent.expression === parent) {
        addNodeSpan(node, "method");
      } else {
        addNodeSpan(node, "property");
      }

      return;
    }

    const qualifiedTypeTokenType = getQualifiedTypeTokenType(node);

    if (qualifiedTypeTokenType) {
      addNodeSpan(node, qualifiedTypeTokenType);
      return;
    }

    if (
      ts.isTypeReferenceNode(parent) ||
      ts.isExpressionWithTypeArguments(parent) ||
      ts.isTypeQueryNode(parent)
    ) {
      addNodeSpan(node, "type");
      return;
    }

    if (ts.isExportSpecifier(parent)) {
      addNodeSpan(node, isTypeOnlyExportSpecifier(parent) ? "type" : "variable");
      return;
    }

    if (ts.isCallExpression(parent) && parent.expression === node) {
      addNodeSpan(node, "function");
      return;
    }

    if (ts.isNewExpression(parent) && parent.expression === node) {
      addNodeSpan(node, "class");
      return;
    }

    addNodeSpan(node, "variable");
  }

  function visit(node: ts.Node): void {
    if (node.kind === ts.SyntaxKind.RegularExpressionLiteral) {
      addNodeSpan(node, "regexp");
    }

    if (ts.isClassDeclaration(node) || ts.isClassExpression(node)) {
      addDeclarationName(node.name, "class", node);
    }

    if (ts.isInterfaceDeclaration(node)) {
      addDeclarationName(node.name, "interface", node);
      addAngleBrackets(node, node.typeParameters);
    }

    if (ts.isTypeAliasDeclaration(node)) {
      addDeclarationName(node.name, "type", node);
      addAngleBrackets(node, node.typeParameters);
    }

    if (ts.isModuleDeclaration(node) && ts.isIdentifier(node.name)) {
      addDeclarationName(node.name, "namespace", node);
    }

    if (ts.isEnumDeclaration(node)) {
      addDeclarationName(node.name, "enum", node);
    }

    if (ts.isEnumMember(node) && ts.isIdentifier(node.name)) {
      addNodeSpan(node.name, "enum-member", ["declaration"]);
    }

    if (ts.isTypeParameterDeclaration(node)) {
      addDeclarationName(node.name, "type-parameter", node);
    }

    if (ts.isFunctionDeclaration(node) || ts.isFunctionExpression(node)) {
      addDeclarationName(node.name, "function", node, node.asteriskToken ? ["generator"] : []);

      if (node.asteriskToken) {
        addNodeSpan(node.asteriskToken, "punctuation");
      }

      addAngleBrackets(node, node.typeParameters);
    }

    if (ts.isMethodDeclaration(node)) {
      addDeclarationName(node.name, "method", node, node.asteriskToken ? ["generator"] : []);

      if (node.asteriskToken) {
        addNodeSpan(node.asteriskToken, "punctuation");
      }

      addAngleBrackets(node, node.typeParameters);
    }

    if (ts.isMethodSignature(node)) {
      addDeclarationName(node.name, "method", node);
      addAngleBrackets(node, node.typeParameters);
    }

    if (ts.isConstructorDeclaration(node)) {
      const constructorToken = node.getFirstToken(sourceFile);

      if (constructorToken) {
        addNodeSpan(constructorToken, "constructor", ["declaration"]);
      }
    }

    if (ts.isPropertyDeclaration(node) || ts.isPropertySignature(node)) {
      if (ts.isIdentifier(node.name)) {
        addNodeSpan(node.name, "property", ["declaration", ...getSemanticModifiers(node)]);
      }
    }

    if (
      (ts.isPropertyAssignment(node) || ts.isShorthandPropertyAssignment(node)) &&
      ts.isIdentifier(node.name)
    ) {
      addNodeSpan(node.name, "property", ["declaration"]);
    }

    if (ts.isGetAccessorDeclaration(node) && ts.isIdentifier(node.name)) {
      addNodeSpan(node.name, "property", ["declaration", "getter", ...getSemanticModifiers(node)]);
    }

    if (ts.isSetAccessorDeclaration(node) && ts.isIdentifier(node.name)) {
      addNodeSpan(node.name, "property", ["declaration", "setter", ...getSemanticModifiers(node)]);
    }

    if (ts.isParameter(node)) {
      const modifiers = ["declaration", ...getSemanticModifiers(node)];

      if (ts.isIdentifier(node.name)) {
        addNodeSpan(node.name, "parameter", modifiers);
      } else {
        const visitBinding = (bindingNode: ts.Node): void => {
          if (ts.isBindingElement(bindingNode) && ts.isIdentifier(bindingNode.name)) {
            addNodeSpan(bindingNode.name, "parameter", modifiers);
          }

          ts.forEachChild(bindingNode, visitBinding);
        };

        visitBinding(node.name);
      }
    }

    if (ts.isVariableDeclaration(node)) {
      const modifiers = ["declaration"];
      const declarationList = node.parent;

      if (
        ts.isVariableDeclarationList(declarationList) &&
        (declarationList.flags & ts.NodeFlags.Const) !== 0
      ) {
        modifiers.push("readonly");
      }

      const visitBinding = (bindingNode: ts.Node): void => {
        if (ts.isIdentifier(bindingNode)) {
          addNodeSpan(bindingNode, "variable", modifiers);
          return;
        }

        ts.forEachChild(bindingNode, visitBinding);
      };

      visitBinding(node.name);
    }

    if (ts.isNamespaceImport(node)) {
      addNodeSpan(node.name, "namespace", ["declaration"]);

      const starPosition = request.source.indexOf("*", node.getStart(sourceFile));

      if (starPosition >= 0 && starPosition < node.name.getStart(sourceFile)) {
        addSpan(starPosition, starPosition + 1, "punctuation");
      }
    }

    if (ts.isImportSpecifier(node)) {
      const tokenType = isTypeOnlyImportSpecifier(node) ? "type" : "variable";
      addNodeSpan(node.name, tokenType, ["declaration"]);
    }

    if (ts.isTypeReferenceNode(node)) {
      addAngleBrackets(node, node.typeArguments);

      if (ts.isIdentifier(node.typeName)) {
        addNodeSpan(node.typeName, "type");
      }
    }

    if (ts.isExpressionWithTypeArguments(node)) {
      addAngleBrackets(node, node.typeArguments);

      if (ts.isIdentifier(node.expression)) {
        addNodeSpan(node.expression, "type");
      }
    }

    if (ts.isCallExpression(node)) {
      addAngleBrackets(node, node.typeArguments);
    }

    if (ts.isNewExpression(node)) {
      addAngleBrackets(node, node.typeArguments);

      if (ts.isIdentifier(node.expression)) {
        addNodeSpan(node.expression, "class");
      }
    }

    if (ts.isDecorator(node) && ts.isIdentifier(node.expression)) {
      addNodeSpan(node.expression, "decorator");
    }

    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const start = node.getStart(sourceFile);
      const end = node.getEnd();

      if (request.source[start] === "<") {
        addSpan(start, start + 1, "punctuation");
      }

      addJsxTagName(node.tagName);

      for (const attribute of node.attributes.properties) {
        if (!ts.isJsxAttribute(attribute)) {
          continue;
        }

        addNodeSpan(attribute.name, "attribute");

        if (attribute.initializer) {
          const equalsPosition = request.source.indexOf("=", attribute.name.getEnd());

          if (
            equalsPosition >= attribute.name.getEnd() &&
            equalsPosition < attribute.initializer.getStart(sourceFile) + 1
          ) {
            addSpan(equalsPosition, equalsPosition + 1, "punctuation");
          }
        }
      }

      if (request.source[end - 1] === ">") {
        addSpan(end - 1, end, "punctuation");
      }

      if (request.source[end - 2] === "/") {
        addSpan(end - 2, end - 1, "punctuation");
      }
    }

    if (ts.isJsxFragment(node)) {
      const openingStart = node.openingFragment.getStart(sourceFile);
      const openingEnd = node.openingFragment.getEnd();
      const closingStart = node.closingFragment.getStart(sourceFile);
      const closingEnd = node.closingFragment.getEnd();

      if (request.source[openingStart] === "<") {
        addSpan(openingStart, openingStart + 1, "punctuation");
      }

      if (request.source[openingEnd - 1] === ">") {
        addSpan(openingEnd - 1, openingEnd, "punctuation");
      }

      if (request.source[closingStart] === "<") {
        addSpan(closingStart, closingStart + 1, "punctuation");
      }

      if (request.source[closingStart + 1] === "/") {
        addSpan(closingStart + 1, closingStart + 2, "punctuation");
      }

      if (request.source[closingEnd - 1] === ">") {
        addSpan(closingEnd - 1, closingEnd, "punctuation");
      }
    }

    if (ts.isJsxClosingElement(node)) {
      const start = node.getStart(sourceFile);
      const end = node.getEnd();

      if (request.source[start] === "<") {
        addSpan(start, start + 1, "punctuation");
      }

      if (request.source[start + 1] === "/") {
        addSpan(start + 1, start + 2, "punctuation");
      }

      addJsxTagName(node.tagName);

      if (request.source[end - 1] === ">") {
        addSpan(end - 1, end, "punctuation");
      }
    }

    if (ts.isBinaryExpression(node)) {
      addNodeSpan(node.operatorToken, "operator");
    }

    if (ts.isIdentifier(node)) {
      classifyIdentifier(node);
    }

    ts.forEachChild(node, visit);
  }

  visit(sourceFile);

  spans.sort((left, right) => left.start - right.start || left.end - right.end);

  return {
    offsetEncoding: "utf-16",
    spans,
  };
}
