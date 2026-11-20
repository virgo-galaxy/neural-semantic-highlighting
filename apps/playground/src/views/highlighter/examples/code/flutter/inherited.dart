import 'package:flutter/material.dart';

class CounterScope extends InheritedNotifier<ValueNotifier<int>> {
  const CounterScope({
    super.key,
    required ValueNotifier<int> counter,
    required super.child,
  }) : super(notifier: counter);

  static ValueNotifier<int> of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<CounterScope>()!.notifier!;
}

class CounterControls extends StatelessWidget {
  const CounterControls({super.key});

  @override
  Widget build(BuildContext context) {
    final counter = CounterScope.of(context);
    return ValueListenableBuilder<int>(
      valueListenable: counter,
      builder: (context, value, child) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('Count: $value'),
          IconButton(
            onPressed: () => counter.value++,
            icon: const Icon(Icons.add),
          ),
        ],
      ),
    );
  }
}
