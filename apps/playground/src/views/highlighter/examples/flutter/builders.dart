import 'package:flutter/material.dart';

class DocumentList extends StatelessWidget {
  final Future<List<String>> documents;
  const DocumentList({super.key, required this.documents});

  @override
  Widget build(BuildContext context) => FutureBuilder<List<String>>(
    future: documents,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return const Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return const Text('Unable to load documents');
      }
      final items = snapshot.data ?? <String>[];
      return ListView.builder(
        itemCount: items.length,
        itemBuilder: (context, index) => ListTile(
          key: ValueKey(items[index]),
          title: Text(items[index]),
        ),
      );
    },
  );
}
