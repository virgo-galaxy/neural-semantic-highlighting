fn main() {
    // Original Unicode, escapes and delimiters stay unchanged.
    let document = r##"{ "title": "星空 🌌", "path": "C:\notes" }"##;
    let request = br#"GET / HTTP/1.1"#;
    let label = c"ready";
    let symbol = '星';
    let escaped = '\n';
    let mask = 0xff_u32;

    /* A block comment can contain /* another comment */ safely. */
    println!("{document} {request:?} {label:?} {symbol} {escaped} {mask:x}");
}
