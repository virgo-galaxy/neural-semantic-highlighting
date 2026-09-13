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

func TestFocusedCorpusReplay(t *testing.T) {
	root := t.TempDir()
	families, _ := focusedFamilies()
	path, err := BuildFocusedCorpus(root, "modern", 2, nil)
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
	if len(manifest.Files) != len(families)*2 {
		t.Fatalf("wrong focused sample count: got %d want %d", len(manifest.Files), len(families)*2)
	}
	before, err := os.ReadFile(LabeledPath(path))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := BuildFocusedCorpus(root, "modern", 2, nil); err != nil {
		t.Fatal(err)
	}
	after, err := os.ReadFile(LabeledPath(path))
	if err != nil {
		t.Fatal(err)
	}
	if string(before) != string(after) {
		t.Fatal("replay changed focused Gold")
	}
	if _, err := BuildFocusedCorpus(root, "modern", 3, nil); err == nil {
		t.Fatal("overwrote an immutable corpus")
	}
	if _, err := BuildFocusedCorpus(root, "../escape", 2, nil); err == nil {
		t.Fatal("allowed path escape")
	}
	if _, err := os.Stat(filepath.Join(root, "sample.json")); !os.IsNotExist(err) {
		t.Fatal("focused generation touched stdlib data")
	}
}

func TestFocusedCurriculumRendersAllFamilies(t *testing.T) {
	families, _ := focusedFamilies()
	for _, family := range families {
		for _, variant := range []int{0, 7, 15, 31} {
			if _, err := renderFocusedFamily(family, variant); err != nil {
				t.Fatalf("%s variant %d: %v", family.ID, variant, err)
			}
		}
	}
}

func TestFocusedCurriculumGoldLabelsEveryFamily(t *testing.T) {
	families, _ := focusedFamilies()
	gold := labeling.NewStrictPackageLabeler(nil)
	for _, family := range families {
		for _, variant := range []int{0, 8, 16, 24} {
			source, err := renderFocusedFamily(family, variant)
			if err != nil {
				t.Fatalf("%s variant %d render: %v", family.ID, variant, err)
			}
			_, err = gold.LabelPackage(labeling.PackageRequest{
				PackagePath:  "example.local/curriculum-check",
				DocumentKind: "go",
				GoVersion:    GoldToolchain,
				Files:        []labeling.SourceFile{{Path: "source.go", Source: source}},
			})
			if err != nil {
				t.Fatalf("%s variant %d does not type-check under Gold: %v\n%s", family.ID, variant, err, source)
			}
		}
	}
}

func TestFocusedCurriculumIsSelfContainedCapabilityMatrix(t *testing.T) {
	families, generator := focusedFamilies()
	if generator != "go-focused-curriculum" {
		t.Fatalf("unexpected generator: %s", generator)
	}
	expected := []string{
		"generic-functions", "comparable-array", "builtins", "integer-range", "function-range",
		"generic-alias", "new-expression", "self-reference", "generic-method", "promoted-field-literal",
		"function-inference", "struct-tags", "strings", "core-semantics",
	}
	counts := map[string]map[string]int{}
	for _, family := range families {
		if counts[family.Feature] == nil {
			counts[family.Feature] = map[string]int{}
		}
		counts[family.Feature][family.Split]++
	}
	if len(counts) != len(expected) {
		t.Fatalf("feature count = %d, want %d: %v", len(counts), len(expected), counts)
	}
	for _, feature := range expected {
		bySplit := counts[feature]
		if bySplit["train"] < 3 || bySplit["validation"] < 2 || bySplit["test"] < 2 {
			t.Fatalf("feature %s has insufficient split coverage: %v", feature, bySplit)
		}
	}
}

func TestFocusedCurriculumHeldOutShapesAreDistinct(t *testing.T) {
	families, _ := focusedFamilies()
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

func TestFocusedCurriculumValidationHasAcceptanceSupport(t *testing.T) {
	families, _ := focusedFamilies()
	targets := map[string]string{
		"self-reference": "interface",
		"function-range": "method",
		"generic-method": "method",
		"generic-alias":  "type-parameter",
		"struct-tags":    "string",
		"strings":        "string",
	}
	counts := map[string]int{}
	gold := labeling.NewStrictPackageLabeler(nil)
	for _, family := range families {
		role, targeted := targets[family.Feature]
		if !targeted || family.Split != "validation" {
			continue
		}
		for variant := 0; variant < 16; variant++ {
			source, err := renderFocusedFamily(family, variant)
			if err != nil {
				t.Fatalf("%s variant %d render: %v", family.ID, variant, err)
			}
			results, err := gold.LabelPackage(labeling.PackageRequest{
				PackagePath:  "example.local/curriculum-support",
				DocumentKind: "go",
				GoVersion:    GoldToolchain,
				Files:        []labeling.SourceFile{{Path: "source.go", Source: source}},
			})
			if err != nil {
				t.Fatalf("%s variant %d Gold: %v\n%s", family.ID, variant, err, source)
			}
			for _, span := range results[0].Result.Spans {
				if span.TokenType == role {
					counts[family.Feature]++
				}
			}
		}
	}
	for feature := range targets {
		if counts[feature] < 32 {
			t.Fatalf("validation target %s has support %d at 16 variants; want >= 32", feature, counts[feature])
		}
	}
}

func TestFocusedCurriculumCoversSelectorTagAndStringGeneralization(t *testing.T) {
	families, _ := focusedFamilies()
	methodValueShapes := 0
	functionFieldNegatives := 0
	nestedMultiTags := 0
	tagLikeNegatives := 0
	stringLong := 0
	stringMultiline := 0
	stringRune := 0
	for _, family := range families {
		if family.Split != "train" {
			continue
		}
		switch family.Feature {
		case "function-range":
			if strings.Contains(family.Source, ".Walk") || strings.Contains(family.Source, ".Emit") ||
				strings.Contains(family.Source, ".Forward") || strings.Contains(family.Source, ".Reverse") ||
				strings.Contains(family.Source, ".Each") || strings.Contains(family.Source, ".Iterate") ||
				strings.Contains(family.Source, ".Entries") || strings.Contains(family.Source, ".Yield") ||
				strings.Contains(family.Source, ".Values") || strings.Contains(family.Source, ".Ascend") {
				methodValueShapes++
			}
			if strings.Contains(family.ID, "function-field") {
				functionFieldNegatives++
			}
		case "struct-tags":
			if strings.Contains(family.Source, "struct {") && strings.Count(family.Source, "json:") >= 2 &&
				strings.Contains(family.Source, "xml:") {
				nestedMultiTags++
			}
			if strings.Contains(family.ID, "taglike-negative") || strings.Contains(family.ID, "quoted-tag-negative") {
				tagLikeNegatives++
			}
		case "strings":
			if len(family.Source) > 700 {
				stringLong++
			}
			if strings.Contains(family.Source, "Usage:") || strings.Contains(family.Source, "SECTION A") ||
				strings.Contains(family.Source, "| Key | Type |") {
				stringMultiline++
			}
			if strings.Contains(family.Source, "[]rune") {
				stringRune++
			}
		}
	}
	if methodValueShapes < 5 {
		t.Fatalf("needs broad bare method-value coverage, got %d families", methodValueShapes)
	}
	if functionFieldNegatives < 1 {
		t.Fatal("needs a function-valued field hard negative")
	}
	if nestedMultiTags < 1 || tagLikeNegatives < 2 {
		t.Fatalf("struct-tag coverage incomplete: nested=%d negatives=%d", nestedMultiTags, tagLikeNegatives)
	}
	if stringLong < 1 || stringMultiline < 2 || stringRune < 1 {
		t.Fatalf("string robustness incomplete: long=%d multiline=%d rune=%d", stringLong, stringMultiline, stringRune)
	}
}
