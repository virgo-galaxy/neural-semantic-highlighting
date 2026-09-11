package dataset

import (
	"archive/zip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/fs"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"strings"
	"testing"
)

func TestModuleSpecValidation(t *testing.T) {
	for _, id := range []string{"../outside", "/tmp/absolute", "x/other", "", "..", "x other"} {
		if err := validateModuleSpec(ModuleSpec{ID: id, Module: "example.com/sample", Version: "v1.0.0"}); err == nil {
			t.Fatalf("accepted invalid id %q", id)
		}
	}
	if err := validateModuleSpec(ModuleSpec{ID: "x-sync", Module: "golang.org/x/sync", Version: "latest"}); err != nil {
		t.Fatal(err)
	}
}

func TestModuleEnvironmentIsIsolated(t *testing.T) {
	t.Setenv("GOFLAGS", "-tags=unexpected")
	t.Setenv("GOWORK", "/unexpected/go.work")
	before := os.Getenv("GOFLAGS")
	root := t.TempDir()
	values := map[string]string{}
	for _, item := range moduleEnvironment(root) {
		key, value, _ := strings.Cut(item, "=")
		values[key] = value
	}
	for key, want := range map[string]string{"GOFLAGS": "", "GOWORK": "off", "GOTOOLCHAIN": "local", "CGO_ENABLED": "0", "GOMODCACHE": filepath.Join(root, "cache", "modules")} {
		if values[key] != want {
			t.Fatalf("%s: got %q, want %q", key, values[key], want)
		}
	}
	if os.Getenv("GOFLAGS") != before {
		t.Fatal("parent environment was modified")
	}
}

func TestCollectModuleKeepsFullPackageContext(t *testing.T) {
	root := t.TempDir()
	large := "package sample\n// " + strings.Repeat("x", 240) + "\nvar Value = helper\n"
	small := "package sample\nvar helper = 1\n"
	writeTestFile(t, filepath.Join(root, "large.go"), large)
	writeTestFile(t, filepath.Join(root, "small.go"), small)
	metadata := &moduleMetadata{Path: "example.com/sample", Version: "v1.0.0"}
	lock := ModuleLock{Toolchain: GoldToolchain, GOOS: runtime.GOOS, GOARCH: runtime.GOARCH, Spec: ModuleSpec{ID: "sample"}, Source: ModuleSource{Module: metadata.Path}}
	manifest, err := collectModule(lock, root, []goListPackage{{Dir: root, ImportPath: metadata.Path, Module: metadata, GoFiles: []string{"large.go", "small.go"}}})
	if err != nil {
		t.Fatal(err)
	}
	if len(manifest.Files) != 1 || len(manifest.ContextFiles) != 2 {
		t.Fatalf("sample/context counts: %d/%d", len(manifest.Files), len(manifest.ContextFiles))
	}
	if manifest.Files[0].Path != "large.go" {
		t.Fatal("wrong sampled file")
	}
}

func TestValidateLegacyAndModuleHeaders(t *testing.T) {
	legacy := SampleManifest{FormatVersion: 1, Toolchain: GoldToolchain, Corpus: StdlibCorpus, GOOS: runtime.GOOS, GOARCH: runtime.GOARCH}
	if err := validateSampleManifest(legacy); err != nil {
		t.Fatal(err)
	}
	legacy.Corpus = "x-sync"
	if err := validateSampleManifest(legacy); err == nil {
		t.Fatal("module identity must not masquerade as legacy stdlib")
	}
	module := legacy
	module.FormatVersion = 2
	if err := validateSampleManifest(module); err == nil {
		t.Fatal("module source metadata is required")
	}
}

// A file:// proxy exercises real resolution and dependency exports without
// network access, credentials, or global package installation.
func TestModulePipelineOffline(t *testing.T) {
	proxy := t.TempDir()
	root := t.TempDir()
	// Module cache directories are read-only by design. Restore permissions
	// only inside this test's temporary cache before testing removes it.
	t.Cleanup(func() {
		_ = filepath.WalkDir(filepath.Join(root, "cache", "modules"), func(path string, entry fs.DirEntry, err error) error {
			if err == nil && entry.IsDir() {
				return os.Chmod(path, 0o755)
			}
			return nil
		})
	})
	t.Setenv("GOPROXY", (&url.URL{Scheme: "file", Path: filepath.ToSlash(proxy)}).String())
	t.Setenv("GOSUMDB", "off") // Only synthetic example.com modules in this test.
	t.Setenv("GONOPROXY", "none")
	t.Setenv("GOPRIVATE", "")
	t.Setenv("GONOSUMDB", "none")
	addProxyModule(t, proxy, "example.com/support", "v1.0.0", "module example.com/support\n\ngo 1.18\n", map[string]string{
		"support.go": "package support\ntype Record struct { Name string }\nfunc (r Record) Render() string { return r.Name }\n",
	})
	source := "package sample\nimport \"example.com/support\"\n// " + strings.Repeat("a", 220) + "\nfunc Read(value support.Record) string { return value.Render() }\n"
	addProxyModule(t, proxy, "example.com/sample", "v1.0.0", "module example.com/sample\n\ngo 1.18\n\nrequire example.com/support v1.0.0\n", map[string]string{
		"sample.go": source,
		"tiny.go":   "package sample\nvar localValue = 1\n",
	})
	configPath := filepath.Join(t.TempDir(), "sources.json")
	config := CorpusConfig{FormatVersion: 1, Sources: []ModuleSpec{{ID: "sample", Module: "example.com/sample", Version: "latest"}}}
	if err := writeJSON(configPath, config); err != nil {
		t.Fatal(err)
	}
	writeTestFile(t, SamplePath(root), "existing stdlib data\n")
	schemaPath := filepath.Join("..", "schema.json")
	result, err := RunModules(root, configPath, schemaPath, "sample", nil)
	if err != nil {
		t.Fatal(err)
	}
	if len(result) != 1 || result[0].Files != 1 || result[0].Source.Version != "v1.0.0" {
		t.Fatalf("unexpected result %#v", result)
	}
	if result[0].TokenTypes["method"] == 0 || result[0].TokenTypes["namespace"] == 0 {
		t.Fatal("dependency-backed selectors were not labeled")
	}
	if result[0].Source.WorkspaceHash == "" {
		t.Fatal("build graph was not locked")
	}
	if content, _ := os.ReadFile(SamplePath(root)); string(content) != "existing stdlib data\n" {
		t.Fatal("stdlib artifact was overwritten")
	}
	before, err := os.ReadFile(LabeledPath(CorpusPath(root, "sample")))
	if err != nil {
		t.Fatal(err)
	}
	addProxyModule(t, proxy, "example.com/sample", "v1.1.0", "module example.com/sample\n\ngo 1.18\n", map[string]string{"new.go": "package sample\nvar Updated = true\n"})
	replayed, err := RunModules(root, configPath, schemaPath, "sample", nil)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(replayed, result) {
		t.Fatal("locked replay changed statistics")
	}
	after, _ := os.ReadFile(LabeledPath(CorpusPath(root, "sample")))
	if string(before) != string(after) {
		t.Fatal("locked replay changed labeled output")
	}
	var manifest SampleManifest
	if err := readJSON(SamplePath(CorpusPath(root, "sample")), &manifest); err != nil {
		t.Fatal(err)
	}
	if len(manifest.ContextFiles) != 2 {
		t.Fatal("excluded small file was lost from package context")
	}
	var entry LabeledEntry
	if err := json.Unmarshal(before, &entry); err != nil {
		t.Fatal(err)
	}
	entry.Source += "// changed\n"
	if err := writeJSON(LabeledPath(CorpusPath(root, "sample")), entry); err != nil {
		t.Fatal(err)
	}
	if _, err := Validate(CorpusPath(root, "sample"), schemaPath); err == nil {
		t.Fatal("accepted changed source")
	}
	mod, err := os.ReadFile(filepath.Join("..", "go.mod"))
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(mod), "example.com/support") {
		t.Fatal("corpus polluted repository dependencies")
	}
}

func TestWorkspaceHashDetectsChanges(t *testing.T) {
	root := t.TempDir()
	writeTestFile(t, filepath.Join(root, "go.mod"), "module example.com/sample\n")
	before, err := workspaceHash(root)
	if err != nil {
		t.Fatal(err)
	}
	writeTestFile(t, filepath.Join(root, "go.sum"), "changed\n")
	after, err := workspaceHash(root)
	if err != nil {
		t.Fatal(err)
	}
	if before == after {
		t.Fatal("workspace hash ignored a dependency change")
	}
}

func TestReadModuleEntryRejectsEscapes(t *testing.T) {
	root := t.TempDir()
	if _, _, err := readModuleEntry(root, goListPackage{Dir: filepath.Dir(root), ImportPath: "example.com/sample"}, "outside.go"); err == nil {
		t.Fatal("accepted escaping source path")
	}
}

func writeTestFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

func addProxyModule(t *testing.T, proxy, module, version, mod string, files map[string]string) {
	t.Helper()
	base := filepath.Join(proxy, filepath.FromSlash(module), "@v")
	writeTestFile(t, filepath.Join(base, version+".mod"), mod)
	writeTestFile(t, filepath.Join(base, version+".info"), fmt.Sprintf(`{"Version":%q,"Time":"2024-01-01T00:00:00Z"}`, version))
	listPath := filepath.Join(base, "list")
	previous, _ := os.ReadFile(listPath)
	writeTestFile(t, listPath, string(previous)+version+"\n")
	archive, err := os.Create(filepath.Join(base, version+".zip"))
	if err != nil {
		t.Fatal(err)
	}
	writer := zip.NewWriter(archive)
	all := map[string]string{"go.mod": mod}
	for name, content := range files {
		all[name] = content
	}
	for name, content := range all {
		entry, err := writer.Create(module + "@" + version + "/" + name)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := entry.Write([]byte(content)); err != nil {
			t.Fatal(err)
		}
	}
	if err := writer.Close(); err != nil {
		t.Fatal(err)
	}
	if err := archive.Close(); err != nil {
		t.Fatal(err)
	}
}

func TestSampleHashUsesOriginalBytes(t *testing.T) {
	root := t.TempDir()
	source := "package sample\r\n// 🌍\r\nvar Value = 1\r\n"
	writeTestFile(t, filepath.Join(root, "source.go"), source)
	entry, got, err := readModuleEntry(root, goListPackage{Dir: root, ImportPath: "example.com/sample"}, "source.go")
	if err != nil {
		t.Fatal(err)
	}
	digest := sha256.Sum256([]byte(source))
	if entry.ContentHash != hex.EncodeToString(digest[:]) || got != source {
		t.Fatal("source bytes changed")
	}
}
