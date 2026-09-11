package dataset

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/labeling"
)

func TestFocusedFamilies(t *testing.T) {
	gold := labeling.NewStrictPackageLabeler(nil)
	for _, feature := range focusedFeatures {
		for form := range feature.Forms {
			for _, variant := range []int{0, 7, 15, 31} {
				source, err := renderFocused(feature, form, variant)
				if err != nil {
					t.Fatal(err)
				}
				_, err = gold.LabelPackage(labeling.PackageRequest{PackagePath: "example.local/focused", DocumentKind: "go", GoVersion: "go1.27.1",
					Files: []labeling.SourceFile{{Path: "source.go", Source: source}}})
				if err != nil {
					t.Fatalf("%s/%d variant %d: %v\n%s", feature.ID, form, variant, err, source)
				}
			}
		}
	}
}

func TestFocusedCorpusReplay(t *testing.T) {
	root := t.TempDir()
	path, err := BuildFocusedCorpus(root, "test-modern", 2, nil)
	if err != nil {
		t.Fatal(err)
	}
	var manifest focusedManifest
	content, err := os.ReadFile(SamplePath(path))
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(content, &manifest); err != nil {
		t.Fatal(err)
	}
	if len(manifest.Files) != len(focusedFeatures)*3*2 {
		t.Fatal("wrong focused sample count")
	}
	before, err := os.ReadFile(LabeledPath(path))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := BuildFocusedCorpus(root, "test-modern", 2, nil); err != nil {
		t.Fatal(err)
	}
	after, err := os.ReadFile(LabeledPath(path))
	if err != nil {
		t.Fatal(err)
	}
	if string(before) != string(after) {
		t.Fatal("replay changed focused Gold")
	}
	if _, err := BuildFocusedCorpus(root, "test-modern", 3, nil); err == nil {
		t.Fatal("overwrote an immutable corpus")
	}
	if _, err := BuildFocusedCorpus(root, "../escape", 2, nil); err == nil {
		t.Fatal("allowed path escape")
	}
	if _, err := os.Stat(filepath.Join(root, "sample.json")); !os.IsNotExist(err) {
		t.Fatal("focused generation touched stdlib data")
	}
}
