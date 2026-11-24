package dataset

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"go/format"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"text/template"

	"github.com/virgo-galaxy/virgo-nsh/packs/go/labeling"
)

type focusedRecord struct {
	LabeledEntry
	Family   string   `json:"family"`
	Features []string `json:"features"`
	Since    string   `json:"since"`
	Variant  int      `json:"variant"`
	Split    string   `json:"split"`
}

type focusedManifest struct {
	SampleManifest
	Kind      string `json:"kind"`
	Generator string `json:"generator"`
	Variants  int    `json:"variants"`
	Families  int    `json:"families"`
}

type focusedFamilySpec struct {
	Feature string
	Since   string
	ID      string
	Split   string
	Source  string
}

func focusedFamilies() ([]focusedFamilySpec, string) {
	return append([]focusedFamilySpec(nil), curriculumFamilies...), "go-focused-curriculum"
}

func renderFocusedFamily(family focusedFamilySpec, variant int) (string, error) {
	t, err := template.New(family.ID).Option("missingkey=error").Parse("package sample\n\n" + family.Source + "\n")
	if err != nil {
		return "", err
	}
	data := struct {
		Name, Type string
		Number     int
	}{
		Name:   fmt.Sprintf("%s%d", []string{"Alpha", "Beta", "Gamma", "Delta", "Sigma", "Omega", "Theta", "Kappa"}[variant%8], variant),
		Type:   []string{"int", "int32", "int64", "float64"}[(variant/8)%4],
		Number: variant + 3,
	}
	var output bytes.Buffer
	if err := t.Execute(&output, data); err != nil {
		return "", err
	}
	formatted, err := format.Source(output.Bytes())
	if err != nil {
		return "", fmt.Errorf("%s variant %d: %w", family.ID, variant, err)
	}
	return string(formatted), nil
}

// BuildFocusedCorpus creates one immutable integrated curriculum outside the repository.
func BuildFocusedCorpus(root, id string, variants int, progress ProgressFunc) (string, error) {
	if err := RequireGoldToolchain(); err != nil {
		return "", err
	}
	if !corpusIDPattern.MatchString(id) || variants < 1 || variants > 32 {
		return "", fmt.Errorf("invalid focused id or variants (1..32)")
	}
	families, generator := focusedFamilies()
	parent := filepath.Join(root, "curricula")
	if err := os.MkdirAll(parent, 0o755); err != nil {
		return "", err
	}
	destination := filepath.Join(parent, id)
	stage, err := os.MkdirTemp(parent, ".focused-")
	if err != nil {
		return "", err
	}
	defer os.RemoveAll(stage)
	output, err := os.Create(LabeledPath(stage))
	if err != nil {
		return "", err
	}
	defer output.Close()
	writer := bufio.NewWriter(output)
	encoder := json.NewEncoder(writer)
	encoder.SetEscapeHTML(false)
	manifest := focusedManifest{SampleManifest: SampleManifest{
		FormatVersion: 1, Toolchain: GoldToolchain, Corpus: id, GOOS: runtime.GOOS, GOARCH: runtime.GOARCH,
	}, Kind: "focused", Generator: generator, Variants: variants, Families: len(families)}
	gold := labeling.NewStrictPackageLabeler(nil)
	seen := map[string]bool{}
	for familyIndex, family := range families {
		if progress != nil {
			progress(familyIndex+1, len(families), family.ID)
		}
		if family.Split != "train" && family.Split != "validation" && family.Split != "test" {
			return "", fmt.Errorf("%s: invalid split %q", family.ID, family.Split)
		}
		for variant := 0; variant < variants; variant++ {
			source, err := renderFocusedFamily(family, variant)
			if err != nil {
				return "", err
			}
			path := fmt.Sprintf("%s/%02d.go", family.ID, variant)
			packagePath := "example.local/curriculum/" + strings.NewReplacer("-", "_", "/", "_").Replace(family.ID)
			results, err := gold.LabelPackage(labeling.PackageRequest{
				PackagePath: packagePath, DocumentKind: DocumentKind, GoVersion: GoldToolchain,
				Files: []labeling.SourceFile{{Path: path, Source: source}},
			})
			if err != nil {
				return "", fmt.Errorf("focused %s: %w", path, err)
			}
			hash := sha256.Sum256([]byte(source))
			contentHash := hex.EncodeToString(hash[:])
			if seen[contentHash] {
				return "", fmt.Errorf("duplicate focused source: %s", path)
			}
			seen[contentHash] = true
			record := focusedRecord{LabeledEntry: LabeledEntry{Package: packagePath, Path: path, DocumentKind: DocumentKind,
				ContentHash: contentHash, Source: source, Result: results[0].Result},
				Family: family.ID, Features: []string{family.Feature}, Since: family.Since, Variant: variant, Split: family.Split}
			if err := encoder.Encode(record); err != nil {
				return "", err
			}
			manifest.Files = append(manifest.Files, SampleEntry{Package: packagePath, Path: path, DocumentKind: DocumentKind,
				Size: int64(len(source)), ContentHash: contentHash})
		}
	}
	if err := writer.Flush(); err != nil {
		return "", err
	}
	if err := output.Close(); err != nil {
		return "", err
	}
	metadata, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(SamplePath(stage), append(metadata, '\n'), 0o644); err != nil {
		return "", err
	}
	if _, err := os.Stat(destination); err == nil {
		for _, name := range []string{"sample.json", "labeled-sample.jsonl"} {
			old, readErr := os.ReadFile(filepath.Join(destination, name))
			if readErr != nil {
				return "", readErr
			}
			fresh, readErr := os.ReadFile(filepath.Join(stage, name))
			if readErr != nil {
				return "", readErr
			}
			if !bytes.Equal(old, fresh) {
				return "", fmt.Errorf("focused corpus %s already exists with different content; choose a new id", id)
			}
		}
		return destination, nil
	} else if !os.IsNotExist(err) {
		return "", err
	}
	if err := os.Rename(stage, destination); err != nil {
		return "", err
	}
	return destination, nil
}
