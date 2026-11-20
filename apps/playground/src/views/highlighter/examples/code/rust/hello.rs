#[derive(Debug, Clone)]
struct User {
    name: String,
    score: u32,
}

impl User {
    fn new(name: &str) -> Self {
        Self { name: name.to_owned(), score: 0 }
    }

    fn greet(&self) -> String {
        format!("Hello, {}!", self.name)
    }
}

fn main() {
    let mut user = User::new("Ada");
    user.score += 10;
    println!("{} Score: {}", user.greet(), user.score);
}
