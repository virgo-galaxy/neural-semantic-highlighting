trait Summarize {
    fn summary(&self) -> String;
}

struct Article<T> {
    title: String,
    content: T,
}

impl<T: std::fmt::Display> Summarize for Article<T> {
    fn summary(&self) -> String {
        format!("{}: {}", self.title, self.content)
    }
}

fn print_summary(item: &impl Summarize) {
    println!("{}", item.summary());
}

fn main() {
    let article = Article { title: "Stable Rust".into(), content: 42 };
    print_summary(&article);
}
