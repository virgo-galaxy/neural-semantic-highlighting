// Bounded modern syntax probes, including Dart 3.13 primary constructors.
class Point(final int x, final int y);

extension type DocumentId(String value) {
  bool get isValid => value.trim().isNotEmpty;
}

enum Status { idle, ready, complete }

class Document {
  final String _name;
  Document({required this._name});
  String get name => _name;
}

void main() {
  final point = Point(3, 5);
  final id = DocumentId('doc_42');
  final document = Document(name: 'Getting started');
  Status status = .ready;

  print('${document.name}: ${id.value}');
  print('(${point.x}, ${point.y}) / $status');
}
