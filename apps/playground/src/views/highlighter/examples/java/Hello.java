package demo;

import java.util.List;

public final class Hello {
    private final String greeting;

    public Hello(String greeting) {
        this.greeting = greeting;
    }

    public void welcome(List<String> names) {
        for (String name : names) {
            System.out.println(greeting + ", " + name);
        }
    }

    public static void main(String[] args) {
        var app = new Hello("Hello");
        app.welcome(List.of("Virgo", "世界 🌍"));
    }
}
