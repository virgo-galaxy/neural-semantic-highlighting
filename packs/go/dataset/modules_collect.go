package dataset

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

func readModuleEntry(sourceRoot string, pkg goListPackage, name string) (SampleEntry, string, error) {
	absolutePath := filepath.Join(pkg.Dir, name)
	relativePath, err := filepath.Rel(sourceRoot, absolutePath)
	if err != nil || relativePath == ".." || strings.HasPrefix(relativePath, ".."+string(filepath.Separator)) || filepath.IsAbs(relativePath) {
		return SampleEntry{}, "", fmt.Errorf("source file escapes module root: %s", absolutePath)
	}
	content, err := os.ReadFile(absolutePath)
	if err != nil {
		return SampleEntry{}, "", err
	}
	digest := sha256.Sum256(content)
	return SampleEntry{Package: pkg.ImportPath, Path: filepath.ToSlash(relativePath), DocumentKind: DocumentKind,
		Size: int64(len(content)), ContentHash: hex.EncodeToString(digest[:])}, string(content), nil
}

func collectModule(lock ModuleLock, sourceRoot string, packages []goListPackage) (SampleManifest, error) {
	manifest := SampleManifest{FormatVersion: ModuleFormatVersion, Toolchain: lock.Toolchain, Corpus: lock.Spec.ID,
		GOOS: lock.GOOS, GOARCH: lock.GOARCH, Source: &lock.Source, Files: []SampleEntry{}}
	selectedPackages := map[string]bool{}
	var all []SampleEntry
	for _, pkg := range packages {
		if pkg.Module == nil || pkg.Module.Path != lock.Source.Module {
			continue
		}
		if len(pkg.CgoFiles) != 0 {
			return manifest, fmt.Errorf("%s: cgo sources are outside the pure-Go corpus policy", pkg.ImportPath)
		}
		for _, name := range pkg.GoFiles {
			entry, _, err := readModuleEntry(sourceRoot, pkg, name)
			if err != nil {
				return manifest, err
			}
			all = append(all, entry)
			if entry.Size < minimumSourceBytes || entry.Size > maximumSourceBytes {
				continue
			}
			manifest.Files = append(manifest.Files, entry)
			selectedPackages[entry.Package] = true
		}
	}
	if len(manifest.Files) == 0 {
		return manifest, fmt.Errorf("%s: no files satisfy source selection", lock.Spec.ID)
	}
	// Files excluded from sampling still participate in type checking and are
	// hashed as context. No selected package is checked as a partial package.
	for _, entry := range all {
		if selectedPackages[entry.Package] {
			manifest.ContextFiles = append(manifest.ContextFiles, entry)
		}
	}
	less := func(files []SampleEntry) {
		sort.Slice(files, func(i, j int) bool {
			if files[i].Package == files[j].Package {
				return files[i].Path < files[j].Path
			}
			return files[i].Package < files[j].Package
		})
	}
	less(manifest.Files)
	less(manifest.ContextFiles)
	return manifest, nil
}
