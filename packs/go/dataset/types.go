package dataset

import "github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/labeling"

const (
	FormatVersion = 1
	GoldToolchain = "go1.27.1"
	DocumentKind  = "go"
	StdlibCorpus  = "stdlib"
)

type SampleManifest struct {
	FormatVersion int           `json:"formatVersion"`
	Toolchain     string        `json:"toolchain"`
	Corpus        string        `json:"corpus"`
	GOOS          string        `json:"goos"`
	GOARCH        string        `json:"goarch"`
	Files         []SampleEntry `json:"files"`
}

type SampleEntry struct {
	Package      string `json:"package"`
	Path         string `json:"path"`
	DocumentKind string `json:"documentKind"`
	Size         int64  `json:"size"`
	ContentHash  string `json:"contentHash"`
}

type LabeledEntry struct {
	Package      string                   `json:"package"`
	Path         string                   `json:"path"`
	DocumentKind string                   `json:"documentKind"`
	ContentHash  string                   `json:"contentHash"`
	Source       string                   `json:"source"`
	Result       labeling.HighlightResult `json:"result"`
}

type LabelSummary struct {
	Files int
}

type ProgressFunc func(current int, total int, packageName string)

type Statistics struct {
	FormatVersion    int            `json:"formatVersion"`
	Toolchain        string         `json:"toolchain"`
	Corpus           string         `json:"corpus"`
	GOOS             string         `json:"goos"`
	GOARCH           string         `json:"goarch"`
	Packages         int            `json:"packages"`
	Files            int            `json:"files"`
	Spans            int            `json:"spans"`
	SourceBytes      int            `json:"sourceBytes"`
	SourceUTF16Units int            `json:"sourceUtf16Units"`
	TokenTypes       map[string]int `json:"tokenTypes"`
	Modifiers        map[string]int `json:"modifiers"`
}
