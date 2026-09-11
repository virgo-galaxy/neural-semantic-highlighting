package dataset

import (
	"os"
	"path/filepath"
)

func Root() (string, error) {
	if root := os.Getenv("NSH_DATASET_ROOT"); root != "" {
		return filepath.Join(root, "go"), nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	return filepath.Join(home, "Datasets", "neural-semantic-highlighting", "go"), nil
}

func SamplePath(root string) string {
	return filepath.Join(root, "sample.json")
}

func LabeledPath(root string) string {
	return filepath.Join(root, "labeled-sample.jsonl")
}

func StatisticsPath(root string) string {
	return filepath.Join(root, "statistics.json")
}
