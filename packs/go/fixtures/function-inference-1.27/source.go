package sample

func Double[T ~int | ~float64](value T) T {
	return value * 2
}

func Square[T ~int | ~float64](value T) T {
	return value * value
}

var operations = map[string]func(int) int{
	"double": Double,
	"square": Square,
}
