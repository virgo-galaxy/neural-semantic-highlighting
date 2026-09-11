package sample

func Count(limit int) int {
	total := 0
	for i := range limit {
		total += i
	}
	return total
}
