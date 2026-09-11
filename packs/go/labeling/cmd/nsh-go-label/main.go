package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/pokeyaro/neural-semantic-highlighting/packs/go/labeling"
)

func main() {
	var sourcePath string
	flag.StringVar(&sourcePath, "source", "", "Path to a Go source file")
	flag.Parse()

	if sourcePath == "" {
		fmt.Fprintln(os.Stderr, "missing required -source path")
		os.Exit(2)
	}

	source, err := os.ReadFile(sourcePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "read source: %v\n", err)
		os.Exit(1)
	}

	result, err := labeling.Label(labeling.HighlightRequest{
		Source:       string(source),
		DocumentKind: "go",
	})
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(result); err != nil {
		fmt.Fprintf(os.Stderr, "encode result: %v\n", err)
		os.Exit(1)
	}
}
