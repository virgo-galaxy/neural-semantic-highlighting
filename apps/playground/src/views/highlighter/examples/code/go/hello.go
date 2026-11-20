package main

import "fmt"

func greet(name string) string {
	message := "hello, " + name
	return message
}

func main() {
	fmt.Println(greet("world"))
}
