package dataset

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
)

const (
	minimumSourceBytes int64 = 200
	maximumSourceBytes int64 = 100_000
)

func CollectStdlib(root string) (SampleManifest, error) {
	if err := RequireGoldToolchain(); err != nil {
		return SampleManifest{}, err
	}

	packages, err := listPackages("std")
	if err != nil {
		return SampleManifest{}, err
	}

	gorootSource := filepath.Join(runtime.GOROOT(), "src")
	files := make([]SampleEntry, 0)

	for _, pkg := range packages {
		if strings.HasPrefix(pkg.ImportPath, "vendor/") {
			continue
		}

		for _, name := range pkg.GoFiles {
			absolutePath := filepath.Join(pkg.Dir, name)
			metadata, err := os.Stat(absolutePath)
			if err != nil {
				return SampleManifest{}, fmt.Errorf("stat %s: %w", absolutePath, err)
			}
			if metadata.Size() < minimumSourceBytes || metadata.Size() > maximumSourceBytes {
				continue
			}

			content, err := os.ReadFile(absolutePath)
			if err != nil {
				return SampleManifest{}, fmt.Errorf("read %s: %w", absolutePath, err)
			}

			relativePath, err := filepath.Rel(gorootSource, absolutePath)
			if err != nil {
				return SampleManifest{}, fmt.Errorf("resolve stdlib path %s: %w", absolutePath, err)
			}

			digest := sha256.Sum256(content)
			files = append(files, SampleEntry{
				Package:      pkg.ImportPath,
				Path:         filepath.ToSlash(relativePath),
				DocumentKind: DocumentKind,
				Size:         metadata.Size(),
				ContentHash:  hex.EncodeToString(digest[:]),
			})
		}
	}

	sort.Slice(files, func(i, j int) bool {
		if files[i].Package == files[j].Package {
			return files[i].Path < files[j].Path
		}
		return files[i].Package < files[j].Package
	})

	manifest := SampleManifest{
		FormatVersion: FormatVersion,
		Toolchain:     runtime.Version(),
		Corpus:        StdlibCorpus,
		GOOS:          runtime.GOOS,
		GOARCH:        runtime.GOARCH,
		Files:         files,
	}

	if err := writeJSON(SamplePath(root), manifest); err != nil {
		return SampleManifest{}, fmt.Errorf("write sample manifest: %w", err)
	}

	return manifest, nil
}
