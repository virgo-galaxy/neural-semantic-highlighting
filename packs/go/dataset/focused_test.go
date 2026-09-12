package dataset

import (
	"encoding/json"
	"go/scanner"
	"go/token"
	"os"
	"path/filepath"
	"strings"
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

func TestFocusedV2HasStructuralDiversityAndHeldOutFamilies(t *testing.T) {
	families, _, err := focusedFamilies("v2")
	if err != nil {
		t.Fatal(err)
	}
	if len(families) < 40 {
		t.Fatalf("expected many structural families, got %d", len(families))
	}
	byFeature := map[string]map[string]int{}
	for _, family := range families {
		if byFeature[family.Feature] == nil {
			byFeature[family.Feature] = map[string]int{}
		}
		byFeature[family.Feature][family.Split]++
	}
	for _, feature := range []string{"self-reference", "function-range", "generic-method", "generic-alias", "struct-tags"} {
		counts := byFeature[feature]
		if counts["train"] < 4 || counts["validation"] < 2 || counts["test"] < 2 {
			t.Fatalf("%s has insufficient structural families: %v", feature, counts)
		}
	}
}

func focusedTemplateShape(source string) string {
	source = strings.NewReplacer("{{.Name}}", "Alpha0", "{{.Type}}", "int", "{{.Number}}", "3").Replace(source)
	var scan scanner.Scanner
	set := token.NewFileSet()
	file := set.AddFile("focused.go", set.Base(), len(source))
	scan.Init(file, []byte(source), nil, 0)
	preserved := map[string]bool{
		"any": true, "bool": true, "byte": true, "comparable": true, "error": true,
		"float32": true, "float64": true, "int": true, "int8": true, "int16": true, "int32": true, "int64": true,
		"rune": true, "string": true, "uint": true, "uint8": true, "uint16": true, "uint32": true, "uint64": true, "uintptr": true,
		"append": true, "cap": true, "clear": true, "close": true, "complex": true, "copy": true, "delete": true,
		"imag": true, "len": true, "make": true, "max": true, "min": true, "new": true, "panic": true, "print": true,
		"println": true, "real": true, "recover": true,
	}
	names := map[string]int{}
	parts := []string{}
	for {
		_, tok, literal := scan.Scan()
		if tok == token.EOF {
			break
		}
		switch tok {
		case token.IDENT:
			if preserved[literal] {
				parts = append(parts, literal)
			} else {
				index, ok := names[literal]
				if !ok {
					index = len(names)
					names[literal] = index
				}
				parts = append(parts, "identifier:"+string(rune('A'+index)))
			}
		case token.INT, token.FLOAT, token.IMAG:
			parts = append(parts, "literal:number")
		case token.CHAR, token.STRING:
			parts = append(parts, "literal:string")
		default:
			parts = append(parts, tok.String())
		}
	}
	return strings.Join(parts, " ")
}

func TestFocusedV2HeldOutShapesAreDistinct(t *testing.T) {
	families, _, err := focusedFamilies("v2")
	if err != nil {
		t.Fatal(err)
	}
	type seenShape struct {
		id    string
		split string
	}
	seen := map[string]seenShape{}
	for _, family := range families {
		shape := focusedTemplateShape(family.Source)
		if previous, ok := seen[shape]; ok && previous.split != family.Split {
			t.Fatalf("held-out near-copy shape: %s (%s) and %s (%s)", previous.id, previous.split, family.ID, family.Split)
		}
		seen[shape] = seenShape{id: family.ID, split: family.Split}
	}
}
func TestFocusedV2R2AddsProtobufStructTagTrainingShapes(t *testing.T) {
	families, _, err := focusedFamilies("v2r2")
	if err != nil {
		t.Fatal(err)
	}
	protobufTrain := 0
	for _, family := range families {
		if family.Split == "train" && strings.HasPrefix(family.ID, "struct-tags/train/protobuf-") {
			protobufTrain++
			if !strings.Contains(family.Source, "protobuf:") || !strings.Contains(family.Source, "proto3") {
				t.Fatalf("protobuf training family lacks realistic protobuf tag content: %s", family.ID)
			}
		}
	}
	if protobufTrain < 5 {
		t.Fatalf("expected at least five protobuf struct-tag training families, got %d", protobufTrain)
	}
}

func TestFocusedV2R2HeldOutShapesAreDistinct(t *testing.T) {
	families, _, err := focusedFamilies("v2r2")
	if err != nil {
		t.Fatal(err)
	}
	type seenShape struct{ id, split string }
	seen := map[string]seenShape{}
	for _, family := range families {
		shape := focusedTemplateShape(family.Source)
		if previous, ok := seen[shape]; ok && previous.split != family.Split {
			t.Fatalf("held-out near-copy shape: %s (%s) and %s (%s)", previous.id, previous.split, family.ID, family.Split)
		}
		seen[shape] = seenShape{id: family.ID, split: family.Split}
	}
}

func TestFocusedV2R3AddsBareMethodValueTrainingShapes(t *testing.T) {
	families, _, err := focusedFamilies("v2r3")
	if err != nil {
		t.Fatal(err)
	}
	methodValueTrain := 0
	negativeField := 0
	for _, family := range families {
		if family.Split != "train" || family.Feature != "function-range" {
			continue
		}
		if strings.Contains(family.ID, "function-field-negative") {
			negativeField++
		}
		if strings.Contains(family.Source, ".Visit") || strings.Contains(family.Source, ".Walk") ||
			strings.Contains(family.Source, ".Scan") || strings.Contains(family.Source, ".Entries") {
			methodValueTrain++
		}
	}
	if methodValueTrain < 4 {
		t.Fatalf("expected at least four bare method-value training families, got %d", methodValueTrain)
	}
	if negativeField != 1 {
		t.Fatalf("expected one function-valued field hard negative, got %d", negativeField)
	}
}

func TestFocusedV2R3HeldOutShapesAreDistinct(t *testing.T) {
	families, _, err := focusedFamilies("v2r3")
	if err != nil {
		t.Fatal(err)
	}
	type seenShape struct{ id, split string }
	seen := map[string]seenShape{}
	for _, family := range families {
		shape := focusedTemplateShape(family.Source)
		if previous, ok := seen[shape]; ok && previous.split != family.Split {
			t.Fatalf("held-out near-copy shape: %s (%s) and %s (%s)", previous.id, previous.split, family.ID, family.Split)
		}
		seen[shape] = seenShape{id: family.ID, split: family.Split}
	}
}

func TestSealedFocusedShapesDoNotOverlapV2R3(t *testing.T) {
	training, _, err := focusedFamilies("v2r3")
	if err != nil {
		t.Fatal(err)
	}
	sealed, _, err := focusedFamilies("sealed-v1")
	if err != nil {
		t.Fatal(err)
	}
	if len(sealed) < 10 {
		t.Fatalf("expected at least ten sealed structural families, got %d", len(sealed))
	}
	trainingShapes := map[string]string{}
	for _, family := range training {
		trainingShapes[focusedTemplateShape(family.Source)] = family.ID
	}
	sealedShapes := map[string]string{}
	featureCounts := map[string]int{}
	for _, family := range sealed {
		if family.Split != "sealed" {
			t.Fatalf("sealed family has non-sealed split: %s => %s", family.ID, family.Split)
		}
		shape := focusedTemplateShape(family.Source)
		if previous, ok := trainingShapes[shape]; ok {
			t.Fatalf("sealed shape overlaps existing curriculum: %s and %s", previous, family.ID)
		}
		if previous, ok := sealedShapes[shape]; ok {
			t.Fatalf("duplicate sealed shape: %s and %s", previous, family.ID)
		}
		sealedShapes[shape] = family.ID
		featureCounts[family.Feature]++
	}
	for _, feature := range []string{"self-reference", "function-range", "generic-method", "generic-alias", "struct-tags"} {
		if featureCounts[feature] < 2 {
			t.Fatalf("sealed feature %s has insufficient structural families: %d", feature, featureCounts[feature])
		}
	}
}
