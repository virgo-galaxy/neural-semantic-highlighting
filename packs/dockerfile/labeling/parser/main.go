// Offline BuildKit AST bridge. Source is parsed, never built or executed.
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/moby/buildkit/frontend/dockerfile/command"
	"github.com/moby/buildkit/frontend/dockerfile/parser"
)

type request struct {
	Source string `json:"source"`
}
type instruction struct {
	Keyword   string           `json:"keyword"`
	StartLine int              `json:"startLine"`
	EndLine   int              `json:"endLine"`
	Original  string           `json:"original"`
	Flags     []string         `json:"flags"`
	JSON      bool             `json:"json"`
	Heredocs  []parser.Heredoc `json:"heredocs"`
}
type response struct {
	Instructions []instruction       `json:"instructions"`
	Escape       string              `json:"escape"`
	Directives   []*parser.Directive `json:"directives"`
	Error        string              `json:"error,omitempty"`
}

func parse(source string) response {
	out := response{Instructions: []instruction{}, Escape: "\\"}
	directives, err := (&parser.DirectiveParser{}).ParseAll([]byte(strings.TrimPrefix(source, "\ufeff")))
	if err != nil {
		out.Error = err.Error()
		return out
	}
	out.Directives = directives
	result, err := parser.Parse(strings.NewReader(source))
	if err != nil {
		if strings.Contains(err.Error(), "file with no instructions") {
			return out
		}
		out.Error = err.Error()
		return out
	}
	out.Escape = string(result.EscapeToken)
	for _, node := range result.AST.Children {
		if _, ok := command.Commands[strings.ToLower(node.Value)]; !ok {
			out.Error = "Unsupported Dockerfile instruction: " + node.Value
			return out
		}
		flags, isJSON := node.Flags, node.Attributes["json"]
		if strings.EqualFold(node.Value, "onbuild") && node.Next != nil && len(node.Next.Children) > 0 {
			child := node.Next.Children[0]
			flags, isJSON = child.Flags, child.Attributes["json"]
		}
		out.Instructions = append(out.Instructions, instruction{node.Value, node.StartLine, node.EndLine, node.Original, flags, isJSON, node.Heredocs})
	}
	return out
}
func main() {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 64*1024), 16*1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		var req request
		var result response
		if err := json.Unmarshal(scanner.Bytes(), &req); err != nil {
			result.Error = err.Error()
		} else {
			result = parse(req.Source)
		}
		raw, err := json.Marshal(result)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Fprintln(writer, string(raw))
		writer.Flush()
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
