// Command nsh-go-syntax-repair streams syntax-proven declaration positions for
// the offline dataset builder. It never loads a package dependency graph.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"

	"github.com/virgo-galaxy/virgo-nsh/packs/go/labeling"
)

func run(input io.Reader, output io.Writer) error {
	decoder, encoder := json.NewDecoder(input), json.NewEncoder(output)
	for {
		var request struct {
			Source string `json:"source"`
		}
		if err := decoder.Decode(&request); err == io.EOF {
			return nil
		} else if err != nil {
			return fmt.Errorf("decode syntax repair request: %w", err)
		}
		spans, err := labeling.TypeSwitchDeclarationSpans(request.Source)
		if err != nil {
			return fmt.Errorf("parse syntax repair request: %w", err)
		}
		if err := encoder.Encode(struct {
			Spans []labeling.SemanticSpan `json:"spans"`
		}{Spans: spans}); err != nil {
			return err
		}
	}
}

func main() {
	if err := run(os.Stdin, os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
