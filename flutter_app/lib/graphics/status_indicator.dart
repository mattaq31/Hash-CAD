import 'package:flutter/material.dart';

class StatusIndicator extends StatelessWidget {
  final String text;

  const StatusIndicator({required this.text});

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 3,
      borderRadius: BorderRadius.circular(4),
      color: Theme.of(context).colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Text(
          text,
          style: Theme.of(context)
              .textTheme
              .labelMedium
              ?.copyWith(
            fontWeight: FontWeight.w600,
            fontSize: 15,
            fontFeatures: const [
              FontFeature.tabularFigures(),
            ],
          ),
        ),
      ),
    );
  }
}