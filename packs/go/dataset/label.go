package dataset

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sort"

	"github.com/virgo-galaxy/virgo-nsh/packs/go/labeling"
)

func LabelStdlib(root string, progress ProgressFunc) (LabelSummary, error) {
	if err := RequireGoldToolchain(); err != nil {
		return LabelSummary{}, err
	}

	var sample SampleManifest
	if err := readJSON(SamplePath(root), &sample); err != nil {
		return LabelSummary{}, fmt.Errorf("read sample manifest: %w", err)
	}
	if err := validateManifestHeader(
		sample.FormatVersion,
		sample.Toolchain,
		sample.Corpus,
		sample.GOOS,
		sample.GOARCH,
	); err != nil {
		return LabelSummary{}, err
	}

	byPackage := make(map[string][]SampleEntry)
	for _, entry := range sample.Files {
		byPackage[entry.Package] = append(byPackage[entry.Package], entry)
	}

	packageNames := make([]string, 0, len(byPackage))
	for packageName := range byPackage {
		packageNames = append(packageNames, packageName)
	}
	sort.Strings(packageNames)

	listedPackages, err := listPackages("std")
	if err != nil {
		return LabelSummary{}, err
	}
	packageMetadata := make(map[string]goListPackage, len(listedPackages))
	for _, pkg := range listedPackages {
		packageMetadata[pkg.ImportPath] = pkg
	}

	if err := os.MkdirAll(root, 0o755); err != nil {
		return LabelSummary{}, fmt.Errorf("create dataset directory: %w", err)
	}

	outputPath := LabeledPath(root)
	temporaryPath := outputPath + ".tmp"
	output, err := os.Create(temporaryPath)
	if err != nil {
		return LabelSummary{}, fmt.Errorf("create labeled dataset: %w", err)
	}
	removeTemporary := true
	defer func() {
		_ = output.Close()
		if removeTemporary {
			_ = os.Remove(temporaryPath)
		}
	}()

	writer := bufio.NewWriterSize(output, 1<<20)
	encoder := json.NewEncoder(writer)
	encoder.SetEscapeHTML(false)

	gorootSource := filepath.Join(runtime.GOROOT(), "src")
	goldLabeler := labeling.NewPackageLabeler()
	labeledCount := 0

	for index, packageName := range packageNames {
		if progress != nil {
			progress(index+1, len(packageNames), packageName)
		}

		pkg, ok := packageMetadata[packageName]
		if !ok {
			return LabelSummary{}, fmt.Errorf("package %s is no longer in go list std", packageName)
		}

		packageFiles := make([]labeling.SourceFile, 0, len(pkg.GoFiles))
		for _, name := range pkg.GoFiles {
			absolutePath := filepath.Join(pkg.Dir, name)
			content, err := os.ReadFile(absolutePath)
			if err != nil {
				return LabelSummary{}, fmt.Errorf("read %s: %w", absolutePath, err)
			}
			relativePath, err := filepath.Rel(gorootSource, absolutePath)
			if err != nil {
				return LabelSummary{}, fmt.Errorf("resolve stdlib path %s: %w", absolutePath, err)
			}
			packageFiles = append(packageFiles, labeling.SourceFile{
				Path:   filepath.ToSlash(relativePath),
				Source: string(content),
			})
		}

		results, err := goldLabeler.LabelPackage(labeling.PackageRequest{
			PackagePath:  packageName,
			DocumentKind: DocumentKind,
			Files:        packageFiles,
		})
		if err != nil {
			return LabelSummary{}, fmt.Errorf("label package %s: %w", packageName, err)
		}

		resultByPath := make(map[string]labeling.HighlightResult, len(results))
		sourceByPath := make(map[string]string, len(packageFiles))
		for _, sourceFile := range packageFiles {
			sourceByPath[sourceFile.Path] = sourceFile.Source
		}
		for _, result := range results {
			resultByPath[result.Path] = result.Result
		}

		for _, entry := range byPackage[packageName] {
			source, ok := sourceByPath[entry.Path]
			if !ok {
				return LabelSummary{}, fmt.Errorf(
					"%s: selected file is not in the active Go build for package %s",
					entry.Path,
					packageName,
				)
			}
			result, ok := resultByPath[entry.Path]
			if !ok {
				return LabelSummary{}, fmt.Errorf("%s: missing Gold result", entry.Path)
			}

			digest := sha256.Sum256([]byte(source))
			contentHash := hex.EncodeToString(digest[:])
			if contentHash != entry.ContentHash {
				return LabelSummary{}, fmt.Errorf(
					"%s: source changed after collection: got %s, want %s",
					entry.Path,
					contentHash,
					entry.ContentHash,
				)
			}

			if err := encoder.Encode(LabeledEntry{
				Package:      entry.Package,
				Path:         entry.Path,
				DocumentKind: entry.DocumentKind,
				ContentHash:  entry.ContentHash,
				Source:       source,
				Result:       result,
			}); err != nil {
				return LabelSummary{}, fmt.Errorf("write labeled entry %s: %w", entry.Path, err)
			}
			labeledCount++
		}
	}

	if err := writer.Flush(); err != nil {
		return LabelSummary{}, fmt.Errorf("flush labeled dataset: %w", err)
	}
	if err := output.Close(); err != nil {
		return LabelSummary{}, fmt.Errorf("close labeled dataset: %w", err)
	}
	if err := os.Rename(temporaryPath, outputPath); err != nil {
		return LabelSummary{}, fmt.Errorf("replace labeled dataset: %w", err)
	}
	removeTemporary = false

	return LabelSummary{Files: labeledCount}, nil
}

func validateManifestHeader(
	formatVersion int,
	toolchain string,
	corpus string,
	goos string,
	goarch string,
) error {
	if formatVersion != FormatVersion {
		return fmt.Errorf("unsupported dataset format version %d", formatVersion)
	}
	if toolchain != GoldToolchain {
		return fmt.Errorf("dataset was collected with %s, expected %s", toolchain, GoldToolchain)
	}
	if corpus != StdlibCorpus {
		return fmt.Errorf("unsupported Go corpus %q", corpus)
	}
	if goos != runtime.GOOS || goarch != runtime.GOARCH {
		return fmt.Errorf(
			"dataset build context is %s/%s, current toolchain is %s/%s",
			goos,
			goarch,
			runtime.GOOS,
			runtime.GOARCH,
		)
	}
	return nil
}
