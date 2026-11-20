import 'package:flutter/material.dart';

class SearchResults extends StatelessWidget {
  final List<({String id, String title})> items;
  final bool loading;
  const SearchResults({super.key, required this.items, this.loading = false});

  @override
  Widget build(BuildContext context) => CustomScrollView(
    slivers: [
      const SliverAppBar(title: Text('Documents'), floating: true),
      if (loading)
        const SliverToBoxAdapter(child: LinearProgressIndicator()),
      SliverList.builder(
        itemCount: items.length,
        itemBuilder: (context, index) {
          final (:id, :title) = items[index];
          return ListTile(
            key: ValueKey(id),
            leading: const Icon(Icons.description),
            title: Text(title),
          );
        },
      ),
    ],
  );
}
