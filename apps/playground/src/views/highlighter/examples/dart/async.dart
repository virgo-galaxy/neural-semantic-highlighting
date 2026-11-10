import 'dart:async';

Future<String> loadTitle(int id) async {
  await Future<void>.delayed(const Duration(milliseconds: 20));
  return 'Document $id';
}

Stream<String> titles(List<int> ids) async* {
  for (final id in ids) {
    yield await loadTitle(id);
  }
}

Future<void> main() async {
  try {
    await for (final title in titles([1, 2, 3])) {
      print(title);
    }
  } on TimeoutException catch (error, stack) {
    print('Timed out: $error\n$stack');
  } finally {
    print('Finished');
  }
}
