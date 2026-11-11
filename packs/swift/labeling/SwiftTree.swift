// Offline source-accurate parsing only. Never typechecks, expands macros or runs input.
import Foundation
import SwiftParser
import SwiftParserDiagnostics
import SwiftSyntax

func fields(_ node: Syntax) -> [SyntaxIdentifier: String] {
    var result: [SyntaxIdentifier: String] = [:]
    func add<S: SyntaxProtocol>(_ name: String, _ value: S?) {
        if let value { result[value.id] = name }
    }
    if let named = node.asProtocol(NamedDeclSyntax.self) { add("name", named.name) }
    if let n = node.as(FunctionDeclSyntax.self) { add("body", n.body); add("signature", n.signature) }
    if let n = node.as(FunctionParameterSyntax.self) { add("firstName", n.firstName); add("secondName", n.secondName); add("type", n.type) }
    if let n = node.as(TupleTypeElementSyntax.self) { add("firstName", n.firstName); add("secondName", n.secondName); add("type", n.type) }
    if let n = node.as(EnumCaseParameterSyntax.self) { add("firstName", n.firstName); add("secondName", n.secondName); add("type", n.type) }
    if let n = node.as(ClosureParameterSyntax.self) { add("firstName", n.firstName); add("secondName", n.secondName); add("type", n.type) }
    if let n = node.as(ClosureShorthandParameterSyntax.self) { add("name", n.name) }
    if let n = node.as(GenericParameterSyntax.self) { add("name", n.name); add("type", n.inheritedType) }
    if let n = node.as(VariableDeclSyntax.self) { add("bindingSpecifier", n.bindingSpecifier); add("bindings", n.bindings) }
    if let n = node.as(PatternBindingSyntax.self) { add("pattern", n.pattern); add("initializer", n.initializer); add("type", n.typeAnnotation) }
    if let n = node.as(IdentifierPatternSyntax.self) { add("name", n.identifier) }
    if let n = node.as(IdentifierTypeSyntax.self) { add("name", n.name) }
    if let n = node.as(MemberTypeSyntax.self) { add("name", n.name); add("base", n.baseType) }
    if let n = node.as(DeclReferenceExprSyntax.self) { add("name", n.baseName) }
    if let n = node.as(MemberAccessExprSyntax.self) { add("base", n.base); add("member", n.declName) }
    if let n = node.as(FunctionCallExprSyntax.self) { add("function", n.calledExpression); add("arguments", n.arguments) }
    if let n = node.as(LabeledExprSyntax.self) { add("label", n.label); add("expression", n.expression) }
    if let n = node.as(ClosureExprSyntax.self) { add("signature", n.signature); add("body", n.statements) }
    if let n = node.as(InitializerDeclSyntax.self) { add("name", n.initKeyword); add("body", n.body) }
    if let n = node.as(DeinitializerDeclSyntax.self) { add("name", n.deinitKeyword); add("body", n.body) }
    if let n = node.as(EnumCaseElementSyntax.self) { add("name", n.name) }
    if let n = node.as(ImportPathComponentSyntax.self) { add("name", n.name) }
    if let n = node.as(AttributeSyntax.self) { add("name", n.attributeName); add("arguments", n.arguments) }
    if let n = node.as(MacroExpansionExprSyntax.self) { add("name", n.macroName) }
    if let n = node.as(MacroExpansionDeclSyntax.self) { add("name", n.macroName) }
    if let n = node.as(AccessorDeclSyntax.self) { add("name", n.accessorSpecifier); add("parameters", n.parameters); add("body", n.body) }
    if let n = node.as(AccessorParametersSyntax.self) { add("name", n.name) }
    if let n = node.as(ExtensionDeclSyntax.self) { add("type", n.extendedType) }
    if let n = node.as(ForStmtSyntax.self) { add("pattern", n.pattern); add("sequence", n.sequence); add("body", n.body) }
    if let n = node.as(OptionalBindingConditionSyntax.self) { add("pattern", n.pattern); add("initializer", n.initializer) }
    if let n = node.as(ValueBindingPatternSyntax.self) { add("pattern", n.pattern) }
    if let n = node.as(LabeledStmtSyntax.self) { add("name", n.labelName) }
    if let n = node.as(BreakStmtSyntax.self) { add("name", n.label) }
    if let n = node.as(ContinueStmtSyntax.self) { add("name", n.label) }
    if let n = node.as(ClosureCaptureSyntax.self) { add("name", n.name); add("expression", n.expression) }
    if let n = node.as(DeclNameArgumentSyntax.self) { add("name", n.name) }
    return result
}

func extract(_ node: Syntax, field: String? = nil) -> [String: Any] {
    var out: [String: Any] = ["kind": String(describing: node.kind),
        "start": node.positionAfterSkippingLeadingTrivia.utf8Offset,
        "end": node.endPositionBeforeTrailingTrivia.utf8Offset]
    if let field { out["field"] = field }
    if node.asProtocol(TypeSyntaxProtocol.self) != nil { out["isType"] = true }
    if let token = node.as(TokenSyntax.self) {
        let kind = String(describing: token.tokenKind)
        out["tokenKind"] = String(kind.prefix { $0 != "(" })
    } else {
        let names = fields(node)
        out["children"] = node.children(viewMode: .sourceAccurate).map { extract($0, field: names[$0.id]) }
    }
    return out
}

func comments(_ tree: SourceFileSyntax) -> [[String: Any]] {
    var result: [[String: Any]] = []
    func trivia(_ value: Trivia, at start: Int, inString: Bool) {
        var offset = start
        for piece in value {
            let count = piece.sourceLength.utf8Length
            switch piece {
            case .lineComment, .docLineComment, .blockComment, .docBlockComment:
                result.append(["start": offset, "end": offset + count, "kind": "comment"])
            case .backslashes, .pounds:
                if inString { result.append(["start": offset, "end": offset + count, "kind": "string"]) }
            default: break
            }
            offset += count
        }
    }
    for token in tree.tokens(viewMode: .sourceAccurate) {
        var parent = token.parent
        var inString = false
        while let node = parent {
            if node.is(StringLiteralExprSyntax.self) { inString = true; break }
            parent = node.parent
        }
        trivia(token.leadingTrivia, at: token.position.utf8Offset, inString: inString)
        trivia(token.trailingTrivia, at: token.endPositionBeforeTrailingTrivia.utf8Offset, inString: inString)
    }
    return result
}

while let line = readLine() {
    autoreleasepool {
        do {
            guard let data = Data(base64Encoded: line), data.count <= 2_000_000,
                  let source = String(data: data, encoding: .utf8) else {
                throw NSError(domain: "SwiftGold", code: 1)
            }
            let tree = Parser.parse(source: source)
            let output: [String: Any]
            if tree.hasError {
                output = ["error": ParseDiagnosticsGenerator.diagnostics(for: tree).map { $0.message }.prefix(5).joined(separator: "; ")]
            } else {
                output = ["tree": extract(Syntax(tree)), "comments": comments(tree)]
            }
            let json = try JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
            FileHandle.standardOutput.write(json + Data([10]))
        } catch {
            FileHandle.standardOutput.write(Data("{\"error\":\"Swift parse-only request failed\"}\n".utf8))
        }
    }
}
