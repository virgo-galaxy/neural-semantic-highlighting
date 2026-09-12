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

	"github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/labeling"
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
	Profile   string `json:"profile,omitempty"`
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

func v1FocusedFamilies() []focusedFamilySpec {
	var result []focusedFamilySpec
	splits := []string{"train", "validation", "test"}
	for _, feature := range focusedFeatures {
		for form, split := range splits {
			result = append(result, focusedFamilySpec{
				Feature: feature.ID,
				Since:   feature.Since,
				ID:      fmt.Sprintf("%s/%s", feature.ID, split),
				Split:   split,
				Source:  feature.Forms[form],
			})
		}
	}
	return result
}

func focusedFamilies(profile string) ([]focusedFamilySpec, string, error) {
	switch profile {
	case "v1":
		return v1FocusedFamilies(), "modern-go-focused-v1", nil
	case "v2":
		targeted := map[string]bool{"self-reference": true, "function-range": true, "generic-method": true, "generic-alias": true, "struct-tags": true}
		families := make([]focusedFamilySpec, 0, len(v1FocusedFamilies())+len(focusedV2Families))
		for _, family := range v1FocusedFamilies() {
			if !targeted[family.Feature] {
				families = append(families, family)
			}
		}
		families = append(families, focusedV2Families...)
		return families, "modern-go-focused-v2", nil
	case "v2r2":
		targeted := map[string]bool{"self-reference": true, "function-range": true, "generic-method": true, "generic-alias": true, "struct-tags": true}
		families := make([]focusedFamilySpec, 0, len(v1FocusedFamilies())+len(focusedV2Families)+len(focusedV2R2ExtraFamilies))
		for _, family := range v1FocusedFamilies() {
			if !targeted[family.Feature] {
				families = append(families, family)
			}
		}
		families = append(families, focusedV2Families...)
		families = append(families, focusedV2R2ExtraFamilies...)
		return families, "modern-go-focused-v2r2", nil
	case "v2r3":
		targeted := map[string]bool{"self-reference": true, "function-range": true, "generic-method": true, "generic-alias": true, "struct-tags": true}
		families := make([]focusedFamilySpec, 0, len(v1FocusedFamilies())+len(focusedV2Families)+len(focusedV2R2ExtraFamilies)+len(focusedV2R3ExtraFamilies))
		for _, family := range v1FocusedFamilies() {
			if !targeted[family.Feature] {
				families = append(families, family)
			}
		}
		families = append(families, focusedV2Families...)
		families = append(families, focusedV2R2ExtraFamilies...)
		families = append(families, focusedV2R3ExtraFamilies...)
		return families, "modern-go-focused-v2r3", nil
	case "v3":
		return append([]focusedFamilySpec(nil), focusedV3Families...), "modern-go-curriculum-v3", nil
	case "sealed-v1":
		return append([]focusedFamilySpec(nil), sealedFocusedFamilies...), "sealed-go-acceptance-v1", nil
	default:
		return nil, "", fmt.Errorf("unknown focused profile %q", profile)
	}
}

func renderFocused(feature focusedFeature, form, variant int) (string, error) {
	if form < 0 || form >= len(feature.Forms) {
		return "", fmt.Errorf("%s: invalid form %d", feature.ID, form)
	}
	splits := []string{"train", "validation", "test"}
	return renderFocusedFamily(focusedFamilySpec{Feature: feature.ID, Since: feature.Since,
		ID: fmt.Sprintf("%s/%s", feature.ID, splits[form]), Split: splits[form], Source: feature.Forms[form]}, variant)
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

// BuildFocusedCorpus preserves the V1 generator for immutable replay.
func BuildFocusedCorpus(root, id string, variants int, progress ProgressFunc) (string, error) {
	return BuildFocusedCorpusProfile(root, id, variants, "v1", progress)
}

// BuildFocusedCorpusProfile creates an immutable focused curriculum outside the repository.
// V2 adds structural diversity and hard negatives; it never reuses validation or test source as training input.
func BuildFocusedCorpusProfile(root, id string, variants int, profile string, progress ProgressFunc) (string, error) {
	if err := RequireGoldToolchain(); err != nil {
		return "", err
	}
	if !corpusIDPattern.MatchString(id) || variants < 1 || variants > 32 {
		return "", fmt.Errorf("invalid focused id or variants (1..32)")
	}
	families, generator, err := focusedFamilies(profile)
	if err != nil {
		return "", err
	}
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
	}, Kind: "focused", Generator: generator, Profile: profile, Variants: variants, Families: len(families)}
	gold := labeling.NewStrictPackageLabeler(nil)
	seen := map[string]bool{}
	for familyIndex, family := range families {
		if progress != nil {
			progress(familyIndex+1, len(families), family.ID)
		}
		allowedSplit := family.Split == "train" || family.Split == "validation" || family.Split == "test"
		if profile == "sealed-v1" {
			allowedSplit = family.Split == "sealed"
		}
		if !allowedSplit {
			return "", fmt.Errorf("%s: invalid split %q for profile %q", family.ID, family.Split, profile)
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
