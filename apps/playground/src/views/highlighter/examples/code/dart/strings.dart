String greeting(String name, List<String> tags) => '''
Hello, $name 🌌
Tags: ${tags.map((tag) => tag.toUpperCase()).join(', ')}
Count: ${tags.length}
''';

void main() {
  final path = r'C:\documents\new';
  final pattern = RegExp(r'^[a-z][a-z0-9_]*$');
  const example = r'''{
  "name": "$literal",
  "comment": "// stays inside the string"
}''';

  print(greeting('Virgo', ['design', 'docs']));
  print('$path / ${pattern.hasMatch('virgo_docs')}');
  print(example);
}
