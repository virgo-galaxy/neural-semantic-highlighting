package sample

type Set[T comparable] = map[T]struct{}

func Has[T comparable](set Set[T], value T) bool {
	_, ok := set[value]
	return ok
}
