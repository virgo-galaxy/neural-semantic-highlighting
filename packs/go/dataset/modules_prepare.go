package dataset

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
)

var corpusIDPattern = regexp.MustCompile(`^[a-z][a-z0-9-]*$`)

func readCorpusConfig(path string) (CorpusConfig, error) {
	var config CorpusConfig
	if err := readJSON(path, &config); err != nil {
		return config, err
	}
	if config.FormatVersion != 1 || len(config.Sources) == 0 {
		return config, fmt.Errorf("corpus config requires formatVersion 1 and at least one source")
	}
	seen := map[string]bool{}
	for _, spec := range config.Sources {
		if err := validateModuleSpec(spec); err != nil {
			return config, err
		}
		if seen[spec.ID] {
			return config, fmt.Errorf("duplicate corpus id %q", spec.ID)
		}
		seen[spec.ID] = true
	}
	return config, nil
}

func validateModuleSpec(spec ModuleSpec) error {
	if !corpusIDPattern.MatchString(spec.ID) {
		return fmt.Errorf("invalid corpus id %q", spec.ID)
	}
	if spec.Module == "" || strings.HasPrefix(spec.Module, "-") || strings.ContainsAny(spec.Module, "@ \t\r\n\\") ||
		strings.Contains(spec.Module, "..") || !strings.Contains(spec.Module, ".") {
		return fmt.Errorf("invalid module path %q", spec.Module)
	}
	if spec.Version == "" || strings.ContainsAny(spec.Version, "@ \t\r\n/\\") || strings.HasPrefix(spec.Version, "-") {
		return fmt.Errorf("invalid module version query %q", spec.Version)
	}
	return nil
}

func workspaceHash(directory string) (string, error) {
	hash := sha256.New()
	for _, name := range []string{"go.mod", "go.sum"} {
		content, err := os.ReadFile(filepath.Join(directory, name))
		if err != nil && !errors.Is(err, os.ErrNotExist) {
			return "", err
		}
		fmt.Fprintf(hash, "%s\x00%d\x00", name, len(content))
		_, _ = hash.Write(content)
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}

func downloadModule(root, workspace, path, version string) (moduleDownload, error) {
	var result moduleDownload
	output, err := runModuleGo(root, workspace, "mod", "download", "-json", path+"@"+version)
	if err != nil {
		return result, err
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return result, err
	}
	if result.Error != "" {
		return result, errors.New(result.Error)
	}
	if result.Path != path || result.Version == "" || result.Dir == "" || result.Sum == "" || result.GoModSum == "" {
		return result, fmt.Errorf("incomplete verified module download for %s", path)
	}
	return result, nil
}

func decodePackageList(content []byte) ([]goListPackage, error) {
	decoder := json.NewDecoder(bytes.NewReader(content))
	var result []goListPackage
	for {
		var pkg goListPackage
		if err := decoder.Decode(&pkg); err != nil {
			if errors.Is(err, io.EOF) {
				return result, nil
			}
			return nil, err
		}
		result = append(result, pkg)
	}
}

func prepareModule(root string, spec ModuleSpec) (ModuleLock, moduleDownload, []goListPackage, error) {
	var lock ModuleLock
	var downloaded moduleDownload
	workspace := filepath.Join(CorpusPath(root, spec.ID), "workspace")
	if err := os.MkdirAll(workspace, 0o755); err != nil {
		return lock, downloaded, nil, err
	}
	lockPath := filepath.Join(CorpusPath(root, spec.ID), "source.lock.json")
	exists := false
	if err := readJSON(lockPath, &lock); err == nil {
		exists = true
		if lock.FormatVersion != 1 || lock.Toolchain != GoldToolchain || lock.GOOS != runtime.GOOS || lock.GOARCH != runtime.GOARCH || lock.Spec != spec {
			return lock, downloaded, nil, fmt.Errorf("%s: source lock differs from this config/toolchain/build; use a new corpus id", spec.ID)
		}
		actual, err := workspaceHash(workspace)
		if err != nil {
			return lock, downloaded, nil, err
		}
		if actual != lock.Source.WorkspaceHash {
			return lock, downloaded, nil, fmt.Errorf("%s: locked workspace changed", spec.ID)
		}
	} else if !errors.Is(err, os.ErrNotExist) {
		return lock, downloaded, nil, err
	}

	if !exists {
		// This small consumer module lives in the external dataset directory.
		// Sources remain unmodified in the dedicated module cache.
		content := "module example.com/corpus/" + spec.ID + "\n\ngo " + strings.TrimPrefix(GoldToolchain, "go") + "\n"
		if err := os.WriteFile(filepath.Join(workspace, "go.mod"), []byte(content), 0o644); err != nil {
			return lock, downloaded, nil, err
		}
	}
	version := spec.Version
	if exists {
		version = lock.Source.Version
	}
	var err error
	downloaded, err = downloadModule(root, workspace, spec.Module, version)
	if err != nil {
		return lock, downloaded, nil, err
	}
	if exists && (downloaded.Version != lock.Source.Version || downloaded.Sum != lock.Source.Sum || downloaded.GoModSum != lock.Source.GoModSum) {
		return lock, downloaded, nil, fmt.Errorf("%s: downloaded module identity differs from source lock", spec.ID)
	}
	if !exists {
		_, err := runModuleGo(root, workspace, "mod", "edit", "-require="+spec.Module+"@"+downloaded.Version)
		if err != nil {
			return lock, downloaded, nil, err
		}
	}
	mode := "-mod=mod"
	if exists {
		mode = "-mod=readonly"
	}
	// -export builds dependency export data but never runs test binaries,
	// generators, application entry points, or framework initialization code.
	output, err := runModuleGo(root, workspace, "list", mode, "-deps", "-export", "-json", spec.Module+"/...")
	if err != nil {
		return lock, downloaded, nil, err
	}
	if _, err := runModuleGo(root, workspace, "mod", "verify"); err != nil {
		return lock, downloaded, nil, err
	}
	packages, err := decodePackageList(output)
	if err != nil {
		return lock, downloaded, nil, err
	}
	var target *moduleMetadata
	for _, pkg := range packages {
		if pkg.Module != nil && pkg.Module.Path == spec.Module {
			if pkg.Module.Version != downloaded.Version {
				return lock, downloaded, nil, fmt.Errorf("%s: module selection changed", spec.ID)
			}
			target = pkg.Module
		}
	}
	if target == nil {
		return lock, downloaded, nil, fmt.Errorf("%s: no active packages in module", spec.ID)
	}
	hash, err := workspaceHash(workspace)
	if err != nil {
		return lock, downloaded, nil, err
	}
	if exists {
		if hash != lock.Source.WorkspaceHash {
			return lock, downloaded, nil, fmt.Errorf("%s: dependency graph changed during replay", spec.ID)
		}
		return lock, downloaded, packages, nil
	}
	lock = ModuleLock{
		FormatVersion: 1, Toolchain: GoldToolchain, GOOS: runtime.GOOS, GOARCH: runtime.GOARCH, Spec: spec,
		Source: ModuleSource{Labeler: ModuleLabelerVersion, Kind: "module", Module: spec.Module, Version: downloaded.Version, Sum: downloaded.Sum,
			GoModSum: downloaded.GoModSum, GoVersion: target.GoVersion, WorkspaceHash: hash, CGOEnabled: false},
	}
	if err := writeJSON(lockPath, lock); err != nil {
		return lock, downloaded, nil, err
	}
	return lock, downloaded, packages, nil
}
