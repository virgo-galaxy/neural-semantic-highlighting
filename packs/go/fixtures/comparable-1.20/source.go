package sample

func Contains[K comparable, V any](items map[K]V, key K) bool {
	_, ok := items[key]
	return ok
}

func ContainsAny(items map[any]int, key any) bool {
	return Contains(items, key)
}

func FourBytes(data []byte) [4]byte {
	return [4]byte(data)
}
