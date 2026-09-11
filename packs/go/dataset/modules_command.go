package dataset

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"time"
)

func moduleEnvironment(root string) []string {
	values := make(map[string]string)
	for _, entry := range os.Environ() {
		key, value, ok := strings.Cut(entry, "=")
		if ok {
			values[key] = value
		}
	}
	// These overrides belong only to child processes. Never persist them with
	// go env -w, edit shell configuration, or modify the repository module.
	for key, value := range map[string]string{
		"GOTOOLCHAIN": "local", "GO111MODULE": "on", "GOWORK": "off",
		"GOFLAGS": "", "GOEXPERIMENT": "", "CGO_ENABLED": "0",
		"GOOS": runtime.GOOS, "GOARCH": runtime.GOARCH,
		"GOMODCACHE": filepath.Join(root, "cache", "modules"),
		"GOCACHE":    filepath.Join(root, "cache", "build"),
	} {
		values[key] = value
	}
	// Respect the user's proxy/checksum configuration. Do not disable sumdb.
	keys := make([]string, 0, len(values))
	for key := range values {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	environment := make([]string, 0, len(keys))
	for _, key := range keys {
		environment = append(environment, key+"="+values[key])
	}
	return environment
}

func runModuleGo(root, directory string, arguments ...string) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Minute)
	defer cancel()
	command := exec.CommandContext(ctx, filepath.Join(runtime.GOROOT(), "bin", "go"), arguments...)
	command.Dir = directory
	command.Env = moduleEnvironment(root)
	var stderr bytes.Buffer
	command.Stderr = &stderr
	output, err := command.Output()
	if err != nil {
		return nil, fmt.Errorf("go %s: %w\n%s", strings.Join(arguments, " "), err, strings.TrimSpace(stderr.String()))
	}
	return output, nil
}
