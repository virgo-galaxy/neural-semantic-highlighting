use std::future::Future;

async fn load_name(id: u64) -> Result<String, String> {
    let name = async { format!("User-{id}") }.await;
    if id == 0 { return Err("Missing user".into()); }
    Ok(name)
}

fn greeting(id: u64) -> impl Future<Output = Result<String, String>> {
    async move {
        let name = load_name(id).await?;
        Ok(format!("Welcome, {name}"))
    }
}

fn main() {
    // The future is lazy; an application supplies its own executor.
    let future = greeting(42);
    drop(future);
}
