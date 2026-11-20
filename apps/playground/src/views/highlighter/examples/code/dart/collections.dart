List<String> labels(List<String>? items, String? featured) => [
  ?featured,
  ...?items,
  if (items?.isEmpty ?? true) 'Untitled',
  for (final item in items ?? <String>[]) item.trim(),
];

Map<String, int> histogram(Iterable<String> words) {
  final counts = <String, int>{};
  for (final word in words) {
    counts.update(word, (value) => value + 1, ifAbsent: () => 1);
  }
  return counts;
}

void main() {
  final values = labels(['Dart', 'Flutter', 'Dart'], null);
  final counts = histogram(values);
  print({for (final MapEntry(:key, :value) in counts.entries) key: value});
}
