import * as ts from "typescript";

import type { HighlightRequest } from "@/core/pack.js";
import type { HighlightResult, SemanticSpan } from "@/core/result.js";

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

interface ProgramContext {
  sourceFile: ts.SourceFile;
  checker: ts.TypeChecker;
}

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

function createProgramContext(
  source: string,
  documentKind: string,
  scriptKind: ts.ScriptKind,
): ProgramContext {
  const fileName = getVirtualFileName(documentKind);

  const options: ts.CompilerOptions = {
    target: ts.ScriptTarget.Latest,
    module: ts.ModuleKind.ESNext,
    jsx: ts.JsxEmit.Preserve,
    noLib: true,
    noResolve: true,
  };

  const sourceFile = ts.createSourceFile(
    fileName,
    source,
    ts.ScriptTarget.Latest,
    true,
    scriptKind,
  );

  const host = ts.createCompilerHost(options, true);

  host.getSourceFile = (requestedFileName) =>
    requestedFileName === fileName ? sourceFile : undefined;
  host.fileExists = (requestedFileName) => requestedFileName === fileName;
  host.readFile = (requestedFileName) => (requestedFileName === fileName ? source : undefined);

  const program = ts.createProgram({
    rootNames: [fileName],
    options,
    host,
  });

  const programSourceFile = program.getSourceFile(fileName);

  if (!programSourceFile) {
    throw new Error(`Failed to create TypeScript source file "${fileName}".`);
  }

  return {
    sourceFile: programSourceFile,
    checker: program.getTypeChecker(),
  };
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

function getDeclarationTokenType(declaration: ts.Declaration): string | undefined {
  if (ts.isClassDeclaration(declaration) || ts.isClassExpression(declaration)) {
    return "class";
  }

  if (ts.isInterfaceDeclaration(declaration)) {
    return "interface";
  }

  if (ts.isEnumDeclaration(declaration)) {
    return "enum";
  }

  if (ts.isEnumMember(declaration)) {
    return "enum-member";
  }

  if (ts.isTypeParameterDeclaration(declaration)) {
    return "type-parameter";
  }

  if (
    ts.isFunctionDeclaration(declaration) ||
    ts.isFunctionExpression(declaration) ||
    ts.isArrowFunction(declaration)
  ) {
    return "function";
  }

  if (ts.isMethodDeclaration(declaration) || ts.isMethodSignature(declaration)) {
    return "method";
  }

  if (
    ts.isPropertyDeclaration(declaration) ||
    ts.isPropertySignature(declaration) ||
    ts.isGetAccessorDeclaration(declaration) ||
    ts.isSetAccessorDeclaration(declaration)
  ) {
    return "property";
  }

  if (ts.isParameter(declaration)) {
    return "parameter";
  }

  if (ts.isVariableDeclaration(declaration)) {
    return "variable";
  }

  if (ts.isBindingElement(declaration)) {
    let parent: ts.Node = declaration.parent;

    while (!ts.isParameter(parent) && !ts.isVariableDeclaration(parent)) {
      parent = parent.parent;
    }

    return ts.isParameter(parent) ? "parameter" : "variable";
  }

  if (ts.isNamespaceImport(declaration)) {
    return "namespace";
  }

  if (ts.isImportSpecifier(declaration)) {
    return declaration.isTypeOnly ? "type" : "variable";
  }

  if (ts.isTypeAliasDeclaration(declaration)) {
    return "type";
  }

  return undefined;
}

function isHandledDeclarationName(node: ts.Identifier): boolean {
  const parent = node.parent;

  return (
    (ts.isClassDeclaration(parent) && parent.name === node) ||
    (ts.isClassExpression(parent) && parent.name === node) ||
    (ts.isInterfaceDeclaration(parent) && parent.name === node) ||
    (ts.isEnumDeclaration(parent) && parent.name === node) ||
    (ts.isEnumMember(parent) && parent.name === node) ||
    (ts.isFunctionDeclaration(parent) && parent.name === node) ||
    (ts.isFunctionExpression(parent) && parent.name === node) ||
    (ts.isMethodDeclaration(parent) && parent.name === node) ||
    (ts.isMethodSignature(parent) && parent.name === node) ||
    (ts.isPropertyDeclaration(parent) && parent.name === node) ||
    (ts.isPropertySignature(parent) && parent.name === node) ||
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

  const { sourceFile, checker } = createProgramContext(
    request.source,
    request.documentKind,
    scriptKind,
  );

  let spans: SemanticSpan[] = [];
  const knownTokenTypes = new Map<string, string>();

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

    knownTokenTypes.set(name.text, tokenType);

    addNodeSpan(name, tokenType, [
      "declaration",
      ...getSemanticModifiers(declaration),
      ...extraModifiers,
    ]);
  }

  function getTokenTypeFromSymbol(node: ts.Identifier): string | undefined {
    const symbol = checker.getSymbolAtLocation(node);

    if (!symbol) {
      return undefined;
    }

    for (const declaration of symbol.getDeclarations() ?? []) {
      const tokenType = getDeclarationTokenType(declaration);

      if (tokenType) {
        return tokenType;
      }
    }

    return undefined;
  }

  function addAngleBrackets(owner: ts.Node, nodes: ts.NodeArray<ts.Node> | undefined): void {
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

  const scanner = ts.createScanner(ts.ScriptTarget.Latest, false, languageVariant, request.source);

  for (let kind = scanner.scan(); kind !== ts.SyntaxKind.EndOfFileToken; kind = scanner.scan()) {
    const tokenType = classifyLexicalToken(kind);

    if (!tokenType) {
      continue;
    }

    addSpan(scanner.getTokenPos(), scanner.getTextPos(), tokenType);
  }

  function classifyIdentifier(node: ts.Identifier): void {
    const parent = node.parent;

    if (ts.isDecorator(parent) && parent.expression === node) {
      addNodeSpan(node, "decorator");
      return;
    }

    if (
      (ts.isJsxOpeningElement(parent) ||
        ts.isJsxSelfClosingElement(parent) ||
        ts.isJsxClosingElement(parent)) &&
      parent.tagName === node
    ) {
      addNodeSpan(node, "tag");
      return;
    }

    if (ts.isJsxAttribute(parent) && parent.name === node) {
      addNodeSpan(node, "attribute");
      return;
    }

    if (isHandledDeclarationName(node)) {
      return;
    }

    if (ts.isPropertyAccessExpression(parent) && parent.name === node) {
      const symbolTokenType = getTokenTypeFromSymbol(node);

      if (symbolTokenType) {
        addNodeSpan(node, symbolTokenType);
        return;
      }

      if (ts.isCallExpression(parent.parent) && parent.parent.expression === parent) {
        addNodeSpan(node, "method");
      } else {
        addNodeSpan(node, "property");
      }

      return;
    }

    if (
      ts.isTypeReferenceNode(parent) ||
      ts.isExpressionWithTypeArguments(parent) ||
      ts.isTypeQueryNode(parent)
    ) {
      addNodeSpan(node, getTokenTypeFromSymbol(node) ?? "type");
      return;
    }

    if (ts.isExportSpecifier(parent)) {
      addNodeSpan(
        node,
        getTokenTypeFromSymbol(node) ??
          knownTokenTypes.get(node.text) ??
          (parent.isTypeOnly ? "type" : "variable"),
      );
      return;
    }

    const symbolTokenType = getTokenTypeFromSymbol(node);

    if (symbolTokenType) {
      addNodeSpan(node, symbolTokenType);
      return;
    }

    if (ts.isCallExpression(parent) && parent.expression === node) {
      addNodeSpan(node, "function");
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

    if (ts.isEnumDeclaration(node)) {
      addDeclarationName(node.name, "enum", node);
    }

    if (ts.isEnumMember(node) && ts.isIdentifier(node.name)) {
      knownTokenTypes.set(node.name.text, "enum-member");
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
        knownTokenTypes.set(node.name.text, "property");
        addNodeSpan(node.name, "property", ["declaration", ...getSemanticModifiers(node)]);
      }
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
          knownTokenTypes.set(bindingNode.text, "variable");
          addNodeSpan(bindingNode, "variable", modifiers);
          return;
        }

        ts.forEachChild(bindingNode, visitBinding);
      };

      visitBinding(node.name);
    }

    if (ts.isNamespaceImport(node)) {
      knownTokenTypes.set(node.name.text, "namespace");
      addNodeSpan(node.name, "namespace", ["declaration"]);

      const starPosition = request.source.indexOf("*", node.getStart(sourceFile));

      if (starPosition >= 0 && starPosition < node.name.getStart(sourceFile)) {
        addSpan(starPosition, starPosition + 1, "punctuation");
      }
    }

    if (ts.isImportSpecifier(node)) {
      const tokenType = node.isTypeOnly ? "type" : "variable";
      knownTokenTypes.set(node.name.text, tokenType);
      addNodeSpan(node.name, tokenType, ["declaration"]);
    }

    if (ts.isTypeReferenceNode(node)) {
      addAngleBrackets(node, node.typeArguments);

      if (ts.isIdentifier(node.typeName)) {
        addNodeSpan(node.typeName, getTokenTypeFromSymbol(node.typeName) ?? "type");
      }
    }

    if (ts.isExpressionWithTypeArguments(node)) {
      addAngleBrackets(node, node.typeArguments);

      if (ts.isIdentifier(node.expression)) {
        addNodeSpan(node.expression, getTokenTypeFromSymbol(node.expression) ?? "type");
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

      addNodeSpan(node.tagName, "tag");

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

    if (ts.isJsxClosingElement(node)) {
      const start = node.getStart(sourceFile);
      const end = node.getEnd();

      if (request.source[start] === "<") {
        addSpan(start, start + 1, "punctuation");
      }

      if (request.source[start + 1] === "/") {
        addSpan(start + 1, start + 2, "punctuation");
      }

      addNodeSpan(node.tagName, "tag");

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
