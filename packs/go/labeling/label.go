package labeling

import (
	"fmt"
	"go/ast"
	"go/importer"
	"go/parser"
	"go/scanner"
	"go/token"
	"go/types"
	"sort"
	"unicode/utf8"
)

type HighlightRequest struct {
	Source       string `json:"source"`
	DocumentKind string `json:"documentKind"`
}

type SemanticSpan struct {
	Start     int      `json:"start"`
	End       int      `json:"end"`
	TokenType string   `json:"tokenType"`
	Modifiers []string `json:"modifiers,omitempty"`
}

type HighlightResult struct {
	OffsetEncoding string         `json:"offsetEncoding"`
	Spans          []SemanticSpan `json:"spans"`
}

type labeler struct {
	source       string
	fileSet      *token.FileSet
	file         *ast.File
	info         *types.Info
	utf16Offsets []int
	spans        []SemanticSpan
}

var predeclaredTypes = map[string]struct{}{
	"any": {}, "bool": {}, "byte": {}, "comparable": {}, "complex128": {}, "complex64": {},
	"error": {}, "float32": {}, "float64": {}, "int": {}, "int16": {}, "int32": {}, "int64": {},
	"int8": {}, "rune": {}, "string": {}, "uint": {}, "uint16": {}, "uint32": {}, "uint64": {},
	"uint8": {}, "uintptr": {},
}

var predeclaredFunctions = map[string]struct{}{
	"append": {}, "cap": {}, "clear": {}, "close": {}, "complex": {}, "copy": {}, "delete": {},
	"imag": {}, "len": {}, "make": {}, "max": {}, "min": {}, "new": {}, "panic": {}, "print": {},
	"println": {}, "real": {}, "recover": {},
}

var predeclaredValues = map[string]struct{}{
	"false": {}, "iota": {}, "nil": {}, "true": {},
}

func Label(request HighlightRequest) (HighlightResult, error) {
	if request.DocumentKind != "go" {
		return HighlightResult{}, fmt.Errorf("unsupported Go document kind %q", request.DocumentKind)
	}

	fileSet := token.NewFileSet()
	file, err := parser.ParseFile(fileSet, "source.go", request.Source, parser.ParseComments|parser.AllErrors)
	if err != nil {
		return HighlightResult{}, fmt.Errorf("parse Go source: %w", err)
	}

	info := &types.Info{
		Defs:       make(map[*ast.Ident]types.Object),
		Uses:       make(map[*ast.Ident]types.Object),
		Selections: make(map[*ast.SelectorExpr]*types.Selection),
		Types:      make(map[ast.Expr]types.TypeAndValue),
	}

	config := types.Config{
		Importer: importer.Default(),
		Error:    func(error) {},
	}
	_, _ = config.Check("nsh.local", fileSet, []*ast.File{file}, info)

	l := &labeler{
		source:       request.Source,
		fileSet:      fileSet,
		file:         file,
		info:         info,
		utf16Offsets: buildUTF16Offsets(request.Source),
	}

	l.labelLexicalTokens()
	l.labelIdentifiers()
	l.sortAndValidate()

	return HighlightResult{
		OffsetEncoding: "utf-16",
		Spans:          l.spans,
	}, nil
}

func buildUTF16Offsets(source string) []int {
	offsets := make([]int, len(source)+1)
	utf16Offset := 0

	for byteOffset := 0; byteOffset < len(source); {
		r, size := utf8.DecodeRuneInString(source[byteOffset:])
		units := 1
		if r > 0xffff {
			units = 2
		}

		for i := 0; i < size; i++ {
			offsets[byteOffset+i] = utf16Offset
		}

		byteOffset += size
		utf16Offset += units
		offsets[byteOffset] = utf16Offset
	}

	return offsets
}

func (l *labeler) utf16(byteOffset int) int {
	if byteOffset < 0 {
		return 0
	}
	if byteOffset >= len(l.utf16Offsets) {
		return l.utf16Offsets[len(l.utf16Offsets)-1]
	}
	return l.utf16Offsets[byteOffset]
}

func (l *labeler) byteRange(start token.Pos, end token.Pos) (int, int) {
	return l.fileSet.PositionFor(start, false).Offset, l.fileSet.PositionFor(end, false).Offset
}

func (l *labeler) addSpan(startByte, endByte int, tokenType string, modifiers ...string) {
	if startByte < 0 || endByte <= startByte || endByte > len(l.source) {
		return
	}

	span := SemanticSpan{
		Start:     l.utf16(startByte),
		End:       l.utf16(endByte),
		TokenType: tokenType,
	}

	if len(modifiers) > 0 {
		seen := make(map[string]struct{}, len(modifiers))
		for _, modifier := range modifiers {
			if modifier == "" {
				continue
			}
			if _, ok := seen[modifier]; ok {
				continue
			}
			seen[modifier] = struct{}{}
			span.Modifiers = append(span.Modifiers, modifier)
		}
	}

	for i := len(l.spans) - 1; i >= 0; i-- {
		existing := l.spans[i]
		if span.Start < existing.End && existing.Start < span.End {
			l.spans = append(l.spans[:i], l.spans[i+1:]...)
		}
	}

	l.spans = append(l.spans, span)
}

func (l *labeler) addNode(node ast.Node, tokenType string, modifiers ...string) {
	start, end := l.byteRange(node.Pos(), node.End())
	l.addSpan(start, end, tokenType, modifiers...)
}

func (l *labeler) labelLexicalTokens() {
	var s scanner.Scanner
	file := l.fileSet.File(l.file.Pos())
	if file == nil {
		return
	}

	s.Init(file, []byte(l.source), nil, scanner.ScanComments)

	for {
		pos, tok, lit := s.Scan()
		if tok == token.EOF {
			break
		}

		if tok == token.SEMICOLON && lit == "\n" {
			continue
		}

		start := l.fileSet.PositionFor(pos, false).Offset
		length := len(lit)
		if length == 0 {
			length = len(tok.String())
		}
		end := start + length

		switch {
		case tok.IsKeyword():
			l.addSpan(start, end, "keyword")
		case tok == token.COMMENT:
			l.addSpan(start, end, "comment")
		case tok == token.STRING || tok == token.CHAR:
			l.addSpan(start, end, "string")
		case tok == token.INT || tok == token.FLOAT || tok == token.IMAG:
			l.addSpan(start, end, "number")
		case isOperator(tok):
			l.addSpan(start, end, "operator")
		case isPunctuation(tok):
			l.addSpan(start, end, "punctuation")
		}
	}
}

func isOperator(tok token.Token) bool {
	switch tok {
	case token.ADD, token.SUB, token.MUL, token.QUO, token.REM,
		token.AND, token.OR, token.XOR, token.SHL, token.SHR, token.AND_NOT,
		token.ADD_ASSIGN, token.SUB_ASSIGN, token.MUL_ASSIGN, token.QUO_ASSIGN, token.REM_ASSIGN,
		token.AND_ASSIGN, token.OR_ASSIGN, token.XOR_ASSIGN, token.SHL_ASSIGN, token.SHR_ASSIGN, token.AND_NOT_ASSIGN,
		token.LAND, token.LOR, token.ARROW, token.INC, token.DEC,
		token.EQL, token.LSS, token.GTR, token.ASSIGN, token.NOT,
		token.NEQ, token.LEQ, token.GEQ, token.DEFINE:
		return true
	default:
		return false
	}
}

func isPunctuation(tok token.Token) bool {
	switch tok {
	case token.LPAREN, token.LBRACK, token.LBRACE, token.COMMA, token.PERIOD,
		token.SEMICOLON, token.COLON, token.ELLIPSIS, token.RPAREN, token.RBRACK, token.RBRACE:
		return true
	default:
		return false
	}
}

func (l *labeler) labelIdentifiers() {
	l.addNode(l.file.Name, "namespace", "declaration")

	parents := make(map[ast.Node]ast.Node)
	ast.Inspect(l.file, func(node ast.Node) bool {
		if node == nil {
			return false
		}
		ast.Inspect(node, func(child ast.Node) bool {
			if child != nil && child != node {
				if _, exists := parents[child]; !exists {
					parents[child] = node
				}
				return false
			}
			return child != nil
		})
		return true
	})

	ast.Inspect(l.file, func(node ast.Node) bool {
		ident, ok := node.(*ast.Ident)
		if !ok || ident.Name == "" || ident == l.file.Name {
			return true
		}

		if ident.Name == "_" {
			if l.isImportName(ident, parents[ident]) {
				l.addNode(ident, "namespace")
			} else {
				l.addNode(ident, "variable")
			}
			return true
		}

		if object := l.info.Defs[ident]; object != nil {
			l.labelDefinition(ident, object, parents[ident])
			return true
		}

		if object := l.info.Uses[ident]; object != nil {
			l.labelUse(ident, object, parents[ident])
			return true
		}

		return true
	})
}

func (l *labeler) labelDefinition(ident *ast.Ident, object types.Object, parent ast.Node) {
	switch obj := object.(type) {
	case *types.PkgName:
		l.addNode(ident, "namespace", "declaration")
	case *types.TypeName:
		if _, ok := obj.Type().(*types.TypeParam); ok {
			l.addNode(ident, "type-parameter", "declaration")
			return
		}
		if _, ok := obj.Type().Underlying().(*types.Interface); ok {
			l.addNode(ident, "interface", "declaration")
			return
		}
		l.addNode(ident, "type", "declaration")
	case *types.Func:
		if signature, ok := obj.Type().(*types.Signature); ok && signature.Recv() != nil {
			l.addNode(ident, "method", "declaration")
			return
		}
		l.addNode(ident, "function", "declaration")
	case *types.Var:
		if obj.IsField() {
			l.addNode(ident, "property", "declaration")
			return
		}
		if isParameterIdentifier(parent) {
			l.addNode(ident, "parameter", "declaration")
			return
		}
		l.addNode(ident, "variable", "declaration")
	case *types.Const:
		l.addNode(ident, "variable", "declaration", "readonly")
	case *types.Label:
		l.addNode(ident, "label", "declaration")
	}
}

func (l *labeler) labelUse(ident *ast.Ident, object types.Object, parent ast.Node) {
	if _, ok := predeclaredTypes[ident.Name]; ok && object.Parent() == types.Universe {
		l.addNode(ident, "type", "default-library")
		return
	}
	if _, ok := predeclaredFunctions[ident.Name]; ok && object.Parent() == types.Universe {
		l.addNode(ident, "function", "default-library")
		return
	}
	if _, ok := predeclaredValues[ident.Name]; ok && object.Parent() == types.Universe {
		l.addNode(ident, "variable", "readonly", "default-library")
		return
	}

	switch obj := object.(type) {
	case *types.PkgName:
		l.addNode(ident, "namespace")
	case *types.TypeName:
		l.addNode(ident, "type")
	case *types.Func:
		if selector, ok := parent.(*ast.SelectorExpr); ok && selector.Sel == ident {
			if selection := l.info.Selections[selector]; selection != nil {
				l.addNode(ident, "method")
				return
			}
			l.addNode(ident, "function")
			return
		}
		if signature, ok := obj.Type().(*types.Signature); ok && signature.Recv() != nil {
			l.addNode(ident, "method")
			return
		}
		if isDirectCallIdentifier(ident, parent) {
			l.addNode(ident, "function")
			return
		}
		l.addNode(ident, "variable")
	case *types.Builtin:
		l.addNode(ident, "function", "default-library")
	case *types.Var:
		if isDirectCallIdentifier(ident, parent) {
			if _, ok := obj.Type().Underlying().(*types.Signature); ok {
				l.addNode(ident, "function")
				return
			}
		}
		if selector, ok := parent.(*ast.SelectorExpr); ok && selector.Sel == ident {
			if selection := l.info.Selections[selector]; selection != nil && obj.IsField() {
				l.addNode(ident, "property")
				return
			}
		}
		if obj.IsField() {
			l.addNode(ident, "property")
			return
		}
		l.addNode(ident, "variable")
	case *types.Const:
		l.addNode(ident, "variable")
	case *types.Label:
		l.addNode(ident, "label")
	case *types.Nil:
		l.addNode(ident, "variable", "readonly", "default-library")
	}
}

func (l *labeler) isImportName(ident *ast.Ident, parent ast.Node) bool {
	importSpec, ok := parent.(*ast.ImportSpec)
	return ok && importSpec.Name == ident
}

func isParameterIdentifier(parent ast.Node) bool {
	field, ok := parent.(*ast.Field)
	if !ok {
		return false
	}

	return len(field.Names) > 0
}

func isDirectCallIdentifier(ident *ast.Ident, parent ast.Node) bool {
	call, ok := parent.(*ast.CallExpr)
	return ok && call.Fun == ident
}

func (l *labeler) sortAndValidate() {
	sort.SliceStable(l.spans, func(i, j int) bool {
		if l.spans[i].Start == l.spans[j].Start {
			return l.spans[i].End < l.spans[j].End
		}
		return l.spans[i].Start < l.spans[j].Start
	})
}
