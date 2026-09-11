package labeling

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"testing"
	"unicode/utf16"
)

type goldSpan struct {
	SemanticSpan
	Text string `json:"text"`
}

type goldFixture struct {
	DocumentKind   string     `json:"documentKind"`
	OffsetEncoding string     `json:"offsetEncoding"`
	Spans          []goldSpan `json:"spans"`
}

func TestGoldFixtures(t *testing.T) {
	entries, err := os.ReadDir("../fixtures")
	if err != nil {
		t.Fatal(err)
	}

	names := make([]string, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() {
			names = append(names, entry.Name())
		}
	}
	sort.Strings(names)

	for _, name := range names {
		name := name
		t.Run(name, func(t *testing.T) {
			fixtureDir := filepath.Join("../fixtures", name)
			source, err := os.ReadFile(filepath.Join(fixtureDir, "source.go"))
			if err != nil {
				t.Fatal(err)
			}

			expectedBytes, err := os.ReadFile(filepath.Join(fixtureDir, "expected.json"))
			if err != nil {
				t.Fatal(err)
			}

			var expected goldFixture
			if err := json.Unmarshal(expectedBytes, &expected); err != nil {
				t.Fatal(err)
			}

			actual, err := Label(HighlightRequest{
				Source:       string(source),
				DocumentKind: expected.DocumentKind,
			})
			if err != nil {
				t.Fatal(err)
			}

			if actual.OffsetEncoding != expected.OffsetEncoding {
				t.Fatalf("offset encoding: got %q, want %q", actual.OffsetEncoding, expected.OffsetEncoding)
			}
			if len(actual.Spans) != len(expected.Spans) {
				t.Fatalf("span count: got %d, want %d", len(actual.Spans), len(expected.Spans))
			}

			for i, want := range expected.Spans {
				got := actual.Spans[i]
				if !equalSpan(got, want.SemanticSpan) {
					t.Fatalf("span %d: got %#v, want %#v", i, got, want.SemanticSpan)
				}
				if text := utf16Slice(string(source), got.Start, got.End); text != want.Text {
					t.Fatalf("span %d text: got %q, want %q", i, text, want.Text)
				}
			}
		})
	}
}

func equalSpan(left, right SemanticSpan) bool {
	if left.Start != right.Start || left.End != right.End || left.TokenType != right.TokenType {
		return false
	}
	if len(left.Modifiers) != len(right.Modifiers) {
		return false
	}
	for i := range left.Modifiers {
		if left.Modifiers[i] != right.Modifiers[i] {
			return false
		}
	}
	return true
}

func utf16Slice(source string, start, end int) string {
	encoded := utf16.Encode([]rune(source))
	return string(utf16.Decode(encoded[start:end]))
}
