package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"

	"github.com/virgo-galaxy/neural-semantic-highlighting/packs/go/lexical"
)

type request struct {
	ID     string `json:"id"`
	Source string `json:"source"`
}

type response struct {
	ID     string         `json:"id"`
	Result lexical.Result `json:"result,omitempty"`
	Error  string         `json:"error,omitempty"`
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	// Real source documents can exceed Scanner's small default token buffer.
	scanner.Buffer(make([]byte, 64*1024), 32*1024*1024)
	encoder := json.NewEncoder(os.Stdout)
	for scanner.Scan() {
		var req request
		if err := json.Unmarshal(scanner.Bytes(), &req); err != nil {
			_ = encoder.Encode(response{Error: fmt.Sprintf("decode request: %v", err)})
			continue
		}
		result, err := lexical.Scan(req.Source)
		if err != nil {
			_ = encoder.Encode(response{ID: req.ID, Error: err.Error()})
			continue
		}
		if err := encoder.Encode(response{ID: req.ID, Result: result}); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
