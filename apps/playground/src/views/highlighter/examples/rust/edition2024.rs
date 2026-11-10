#[unsafe(no_mangle)]
pub extern "C" fn add_one(value: u32) -> u32 {
    value + 1
}

struct Buffer<const N: usize> {
    values: [u8; N],
}

fn is_ready(value: Option<u32>) -> bool {
    if let Some(found) = value && found > 3 {
        true
    } else {
        false
    }
}

fn main() {
    let r#gen = Buffer { values: [1, 2, 3, 4] };
    assert!(is_ready(Some(add_one(4))));
    println!("{} bytes", r#gen.values.len());
}
