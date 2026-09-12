package dataset

// focusedV3Families is the clean, integrated curriculum used by the final Go
// training candidate. It is intentionally defined as one coherent capability
// matrix rather than layering historical V2 repair sets. Historical profiles
// remain available only for experiment replay.
var focusedV3Families = []focusedFamilySpec{
	// Go 1.18 generics and type sets.
	{"generic-functions", "1.18", "generic-functions/train/map-reduce", "train", `func Map{{.Name}}[T any, U any](in []T, fn func(T) U) []U { out := make([]U, 0, len(in)); for _, value := range in { out = append(out, fn(value)) }; return out }
func Reduce{{.Name}}[T any](in []T, zero T, fn func(T, T) T) T { acc := zero; for _, value := range in { acc = fn(acc, value) }; return acc }
var mapped{{.Name}} = Map{{.Name}}([]int{1, {{.Number}}}, func(v int) string { return "item" })`},
	{"generic-functions", "1.18", "generic-functions/train/type-set-union", "train", `type Scalar{{.Name}} interface { ~int | ~int32 | ~int64 | ~float64 }
func MaxOf{{.Name}}[T Scalar{{.Name}}](values []T) T { best := values[0]; for _, value := range values[1:] { if value > best { best = value } }; return best }
var max{{.Name}} = MaxOf{{.Name}}([]{{.Type}}{1, {{.Number}}})`},
	{"generic-functions", "1.18", "generic-functions/train/generic-container", "train", `type Table{{.Name}}[K comparable, V any] struct { values map[K]V }
func NewTable{{.Name}}[K comparable, V any]() *Table{{.Name}}[K, V] { return &Table{{.Name}}[K,V]{values: make(map[K]V)} }
func (t *Table{{.Name}}[K,V]) Put(key K, value V) { t.values[key] = value }`},
	{"generic-functions", "1.18", "generic-functions/validation/channel-map", "validation", `func Drain{{.Name}}[T any](in <-chan T) []T { out := []T{}; for value := range in { out = append(out, value) }; return out }
func Send{{.Name}}[T any](out chan<- T, value T) { out <- value }`},
	{"generic-functions", "1.18", "generic-functions/validation/constraint-embedding", "validation", `type Ordered{{.Name}} interface { ~int | ~int64 | ~string }
type Keyed{{.Name}}[T Ordered{{.Name}}] interface { Key() T }
func Keys{{.Name}}[T Ordered{{.Name}}, V Keyed{{.Name}}[T]](items []V) []T { out := make([]T, 0, len(items)); for _, item := range items { out = append(out, item.Key()) }; return out }`},
	{"generic-functions", "1.18", "generic-functions/test/generic-closure", "test", `func Binder{{.Name}}[T any](prefix string) func(T) string { return func(value T) string { return prefix } }
var bind{{.Name}} = Binder{{.Name}}[{{.Type}}]("prefix")`},
	{"generic-functions", "1.18", "generic-functions/test/multi-constraint", "test", `type NumericKey{{.Name}} interface { comparable; ~int | ~int64 }
func Index{{.Name}}[K NumericKey{{.Name}}, V any](pairs map[K]V, key K) (V, bool) { value, ok := pairs[key]; return value, ok }`},

	// Go 1.20 comparable and slice-to-array behavior.
	{"comparable-array", "1.20", "comparable-array/train/interface-comparable", "train", `func Same{{.Name}}[T comparable](left, right T) bool { return left == right }
func AnySame{{.Name}}(left, right any) bool { return Same{{.Name}}[any](left, right) }`},
	{"comparable-array", "1.20", "comparable-array/train/slice-array-pointer", "train", `func Prefix{{.Name}}(values []{{.Type}}) *[2]{{.Type}} { return (*[2]{{.Type}})(values) }
var prefix{{.Name}} = Prefix{{.Name}}([]{{.Type}}{1, {{.Number}}, 3})`},
	{"comparable-array", "1.20", "comparable-array/train/comparable-map-key", "train", `func Count{{.Name}}[K comparable](values []K) map[K]int { out := map[K]int{}; for _, value := range values { out[value]++ }; return out }
var counts{{.Name}} = Count{{.Name}}([]any{"x", {{.Number}}, true})`},
	{"comparable-array", "1.20", "comparable-array/validation/direct-array-conversion", "validation", `func Pair{{.Name}}(values []{{.Type}}) [2]{{.Type}} { return [2]{{.Type}}(values) }
func PairHead{{.Name}}(values []{{.Type}}) {{.Type}} { pair := Pair{{.Name}}(values); return pair[0] }`},
	{"comparable-array", "1.20", "comparable-array/validation/comparable-wrapper", "validation", `type Wrapper{{.Name}}[T comparable] struct { Value T }
func EqualWrapper{{.Name}}[T comparable](a, b Wrapper{{.Name}}[T]) bool { return a == b }`},
	{"comparable-array", "1.20", "comparable-array/test/nested-array", "test", `func Window{{.Name}}(values []{{.Type}}) [2][2]{{.Type}} { flat := [4]{{.Type}}(values); return [2][2]{{.Type}}{ {flat[0], flat[1]}, {flat[2], flat[3]} } }`},
	{"comparable-array", "1.20", "comparable-array/test/interface-map", "test", `func Present{{.Name}}[K comparable](items map[K]struct{}, key K) bool { _, ok := items[key]; return ok }
var present{{.Name}} = Present{{.Name}}(map[any]struct{}{"x": {}}, any("x"))`},

	// Go 1.21 predeclared min/max/clear and inference improvements.
	{"builtins", "1.21", "builtins/train/min-max", "train", `func Clamp{{.Name}}(value, low, high {{.Type}}) {{.Type}} { return min(max(value, low), high) }
var clamped{{.Name}} = Clamp{{.Name}}({{.Number}}, 0, 100)`},
	{"builtins", "1.21", "builtins/train/clear-map", "train", `func ResetMap{{.Name}}(values map[string]{{.Type}}) int { before := len(values); clear(values); return before }`},
	{"builtins", "1.21", "builtins/train/clear-slice", "train", `func ZeroSlice{{.Name}}(values []{{.Type}}) []{{.Type}} { clear(values); return values }`},
	{"builtins", "1.21", "builtins/validation/nested-minmax", "validation", `func Spread{{.Name}}(a, b, c {{.Type}}) {{.Type}} { return max(a,b,c) - min(a,b,c) }`},
	{"builtins", "1.21", "builtins/validation/generic-bounds", "validation", `type OrderedBuiltin{{.Name}} interface { ~int | ~int64 | ~float64 }
func Bounds{{.Name}}[T OrderedBuiltin{{.Name}}](values []T) (T,T) { low, high := values[0], values[0]; for _, value := range values[1:] { low, high = min(low,value), max(high,value) }; return low, high }`},
	{"builtins", "1.21", "builtins/test/clear-nested", "test", `func Empty{{.Name}}(values map[string][]{{.Type}}) { for key := range values { clear(values[key]) }; clear(values) }`},
	{"builtins", "1.21", "builtins/test/minmax-expression", "test", `func Center{{.Name}}(left, value, right {{.Type}}) {{.Type}} { return min(right, max(left, value)) }`},

	// Go 1.22 integer range.
	{"integer-range", "1.22", "integer-range/train/index-append", "train", `func Indices{{.Name}}(count int) []int { out := make([]int,0,count); for i := range count { out = append(out,i) }; return out }`},
	{"integer-range", "1.22", "integer-range/train/repeat-side-effect", "train", `func Repeat{{.Name}}(count int, fn func()) { for range count { fn() } }`},
	{"integer-range", "1.22", "integer-range/train/nested-grid", "train", `func Grid{{.Name}}(width, height int) [][2]int { out := [][2]int{}; for y := range height { for x := range width { out = append(out,[2]int{x,y}) } }; return out }`},
	{"integer-range", "1.22", "integer-range/validation/countdown-build", "validation", `func Build{{.Name}}(count int) map[int]bool { out := map[int]bool{}; for i := range count { out[count-i-1] = true }; return out }`},
	{"integer-range", "1.22", "integer-range/validation/range-expression", "validation", `func Touch{{.Name}}(base int) int { total := 0; for i := range base + {{.Number}} { total += i }; return total }`},
	{"integer-range", "1.22", "integer-range/test/labeled-loop", "test", `func FirstEven{{.Name}}(limit int) int { result := -1; outer: for i := range limit { if i%2 == 0 { result = i; break outer } }; return result }`},
	{"integer-range", "1.22", "integer-range/test/generic-count", "test", `func Fill{{.Name}}[T any](count int, value T) []T { out := make([]T,count); for i := range count { out[i] = value }; return out }`},

	// Go 1.23 range-over-function. Bare method values and visually similar
	// function-valued fields are deliberately interleaved as one capability.
	{"function-range", "1.23", "function-range/train/free-sequence", "train", `func Seq{{.Name}}(yield func(int) bool) { for i := 0; i < {{.Number}}; i++ { if !yield(i) { return } } }
func SumSeq{{.Name}}() int { total := 0; for value := range Seq{{.Name}} { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/direct-pointer-method", "train", `type Cursor{{.Name}} struct { End int }
func (c *Cursor{{.Name}}) Walk(yield func(int) bool) { for i := 0; i < c.End; i++ { if !yield(i) { return } } }
func SumCursor{{.Name}}(c *Cursor{{.Name}}) int { total := 0; for value := range c.Walk { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/bound-method-local", "train", `type Reader{{.Name}} struct { Limit int }
func (r Reader{{.Name}}) Emit(yield func(int) bool) { for i := range r.Limit { if !yield(i) { return } } }
func ReadAll{{.Name}}(r Reader{{.Name}}) int { next := r.Emit; total := 0; for value := range next { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/conditional-method-selection", "train", `type SwitchIter{{.Name}} struct { Limit int }
func (s *SwitchIter{{.Name}}) Forward(yield func(int) bool) { for i := range s.Limit { if !yield(i) { return } } }
func (s *SwitchIter{{.Name}}) Reverse(yield func(int) bool) { for i := range s.Limit { if !yield(s.Limit-i-1) { return } } }
func SelectIter{{.Name}}(s *SwitchIter{{.Name}}, reverse bool) int { iter := s.Forward; if reverse { iter = s.Reverse }; total := 0; for value := range iter { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/indexed-generic-receiver", "train", `type Bucket{{.Name}}[T any] struct { Values []T }
func (b *Bucket{{.Name}}[T]) Each(yield func(T) bool) { for _, value := range b.Values { if !yield(value) { return } } }
func FirstBucket{{.Name}}[T any](items []*Bucket{{.Name}}[T], index int) T { var zero T; if index < len(items) { for value := range items[index].Each { return value } }; return zero }`},
	{"function-range", "1.23", "function-range/train/interface-method-value", "train", `type Iterable{{.Name}} interface { Iterate(func(int) bool) }
func FirstIter{{.Name}}(src Iterable{{.Name}}) int { for value := range src.Iterate { return value }; return -1 }`},
	{"function-range", "1.23", "function-range/train/promoted-method-value", "train", `type IterBase{{.Name}} struct { Limit int }
func (b *IterBase{{.Name}}) Entries(yield func(int) bool) { for i := range b.Limit { if !yield(i) { return } } }
type IterWrap{{.Name}} struct { *IterBase{{.Name}} }
func SumWrap{{.Name}}(w *IterWrap{{.Name}}) int { total := 0; for value := range w.Entries { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/function-field-negative", "train", `type CallbackHolder{{.Name}} struct { Iterate func(func(int) bool) }
func SumCallback{{.Name}}(src CallbackHolder{{.Name}}) int { total := 0; for value := range src.Iterate { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/function-return-negative", "train", `func IteratorFactory{{.Name}}(limit int) func(func(int) bool) { return func(yield func(int) bool) { for i := range limit { if !yield(i) { return } } } }
func FactorySum{{.Name}}() int { iter := IteratorFactory{{.Name}}({{.Number}}); total := 0; for value := range iter { total += value }; return total }`},
	{"function-range", "1.23", "function-range/validation/branch-bound-method", "validation", `type Brancher{{.Name}} struct { N int }
func (b Brancher{{.Name}}) Even(yield func(int) bool) { for i := range b.N { if i%2 == 0 && !yield(i) { return } } }
func (b Brancher{{.Name}}) Odd(yield func(int) bool) { for i := range b.N { if i%2 != 0 && !yield(i) { return } } }
func BranchSum{{.Name}}(b Brancher{{.Name}}, even bool) int { var iter func(func(int) bool); if even { iter = b.Even } else { iter = b.Odd }; total := 0; for value := range iter { total += value }; return total }`},
	{"function-range", "1.23", "function-range/validation/map-selected-method", "validation", `type Stream{{.Name}}[T any] struct { Items []T }
func (s *Stream{{.Name}}[T]) Values(yield func(T) bool) { for _, item := range s.Items { if !yield(item) { return } } }
func PickStream{{.Name}}[T any](streams map[string]*Stream{{.Name}}[T], key string) T { var zero T; stream, ok := streams[key]; if !ok { return zero }; for value := range stream.Values { return value }; return zero }`},
	{"function-range", "1.23", "function-range/test/nested-selector-method", "test", `type Source{{.Name}} struct { Limit int }
func (s *Source{{.Name}}) Next(yield func(int) bool) { for i := range s.Limit { if !yield(i) { return } } }
type Holder{{.Name}} struct { Source *Source{{.Name}} }
func HolderSum{{.Name}}(h Holder{{.Name}}) int { total := 0; for value := range h.Source.Next { total += value }; return total }`},
	{"function-range", "1.23", "function-range/test/method-value-argument", "test", `type Scanner{{.Name}} struct { Limit int }
func (s Scanner{{.Name}}) Scan(yield func(int) bool) { for i := range s.Limit { if !yield(i) { return } } }
func ConsumeIter{{.Name}}(iter func(func(int) bool)) int { count := 0; for range iter { count++ }; return count }
func ScanCount{{.Name}}(s Scanner{{.Name}}) int { return ConsumeIter{{.Name}}(s.Scan) }`},

	// Go 1.24 generic aliases.
	{"generic-alias", "1.24", "generic-alias/train/map", "train", `type Lookup{{.Name}}[K comparable, V any] = map[K]V
func Get{{.Name}}[K comparable, V any](m Lookup{{.Name}}[K,V], key K) (V,bool) { value, ok := m[key]; return value, ok }`},
	{"generic-alias", "1.24", "generic-alias/train/slice", "train", `type List{{.Name}}[T any] = []T
func Head{{.Name}}[T any](values List{{.Name}}[T]) T { return values[0] }`},
	{"generic-alias", "1.24", "generic-alias/train/function", "train", `type Predicate{{.Name}}[T any] = func(T) bool
func Filter{{.Name}}[T any](values []T, keep Predicate{{.Name}}[T]) []T { out := []T{}; for _, value := range values { if keep(value) { out = append(out,value) } }; return out }`},
	{"generic-alias", "1.24", "generic-alias/train/pointer", "train", `type Ref{{.Name}}[T any] = *T
func Deref{{.Name}}[T any](value Ref{{.Name}}[T]) T { return *value }`},
	{"generic-alias", "1.24", "generic-alias/train/defined-type-negative", "train", `type Defined{{.Name}}[T any] []T
func DefinedLen{{.Name}}[T any](values Defined{{.Name}}[T]) int { return len(values) }`},
	{"generic-alias", "1.24", "generic-alias/validation/channel", "validation", `type Receive{{.Name}}[T any] = <-chan T
func One{{.Name}}[T any](ch Receive{{.Name}}[T]) T { return <-ch }`},
	{"generic-alias", "1.24", "generic-alias/validation/nested-map", "validation", `type Index{{.Name}}[K comparable, V any] = map[K][]V
func AppendIndex{{.Name}}[K comparable, V any](index Index{{.Name}}[K,V], key K, value V) { index[key] = append(index[key], value) }`},
	{"generic-alias", "1.24", "generic-alias/test/resolver", "test", `type Resolver{{.Name}}[K comparable, V any] = func(K) (V,bool)
func Resolve{{.Name}}[K comparable,V any](fn Resolver{{.Name}}[K,V], key K, fallback V) V { value, ok := fn(key); if !ok { return fallback }; return value }`},
	{"generic-alias", "1.24", "generic-alias/test/matrix", "test", `type Matrix{{.Name}}[T any] = [][]T
func Corner{{.Name}}[T any](m Matrix{{.Name}}[T]) T { return m[len(m)-1][len(m[len(m)-1])-1] }`},

	// Go 1.26 new(expression) and generic self-reference.
	{"new-expression", "1.26", "new-expression/train/converted-value", "train", `func Pointer{{.Name}}() *{{.Type}} { return new({{.Type}}({{.Number}})) }`},
	{"new-expression", "1.26", "new-expression/train/comparison", "train", `func Enabled{{.Name}}(count int) *bool { return new(count > {{.Number}}) }`},
	{"new-expression", "1.26", "new-expression/train/string-expression", "train", `func Label{{.Name}}(base string) *string { return new(base + "-item") }`},
	{"new-expression", "1.26", "new-expression/validation/arithmetic", "validation", `func OffsetPtr{{.Name}}(base int) *int { return new(base*2 + {{.Number}}) }`},
	{"new-expression", "1.26", "new-expression/validation/composite-call", "validation", `func LengthPtr{{.Name}}(values []string) *int { return new(len(values)) }`},
	{"new-expression", "1.26", "new-expression/test/index-expression", "test", `func FirstPtr{{.Name}}(values []{{.Type}}) *{{.Type}} { return new(values[0]) }`},
	{"new-expression", "1.26", "new-expression/test/boolean-chain", "test", `func FlagPtr{{.Name}}(a,b bool) *bool { return new(a && !b) }`},

	{"self-reference", "1.26", "self-reference/train/value-method", "train", `type Mergeable{{.Name}}[T Mergeable{{.Name}}[T]] interface { Merge(T) T }
func Fold{{.Name}}[T Mergeable{{.Name}}[T]](head T, rest []T) T { for _, value := range rest { head = head.Merge(value) }; return head }`},
	{"self-reference", "1.26", "self-reference/train/multi-method", "train", `type Node{{.Name}}[T Node{{.Name}}[T]] interface { Clone() T; Equal(T) bool }
func SameNode{{.Name}}[T Node{{.Name}}[T]](left,right T) bool { return left.Clone().Equal(right) }`},
	{"self-reference", "1.26", "self-reference/train/collection", "train", `type Child{{.Name}}[T Child{{.Name}}[T]] interface { Children() []T }
func CountTree{{.Name}}[T Child{{.Name}}[T]](root T) int { total := 1; for _, child := range root.Children() { total += CountTree{{.Name}}(child) }; return total }`},
	{"self-reference", "1.26", "self-reference/train/non-self-negative", "train", `type PlainConstraint{{.Name}}[T any] interface { Value() T }
func PlainValue{{.Name}}[T any, V PlainConstraint{{.Name}}[T]](value V) T { return value.Value() }`},
	{"self-reference", "1.26", "self-reference/validation/ordering", "validation", `type OrderedNode{{.Name}}[T OrderedNode{{.Name}}[T]] interface { Before(T) bool }
func Earlier{{.Name}}[T OrderedNode{{.Name}}[T]](a,b T) T { if a.Before(b) { return a }; return b }`},
	{"self-reference", "1.26", "self-reference/validation/walk", "validation", `type Walker{{.Name}}[T Walker{{.Name}}[T]] interface { Next() (T,bool) }
func Steps{{.Name}}[T Walker{{.Name}}[T]](value T) int { count := 0; for { next, ok := value.Next(); if !ok { return count }; value = next; count++ } }`},
	{"self-reference", "1.26", "self-reference/test/rewrite", "test", `type Rewrite{{.Name}}[T Rewrite{{.Name}}[T]] interface { Rewrite() T; Stable() bool }
func Normalize{{.Name}}[T Rewrite{{.Name}}[T]](value T) T { for !value.Stable() { value = value.Rewrite() }; return value }`},
	{"self-reference", "1.26", "self-reference/test/frontier", "test", `type Neighbor{{.Name}}[T Neighbor{{.Name}}[T]] interface { Neighbors() []T }
func Frontier{{.Name}}[T Neighbor{{.Name}}[T]](root T) []T { out := []T{root}; for i := 0; i < len(out); i++ { out = append(out, out[i].Neighbors()...) }; return out }`},

	// Go 1.27 generic methods.
	{"generic-method", "1.27", "generic-method/train/value-receiver", "train", `type Box{{.Name}}[T any] struct { Value T }
func (b Box{{.Name}}[T]) Map[U any](fn func(T) U) U { return fn(b.Value) }
var mappedBox{{.Name}} = (Box{{.Name}}[int]{Value: {{.Number}}}).Map[string](func(v int) string { return "x" })`},
	{"generic-method", "1.27", "generic-method/train/pointer-receiver", "train", `type Decoder{{.Name}} struct { Offset int }
func (d *Decoder{{.Name}}) Read[T any](fn func(int) T) T { value := fn(d.Offset); d.Offset++; return value }
var decoder{{.Name}} = &Decoder{{.Name}}{}`},
	{"generic-method", "1.27", "generic-method/train/two-method-params", "train", `type Pairer{{.Name}}[K comparable] struct { Key K }
func (p Pairer{{.Name}}[K]) Pair[V any, U any](value V, fn func(V) U) map[K]U { return map[K]U{p.Key: fn(value)} }`},
	{"generic-method", "1.27", "generic-method/train/method-value", "train", `type Converter{{.Name}} struct{}
func (Converter{{.Name}}) Convert[T any](value T) T { return value }
var convert{{.Name}} = (Converter{{.Name}}{}).Convert[int]
var converted{{.Name}} = convert{{.Name}}({{.Number}})`},
	{"generic-method", "1.27", "generic-method/train/plain-method-negative", "train", `type PlainMethod{{.Name}}[T any] struct { Value T }
func (p PlainMethod{{.Name}}[T]) Get() T { return p.Value }`},
	{"generic-method", "1.27", "generic-method/validation/map-result", "validation", `type Keyer{{.Name}}[K comparable] struct { Key K }
func (k Keyer{{.Name}}[K]) Bind[V any](value V) map[K]V { return map[K]V{k.Key:value} }
var bound{{.Name}} = (Keyer{{.Name}}[string]{Key:"x"}).Bind[int]({{.Number}})`},
	{"generic-method", "1.27", "generic-method/validation/pointer-transform", "validation", `type Vault{{.Name}}[T any] struct { Item T }
func (v *Vault{{.Name}}[T]) Transform[U any](fn func(T) U) U { return fn(v.Item) }
var vault{{.Name}} = &Vault{{.Name}}[int]{Item: {{.Number}}}`},
	{"generic-method", "1.27", "generic-method/test/chained", "test", `type Stage{{.Name}}[T any] struct { Value T }
func (s Stage{{.Name}}[T]) Into[U any](fn func(T) U) Stage{{.Name}}[U] { return Stage{{.Name}}[U]{Value:fn(s.Value)} }
var staged{{.Name}} = (Stage{{.Name}}[int]{Value:1}).Into[string](func(int) string { return "x" }).Into[int](func(string) int { return {{.Number}} })`},
	{"generic-method", "1.27", "generic-method/test/constrained-param", "test", `type NumericMethod{{.Name}} interface { ~int | ~int32 | ~int64 | ~float64 }
type Scale{{.Name}} struct{}
func (Scale{{.Name}}) Twice[T NumericMethod{{.Name}}](value T) T { return value + value }
var twice{{.Name}} = (Scale{{.Name}}{}).Twice[{{.Type}}]({{.Number}})`},

	// Go 1.27 promoted fields in struct literals.
	{"promoted-field-literal", "1.27", "promoted-field-literal/train/one-level", "train", `type Identity{{.Name}} struct { Code int }
type Record{{.Name}} struct { Identity{{.Name}}; Name string }
var record{{.Name}} = Record{{.Name}}{Code: {{.Number}}, Name:"x"}`},
	{"promoted-field-literal", "1.27", "promoted-field-literal/train/two-level", "train", `type Settings{{.Name}} struct { Enabled bool }
type Base{{.Name}} struct { Settings{{.Name}} }
type Worker{{.Name}} struct { Base{{.Name}}; Count int }
var worker{{.Name}} = Worker{{.Name}}{Enabled:true, Count:{{.Number}}}`},
	// Go 1.27 promoted-field keys do not perform implicit pointer indirection.
	// Keep pointer embedding as an explicit control case instead of generating
	// an invalid flattened literal such as Item{ID: 1}.
	{"promoted-field-literal", "1.27", "promoted-field-literal/train/pointer-embed-explicit", "train", `type Meta{{.Name}} struct { ID int }
type Item{{.Name}} struct { *Meta{{.Name}}; Label string }
var item{{.Name}} = Item{{.Name}}{Meta{{.Name}}:&Meta{{.Name}}{ID:{{.Number}}}, Label:"x"}`},
	{"promoted-field-literal", "1.27", "promoted-field-literal/validation/mixed-fields", "validation", `type Position{{.Name}} struct { X,Y {{.Type}} }
type Point{{.Name}} struct { Position{{.Name}}; Name string; Active bool }
func Move{{.Name}}(p Point{{.Name}}) Point{{.Name}} { return Point{{.Name}}{X:p.X+1,Y:p.Y,Name:p.Name,Active:true} }`},
	{"promoted-field-literal", "1.27", "promoted-field-literal/validation/nested-embed", "validation", `type Audit{{.Name}} struct { Revision int }
type Core{{.Name}} struct { Audit{{.Name}} }
type Entity{{.Name}} struct { Core{{.Name}}; Value string }
var entity{{.Name}} = Entity{{.Name}}{Revision:{{.Number}},Value:"ok"}`},
	{"promoted-field-literal", "1.27", "promoted-field-literal/test/generic-embed", "test", `type Payload{{.Name}}[T any] struct { Value T }
type Envelope{{.Name}}[T any] struct { Payload{{.Name}}[T]; Tag string }
var envelope{{.Name}} = Envelope{{.Name}}[int]{Value:{{.Number}},Tag:"x"}`},
	{"promoted-field-literal", "1.27", "promoted-field-literal/test/multi-embed", "test", `type Left{{.Name}} struct { A int }
type Right{{.Name}} struct { B int }
type Both{{.Name}} struct { Left{{.Name}}; Right{{.Name}}; C int }
var both{{.Name}} = Both{{.Name}}{A:1,B:2,C:{{.Number}}}`},

	// Go 1.27 broader generic function inference.
	{"function-inference", "1.27", "function-inference/train/map-value", "train", `func Identity{{.Name}}[T any](value T) T { return value }
var transforms{{.Name}} = map[string]func({{.Type}}){{.Type}}{"id":Identity{{.Name}}}`},
	{"function-inference", "1.27", "function-inference/train/struct-field", "train", `func Twice{{.Name}}[T ~int | ~int32 | ~int64 | ~float64](value T) T { return value+value }
type Pipeline{{.Name}} struct { Apply func({{.Type}}){{.Type}} }
var pipeline{{.Name}} = Pipeline{{.Name}}{Apply:Twice{{.Name}}}`},
	{"function-inference", "1.27", "function-inference/train/slice-function", "train", `func Zero{{.Name}}[T any](value T) T { var zero T; return zero }
var steps{{.Name}} = []func(string)string{Zero{{.Name}}}`},
	{"function-inference", "1.27", "function-inference/validation/callback-argument", "validation", `func Keep{{.Name}}[T comparable](value T) bool { var zero T; return value != zero }
func ApplyPred{{.Name}}(values []int, pred func(int)bool) int { count:=0; for _,v:=range values { if pred(v) { count++ } }; return count }
var kept{{.Name}} = ApplyPred{{.Name}}([]int{1,{{.Number}}},Keep{{.Name}})`},
	{"function-inference", "1.27", "function-inference/validation/return-function", "validation", `func Echo{{.Name}}[T any](value T) T { return value }
func StringEcho{{.Name}}() func(string)string { return Echo{{.Name}} }`},
	{"function-inference", "1.27", "function-inference/test/interface-field", "test", `func First{{.Name}}[T any](value T) T { return value }
type Runner{{.Name}} struct { Run func(int)int }
var runner{{.Name}} = Runner{{.Name}}{Run:First{{.Name}}}`},
	{"function-inference", "1.27", "function-inference/test/nested-call", "test", `func Wrap{{.Name}}[T any](value T) []T { return []T{value} }
func UseWrap{{.Name}}(fn func(string)[]string) []string { return fn("x") }
var wrapped{{.Name}} = UseWrap{{.Name}}(Wrap{{.Name}})`},

	// Struct tags are one lexical span regardless of the internal mini-language.
	// Training mixes single/multi-key tags, nested placement, protobuf-like
	// values, and raw-string hard negatives so the model learns context as well
	// as delimiters.
	{"struct-tags", "1.18", "struct-tags/train/json-validation", "train", `type Profile{{.Name}} struct { ID int ` + "`json:\"id\" validate:\"required,gte=1\"`" + `; Name string ` + "`json:\"name,omitempty\" validate:\"omitempty,min=2\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/train/database-codecs", "train", `type Stored{{.Name}} struct { Key string ` + "`json:\"key\" db:\"record_key\" gorm:\"column:record_key;primaryKey\"`" + `; Data []byte ` + "`json:\"data,omitempty\" db:\"payload\" custom:\"codec:binary;version=2\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/train/nested-multikey", "train", `type Envelope{{.Name}} struct { Header struct { Trace string ` + "`json:\"trace\" xml:\"trace,attr\" validate:\"omitempty,uuid\"`" + `; Flags []string ` + "`json:\"flags,omitempty\" xml:\"flag\"`" + ` } ` + "`json:\"header\" yaml:\"header\"`" + `; Payload []byte ` + "`json:\"payload,omitempty\" yaml:\"payload,omitempty\" custom:\"codec:base64;limit=8192\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/train/protobuf-fields", "train", `type Wire{{.Name}} struct { ID int64 ` + "`protobuf:\"varint,7,opt,name=id,proto3\" json:\"id,omitempty\"`" + `; Payload []byte ` + "`protobuf:\"bytes,11,opt,name=payload,proto3\" json:\"payload,omitempty\"`" + `; Values []int32 ` + "`protobuf:\"varint,19,rep,packed,name=values,proto3\" json:\"values,omitempty\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/train/protobuf-map", "train", `type MapWire{{.Name}} struct { Labels map[string]string ` + "`protobuf:\"bytes,9,rep,name=labels,proto3\" json:\"labels,omitempty\" protobuf_key:\"bytes,1,opt,name=key,proto3\" protobuf_val:\"bytes,2,opt,name=value,proto3\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/train/many-adjacent-keys", "train", `type Config{{.Name}} struct { Endpoint string ` + "`json:\"endpoint\" yaml:\"endpoint\" toml:\"endpoint\" mapstructure:\"endpoint\" validate:\"required,url\" custom:\"source:remote;cache=1\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/train/raw-taglike-negative", "train", "func TagText{{.Name}}() string { return `json:\"name,omitempty\" xml:\"name,attr\" validate:\"required\"` }"},
	{"struct-tags", "1.18", "struct-tags/train/quoted-tag-negative", "train", `func QuotedTagText{{.Name}}() string { return "json:\"name,omitempty\" xml:\"name,attr\"" }`},
	{"struct-tags", "1.18", "struct-tags/validation/nested-codec-stack", "validation", `type Message{{.Name}} struct { Meta struct { ID string ` + "`json:\"id\" yaml:\"id\" validate:\"required,uuid4\"`" + ` } ` + "`json:\"meta,omitempty\" xml:\"meta\"`" + `; Body []byte ` + "`json:\"body,omitempty\" custom:\"compression:zstd;level=3\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/validation/mixed-storage-wire", "validation", `type Persisted{{.Name}} struct { Count int32 ` + "`protobuf:\"zigzag32,5,opt,name=count,proto3\" json:\"count,omitempty\" db:\"count\"`" + `; Ratio float64 ` + "`protobuf:\"fixed64,12,opt,name=ratio,proto3\" json:\"ratio,omitempty\" db:\"ratio\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/test/anonymous-transport", "test", `type Transport{{.Name}} struct { Inner struct { Code int ` + "`json:\"code\" xml:\"code,attr\"`" + `; Note string ` + "`json:\"note,omitempty\" yaml:\"note,omitempty\" validate:\"omitempty,max=128\"`" + ` } ` + "`json:\"inner\" custom:\"transport:v3;required\"`" + ` }`},
	{"struct-tags", "1.18", "struct-tags/test/custom-stack", "test", `type Event{{.Name}} struct { Kind string ` + "`json:\"kind\" custom:\"kind:v3;required\" schema:\"enum=created|updated|deleted\"`" + `; Meta map[string]string ` + "`json:\"meta,omitempty\" custom:\"codec:map;escape=comma,colon\"`" + ` }`},

	// String robustness is a first-class lexical capability. These families
	// cover quotes and format verbs inside interpreted strings, rune literals,
	// raw strings, multiline help text, markdown-like content, and spans longer
	// than the 512-byte model context. The target remains one exact string span.
	{"strings", "1.18", "strings/train/quoted-format", "train", `func ErrorText{{.Name}}() string { return "route '%s' contains wildcard '*' and parameter '{id}' near path '/api/%s'" }`},
	{"strings", "1.18", "strings/train/escaped-content", "train", `func Escaped{{.Name}}() string { return "line one\\nline two\\t\\\"quoted\\\" \\u263a %03d" }`},
	{"strings", "1.18", "strings/train/rune-punctuation", "train", `func Runes{{.Name}}() []rune { return []rune{'[',']','{','}','*','%',':','\n'} }`},
	{"strings", "1.18", "strings/train/raw-singleline", "train", "func RawOne{{.Name}}() string { return `GET /users/{id}?sort=-created_at | status=%d | note='quoted'` }"},
	{"strings", "1.18", "strings/train/raw-multiline-help", "train", "func Help{{.Name}}() string { return `Usage: sample [flags]\n\nCommands:\n  serve      start the service\n  inspect    print values matching '{pattern}'\n\nFlags:\n  --addr string      address such as 127.0.0.1:8080\n  --format string    output format: '%s' or json\n  --retry int        retry count (default 3)\n\nExamples:\n  sample serve --addr=:8080\n  sample inspect --format='table'\n` }"},
	{"strings", "1.18", "strings/train/raw-markdown-table", "train", "func Docs{{.Name}}() string { return `# Configuration\n\n| Key | Type | Example |\n| --- | --- | --- |\n| endpoint | string | https://example.test/api |\n| selector | string | kind='worker',state!=stopped |\n| template | string | /v1/{tenant}/{id} |\n\nUse **quotes**, backticks in prose, commas, colons, braces, and %s literally.\n` }"},
	{"strings", "1.18", "strings/train/very-long-raw", "train", "func LongHelp{{.Name}}() string { return `SECTION A\nThis command accepts a configuration file, environment overrides, selectors such as service='api',state!=disabled, and templates like /v1/{tenant}/{resource}. Values may contain commas, colons, percent verbs such as %s and %03d, quoted words such as 'ready', and wildcard characters such as * or ?.\n\nSECTION B\nWhen diagnostics are enabled the program prints a table with columns NAME | TYPE | VALUE | SOURCE. The VALUE column may contain JSON fragments like {\"enabled\":true}, URL examples like https://example.test/a?b=c&d=e, or shell-like text such as --label='team:core'. None of those internal punctuation marks ends the Go raw string.\n\nSECTION C\nExamples:\n  sample run --selector=kind='worker' --format='%s'\n  sample inspect --path=/v1/{tenant}/{id} --output=table\n  sample config --set=retry:3,timeout:5s,enabled:true\n\nThe complete help block intentionally exceeds one model context so fixed and adaptive inference must preserve a single lexical span across window boundaries.` }"},
	{"strings", "1.18", "strings/train/comment-negative", "train", `// This comment contains "quoted text", '%s', braces {id}, and a raw-looking marker.
func CommentNegative{{.Name}}() int { return {{.Number}} }`},
	{"strings", "1.18", "strings/validation/interpreted-diagnostics", "validation", `func Diagnostic{{.Name}}(ok bool) string { if ok { return "cannot mount path '%s': wildcard '*' must appear after '/{name}', got value=%q" }; return "" }`},
	{"strings", "1.18", "strings/validation/raw-cli-manual", "validation", "func Manual{{.Name}}(prefix string) string { text := `COMMAND\n  tool deploy [flags]\n\nDESCRIPTION\n  Deploy resources selected by app='web',tier!=cache. Templates may use /{namespace}/{name}.\n\nOPTIONS\n  --set string       comma-separated key:value pairs\n  --message string   text containing quotes such as 'ready'\n  --printf string    formatting pattern such as %q or %03d\n\nThe parser must keep this entire raw literal as one string span.`; return prefix + text }"},
	{"strings", "1.18", "strings/validation/rune-and-escape", "validation", `func Symbols{{.Name}}() (rune,string) { return '{', "value=\\\"%s\\\"; path=/v2/{id}; set=[a,b,c]" }`},
	{"strings", "1.18", "strings/test/raw-long-table", "test", "func LongTable{{.Name}}(enabled bool) string { if !enabled { return \"\" }; text := `NAME            KIND            VALUE\nendpoint        url             https://example.test/v2/{id}\nselector        expression      state='ready',attempts>=3\nformat          template        [%s] {name}: {value}\ndescription     text            This row contains punctuation | commas, colons: braces {}, wildcard *, question ?, and quoted 'words'.\nfooter          text            The raw literal continues across many tokens and must remain one semantic span even when a model window boundary appears in the middle of this documentation block.`; return text }"},
	{"strings", "1.18", "strings/test/embedded-quotes", "test", `func Message{{.Name}}(prefix string) string { return prefix + ": expected one of ['start','stop','status']; received %q at key {command}" }`},
}
