package labeling

import (
	"testing"
	"unicode/utf16"
)

func TestLabelPackageResolvesCrossFileSymbols(t *testing.T) {
	const mainSource = `package crossfile

func run(service Service) {
	service.Start()
}
`

	results, err := LabelPackage(PackageRequest{
		PackagePath:  "example.com/crossfile",
		DocumentKind: "go",
		Files: []SourceFile{
			{
				Path: "service.go",
				Source: `package crossfile

type Service struct{}

func (Service) Start() {}
`,
			},
			{
				Path:   "main.go",
				Source: mainSource,
			},
		},
	})
	if err != nil {
		t.Fatal(err)
	}

	if len(results) != 2 {
		t.Fatalf("result count: got %d, want 2", len(results))
	}

	mainResult := results[1].Result
	assertSpanText(t, results[1].Path, mainSource, mainResult, "Service", "type")
	assertSpanText(t, results[1].Path, mainSource, mainResult, "Start", "method")
}

func assertSpanText(
	t *testing.T,
	path string,
	source string,
	result HighlightResult,
	text string,
	tokenType string,
) {
	t.Helper()

	for _, span := range result.Spans {
		if span.TokenType != tokenType {
			continue
		}
		if utf16SliceForTest(source, span.Start, span.End) == text {
			return
		}
	}

	t.Fatalf("%s: did not find %q labeled as %q", path, text, tokenType)
}

func utf16SliceForTest(source string, start int, end int) string {
	encoded := utf16.Encode([]rune(source))
	return string(utf16.Decode(encoded[start:end]))
}
