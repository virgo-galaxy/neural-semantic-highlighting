fn longest<'a>(left: &'a str, right: &'a str) -> &'a str {
    if left.len() >= right.len() { left } else { right }
}

fn first<T>(items: &[T]) -> Option<&T> {
    items.first()
}

fn main() {
    let owned = String::from("Ownership");
    let borrowed = &owned;
    let names = [borrowed.as_str(), "Rust"];

    if let Some(name) = first(&names) {
        println!("{}", longest(name, "Virgo"));
    }
}
