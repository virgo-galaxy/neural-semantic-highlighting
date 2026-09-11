package labeling

import (
	"go/ast"
	"go/parser"
	"go/token"
	"go/types"
	"reflect"
	"strings"
	"testing"
)

const switchSource = `package sample

func describe(input any) any {
	// A non-BMP character before the guard: 🚀
	switch value := input.(type) {
	case int:
		return value + 1
	case string, []byte:
		return value
	default:
		return value
	}
}
`

func TestTypeSwitchGuardHasNoSingleDefinitionObject(t *testing.T) {
	files := token.NewFileSet()
	file, err := parser.ParseFile(files, "source.go", switchSource, 0)
	if err != nil {
		t.Fatal(err)
	}
	info := &types.Info{Defs: make(map[*ast.Ident]types.Object), Implicits: make(map[ast.Node]types.Object)}
	var config types.Config
	if _, err := config.Check("sample", files, []*ast.File{file}, info); err != nil {
		t.Fatal(err)
	}
	guard := typeSwitchDeclarations(file)[0]
	object, recorded := info.Defs[guard]
	if !recorded || object != nil {
		t.Fatalf("expected recorded nil Defs entry, got %v, %v", object, recorded)
	}
	caseObjects := 0
	for node := range info.Implicits {
		if _, ok := node.(*ast.CaseClause); ok {
			caseObjects++
		}
	}
	if caseObjects != 3 {
		t.Fatalf("expected three case-local objects, got %d", caseObjects)
	}
}

func TestTypeSwitchGoldIncludesGuardAndReferences(t *testing.T) {
	results, err := NewStrictPackageLabeler(nil).LabelPackage(PackageRequest{
		PackagePath: "sample", DocumentKind: "go", Files: []SourceFile{{Path: "source.go", Source: switchSource}},
	})
	if err != nil {
		t.Fatal(err)
	}
	offsets := buildUTF16Offsets(switchSource)
	count := 0
	for cursor := 0; ; {
		index := strings.Index(switchSource[cursor:], "value")
		if index < 0 {
			break
		}
		index += cursor
		want := SemanticSpan{Start: offsets[index], End: offsets[index+5], TokenType: "variable"}
		if count == 0 {
			want.Modifiers = []string{"declaration"}
		}
		found := false
		for _, span := range results[0].Result.Spans {
			if reflect.DeepEqual(span, want) {
				found = true
			}
		}
		if !found {
			t.Fatalf("missing expected receiver-independent guard/reference span: %#v", want)
		}
		cursor = index + 5
		count++
	}
	if count != 4 {
		t.Fatalf("expected four guard/reference occurrences, got %d", count)
	}
}

func TestSyntaxRepairOnlyFindsExplicitTypeSwitchDeclarations(t *testing.T) {
	cases := []struct {
		name, source string
		identifiers  []string
	}{
		{"guard", switchSource, []string{"value"}},
		{"nested-shadow", `package sample
func f(x any) { switch v := x.(type) { case any: switch v := v.(type) { case int: _ = v } } }`, []string{"v", "v"}},
		{"initializer", `package sample
func f(x any) { switch n := 1; value /* note */ := x.(type) { default: _, _ = n, value } }`, []string{"value"}},
		{"empty-cases", `package sample
func f(x any) { switch value := x.(type) {} }`, []string{"value"}},
		{"unbound-type-switch", `package sample
func f(x any) { switch x.(type) { case int: } }`, nil},
		{"blank-guard", `package sample
func f(x any) { switch _ := x.(type) { default: } }`, nil},
		{"value-switch-and-assertion", `package sample
func f(x any) { y := x.(int); switch z := y; z { case 1: } }`, nil},
		{"string-and-comment", "package sample\n// switch fake := x.(type)\nvar note = `switch fake := x.(type) {}`\n", nil},
		{"crlf-and-unicode", "package sample\r\nvar label = \"🚀\"\r\nfunc f(x any) { switch café := x.(type) { default: _ = café } }", []string{"café"}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			spans, err := TypeSwitchDeclarationSpans(tc.source)
			if err != nil {
				t.Fatal(err)
			}
			if len(spans) != len(tc.identifiers) {
				t.Fatalf("got %d declarations, want %d", len(spans), len(tc.identifiers))
			}
			offsets := buildUTF16Offsets(tc.source)
			for i, span := range spans {
				if span.TokenType != "variable" || !reflect.DeepEqual(span.Modifiers, []string{"declaration"}) {
					t.Fatalf("unexpected declaration semantics: %#v", span)
				}
				start, end := -1, -1
				for byteIndex, unit := range offsets {
					if unit == span.Start && start == -1 {
						start = byteIndex
					}
					if unit == span.End && end == -1 {
						end = byteIndex
					}
				}
				if tc.source[start:end] != tc.identifiers[i] {
					t.Fatalf("wrong identifier boundary: %q", tc.source[start:end])
				}
			}
		})
	}
}

func TestSyntaxRepairRejectsMalformedSource(t *testing.T) {
	if _, err := TypeSwitchDeclarationSpans("package sample\nfunc {"); err == nil {
		t.Fatal("expected parser error")
	}
}
