package labeling

import (
	"go/ast"
	"go/parser"
	"go/token"
)

// typeSwitchDeclarations finds explicit identifiers whose case-local objects
// are not represented by a single object in types.Info.Defs. This is a syntactic
// declaration, regardless of the types selected by the individual case clauses.
func typeSwitchDeclarations(file *ast.File) []*ast.Ident {
	var identifiers []*ast.Ident
	ast.Inspect(file, func(node ast.Node) bool {
		statement, ok := node.(*ast.TypeSwitchStmt)
		if !ok {
			return true
		}
		assignment, ok := statement.Assign.(*ast.AssignStmt)
		if !ok || assignment.Tok != token.DEFINE || len(assignment.Lhs) != 1 || len(assignment.Rhs) != 1 {
			return true
		}
		assertion, ok := assignment.Rhs[0].(*ast.TypeAssertExpr)
		if !ok || assertion.Type != nil {
			return true
		}
		identifier, ok := assignment.Lhs[0].(*ast.Ident)
		if ok && identifier.Name != "_" {
			identifiers = append(identifiers, identifier)
		}
		return true
	})
	return identifiers
}

// TypeSwitchDeclarationSpans returns only syntax-proven type-switch guard
// declarations. It does not import packages, type-check a module, resolve other
// identifiers, or infer labels for arbitrary gaps in an existing Gold record.
func TypeSwitchDeclarationSpans(source string) ([]SemanticSpan, error) {
	fileSet := token.NewFileSet()
	file, err := parser.ParseFile(fileSet, "source.go", source, parser.AllErrors)
	if err != nil {
		return nil, err
	}
	offsets := buildUTF16Offsets(source)
	spans := make([]SemanticSpan, 0)
	for _, identifier := range typeSwitchDeclarations(file) {
		start := fileSet.PositionFor(identifier.Pos(), false).Offset
		end := fileSet.PositionFor(identifier.End(), false).Offset
		spans = append(spans, SemanticSpan{
			Start: offsets[start], End: offsets[end], TokenType: "variable",
			Modifiers: []string{"declaration"},
		})
	}
	return spans, nil
}
