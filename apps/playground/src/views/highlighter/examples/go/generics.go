package collection

type Ordered interface {
	~int | ~int64 | ~float64 | ~string
}

type Pair[K comparable, V any] struct {
	Key   K
	Value V
}

func Max[T Ordered](left, right T) T {
	if left > right {
		return left
	}
	return right
}

func Map[T any, R any](items []T, transform func(T) R) []R {
	result := make([]R, 0, len(items))
	for _, item := range items {
		result = append(result, transform(item))
	}
	return result
}
