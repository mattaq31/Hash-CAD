import 'package:flutter/material.dart';

class ValencyIndicator extends StatelessWidget {
  final int value; // Score: 1 = best, higher = worse (unbounded)
  const ValencyIndicator({super.key, required this.value});

  @override
  Widget build(BuildContext context) {
    final color = _getColor(value);

    return Container(
      width: 60,
      height: 60,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color.withValues(alpha: 0.9),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.5),
            blurRadius: 6,
            spreadRadius: 2,
          ),
        ],
      ),
      alignment: Alignment.center,
      child: Text(
        value.toString(),
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 16,
        ),
      ),
    );
  }

  /// Color transitions from green → orange → red
  Color _getColor(int v) {
    if (v <= 3) return Colors.green;
    if (v <= 5) return Colors.orange;
    if (v <= 7) return Colors.deepOrange;
    return Colors.red;
  }
}