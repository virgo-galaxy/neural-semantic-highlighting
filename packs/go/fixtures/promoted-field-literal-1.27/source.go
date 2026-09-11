package sample

type Base struct {
	ID int
}

type User struct {
	Base
	Name string
}

var defaultUser = User{
	ID:   7,
	Name: "Mittens",
}
