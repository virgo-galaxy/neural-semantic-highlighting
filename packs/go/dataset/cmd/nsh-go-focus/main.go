package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/dataset"
)

func main() {
	id := flag.String("id", "modern-v1", "Immutable focused corpus id")
	profile := flag.String("profile", "v1", "Focused curriculum profile: v1 or v2")
	variants := flag.Int("variants", 16, "Variants per structural family (1..32)")
	flag.Parse()
	if flag.NArg() != 0 {
		fmt.Fprintln(os.Stderr, "unexpected positional arguments")
		os.Exit(2)
	}
	root, err := dataset.Root()
	if err == nil {
		var path string
		path, err = dataset.BuildFocusedCorpusProfile(root, *id, *variants, *profile, func(current, total int, name string) {
			fmt.Printf("[%d/%d] focused: %s\n", current, total, name)
		})
		if err == nil {
			fmt.Printf("Focused Gold corpus written to %s\n", path)
		}
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
