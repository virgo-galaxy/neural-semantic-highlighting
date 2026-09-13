package lexical

import "testing"

func TestScanKeepsLexicalContainersWhole(t *testing.T) {
	source := "package sample\n// comment with {x} and %s\nvar a = `raw\n// not a comment\n{x}`\nvar b = \"value=\\\"%s\\\"\"\n"
	result, err := Scan(source)
	if err != nil {
		t.Fatal(err)
	}
	want := map[string]int{"comment": 1, "string": 2}
	got := map[string]int{}
	for _, span := range result.Spans {
		got[span.Kind]++
	}
	for kind, count := range want {
		if got[kind] != count {
			t.Fatalf("%s spans = %d, want %d", kind, got[kind], count)
		}
	}
}

func TestScanOmitsVirtualSemicolons(t *testing.T) {
	result, err := Scan("package sample\nvar x = 1\n")
	if err != nil {
		t.Fatal(err)
	}
	for _, span := range result.Spans {
		if span.Kind == "punctuation" && span.Text == "\n" {
			t.Fatal("virtual semicolon leaked into lexical spans")
		}
	}
}
