package dataset

// V2 deliberately varies syntax shape, not only identifier spelling. Validation
// and test families are disjoint from training families. Hard-negative families
// are train-only and teach distinctions between visually similar constructs.
var focusedV2Families = []focusedFamilySpec{
	// Self-referential constraints.
	{"self-reference", "1.26", "self-reference/train/value-method", "train", `type Mergeable{{.Name}}[T Mergeable{{.Name}}[T]] interface { Merge(T) T }
func Fold{{.Name}}[T Mergeable{{.Name}}[T]](head T, rest []T) T { for _, value := range rest { head = head.Merge(value) }; return head }`},
	{"self-reference", "1.26", "self-reference/train/multi-method", "train", `type Node{{.Name}}[T Node{{.Name}}[T]] interface { Clone() T; Equal(T) bool }
func Same{{.Name}}[T Node{{.Name}}[T]](left, right T) bool { return left.Clone().Equal(right) }`},
	{"self-reference", "1.26", "self-reference/train/struct-constraint", "train", `type Copyable{{.Name}}[T Copyable{{.Name}}[T]] interface { Copy() T }
type Holder{{.Name}}[T Copyable{{.Name}}[T]] struct { Value T }
func Duplicate{{.Name}}[T Copyable{{.Name}}[T]](h Holder{{.Name}}[T]) T { return h.Value.Copy() }`},
	{"self-reference", "1.26", "self-reference/train/nested-use", "train", `type Reducible{{.Name}}[T Reducible{{.Name}}[T]] interface { Reduce(T) T }
func ReduceAll{{.Name}}[T Reducible{{.Name}}[T]](values []T) T { out := values[0]; for _, value := range values[1:] { out = out.Reduce(value) }; return out }`},
	{"self-reference", "1.26", "self-reference/train/non-self-interface-negative", "train", `type Decoder{{.Name}}[T any] interface { Decode(T) error }
func Decode{{.Name}}[T any](d Decoder{{.Name}}[T], value T) error { return d.Decode(value) }`},
	{"self-reference", "1.26", "self-reference/train/defined-type-negative", "train", `type Box{{.Name}}[T any] struct { Value T }
type BoxList{{.Name}}[T any] []Box{{.Name}}[T]
func First{{.Name}}[T any](values BoxList{{.Name}}[T]) T { return values[0].Value }`},
	{"self-reference", "1.26", "self-reference/validation/ordering", "validation", `type Ordered{{.Name}}[T Ordered{{.Name}}[T]] interface { Before(T) bool; Copy() T }
func Earlier{{.Name}}[T Ordered{{.Name}}[T]](a, b T) T { if a.Before(b) { return a.Copy() }; return b.Copy() }`},
	{"self-reference", "1.26", "self-reference/validation/container", "validation", `type Chain{{.Name}}[T Chain{{.Name}}[T]] interface { Next() (T, bool) }
type Link{{.Name}}[T Chain{{.Name}}[T]] struct { Current T; Steps int }
func Advance{{.Name}}[T Chain{{.Name}}[T]](link *Link{{.Name}}[T]) (T, bool) { current := link.Current; for i := 0; i < link.Steps; i++ { next, ok := current.Next(); if !ok { return current, false }; current = next }; return current, true }`},
	{"self-reference", "1.26", "self-reference/test/combine", "test", `type Combiner{{.Name}}[T Combiner{{.Name}}[T]] interface { Combine(T) T; Empty() bool }
func Join{{.Name}}[T Combiner{{.Name}}[T]](a, b T) T { if a.Empty() { return b }; return a.Combine(b) }`},
	{"self-reference", "1.26", "self-reference/test/tree", "test", `type TreeNode{{.Name}}[T TreeNode{{.Name}}[T]] interface { Children() []T }
func ChildCount{{.Name}}[T TreeNode{{.Name}}[T]](node T) int { return len(node.Children()) }`},

	// Range over functions and methods.
	{"function-range", "1.23", "function-range/train/free-seq", "train", `func Sequence{{.Name}}(yield func(int) bool) { for i := 0; i < {{.Number}}; i++ { if !yield(i) { return } } }
func Sum{{.Name}}() int { total := 0; for value := range Sequence{{.Name}} { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/value-method", "train", `type Counter{{.Name}} struct { Limit int }
func (c Counter{{.Name}}) Values(yield func(int) bool) { for i := 0; i < c.Limit; i++ { if !yield(i) { return } } }
func SumCounter{{.Name}}(c Counter{{.Name}}) int { total := 0; for value := range c.Values { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/generic-method", "train", `type Items{{.Name}}[T any] []T
func (items Items{{.Name}}[T]) Each(yield func(T) bool) { for _, value := range items { if !yield(value) { return } } }
func First{{.Name}}(items Items{{.Name}}[{{.Type}}]) {{.Type}} { for value := range items.Each { return value }; return 0 }`},
	{"function-range", "1.23", "function-range/train/method-returning-seq", "train", `type Bag{{.Name}}[T any] []T
func (b Bag{{.Name}}[T]) Iter() func(func(T) bool) { return func(yield func(T) bool) { for _, value := range b { if !yield(value) { return } } } }
func Count{{.Name}}(b Bag{{.Name}}[{{.Type}}]) int { n := 0; for range b.Iter() { n++ }; return n }`},
	{"function-range", "1.23", "function-range/train/two-value-method", "train", `type PairMap{{.Name}} map[string]{{.Type}}
func (m PairMap{{.Name}}) Pairs(yield func(string, {{.Type}}) bool) { for key, value := range m { if !yield(key, value) { return } } }
func Find{{.Name}}(m PairMap{{.Name}}) string { for key, value := range m.Pairs { if value > {{.Number}} { return key } }; return "" }`},
	{"function-range", "1.23", "function-range/train/slice-negative", "train", `func Values{{.Name}}() []{{.Type}} { return []{{.Type}}{1, {{.Number}}} }
func SumSlice{{.Name}}() {{.Type}} { var total {{.Type}}; for _, value := range Values{{.Name}}() { total += value }; return total }`},
	{"function-range", "1.23", "function-range/validation/pointer-method", "validation", `type Stream{{.Name}} struct { Limit int }
func (s *Stream{{.Name}}) All(yield func(int) bool) { for i := 0; i < s.Limit; i++ { if !yield(i) { break } } }
func Last{{.Name}}(s *Stream{{.Name}}) int { last := -1; for value := range s.All { last = value }; return last }`},
	{"function-range", "1.23", "function-range/validation/returned-generic", "validation", `type Source{{.Name}}[T any] []T
func (s Source{{.Name}}[T]) Seq() func(func(T) bool) { return func(yield func(T) bool) { for _, value := range s { if !yield(value) { return } } } }
func Pick{{.Name}}(s Source{{.Name}}[{{.Type}}]) {{.Type}} { for value := range s.Seq() { return value }; return 0 }`},
	{"function-range", "1.23", "function-range/test/selector-method", "test", `type Queue{{.Name}}[T any] []T
func (q Queue{{.Name}}[T]) Walk(yield func(T) bool) { for _, value := range q { if !yield(value) { return } } }
func Consume{{.Name}}(q Queue{{.Name}}[{{.Type}}]) {{.Type}} { var last {{.Type}}; for value := range q.Walk { last = value }; return last }`},
	{"function-range", "1.23", "function-range/test/two-value-returned", "test", `type Table{{.Name}} map[string]{{.Type}}
func (t Table{{.Name}}) Iter() func(func(string, {{.Type}}) bool) { return func(yield func(string, {{.Type}}) bool) { for k, v := range t { if !yield(k, v) { return } } } }
func FirstKey{{.Name}}(t Table{{.Name}}) string { for key := range t.Iter() { return key }; return "" }`},

	// Generic methods (Go 1.27).
	{"generic-method", "1.27", "generic-method/train/value-generic-receiver", "train", `type Box{{.Name}}[T any] struct { Value T }
func (b Box{{.Name}}[T]) Map[U any](fn func(T) U) U { return fn(b.Value) }
var mapped{{.Name}} = (Box{{.Name}}[int]{Value: {{.Number}}}).Map(func(v int) string { return "value" })`},
	{"generic-method", "1.27", "generic-method/train/pointer-plain-receiver", "train", `type Decoder{{.Name}} struct { Offset int }
func (d *Decoder{{.Name}}) Read[T any](fn func(int) T) T { value := fn(d.Offset); d.Offset++; return value }
var decoded{{.Name}} = (&Decoder{{.Name}}{}).Read[{{.Type}}](func(v int) {{.Type}} { return {{.Type}}(v) })`},
	{"generic-method", "1.27", "generic-method/train/two-method-params", "train", `type Entry{{.Name}}[K comparable] struct { Key K }
func (e Entry{{.Name}}[K]) Pair[V any, R any](value V, fn func(K, V) R) R { return fn(e.Key, value) }
var paired{{.Name}} = (Entry{{.Name}}[string]{Key: "k"}).Pair({{.Number}}, func(k string, v int) string { return k })`},
	{"generic-method", "1.27", "generic-method/train/method-value", "train", `type Wrapper{{.Name}}[T any] struct { Value T }
func (w Wrapper{{.Name}}[T]) Convert[U any](fn func(T) U) U { return fn(w.Value) }
var wrapper{{.Name}} = Wrapper{{.Name}}[int]{Value: {{.Number}}}
var converter{{.Name}} = wrapper{{.Name}}.Convert[string]`},
	{"generic-method", "1.27", "generic-method/train/free-function-negative", "train", `type Holder{{.Name}}[T any] struct { Value T }
func Convert{{.Name}}[T any, U any](h Holder{{.Name}}[T], fn func(T) U) U { return fn(h.Value) }
var converted{{.Name}} = Convert{{.Name}}(Holder{{.Name}}[int]{Value: {{.Number}}}, func(v int) string { return "x" })`},
	{"generic-method", "1.27", "generic-method/train/plain-method-negative", "train", `type Plain{{.Name}}[T any] struct { Value T }
func (p Plain{{.Name}}[T]) ValueOr(other T) T { if any(p.Value) == nil { return other }; return p.Value }
var plain{{.Name}} = (Plain{{.Name}}[int]{Value: {{.Number}}}).ValueOr(0)`},
	{"generic-method", "1.27", "generic-method/validation/map-result", "validation", `type Record{{.Name}}[K comparable] struct { Key K }
func (r Record{{.Name}}[K]) Bind[V any](value V) map[K]V { return map[K]V{r.Key: value} }
var bound{{.Name}} = (Record{{.Name}}[string]{Key: "k"}).Bind({{.Number}})`},
	{"generic-method", "1.27", "generic-method/validation/pointer-generic", "validation", `type Cell{{.Name}}[T any] struct { Value T }
func (c *Cell{{.Name}}[T]) Apply[U any](fn func(*T) U) U { return fn(&c.Value) }
var applied{{.Name}} = (&Cell{{.Name}}[int]{Value: {{.Number}}}).Apply(func(v *int) string { return "ok" })`},
	{"generic-method", "1.27", "generic-method/test/chained", "test", `type StreamBox{{.Name}}[T any] struct { Values []T }
func (s StreamBox{{.Name}}[T]) FirstAs[U any](fn func(T) U) U { return fn(s.Values[0]) }
var first{{.Name}} = (StreamBox{{.Name}}[int]{Values: []int{1, {{.Number}}}}).FirstAs(func(v int) float64 { return float64(v) })`},
	{"generic-method", "1.27", "generic-method/test/constrained-method-param", "test", `type KeyBox{{.Name}}[T any] struct { Value T }
func (b KeyBox{{.Name}}[T]) IndexBy[K comparable](fn func(T) K) map[K]T { return map[K]T{fn(b.Value): b.Value} }
var indexed{{.Name}} = (KeyBox{{.Name}}[int]{Value: {{.Number}}}).IndexBy(func(v int) string { return "k" })`},

	// Generic aliases.
	{"generic-alias", "1.24", "generic-alias/train/map", "train", `type Set{{.Name}}[T comparable] = map[T]struct{}
func Has{{.Name}}[T comparable](set Set{{.Name}}[T], value T) bool { _, ok := set[value]; return ok }`},
	{"generic-alias", "1.24", "generic-alias/train/slice", "train", `type List{{.Name}}[T any] = []T
func First{{.Name}}[T any](values List{{.Name}}[T]) T { return values[0] }`},
	{"generic-alias", "1.24", "generic-alias/train/pointer", "train", `type Box{{.Name}}[T any] struct { Value T }
type BoxRef{{.Name}}[T any] = *Box{{.Name}}[T]
func Read{{.Name}}[T any](value BoxRef{{.Name}}[T]) T { return value.Value }`},
	{"generic-alias", "1.24", "generic-alias/train/function", "train", `type Predicate{{.Name}}[T any] = func(T) bool
func Keep{{.Name}}[T any](value T, predicate Predicate{{.Name}}[T]) bool { return predicate(value) }`},
	{"generic-alias", "1.24", "generic-alias/train/defined-type-negative", "train", `type DefinedList{{.Name}}[T any] []T
func Len{{.Name}}[T any](values DefinedList{{.Name}}[T]) int { return len(values) }`},
	{"generic-alias", "1.24", "generic-alias/train/non-generic-alias-negative", "train", `type IDs{{.Name}} = []int
func CountIDs{{.Name}}(values IDs{{.Name}}) int { return len(values) }`},
	{"generic-alias", "1.24", "generic-alias/validation/nested", "validation", `type Pair{{.Name}}[A, B any] struct { Left A; Right B }
type StringPair{{.Name}}[T any] = Pair{{.Name}}[string, T]
func Right{{.Name}}[T any](pair StringPair{{.Name}}[T]) T { return pair.Right }`},
	{"generic-alias", "1.24", "generic-alias/validation/channel", "validation", `type Channel{{.Name}}[T any] = chan T
func Send{{.Name}}[T any](ch Channel{{.Name}}[T], value T) { ch <- value }`},
	{"generic-alias", "1.24", "generic-alias/test/function-return", "test", `type Factory{{.Name}}[T any] = func() T
func Build{{.Name}}[T any](factory Factory{{.Name}}[T]) T { return factory() }`},
	{"generic-alias", "1.24", "generic-alias/test/nested-map", "test", `type Lookup{{.Name}}[K comparable, V any] = map[K][]V
func Values{{.Name}}[K comparable, V any](lookup Lookup{{.Name}}[K, V], key K) []V { return lookup[key] }`},

	// Struct tags remain a single string span; V2 varies tag grammar and placement.
	{"struct-tags", "1.18", "struct-tags/train/json-gorm", "train", `type User{{.Name}} struct {
 ID int ` + "`json:\"id\" gorm:\"primaryKey;column:id\"`" + `
 Name string ` + "`json:\"name,omitempty\" gorm:\"size:128;not null\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/train/xml-yaml", "train", `type Document{{.Name}} struct {
 Code string ` + "`xml:\"code,attr\" yaml:\"code\"`" + `
 Values []{{.Type}} ` + "`xml:\"value\" yaml:\"values,omitempty\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/train/validate-db", "train", `type Row{{.Name}} struct {
 Email string ` + "`db:\"email_address\" validate:\"required,email\"`" + `
 Count int ` + "`db:\"item_count\" validate:\"gte=0,lte=100\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/train/embedded", "train", `type Base{{.Name}} struct { ID int ` + "`json:\"id\"`" + ` }
type Wrapped{{.Name}} struct {
 Base{{.Name}} ` + "`json:\"base\"`" + `
 Note string ` + "`custom:\"a:b;c,d\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/train/raw-string-negative", "train", `var Metadata{{.Name}} = ` + "`json:\"name\" gorm:\"column:name\"`" + `
type Plain{{.Name}} struct { Name string }`},
	{"struct-tags", "1.18", "struct-tags/train/quoted-tag", "train", `type Quoted{{.Name}} struct {
 Enabled bool "json:\"enabled\" custom:\"flag\""
 Note string ` + "`json:\"note\" custom:\"x:y;z\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/validation/nested", "validation", `type Payload{{.Name}} struct {
 Meta struct { Code int ` + "`json:\"code\" xml:\"code,attr\"`" + ` } ` + "`json:\"meta\"`" + `
 Values []string ` + "`json:\"values\" binding:\"required,dive\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/validation/protobuf-style", "validation", `type Message{{.Name}} struct {
 ID int32 ` + "`protobuf:\"varint,1,opt,name=id,proto3\" json:\"id,omitempty\"`" + `
 Text string ` + "`protobuf:\"bytes,2,opt,name=text,proto3\" json:\"text,omitempty\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/test/mixed", "test", `type Config{{.Name}} struct {
 Path *string ` + "`json:\"path,omitempty\" yaml:\"path\" validate:\"omitempty,min=1\"`" + `
 Limits map[string]int ` + "`json:\"limits\" gorm:\"serializer:json\"`" + `
 Enabled bool ` + "`json:\"enabled\" custom:\"feature:toggle\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/test/custom", "test", `type Event{{.Name}} struct {
 Kind string ` + "`json:\"kind\" custom:\"kind:v2;required\"`" + `
 Data []byte ` + "`json:\"data,omitempty\" custom:\"codec:raw\"`" + `
 Meta struct { TraceID string ` + "`json:\"trace_id\"`" + ` } ` + "`custom:\"meta:trace\"`" + `
}`},
}

// V2R2 keeps the V2 held-out families unchanged and only expands train-time
// coverage for protobuf-style struct tags. The diagnostic showed that ordinary
// json/xml/binding tags were already stable while long protobuf tags containing
// comma-separated numeric and symbolic options were split internally.
var focusedV2R2ExtraFamilies = []focusedFamilySpec{
	{"struct-tags", "1.18", "struct-tags/train/protobuf-three-fields", "train", `type Wire{{.Name}} struct {
 ID int64 ` + "`protobuf:\"varint,7,opt,name=id,proto3\" json:\"id,omitempty\"`" + `
 Payload []byte ` + "`protobuf:\"bytes,11,opt,name=payload,proto3\" json:\"payload,omitempty\"`" + `
 Active bool ` + "`protobuf:\"varint,19,opt,name=active,proto3\" json:\"active,omitempty\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/train/protobuf-repeated-and-map", "train", `type Collection{{.Name}} struct {
 Values []int32 ` + "`protobuf:\"varint,3,rep,packed,name=values,proto3\" json:\"values,omitempty\"`" + `
 Labels map[string]string ` + "`protobuf:\"bytes,9,rep,name=labels,proto3\" json:\"labels,omitempty\" protobuf_key:\"bytes,1,opt,name=key,proto3\" protobuf_val:\"bytes,2,opt,name=value,proto3\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/train/protobuf-nested-layout", "train", `type Header{{.Name}} struct {
 Version uint32 ` + "`protobuf:\"varint,1,opt,name=version,proto3\" json:\"version,omitempty\"`" + `
}
type Envelope{{.Name}} struct {
 Header *Header{{.Name}} ` + "`protobuf:\"bytes,4,opt,name=header,proto3\" json:\"header,omitempty\"`" + `
 Items []string ` + "`protobuf:\"bytes,8,rep,name=items,proto3\" json:\"items,omitempty\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/train/protobuf-mixed-wire-types", "train", `type Metrics{{.Name}} struct {
 Count int32 ` + "`protobuf:\"zigzag32,5,opt,name=count,proto3\" json:\"count,omitempty\"`" + `
 Ratio float64 ` + "`protobuf:\"fixed64,12,opt,name=ratio,proto3\" json:\"ratio,omitempty\"`" + `
 Name string ` + "`protobuf:\"bytes,21,opt,name=name,proto3\" json:\"name,omitempty\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/train/protobuf-tag-stack", "train", `type Generated{{.Name}} struct {
 State int ` + "`protogen:\"open.v1\"`" + `
 Key string ` + "`protobuf:\"bytes,2,opt,name=key,proto3\" json:\"key,omitempty\" yaml:\"key\"`" + `
 Children []int64 ` + "`protobuf:\"varint,15,rep,packed,name=children,proto3\" json:\"children,omitempty\" custom:\"wire:v2;required\"`" + `
}`},
}

// V2R3 expands only function-range training coverage. The validation diagnostic
// showed that bare pointer-receiver method values used as range iterators were
// consistently classified as properties, while method declarations and called
// methods were already correct. These train-only families teach method values
// in several contexts and include a function-valued field hard negative.
var focusedV2R3ExtraFamilies = []focusedFamilySpec{
	{"function-range", "1.23", "function-range/train/pointer-method-value-binding", "train", `type Cursor{{.Name}} struct { Limit int }
func (c *Cursor{{.Name}}) Visit(yield func(int) bool) { for i := 0; i < c.Limit; i++ { if !yield(i) { return } } }
func SumCursor{{.Name}}(c *Cursor{{.Name}}) int { iter := c.Visit; total := 0; for value := range iter { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/interface-method-value", "train", `type Iterable{{.Name}} interface { Walk(func(int) bool) }
func FirstWalk{{.Name}}(src Iterable{{.Name}}) int { for value := range src.Walk { return value }; return -1 }`},
	{"function-range", "1.23", "function-range/train/pointer-method-value-argument", "train", `type Scanner{{.Name}} struct { End int }
func (s *Scanner{{.Name}}) Scan(yield func(int) bool) { for i := 0; i < s.End; i++ { if !yield(i) { break } } }
func Consume{{.Name}}(iter func(func(int) bool)) int { count := 0; for range iter { count++ }; return count }
func CountScan{{.Name}}(s *Scanner{{.Name}}) int { return Consume{{.Name}}(s.Scan) }`},
	{"function-range", "1.23", "function-range/train/embedded-pointer-method-value", "train", `type BaseIter{{.Name}} struct { Limit int }
func (b *BaseIter{{.Name}}) Entries(yield func(int) bool) { for i := 0; i < b.Limit; i++ { if !yield(i) { return } } }
type EmbeddedIter{{.Name}} struct { *BaseIter{{.Name}} }
func SumEmbedded{{.Name}}(e *EmbeddedIter{{.Name}}) int { total := 0; for value := range e.Entries { total += value }; return total }`},
	{"function-range", "1.23", "function-range/train/function-field-negative", "train", `type FunctionField{{.Name}} struct { Values func(func(int) bool) }
func SumField{{.Name}}(src FunctionField{{.Name}}) int { total := 0; for value := range src.Values { total += value }; return total }`},
}
