package dataset

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"unicode/utf16"
)

const targetedMinerGenerator = "targeted-go-feature-miner"

var targetedFeatureSince = map[string]string{
	"self-reference": "1.26",
	"function-range": "1.23",
	"generic-method": "1.27",
	"generic-alias":  "1.24",
	"struct-tags":    "1.18",
}

type minedManifest struct {
	focusedManifest
	FeatureCounts map[string]int `json:"featureCounts"`
	Sources       []string       `json:"sources"`
}

func containsIdent(node ast.Node, name string) bool {
	found := false
	ast.Inspect(node, func(child ast.Node) bool {
		if ident, ok := child.(*ast.Ident); ok && ident.Name == name {
			found = true
			return false
		}
		return !found
	})
	return found
}

func isMethodShapedRange(expr ast.Expr) bool {
	switch value := expr.(type) {
	case *ast.SelectorExpr:
		return true
	case *ast.ParenExpr:
		return isMethodShapedRange(value.X)
	default:
		return false
	}
}

// MineSourceFeatures detects only source-level structures that are reliable
// without executing code or guessing from identifier spelling.
func MineSourceFeatures(filename, source string) ([]string, error) {
	file, err := parser.ParseFile(token.NewFileSet(), filename, source, parser.SkipObjectResolution)
	if err != nil {
		return nil, err
	}
	found := map[string]bool{}
	ast.Inspect(file, func(node ast.Node) bool {
		switch value := node.(type) {
		case *ast.FuncDecl:
			if value.Recv != nil && value.Type.TypeParams != nil && len(value.Type.TypeParams.List) != 0 {
				found["generic-method"] = true
			}
		case *ast.TypeSpec:
			if value.TypeParams != nil && value.Assign.IsValid() {
				found["generic-alias"] = true
			}
			if _, ok := value.Type.(*ast.InterfaceType); ok && value.TypeParams != nil {
				for _, field := range value.TypeParams.List {
					if containsIdent(field.Type, value.Name.Name) {
						found["self-reference"] = true
						break
					}
				}
			}
		case *ast.RangeStmt:
			if isMethodShapedRange(value.X) {
				found["function-range"] = true
			}
		case *ast.StructType:
			for _, field := range value.Fields.List {
				if field.Tag != nil {
					found["struct-tags"] = true
					break
				}
			}
		}
		return true
	})
	features := make([]string, 0, len(found))
	for feature := range found {
		features = append(features, feature)
	}
	sort.Strings(features)
	return features, nil
}

func earliestSince(features []string) string {
	result := ""
	for _, feature := range features {
		value := targetedFeatureSince[feature]
		if result == "" || value < result {
			result = value
		}
	}
	return result
}

func utf16OffsetForByte(source string, byteOffset int) int {
	if byteOffset <= 0 {
		return 0
	}
	return len(utf16.Encode([]rune(source[:byteOffset])))
}

func rangeMethodGoldConfirmed(filename string, record LabeledEntry) bool {
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, filename, record.Source, parser.SkipObjectResolution)
	if err != nil {
		return false
	}
	starts := map[int]bool{}
	ast.Inspect(file, func(node ast.Node) bool {
		rangeStmt, ok := node.(*ast.RangeStmt)
		if !ok {
			return true
		}
		expr := rangeStmt.X
		for {
			paren, ok := expr.(*ast.ParenExpr)
			if !ok {
				break
			}
			expr = paren.X
		}
		selector, ok := expr.(*ast.SelectorExpr)
		if !ok {
			return true
		}
		starts[utf16OffsetForByte(record.Source, fset.Position(selector.Sel.Pos()).Offset)] = true
		return true
	})
	for _, span := range record.Result.Spans {
		if starts[span.Start] && span.TokenType == "method" {
			return true
		}
	}
	return false
}

func confirmedFeatures(filename string, record LabeledEntry) ([]string, error) {
	features, err := MineSourceFeatures(filename, record.Source)
	if err != nil {
		return nil, err
	}
	if rangeMethodGoldConfirmed(filename, record) {
		return features, nil
	}
	filtered := features[:0]
	for _, feature := range features {
		if feature != "function-range" {
			filtered = append(filtered, feature)
		}
	}
	return filtered, nil
}

// BuildTargetedMinedCorpus filters already Gold-labeled, explicitly configured
// module corpora into a train-only focused stream. Validation and test examples
// come from structurally independent synthetic families; mined records
// stay train-only.
func BuildTargetedMinedCorpus(root, configPath, id string, progress ProgressFunc) (string, error) {
	if err := RequireGoldToolchain(); err != nil {
		return "", err
	}
	if !corpusIDPattern.MatchString(id) {
		return "", fmt.Errorf("invalid targeted corpus id %q", id)
	}
	config, err := readCorpusConfig(configPath)
	if err != nil {
		return "", err
	}
	parent := filepath.Join(root, "curricula")
	if err := os.MkdirAll(parent, 0o755); err != nil {
		return "", err
	}
	destination := filepath.Join(parent, id)
	stage, err := os.MkdirTemp(parent, ".mined-")
	if err != nil {
		return "", err
	}
	defer os.RemoveAll(stage)
	output, err := os.Create(LabeledPath(stage))
	if err != nil {
		return "", err
	}
	writer := bufio.NewWriterSize(output, 1<<20)
	encoder := json.NewEncoder(writer)
	encoder.SetEscapeHTML(false)
	counts := map[string]int{}
	sources := make([]string, 0, len(config.Sources))
	seen := map[string]bool{}
	families := map[string]bool{}
	manifest := minedManifest{focusedManifest: focusedManifest{SampleManifest: SampleManifest{
		FormatVersion: 1, Toolchain: GoldToolchain, Corpus: id, GOOS: runtime.GOOS, GOARCH: runtime.GOARCH,
	}, Kind: "focused", Generator: targetedMinerGenerator, Variants: 1},
		FeatureCounts: counts}
	for index, spec := range config.Sources {
		if progress != nil {
			progress(index+1, len(config.Sources), "Mining "+spec.ID+" ("+spec.Module+")")
		}
		corpus := CorpusPath(root, spec.ID)
		var sourceManifest SampleManifest
		if err := readJSON(SamplePath(corpus), &sourceManifest); err != nil {
			return "", fmt.Errorf("%s: build the configured module corpus before mining: %w", spec.ID, err)
		}
		if sourceManifest.Source == nil || sourceManifest.Source.Module != spec.Module || sourceManifest.Toolchain != GoldToolchain {
			return "", fmt.Errorf("%s: module corpus identity mismatch", spec.ID)
		}
		sources = append(sources, spec.Module+"@"+sourceManifest.Source.Version)
		input, err := os.Open(LabeledPath(corpus))
		if err != nil {
			return "", err
		}
		scanner := bufio.NewScanner(input)
		scanner.Buffer(make([]byte, 64<<10), 16<<20)
		for scanner.Scan() {
			var record LabeledEntry
			if err := json.Unmarshal(scanner.Bytes(), &record); err != nil {
				input.Close()
				return "", err
			}
			features, err := confirmedFeatures(record.Path, record)
			if err != nil {
				input.Close()
				return "", fmt.Errorf("%s:%s: %w", spec.ID, record.Path, err)
			}
			if len(features) == 0 || seen[record.ContentHash] {
				continue
			}
			seen[record.ContentHash] = true
			family := "targeted-real/" + spec.ID + "/" + record.Package
			families[family] = true
			for _, feature := range features {
				counts[feature]++
			}
			focused := focusedRecord{LabeledEntry: record, Family: family, Features: features,
				Since: earliestSince(features), Variant: 0, Split: "train"}
			if err := encoder.Encode(focused); err != nil {
				input.Close()
				return "", err
			}
			manifest.Files = append(manifest.Files, SampleEntry{Package: record.Package, Path: record.Path,
				DocumentKind: record.DocumentKind, Size: int64(len([]byte(record.Source))), ContentHash: record.ContentHash})
		}
		if err := scanner.Err(); err != nil {
			input.Close()
			return "", err
		}
		if err := input.Close(); err != nil {
			return "", err
		}
	}
	if len(manifest.Files) == 0 {
		return "", fmt.Errorf("targeted miner found no requested features; expand the explicit module allowlist")
	}
	manifest.Families = len(families)
	manifest.Sources = sources
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
				return "", fmt.Errorf("targeted corpus %s already exists with different content; choose a new id", id)
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
