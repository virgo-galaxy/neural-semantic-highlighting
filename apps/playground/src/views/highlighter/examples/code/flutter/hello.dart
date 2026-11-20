import 'package:flutter/material.dart';

void main() => runApp(const DocumentsApp());

class DocumentsApp extends StatelessWidget {
  const DocumentsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: ThemeData(colorSchemeSeed: Colors.indigo),
      home: Scaffold(
        appBar: AppBar(title: const Text('Virgo Documents')),
        body: const Center(child: DocumentCard(title: 'Getting started')),
      ),
    );
  }
}

class DocumentCard extends StatelessWidget {
  final String title;
  const DocumentCard({super.key, required this.title});

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.description_outlined),
          const SizedBox(height: 12),
          Text(title, style: Theme.of(context).textTheme.titleLarge),
        ],
      ),
    ),
  );
}
