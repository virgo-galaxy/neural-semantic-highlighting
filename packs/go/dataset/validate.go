package dataset

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"runtime"
	"sort"
	"unicode/utf16"

	"github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/labeling"
)

type packSchema struct {
	TokenTypes []schemaEntry `json:"tokenTypes"`
	Modifiers  []schemaEntry `json:"tokenModifiers"`
}

type schemaEntry struct {
	ID string `json:"id"`
}

func Validate(root string, schemaPath string) (Statistics, error) {
	if err := RequireGoldToolchain(); err != nil {
		return Statistics{}, err
	}

	var sample SampleManifest
	if err := readJSON(SamplePath(root), &sample); err != nil {
		return Statistics{}, fmt.Errorf("read sample manifest: %w", err)
	}
	if err := validateSampleManifest(sample); err != nil {
		return Statistics{}, err
	}

	schemaContent, err := os.ReadFile(schemaPath)
	if err != nil {
		return Statistics{}, fmt.Errorf("read schema: %w", err)
	}
	var schema packSchema
	if err := json.Unmarshal(schemaContent, &schema); err != nil {
		return Statistics{}, fmt.Errorf("decode schema: %w", err)
	}

	validTokenTypes := make(map[string]struct{}, len(schema.TokenTypes))
	for _, entry := range schema.TokenTypes {
		validTokenTypes[entry.ID] = struct{}{}
	}
	validModifiers := make(map[string]struct{}, len(schema.Modifiers))
	for _, entry := range schema.Modifiers {
		validModifiers[entry.ID] = struct{}{}
	}

	sampleByKey := make(map[string]SampleEntry, len(sample.Files))
	for _, entry := range sample.Files {
		key := datasetKey(entry.Package, entry.Path)
		if _, exists := sampleByKey[key]; exists {
			return Statistics{}, fmt.Errorf("duplicate sample entry %s", key)
		}
		sampleByKey[key] = entry
	}

	input, err := os.Open(LabeledPath(root))
	if err != nil {
		return Statistics{}, fmt.Errorf("open labeled dataset: %w", err)
	}
	defer input.Close()
	decoder := json.NewDecoder(bufio.NewReaderSize(input, 1<<20))

	statistics := Statistics{
		FormatVersion: sample.FormatVersion,
		Source:        sample.Source,
		Toolchain:     sample.Toolchain,
		Corpus:        sample.Corpus,
		GOOS:          sample.GOOS,
		GOARCH:        sample.GOARCH,
		TokenTypes:    map[string]int{},
		Modifiers:     map[string]int{},
	}
	packages := make(map[string]struct{})
	seen := make(map[string]struct{}, len(sample.Files))

	for {
		var entry LabeledEntry
		if err := decoder.Decode(&entry); err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return Statistics{}, fmt.Errorf("decode labeled dataset: %w", err)
		}

		key := datasetKey(entry.Package, entry.Path)
		if _, exists := seen[key]; exists {
			return Statistics{}, fmt.Errorf("duplicate labeled entry %s", key)
		}
		seen[key] = struct{}{}

		sampleEntry, ok := sampleByKey[key]
		if !ok {
			return Statistics{}, fmt.Errorf("labeled entry is not in sample manifest: %s", key)
		}
		if entry.DocumentKind != sampleEntry.DocumentKind {
			return Statistics{}, fmt.Errorf("%s: document kind changed", key)
		}

		digest := sha256.Sum256([]byte(entry.Source))
		contentHash := hex.EncodeToString(digest[:])
		if contentHash != sampleEntry.ContentHash || contentHash != entry.ContentHash {
			return Statistics{}, fmt.Errorf("%s: content hash mismatch", key)
		}
		if int64(len(entry.Source)) != sampleEntry.Size {
			return Statistics{}, fmt.Errorf(
				"%s: source size is %d bytes, expected %d",
				key,
				len(entry.Source),
				sampleEntry.Size,
			)
		}
		if entry.Result.OffsetEncoding != "utf-16" {
			return Statistics{}, fmt.Errorf(
				"%s: offset encoding is %q, expected utf-16",
				key,
				entry.Result.OffsetEncoding,
			)
		}
		if len(entry.Result.Spans) == 0 {
			return Statistics{}, fmt.Errorf("%s: no semantic spans", key)
		}

		utf16Length := len(utf16.Encode([]rune(entry.Source)))
		if err := validateSpans(key, entry.Result.Spans, utf16Length, validTokenTypes, validModifiers); err != nil {
			return Statistics{}, err
		}

		statistics.Files++
		statistics.SourceBytes += len(entry.Source)
		statistics.SourceUTF16Units += utf16Length
		packages[entry.Package] = struct{}{}
		for _, span := range entry.Result.Spans {
			statistics.Spans++
			statistics.TokenTypes[span.TokenType]++
			for _, modifier := range span.Modifiers {
				statistics.Modifiers[modifier]++
			}
		}
	}

	if len(seen) != len(sampleByKey) {
		missing := make([]string, 0)
		for key := range sampleByKey {
			if _, ok := seen[key]; !ok {
				missing = append(missing, key)
			}
		}
		sort.Strings(missing)
		return Statistics{}, fmt.Errorf("sample entries were not labeled: %v", missing)
	}

	statistics.Packages = len(packages)
	if err := writeJSON(StatisticsPath(root), statistics); err != nil {
		return Statistics{}, fmt.Errorf("write statistics: %w", err)
	}

	return statistics, nil
}

func validateSampleManifest(sample SampleManifest) error {
	if sample.FormatVersion == FormatVersion {
		return validateManifestHeader(sample.FormatVersion, sample.Toolchain, sample.Corpus, sample.GOOS, sample.GOARCH)
	}
	if sample.FormatVersion != ModuleFormatVersion {
		return fmt.Errorf("unsupported dataset format version %d", sample.FormatVersion)
	}
	if sample.Toolchain != GoldToolchain || sample.GOOS != runtime.GOOS || sample.GOARCH != runtime.GOARCH {
		return fmt.Errorf("module corpus toolchain/build context does not match this execution")
	}
	if !corpusIDPattern.MatchString(sample.Corpus) || sample.Source == nil {
		return fmt.Errorf("module corpus is missing a valid id or source identity")
	}
	source := sample.Source
	if source.Labeler != ModuleLabelerVersion || source.Kind != "module" || source.Module == "" || source.Version == "" || source.Sum == "" || source.GoModSum == "" || source.WorkspaceHash == "" || source.CGOEnabled {
		return fmt.Errorf("incomplete or unsupported module corpus identity")
	}
	if len(sample.Files) == 0 || len(sample.ContextFiles) == 0 {
		return fmt.Errorf("module corpus has no sampled files or package context")
	}
	context := map[string]SampleEntry{}
	for _, entry := range sample.ContextFiles {
		key := datasetKey(entry.Package, entry.Path)
		if _, exists := context[key]; exists {
			return fmt.Errorf("duplicate package context %s", key)
		}
		context[key] = entry
	}
	for _, entry := range sample.Files {
		if context[datasetKey(entry.Package, entry.Path)] != entry {
			return fmt.Errorf("sample %s is missing matching package context", entry.Path)
		}
	}
	return nil
}

func validateSpans(
	key string,
	spans []labeling.SemanticSpan,
	utf16Length int,
	validTokenTypes map[string]struct{},
	validModifiers map[string]struct{},
) error {
	previousEnd := 0
	for _, span := range spans {
		if _, ok := validTokenTypes[span.TokenType]; !ok {
			return fmt.Errorf("%s: unknown token type %q", key, span.TokenType)
		}
		for _, modifier := range span.Modifiers {
			if _, ok := validModifiers[modifier]; !ok {
				return fmt.Errorf("%s: unknown modifier %q", key, modifier)
			}
		}
		if span.Start < 0 || span.End > utf16Length {
			return fmt.Errorf(
				"%s: span %d-%d is outside UTF-16 length %d",
				key,
				span.Start,
				span.End,
				utf16Length,
			)
		}
		if span.Start >= span.End {
			return fmt.Errorf("%s: empty or reversed span %d-%d", key, span.Start, span.End)
		}
		if span.Start < previousEnd {
			return fmt.Errorf("%s: overlapping or unsorted span %d-%d", key, span.Start, span.End)
		}
		previousEnd = span.End
	}
	return nil
}

func datasetKey(packageName string, path string) string {
	return packageName + ":" + path
}
