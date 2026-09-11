package dataset

import (
	"fmt"
	"os"
	"path/filepath"
)

// RunModules builds each requested corpus independently. A module dependency is
// resolved for Gold context, but is not automatically selected as training data.
func RunModules(root, configPath, schemaPath, sourceID string, progress ProgressFunc) ([]Statistics, error) {
	if err := RequireGoldToolchain(); err != nil {
		return nil, err
	}
	config, err := readCorpusConfig(configPath)
	if err != nil {
		return nil, err
	}
	root, err = filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	var selected []ModuleSpec
	for _, source := range config.Sources {
		if sourceID == "" || source.ID == sourceID {
			selected = append(selected, source)
		}
	}
	if len(selected) == 0 {
		return nil, fmt.Errorf("unknown corpus id %q", sourceID)
	}
	var statistics []Statistics
	for _, spec := range selected {
		if progress != nil {
			progress(0, 0, "Preparing "+spec.ID+" ("+spec.Module+")")
		}
		result, err := buildModuleCorpus(root, schemaPath, spec, progress)
		if err != nil {
			return statistics, fmt.Errorf("corpus %s: %w", spec.ID, err)
		}
		statistics = append(statistics, result)
	}
	return statistics, nil
}

func buildModuleCorpus(root, schemaPath string, spec ModuleSpec, progress ProgressFunc) (Statistics, error) {
	if err := validateModuleSpec(spec); err != nil {
		return Statistics{}, err
	}
	corpusRoot := CorpusPath(root, spec.ID)
	if err := os.MkdirAll(corpusRoot, 0o755); err != nil {
		return Statistics{}, err
	}
	busyPath := filepath.Join(corpusRoot, ".dataset.lock")
	busy, err := os.OpenFile(busyPath, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o644)
	if err != nil {
		return Statistics{}, fmt.Errorf("cannot lock %s; another run may be active: %w", corpusRoot, err)
	}
	fmt.Fprintf(busy, "pid=%d\n", os.Getpid())
	_ = busy.Close()
	defer os.Remove(busyPath)
	lock, downloaded, packages, err := prepareModule(root, spec)
	if err != nil {
		return Statistics{}, err
	}
	sample, err := collectModule(lock, downloaded.Dir, packages)
	if err != nil {
		return Statistics{}, err
	}
	stage, err := os.MkdirTemp(corpusRoot, ".build-")
	if err != nil {
		return Statistics{}, err
	}
	defer os.RemoveAll(stage)
	if err := writeJSON(SamplePath(stage), sample); err != nil {
		return Statistics{}, err
	}
	if err := labelModule(stage, downloaded.Dir, sample, packages, progress); err != nil {
		return Statistics{}, err
	}
	statistics, err := Validate(stage, schemaPath)
	if err != nil {
		return Statistics{}, err
	}
	// Publish only after every package and every document has been validated.
	for _, path := range []string{LabeledPath(stage), SamplePath(stage), StatisticsPath(stage)} {
		if err := os.Rename(path, filepath.Join(corpusRoot, filepath.Base(path))); err != nil {
			return Statistics{}, err
		}
	}
	return statistics, nil
}
