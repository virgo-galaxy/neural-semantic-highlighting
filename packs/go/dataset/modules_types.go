package dataset

import "path/filepath"

const ModuleFormatVersion = 2

const ModuleLabelerVersion = "go-gold-module-v1"

// CorpusConfig is an explicit allowlist, not an ecosystem-wide crawler.
type CorpusConfig struct {
	FormatVersion int          `json:"formatVersion"`
	Sources       []ModuleSpec `json:"sources"`
}

type ModuleSpec struct {
	ID      string `json:"id"`
	Module  string `json:"module"`
	Version string `json:"version"`
}

// ModuleSource identifies the immutable archive and the resolved build graph.
// It deliberately contains no machine-specific cache or source paths.
type ModuleSource struct {
	Labeler       string `json:"labeler"`
	Kind          string `json:"kind"`
	Module        string `json:"module"`
	Version       string `json:"version"`
	Sum           string `json:"sum"`
	GoModSum      string `json:"goModSum"`
	GoVersion     string `json:"goVersion"`
	WorkspaceHash string `json:"workspaceHash"`
	CGOEnabled    bool   `json:"cgoEnabled"`
}

type ModuleLock struct {
	FormatVersion int          `json:"formatVersion"`
	Toolchain     string       `json:"toolchain"`
	GOOS          string       `json:"goos"`
	GOARCH        string       `json:"goarch"`
	Spec          ModuleSpec   `json:"spec"`
	Source        ModuleSource `json:"source"`
}

type moduleDownload struct {
	Path     string `json:"Path"`
	Version  string `json:"Version"`
	Dir      string `json:"Dir"`
	Sum      string `json:"Sum"`
	GoModSum string `json:"GoModSum"`
	Error    string `json:"Error"`
}

type moduleMetadata struct {
	Path      string `json:"Path"`
	Version   string `json:"Version"`
	GoVersion string `json:"GoVersion"`
}

func CorpusPath(root, id string) string {
	return filepath.Join(root, "corpora", id)
}
