package dataset

// Each row contains three structurally different families: training, validation,
// and test. Variants of a family never cross these boundaries. These small held-out
// samples are pipeline diagnostics, not the final independent model challenges.
type focusedFeature struct {
	ID    string
	Since string
	Forms [3]string
}

var focusedFeatures = []focusedFeature{
	{"generic-functions", "1.18", [3]string{
		`func Transform{{.Name}}[T any, R any](items []T, convert func(T) R) []R {
 out := make([]R, 0, len(items))
 for _, item := range items { out = append(out, convert(item)) }
 return out
}
var result = Transform{{.Name}}([]{{.Type}}{1, {{.Number}}}, func(v {{.Type}}) string { return "value" })`,
		`type Store{{.Name}}[K comparable, V any] struct { values map[K]V }
func (s *Store{{.Name}}[K,V]) Lookup(key K) (V, bool) { value, found := s.values[key]; return value, found }
var instance = Store{{.Name}}[string, {{.Type}}]{values: map[string]{{.Type}}{"sample": {{.Number}}}}`,
		`type Numeric{{.Name}} interface { ~int | ~int32 | ~int64 | ~float64 }
func Sum{{.Name}}[T Numeric{{.Name}}](values ...T) T { var total T; for _, value := range values { total += value }; return total }
var total = Sum{{.Name}}({{.Type}}({{.Number}}), {{.Type}}(2))`,
	}},
	{"comparable-array", "1.20", [3]string{
		`func Equal{{.Name}}[T comparable](a, b T) bool { return a == b }
var left any = {{.Number}}
var same = Equal{{.Name}}[any](left, "sample")`,
		`func Pair{{.Name}}(values []{{.Type}}) [2]{{.Type}} { return [2]{{.Type}}(values) }
var pair = Pair{{.Name}}([]{{.Type}}{1, {{.Number}}, 3})`,
		`func Count{{.Name}}[K comparable](items []K) map[K]int { counts := make(map[K]int); for _, item := range items { counts[item]++ }; return counts }
var frequencies = Count{{.Name}}([]any{"item", {{.Number}}, true})`,
	}},
	{"builtins", "1.21", [3]string{
		`func Clamp{{.Name}}(value, low, high {{.Type}}) {{.Type}} { return min(max(value, low), high) }
var clamped = Clamp{{.Name}}({{.Number}}, 0, 100)`,
		`type Cache{{.Name}} struct { values map[string]{{.Type}} }
func (c *Cache{{.Name}}) Reset() { clear(c.values) }
var cache = Cache{{.Name}}{values: map[string]{{.Type}}{"sample": {{.Number}}}}`,
		`func Bounds{{.Name}}(items []{{.Type}}) ({{.Type}}, {{.Type}}) {
 low, high := items[0], items[0]
 for _, value := range items[1:] { low, high = min(low, value), max(high, value) }
 clear(items)
 return low, high
}`,
	}},
	{"integer-range", "1.22", [3]string{
		`func Indices{{.Name}}(count int) []int { result := make([]int, 0, count); for index := range count { result = append(result, index) }; return result }
var indices = Indices{{.Name}}({{.Number}})`,
		`func Repeat{{.Name}}(action func()) { for range {{.Number}} { action() } }
var calls int
func Run{{.Name}}() { Repeat{{.Name}}(func() { calls++ }) }`,
		`func Grid{{.Name}}(width, height int) [][2]int { var result [][2]int; for y := range height { for x := range width { result = append(result, [2]int{x,y}) } }; return result }
var points = Grid{{.Name}}({{.Number}}, 2)`,
	}},
	{"function-range", "1.23", [3]string{
		`func Sequence{{.Name}}(yield func(int) bool) { for i := 0; i < {{.Number}}; i++ { if !yield(i) { return } } }
func Total{{.Name}}() int { total := 0; for value := range Sequence{{.Name}} { total += value }; return total }`,
		`func Pairs{{.Name}}(items map[string]{{.Type}}) func(func(string, {{.Type}}) bool) {
 return func(yield func(string, {{.Type}}) bool) { for key, value := range items { if !yield(key, value) { return } } }
}
func Find{{.Name}}(items map[string]{{.Type}}) string { for key, value := range Pairs{{.Name}}(items) { if value > {{.Number}} { return key } }; return "" }`,
		`type Items{{.Name}}[T any] []T
func (items Items{{.Name}}[T]) Each(yield func(T) bool) { for _, value := range items { if !yield(value) { break } } }
func First{{.Name}}() {{.Type}} { for value := range (Items{{.Name}}[{{.Type}}]{1, {{.Number}}}).Each { return value }; return 0 }`,
	}},
	{"generic-alias", "1.24", [3]string{
		`type Set{{.Name}}[T comparable] = map[T]struct{}
func Contains{{.Name}}(items Set{{.Name}}[string], key string) bool { _, ok := items[key]; return ok }
var known = Set{{.Name}}[string]{"sample": {}}`,
		`type Box{{.Name}}[T any] struct { Value T }
type Reference{{.Name}}[T any] = *Box{{.Name}}[T]
func Read{{.Name}}(box Reference{{.Name}}[{{.Type}}]) {{.Type}} { return box.Value }
var box = &Box{{.Name}}[{{.Type}}]{Value: {{.Number}}}`,
		`type Callback{{.Name}}[T any] = func(T) bool
func Select{{.Name}}[T any](values []T, keep Callback{{.Name}}[T]) []T { var out []T; for _, value := range values { if keep(value) { out = append(out, value) } }; return out }
var selected = Select{{.Name}}([]int{1, {{.Number}}}, func(v int) bool { return v > 1 })`,
	}},
	{"new-expression", "1.26", [3]string{
		`func Value{{.Name}}() *{{.Type}} { return new({{.Type}}({{.Number}})) }
var pointer = Value{{.Name}}()`,
		`type Options{{.Name}} struct { Enabled *bool; Limit *int }
func Configure{{.Name}}(limit int) Options{{.Name}} { return Options{{.Name}}{Enabled: new(limit > 0), Limit: new(limit + {{.Number}})} }`,
		`func Text{{.Name}}(base string) *string { return new(base + "-sample") }
var pointers = []*string{Text{{.Name}}("first"), new("second")}`,
	}},
	{"self-reference", "1.26", [3]string{
		`type Mergeable{{.Name}}[T Mergeable{{.Name}}[T]] interface { Merge(T) T }
func Fold{{.Name}}[T Mergeable{{.Name}}[T]](head T, rest []T) T { for _, value := range rest { head = head.Merge(value) }; return head }`,
		`type Comparable{{.Name}}[T Comparable{{.Name}}[T]] interface { Less(T) bool }
func Choose{{.Name}}[T Comparable{{.Name}}[T]](left, right T) T { if left.Less(right) { return left }; return right }`,
		`type Copyable{{.Name}}[T Copyable{{.Name}}[T]] interface { Copy() T }
type Container{{.Name}}[T Copyable{{.Name}}[T]] struct { value T }
func (c Container{{.Name}}[T]) Duplicate() Container{{.Name}}[T] { return Container{{.Name}}[T]{value: c.value.Copy()} }`,
	}},
	{"generic-method", "1.27", [3]string{
		`type Source{{.Name}}[T any] struct { items []T }
func (s Source{{.Name}}[T]) Convert[R any](fn func(T) R) []R { out := make([]R, 0, len(s.items)); for _, item := range s.items { out = append(out, fn(item)) }; return out }
var converted = (Source{{.Name}}[int]{items: []int{1, {{.Number}}}}).Convert(func(v int) bool { return v > 0 })`,
		`type Decoder{{.Name}} struct { offset int }
func (d *Decoder{{.Name}}) Read[T any](decode func(int) T) T { result := decode(d.offset); d.offset++; return result }
var decoder = Decoder{{.Name}}{}
var decoded = decoder.Read[{{.Type}}](func(index int) {{.Type}} { return {{.Type}}(index + {{.Number}}) })`,
		`type Entry{{.Name}}[K comparable] struct { key K }
func (e Entry{{.Name}}[K]) Pair[V any](value V) map[K]V { return map[K]V{e.key: value} }
func Build{{.Name}}() map[string]{{.Type}} { return (Entry{{.Name}}[string]{key: "sample"}).Pair[{{.Type}}]({{.Number}}) }`,
	}},
	{"promoted-field-literal", "1.27", [3]string{
		`type Identity{{.Name}} struct { Code int }
type Record{{.Name}} struct { Identity{{.Name}}; Name string }
func Create{{.Name}}() Record{{.Name}} { return Record{{.Name}}{Code: {{.Number}}, Name: "sample"} }`,
		`type Settings{{.Name}} struct { Enabled bool }
type Base{{.Name}} struct { Settings{{.Name}} }
type Worker{{.Name}} struct { Base{{.Name}}; Count int }
var worker = Worker{{.Name}}{Enabled: true, Count: {{.Number}}}`,
		`type Position{{.Name}} struct { X, Y {{.Type}} }
type Point{{.Name}} struct { Position{{.Name}}; Label string }
func Offset{{.Name}}(p Point{{.Name}}) Point{{.Name}} { return Point{{.Name}}{X: p.X + {{.Number}}, Y: p.Y, Label: p.Label} }`,
	}},
	{"function-inference", "1.27", [3]string{
		`func Identity{{.Name}}[T any](value T) T { return value }
var transforms = map[string]func({{.Type}}) {{.Type}}{"identity": Identity{{.Name}}}
var transformed = transforms["identity"]({{.Number}})`,
		`func Twice{{.Name}}[T ~int | ~int32 | ~int64 | ~float64](value T) T { return value + value }
type Pipeline{{.Name}} struct { Apply func({{.Type}}) {{.Type}} }
var pipeline = Pipeline{{.Name}}{Apply: Twice{{.Name}}}`,
		`func Zero{{.Name}}[T any](value T) T { var empty T; return empty }
var steps = []func(string) string{Zero{{.Name}}}
func Execute{{.Name}}(text string) string { for _, step := range steps { text = step(text) }; return text }`,
	}},
	{"struct-tags", "1.18", [3]string{
		`type Profile{{.Name}} struct {
 ID int ` + "`json:\"id\" gorm:\"primaryKey;column:id\"`" + `
 Name string ` + "`json:\"name,omitempty\" binding:\"required,min=2\"`" + `
}
func (p Profile{{.Name}}) Valid() bool { return p.ID > {{.Number}} && p.Name != "" }`,
		`type Payload{{.Name}} struct {
 Meta struct { Code int ` + "`xml:\"code,attr\"`" + ` } ` + "`json:\"meta\" yaml:\"meta\"`" + `
 Values []string ` + "`json:\"values\" validate:\"dive,required\"`" + `
}
var payload = Payload{{.Name}}{Values: []string{"sample"}}`,
		`// Options{{.Name}} describes externally supplied settings.
//go:generate echo configuration
/* Tags remain string spans, including punctuation inside values. */
type Options{{.Name}} struct {
 Enabled bool "json:\"enabled\" custom:\"flag\""
 Note string ` + "`json:\"note\" custom:\"a:b;c,d\"`" + `
}
func Check{{.Name}}(o *Options{{.Name}}) bool { return o != nil && o.Enabled }`,
	}},
}
