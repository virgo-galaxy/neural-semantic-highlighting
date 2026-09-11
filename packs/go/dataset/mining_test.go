package dataset

import (
	"reflect"
	"testing"
)

func TestMineSourceFeatures(t *testing.T) {
	source := `package sample

type Mergeable[T Mergeable[T]] interface { Merge(T) T }
type Alias[T any] = []T
type Box[T any] struct { Value T ` + "`json:\"value\"`" + ` }
func (b Box[T]) Map[U any](fn func(T) U) U { return fn(b.Value) }
type Items[T any] []T
func (items Items[T]) Each(yield func(T) bool) { for _, value := range items { if !yield(value) { return } } }
func Read(items Items[int]) int { for value := range items.Each { return value }; return 0 }
`
	features, err := MineSourceFeatures("source.go", source)
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"function-range", "generic-alias", "generic-method", "self-reference", "struct-tags"}
	if !reflect.DeepEqual(features, want) {
		t.Fatalf("features = %v, want %v", features, want)
	}
}

func TestMineSourceFeaturesAvoidsOrdinaryConstructs(t *testing.T) {
	source := `package sample

type Box[T any] struct { Value T }
func (b Box[T]) ValueOr(other T) T { return b.Value }
func Values() []int { return []int{1, 2} }
func Read() int { for _, value := range Values() { return value }; return 0 }
`
	features, err := MineSourceFeatures("source.go", source)
	if err != nil {
		t.Fatal(err)
	}
	if len(features) != 0 {
		t.Fatalf("unexpected features: %v", features)
	}
}
