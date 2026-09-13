package lexical

import (
	"fmt"
	"go/scanner"
	"go/token"
	"sort"
	"unicode/utf8"
)

// Span is one lexical Go token expressed in public UTF-16 offsets.
// Identifiers deliberately remain unresolved: the neural semantic stage owns
// namespace/type/function/method/property/etc. classification.
type Span struct {
	Start int    `json:"start"`
	End   int    `json:"end"`
	Kind  string `json:"kind"`
	Text  string `json:"text,omitempty"`
}

// Result is the deterministic lexical scaffold consumed by the semantic stage.
type Result struct {
	OffsetEncoding string `json:"offsetEncoding"`
	Spans          []Span `json:"spans"`
}

func utf16Offsets(source string) []int {
	offsets := make([]int, len(source)+1)
	units := 0
	for byteOffset := 0; byteOffset < len(source); {
		r, size := utf8.DecodeRuneInString(source[byteOffset:])
		width := 1
		if r > 0xffff {
			width = 2
		}
		for i := 0; i < size; i++ {
			offsets[byteOffset+i] = units
		}
		units += width
		byteOffset += size
		offsets[byteOffset] = units
	}
	return offsets
}

func tokenKind(tok token.Token) string {
	switch {
	case tok == token.IDENT:
		return "identifier"
	case tok.IsKeyword():
		return "keyword"
	case tok == token.COMMENT:
		return "comment"
	case tok == token.STRING || tok == token.CHAR:
		return "string"
	case tok == token.INT || tok == token.FLOAT || tok == token.IMAG:
		return "number"
	case isOperator(tok):
		return "operator"
	case isPunctuation(tok):
		return "punctuation"
	default:
		return ""
	}
}

func isOperator(tok token.Token) bool {
	switch tok {
	case token.ADD, token.SUB, token.MUL, token.QUO, token.REM,
		token.AND, token.OR, token.XOR, token.SHL, token.SHR, token.AND_NOT,
		token.ADD_ASSIGN, token.SUB_ASSIGN, token.MUL_ASSIGN, token.QUO_ASSIGN, token.REM_ASSIGN,
		token.AND_ASSIGN, token.OR_ASSIGN, token.XOR_ASSIGN, token.SHL_ASSIGN, token.SHR_ASSIGN, token.AND_NOT_ASSIGN,
		token.LAND, token.LOR, token.ARROW, token.INC, token.DEC, token.TILDE,
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

// Scan returns source-backed lexical spans only. Virtual semicolons inserted by
// go/scanner are intentionally omitted because they do not occupy source text.
func Scan(source string) (Result, error) {
	fileSet := token.NewFileSet()
	file := fileSet.AddFile("source.go", -1, len(source))
	offsets := utf16Offsets(source)
	var scan scanner.Scanner
	var firstErr error
	scan.Init(file, []byte(source), func(_ token.Position, msg string) {
		if firstErr == nil {
			firstErr = fmt.Errorf("scan Go source: %s", msg)
		}
	}, scanner.ScanComments)

	spans := make([]Span, 0, len(source)/4)
	for {
		pos, tok, lit := scan.Scan()
		if tok == token.EOF {
			break
		}
		if tok == token.SEMICOLON && lit == "\n" {
			continue
		}
		kind := tokenKind(tok)
		if kind == "" {
			continue
		}
		start := file.Offset(pos)
		text := lit
		if text == "" {
			text = tok.String()
		}
		end := start + len(text)
		if start < 0 || end > len(source) || start >= end || source[start:end] != text {
			return Result{}, fmt.Errorf("scanner span does not match source at bytes %d..%d for %q", start, end, text)
		}
		spans = append(spans, Span{Start: offsets[start], End: offsets[end], Kind: kind, Text: text})
	}
	if firstErr != nil {
		return Result{}, firstErr
	}
	sort.Slice(spans, func(i, j int) bool { return spans[i].Start < spans[j].Start })
	return Result{OffsetEncoding: "utf-16", Spans: spans}, nil
}
