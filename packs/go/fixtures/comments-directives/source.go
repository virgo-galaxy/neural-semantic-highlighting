//go:build !ignore

// Package comments demonstrates ordinary documentation and directive boundaries.
package comments

//go:generate echo generation-is-not-run-by-labeling

/*
Record keeps a value.

	Multi-line text remains a single comment span.
*/
type Record struct {
	// Name identifies the record.
	Name string
}

// NameOf returns the stored name. See [Record].
func NameOf(record Record) string {
	return record.Name // A trailing line comment.
}
