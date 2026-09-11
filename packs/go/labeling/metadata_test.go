package labeling

import (
	"strings"
	"testing"
	"unicode/utf16"
)

func TestStructTagBoundaries(t *testing.T) {
	cases := []struct{ name, literal string }{
		{"multiple-conventions", "`json:\"name,omitempty\" gorm:\"column:name;index\" binding:\"required\"`"},
		{"custom-key", "`custom:\"a:b;c,d=1\"`"},
		{"interpreted-string", `"json:\"name,omitempty\""`},
		{"empty-tag", "``"},
		{"free-form-language-tag", "`not a key-value convention`"},
		{"unicode", "`json:\"title\" custom:\"🌍\"`"},
		{"raw-carriage-return", "`custom:\"a\"\r custom2:\"b\"`"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			source := "package sample\n// 🌍 preserves non-BMP offset coverage.\ntype Record struct {\nName string " + tc.literal + "\n}\n"
			result, err := Label(HighlightRequest{Source: source, DocumentKind: "go"})
			if err != nil {
				t.Fatal(err)
			}
			assertExactRegion(t, source, result, tc.literal, "string")
		})
	}
}

func TestCommentPhysicalBoundaries(t *testing.T) {
	for name, comment := range map[string]string{
		"line":          "// The declaration remains ordinary code.",
		"block":         "/* First line.\nSecond line. */",
		"block-crlf":    "/* First line.\r\nSecond line. */",
		"generate":      "//go:generate echo generate-is-not-executed",
		"documentation": "// Record stores a value. See [Record].",
	} {
		t.Run(name, func(t *testing.T) {
			source := "package sample\n" + comment + "\nvar Value = 1\n"
			result, err := Label(HighlightRequest{Source: source, DocumentKind: "go"})
			if err != nil {
				t.Fatal(err)
			}
			assertExactRegion(t, source, result, comment, "comment")
			assertSpanText(t, "source.go", source, result, "Value", "variable")
		})
	}
}

func assertExactRegion(t *testing.T, source string, result HighlightResult, region, tokenType string) {
	t.Helper()
	byteStart := strings.Index(source, region)
	if byteStart < 0 {
		t.Fatal("test region not found")
	}
	start := len(utf16.Encode([]rune(source[:byteStart])))
	end := start + len(utf16.Encode([]rune(region)))
	count := 0
	for _, span := range result.Spans {
		if span.Start < end && start < span.End {
			count++
			if span.Start != start || span.End != end || span.TokenType != tokenType || len(span.Modifiers) != 0 {
				t.Fatalf("region must be one exact %s span: got %#v; want %d..%d", tokenType, span, start, end)
			}
		}
	}
	if count != 1 {
		t.Fatalf("overlapping span count: got %d, want 1", count)
	}
}

func TestStrictPackageLabelerRejectsTypeErrors(t *testing.T) {
	for name, source := range map[string]string{
		"undefined-name": "package sample\nvar X = missingName\n",
		"missing-import": "package sample\nimport \"example.com/missing\"\nvar X = missing.Value\n",
		"mixed-types":    "package sample\nvar X int = \"text\"\n",
	} {
		t.Run(name, func(t *testing.T) {
			results, err := NewStrictPackageLabeler(nil).LabelPackage(PackageRequest{DocumentKind: "go", Files: []SourceFile{{Path: "source.go", Source: source}}})
			if err == nil || results != nil {
				t.Fatalf("invalid corpus must not produce Gold: %#v, %v", results, err)
			}
		})
	}
}

func TestStrictPackageLabelerCrossFile(t *testing.T) {
	results, err := NewStrictPackageLabeler(nil).LabelPackage(PackageRequest{DocumentKind: "go", GoVersion: "go1.18", Files: []SourceFile{
		{Path: "types.go", Source: "package sample\ntype Record struct { Name string }\n"},
		{Path: "use.go", Source: "package sample\nfunc Name(r Record) string { return r.Name }\n"},
	}})
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 2 {
		t.Fatalf("got %d files, want 2", len(results))
	}
}

func TestEmbeddedFieldIsTypeUse(t *testing.T) {
	const source = "package sample\ntype Base struct { Name string }\ntype Record struct { *Base }\n"
	result, err := Label(HighlightRequest{Source: source, DocumentKind: "go"})
	if err != nil {
		t.Fatal(err)
	}
	start := strings.LastIndex(source, "Base")
	found := false
	for _, span := range result.Spans {
		if span.Start == start && span.End == start+4 {
			found = true
			if span.TokenType != "type" || len(span.Modifiers) != 0 {
				t.Fatalf("embedded Base is an explicit type use: %#v", span)
			}
		}
	}
	if !found {
		t.Fatal("embedded type not labeled")
	}
}
