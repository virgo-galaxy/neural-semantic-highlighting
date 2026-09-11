package dataset

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
)

type goListPackage struct {
	Dir        string   `json:"Dir"`
	ImportPath string   `json:"ImportPath"`
	GoFiles    []string `json:"GoFiles"`
}

func listPackages(pattern string) ([]goListPackage, error) {
	goCommand := filepath.Join(runtime.GOROOT(), "bin", "go")
	command := exec.Command(goCommand, "list", "-json", pattern)
	command.Env = append(os.Environ(), "GOTOOLCHAIN=local")

	stdout, err := command.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("open go list stdout: %w", err)
	}
	command.Stderr = os.Stderr

	if err := command.Start(); err != nil {
		return nil, fmt.Errorf("start go list: %w", err)
	}

	decoder := json.NewDecoder(stdout)
	packages := make([]goListPackage, 0)
	for {
		var pkg goListPackage
		if err := decoder.Decode(&pkg); err != nil {
			if errors.Is(err, io.EOF) {
				break
			}
			return nil, fmt.Errorf("decode go list output: %w", err)
		}
		packages = append(packages, pkg)
	}

	if err := command.Wait(); err != nil {
		return nil, fmt.Errorf("go list %q: %w", pattern, err)
	}

	return packages, nil
}
