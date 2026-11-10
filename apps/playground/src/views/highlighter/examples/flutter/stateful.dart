import 'package:flutter/material.dart';

class Counter extends StatefulWidget {
  final int initial;
  const Counter({super.key, this.initial = 0});

  @override
  State<Counter> createState() => _CounterState();
}

class _CounterState extends State<Counter> {
  late int count;

  @override
  void initState() {
    super.initState();
    count = widget.initial;
  }

  void increment() => setState(() => count++);

  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Text('Count: $count'),
      IconButton(onPressed: increment, icon: const Icon(Icons.add)),
    ],
  );
}
