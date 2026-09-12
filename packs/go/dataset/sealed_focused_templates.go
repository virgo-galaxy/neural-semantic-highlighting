package dataset

// sealedFocusedFamilies is a one-time external acceptance set. These families
// are deliberately absent from every train/validation/test profile. They are
// generated only by the sealed-v1 profile and must never be added to a prepared
// training snapshot.
var sealedFocusedFamilies = []focusedFamilySpec{
	// Self-referential constraints: new control-flow and collection shapes.
	{"self-reference", "1.26", "self-reference/sealed/rewrite-loop", "sealed", `type Rewriter{{.Name}}[T Rewriter{{.Name}}[T]] interface { Rewrite(int) T; Stable() bool }
func Settle{{.Name}}[T Rewriter{{.Name}}[T]](value T, budget int) T { for budget > 0 && !value.Stable() { value = value.Rewrite(budget); budget-- }; return value }`},
	{"self-reference", "1.26", "self-reference/sealed/neighbor-frontier", "sealed", `type Neighbor{{.Name}}[T Neighbor{{.Name}}[T]] interface { Neighbors() []T; Key() string }
func Frontier{{.Name}}[T Neighbor{{.Name}}[T]](root T) map[string]T { seen := map[string]T{root.Key(): root}; queue := []T{root}; for len(queue) > 0 { current := queue[0]; queue = queue[1:]; for _, next := range current.Neighbors() { if _, ok := seen[next.Key()]; !ok { seen[next.Key()] = next; queue = append(queue, next) } } }; return seen }`},

	// Range-over-function method values: no-call selectors in shapes not used by
	// the focused curriculum, including conditional binding and two-value yields.
	{"function-range", "1.23", "function-range/sealed/conditional-method-binding", "sealed", `type Emitter{{.Name}} struct { Start, Stop int }
func (e *Emitter{{.Name}}) Emit(yield func(int) bool) { for value := e.Start; value < e.Stop; value++ { if !yield(value) { return } } }
func Measure{{.Name}}(e *Emitter{{.Name}}) int { var sequence func(func(int) bool); if e != nil { sequence = e.Emit }; count := 0; if sequence != nil { for range sequence { count++ } }; return count }`},
	{"function-range", "1.23", "function-range/sealed/indexed-generic-method-value", "sealed", `type Catalog{{.Name}}[T any] struct { Items []T }
func (c *Catalog{{.Name}}[T]) Enumerate(yield func(int, T) bool) { for index, value := range c.Items { if !yield(index, value) { return } } }
func Snapshot{{.Name}}[T any](c *Catalog{{.Name}}[T]) map[int]T { output := map[int]T{}; for index, value := range c.Enumerate { output[index] = value }; return output }`},

	// Go 1.27 generic methods: distinct receiver and use-site structures.
	{"generic-method", "1.27", "generic-method/sealed/non-generic-receiver-two-params", "sealed", `type Projector{{.Name}} struct { Prefix string }
func (p Projector{{.Name}}) Project[T any, U comparable](value T, convert func(string, T) U) U { return convert(p.Prefix, value) }
var projected{{.Name}} = (Projector{{.Name}}{Prefix: "p"}).Project({{.Number}}, func(prefix string, value int) string { return prefix })`},
	{"generic-method", "1.27", "generic-method/sealed/generic-receiver-method-value", "sealed", `type Vault{{.Name}}[T any] struct { Item T }
func (v *Vault{{.Name}}[T]) Transform[U any](convert func(T) U) U { return convert(v.Item) }
var vault{{.Name}} = &Vault{{.Name}}[int]{Item: {{.Number}}}
var transform{{.Name}} = vault{{.Name}}.Transform[float64]
var transformed{{.Name}} = transform{{.Name}}(func(value int) float64 { return float64(value) })`},

	// Generic aliases: new composite and callable alias shapes.
	{"generic-alias", "1.24", "generic-alias/sealed/matrix", "sealed", `type Matrix{{.Name}}[T any] = [][]T
func Corner{{.Name}}[T any](matrix Matrix{{.Name}}[T]) (T, T) { return matrix[0][0], matrix[len(matrix)-1][len(matrix[len(matrix)-1])-1] }`},
	{"generic-alias", "1.24", "generic-alias/sealed/resolver", "sealed", `type Resolver{{.Name}}[K comparable, V any] = func(K) (V, bool)
func ResolveOr{{.Name}}[K comparable, V any](resolve Resolver{{.Name}}[K, V], key K, fallback V) V { value, ok := resolve(key); if !ok { return fallback }; return value }`},

	// Struct tags: long mixed grammars and nested placement, but not copies of
	// protobuf-focused training families.
	{"struct-tags", "1.18", "struct-tags/sealed/config-codecs", "sealed", `type CodecConfig{{.Name}} struct {
 Endpoint string ` + "`json:\"endpoint\" yaml:\"endpoint\" mapstructure:\"endpoint\" validate:\"required,url\"`" + `
 Retry []int ` + "`json:\"retry,omitempty\" toml:\"retry\" mapstructure:\"retry\" validate:\"omitempty,dive,gte=0\"`" + `
 Handler func(string) error ` + "`json:\"-\" custom:\"runtime:handler;optional\"`" + `
}`},
	{"struct-tags", "1.18", "struct-tags/sealed/nested-transport", "sealed", `type Transport{{.Name}} struct {
 Header struct { Trace string ` + "`json:\"trace\" xml:\"trace,attr\" validate:\"omitempty,uuid\"`" + `; Flags []string ` + "`json:\"flags,omitempty\" xml:\"flag\"`" + ` } ` + "`json:\"header\" yaml:\"header\"`" + `
 Payload []byte ` + "`json:\"payload,omitempty\" yaml:\"payload,omitempty\" custom:\"codec:base64;limit=4096\"`" + `
}
`},
}
