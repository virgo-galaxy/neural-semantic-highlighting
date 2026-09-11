package sample

type Adder[A Adder[A]] interface {
	Add(A) A
}

func Sum[A Adder[A]](left, right A) A {
	return left.Add(right)
}
