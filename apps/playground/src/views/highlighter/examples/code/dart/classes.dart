mixin Named {
  String get name;
  String describe() => 'Item: $name';
}

class Catalog<T extends Object> with Named {
  @override
  final String name;
  final List<T> _items;

  Catalog(this.name, Iterable<T> items) : _items = List.of(items);

  factory Catalog.empty(String name) => Catalog(name, <T>[]);

  int get length => _items.length;
  T operator [](int index) => _items[index];
  void add(T value) => _items.add(value);
}

extension CleanLabel on String {
  String get label => trim().toUpperCase();
}

void main() {
  final catalog = Catalog<String>.empty('Virgo')
    ..add('Design')
    ..add('Cloud Docs');
  print('${catalog.describe()}: ${catalog[0].label}');
}
