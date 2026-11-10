import 'package:flutter/material.dart';

Future<void> openDocument(BuildContext context, String title) async {
  final saved = await Navigator.of(context).push<bool>(
    MaterialPageRoute(
      builder: (context) => DocumentPage(title: title),
    ),
  );
  if (!context.mounted) return;
  if (saved == true) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Document saved')),
    );
  }
}

class DocumentPage extends StatelessWidget {
  final String title;
  const DocumentPage({super.key, required this.title});

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(title)),
    body: Center(
      child: FilledButton(
        onPressed: () => Navigator.of(context).pop(true),
        child: const Text('Save and return'),
      ),
    ),
  );
}
