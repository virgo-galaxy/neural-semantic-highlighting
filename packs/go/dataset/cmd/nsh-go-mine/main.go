package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/dataset"
)

func main() {
	config := flag.String("config", "dataset/sources/targeted.json", "Explicit module allowlist to mine")
	id := flag.String("id", "targeted-real-v2", "Immutable mined curriculum id")
	flag.Parse()
	if flag.NArg() != 0 {
		fmt.Fprintln(os.Stderr, "unexpected positional arguments")
		os.Exit(2)
	}
	root, err := dataset.Root()
	if err == nil {
		var path string
		path, err = dataset.BuildTargetedMinedCorpus(root, *config, *id, func(current, total int, name string) {
			fmt.Printf("[%d/%d] %s\n", current, total, name)
		})
		if err == nil {
			fmt.Printf("Targeted real-world curriculum written to %s\n", path)
		}
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
