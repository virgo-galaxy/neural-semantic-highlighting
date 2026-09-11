package main

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"
)

func TestStreamingSyntaxRepair(t *testing.T) {
	var input bytes.Buffer
	encoder := json.NewEncoder(&input)
	for _, source := range []string{"package sample", "package sample\nfunc f(x any) { switch v := x.(type) { default: _ = v } }"} {
		if err := encoder.Encode(map[string]string{"source": source}); err != nil {
			t.Fatal(err)
		}
	}
	var output bytes.Buffer
	if err := run(&input, &output); err != nil {
		t.Fatal(err)
	}
	lines := strings.Split(strings.TrimSpace(output.String()), "\n")
	if len(lines) != 2 || lines[0] != `{"spans":[]}` || !strings.Contains(lines[1], `"declaration"`) {
		t.Fatalf("unexpected stream: %s", output.String())
	}
}

func TestInvalidRequestsFail(t *testing.T) {
	for _, text := range []string{`{bad`, `{"source":"package {"}`} {
		if err := run(strings.NewReader(text), &bytes.Buffer{}); err == nil {
			t.Fatalf("expected error for %q", text)
		}
	}
}
