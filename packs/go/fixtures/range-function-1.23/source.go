package sample

func CountTo(limit int) func(func(int) bool) {
	return func(yield func(int) bool) {
		for i := 0; i < limit; i++ {
			if !yield(i) {
				return
			}
		}
	}
}

func Sum(seq func(func(int) bool)) int {
	total := 0
	for value := range seq {
		total += value
	}
	return total
}
