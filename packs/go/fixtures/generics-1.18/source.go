package sample

type Box[T any] struct {
	value T
}

func Map[T any, R any](value T, fn func(T) R) R {
	return fn(value)
}
