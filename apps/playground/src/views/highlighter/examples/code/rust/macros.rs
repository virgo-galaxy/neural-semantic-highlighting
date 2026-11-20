macro_rules! list {
    ($($value:expr),* $(,)?) => {
        vec![$($value),*]
    };
}

macro_rules! announce {
    ($label:expr, $value:expr) => {
        println!("{} = {:?}", $label, $value)
    };
}

fn main() {
    let values = list![2, 4, 8,];
    let doubled: Vec<_> = values.iter().map(|value| value * 2).collect();
    announce!("doubled", doubled);
    assert_eq!(doubled.len(), 3);
}
