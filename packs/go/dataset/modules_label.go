package dataset

import (
	"bufio"
	"encoding/json"
	"fmt"
	"go/importer"
	"go/token"
	"io"
	"os"
	"sort"

	"github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/labeling"
)

func labelModule(outputRoot, sourceRoot string, sample SampleManifest, packages []goListPackage, progress ProgressFunc) error {
	exportFiles := map[string]string{}
	metadata := map[string]goListPackage{}
	for _, pkg := range packages {
		metadata[pkg.ImportPath] = pkg
		if pkg.Export != "" {
			exportFiles[pkg.ImportPath] = pkg.Export
		}
	}
	lookup := func(path string) (io.ReadCloser, error) {
		file, ok := exportFiles[path]
		if !ok {
			return nil, fmt.Errorf("no export data for imported package %q", path)
		}
		return os.Open(file)
	}
	gold := labeling.NewStrictPackageLabeler(importer.ForCompiler(token.NewFileSet(), "gc", lookup))
	byPackage := map[string][]SampleEntry{}
	contextByKey := map[string]SampleEntry{}
	for _, entry := range sample.Files {
		byPackage[entry.Package] = append(byPackage[entry.Package], entry)
	}
	for _, entry := range sample.ContextFiles {
		contextByKey[datasetKey(entry.Package, entry.Path)] = entry
	}
	names := make([]string, 0, len(byPackage))
	for name := range byPackage {
		names = append(names, name)
	}
	sort.Strings(names)
	output, err := os.Create(LabeledPath(outputRoot))
	if err != nil {
		return err
	}
	defer output.Close()
	writer := bufio.NewWriterSize(output, 1<<20)
	encoder := json.NewEncoder(writer)
	encoder.SetEscapeHTML(false)
	for index, name := range names {
		if progress != nil {
			progress(index+1, len(names), sample.Corpus+": "+name)
		}
		pkg, ok := metadata[name]
		if !ok {
			return fmt.Errorf("%s: missing active package", name)
		}
		files := make([]labeling.SourceFile, 0, len(pkg.GoFiles))
		sourceByPath := map[string]string{}
		for _, file := range pkg.GoFiles {
			entry, source, err := readModuleEntry(sourceRoot, pkg, file)
			if err != nil {
				return err
			}
			if expected, ok := contextByKey[datasetKey(name, entry.Path)]; !ok || entry != expected {
				return fmt.Errorf("%s: package context changed after collection", entry.Path)
			}
			files = append(files, labeling.SourceFile{Path: entry.Path, Source: source})
			sourceByPath[entry.Path] = source
		}
		goVersion := ""
		if sample.Source.GoVersion != "" {
			goVersion = "go" + sample.Source.GoVersion
		}
		results, err := gold.LabelPackage(labeling.PackageRequest{PackagePath: name, DocumentKind: DocumentKind, Files: files, GoVersion: goVersion})
		if err != nil {
			return err
		}
		resultByPath := map[string]labeling.HighlightResult{}
		for _, result := range results {
			resultByPath[result.Path] = result.Result
		}
		for _, entry := range byPackage[name] {
			result, ok := resultByPath[entry.Path]
			if !ok {
				return fmt.Errorf("%s: missing Gold result", entry.Path)
			}
			if err := encoder.Encode(LabeledEntry{Package: name, Path: entry.Path, DocumentKind: DocumentKind,
				ContentHash: entry.ContentHash, Source: sourceByPath[entry.Path], Result: result}); err != nil {
				return err
			}
		}
	}
	if err := writer.Flush(); err != nil {
		return err
	}
	return output.Close()
}
