package sample

type Box[T any] struct {
	value T
}

func (box Box[T]) Map[R any](fn func(T) R) R {
	return fn(box.value)
}
