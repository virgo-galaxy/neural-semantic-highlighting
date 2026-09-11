package labeling

import (
	"strings"
	"testing"
)

func TestApproximationIsAnOperator(t *testing.T) {
	source := "package sample\nfunc Keep[T ~int | ~string](value T) T { return value }\n"
	results, err := NewStrictPackageLabeler(nil).LabelPackage(PackageRequest{
		PackagePath: "example.local/constraints", DocumentKind: "go",
		Files: []SourceFile{{Path: "source.go", Source: source}},
	})
	if err != nil {
		t.Fatal(err)
	}
	found := 0
	for _, span := range results[0].Result.Spans {
		if source[span.Start:span.End] == "~" {
			found++
			if span.TokenType != "operator" {
				t.Fatalf("tilde classified as %s", span.TokenType)
			}
		}
	}
	if found != strings.Count(source, "~") {
		t.Fatalf("found %d approximation operators", found)
	}
}
