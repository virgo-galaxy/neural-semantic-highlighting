import 'package:flutter/material.dart';

class DocumentCard extends StatelessWidget {
  final String title;
  final VoidCallback onOpen;

  const DocumentCard({
    super.key,
    required this.title,
    required this.onOpen,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            FilledButton(onPressed: onOpen, child: const Text('Open document')),
          ],
        ),
      ),
    );
  }
}
