package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/dataset"
)

func main() {
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "usage: nsh-go-dataset <collect|label|validate|modules>\n")
	}
	if len(os.Args) > 1 && os.Args[1] == "modules" {
		runModules(os.Args[2:])
		return
	}
	flag.Parse()

	if flag.NArg() != 1 {
		flag.Usage()
		os.Exit(2)
	}

	root, err := dataset.Root()
	if err != nil {
		fail(err)
	}

	switch flag.Arg(0) {
	case "collect":
		manifest, err := dataset.CollectStdlib(root)
		if err != nil {
			fail(err)
		}
		fmt.Printf("Collected %d Go stdlib files with %s (%s/%s).\n", len(manifest.Files), manifest.Toolchain, manifest.GOOS, manifest.GOARCH)
		fmt.Printf("Written to %s\n", dataset.SamplePath(root))
	case "label":
		summary, err := dataset.LabelStdlib(root, func(current int, total int, packageName string) {
			if current == 1 || current%25 == 0 || current == total {
				fmt.Printf("[%d/%d] %s\n", current, total, packageName)
			}
		})
		if err != nil {
			fail(err)
		}
		fmt.Printf("Labeled %d Go stdlib files with package-aware Gold labels.\n", summary.Files)
		fmt.Printf("Written to %s\n", dataset.LabeledPath(root))
	case "validate":
		statistics, err := dataset.Validate(root, filepath.Join("schema.json"))
		if err != nil {
			fail(err)
		}
		printStatistics(statistics)
		fmt.Printf("Statistics written to %s\n", dataset.StatisticsPath(root))
	default:
		flag.Usage()
		os.Exit(2)
	}
}

func runModules(arguments []string) {
	flags := flag.NewFlagSet("modules", flag.ExitOnError)
	config := flags.String("config", "dataset/sources/official.json", "Corpus source configuration")
	source := flags.String("source", "", "Run only this corpus id; empty runs every configured source")
	if err := flags.Parse(arguments); err != nil {
		fail(err)
	}
	if flags.NArg() != 0 {
		fail(fmt.Errorf("unexpected arguments: %v", flags.Args()))
	}
	root, err := dataset.Root()
	if err != nil {
		fail(err)
	}
	statistics, err := dataset.RunModules(root, *config, "schema.json", *source, func(current, total int, name string) {
		if total == 0 {
			fmt.Println(name)
			return
		}
		if current == 1 || current%25 == 0 || current == total {
			fmt.Printf("[%d/%d] %s\n", current, total, name)
		}
	})
	for _, stats := range statistics {
		printStatistics(stats)
		fmt.Printf("Statistics written to %s\n", dataset.StatisticsPath(dataset.CorpusPath(root, stats.Corpus)))
	}
	if err != nil {
		fail(err)
	}
}

func printStatistics(statistics dataset.Statistics) {
	fmt.Println("Go Dataset Statistics")
	fmt.Println("---------------------")
	fmt.Printf("Corpus:      %s\n", statistics.Corpus)
	fmt.Printf("Toolchain:   %s\n", statistics.Toolchain)
	fmt.Printf("Build:       %s/%s\n", statistics.GOOS, statistics.GOARCH)
	fmt.Printf("Packages:    %d\n", statistics.Packages)
	fmt.Printf("Files:       %d\n", statistics.Files)
	fmt.Printf("Spans:       %d\n", statistics.Spans)
	fmt.Printf("Source bytes:%d\n", statistics.SourceBytes)
	fmt.Println()

	keys := make([]string, 0, len(statistics.TokenTypes))
	for key := range statistics.TokenTypes {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	fmt.Println("Token types:")
	for _, key := range keys {
		fmt.Printf("  %-16s %d\n", key+":", statistics.TokenTypes[key])
	}

	keys = keys[:0]
	for key := range statistics.Modifiers {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	fmt.Println()
	fmt.Println("Modifiers:")
	for _, key := range keys {
		fmt.Printf("  %-16s %d\n", key+":", statistics.Modifiers[key])
	}
	fmt.Println()
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
