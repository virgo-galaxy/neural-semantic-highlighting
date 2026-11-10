#[derive(Debug)]
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Text(String),
}

fn handle(message: Message) -> String {
    match message {
        Message::Quit => "Goodbye".into(),
        Message::Move { x, y } if x == y => format!("Diagonal: {x}"),
        Message::Move { x, y } => format!("Position: {x}, {y}"),
        Message::Text(text) => text.to_uppercase(),
    }
}

fn main() {
    let messages = [Message::Move { x: 3, y: 3 }, Message::Text("Ready".into()), Message::Quit];
    for message in messages {
        println!("{}", handle(message));
    }
}
