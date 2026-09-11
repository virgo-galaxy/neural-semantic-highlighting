package sample

func Clamp[T ~int | ~float64](value, low, high T) T {
	return min(max(value, low), high)
}

func Reset[K comparable, V any](items map[K]V) {
	clear(items)
}
