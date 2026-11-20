import 'dart:math' as math;
import 'package:flutter/material.dart';

class Orbit extends StatefulWidget {
  const Orbit({super.key});
  @override
  State<Orbit> createState() => _OrbitState();
}

class _OrbitState extends State<Orbit> with SingleTickerProviderStateMixin {
  late final AnimationController controller;

  @override
  void initState() {
    super.initState();
    controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat();
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: controller,
    child: const Icon(Icons.auto_awesome),
    builder: (context, child) => Transform.rotate(
      angle: controller.value * math.pi * 2,
      child: child,
    ),
  );
}
