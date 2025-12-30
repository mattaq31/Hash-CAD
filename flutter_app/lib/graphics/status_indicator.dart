import 'package:flutter/material.dart';

class StatusIndicator extends StatelessWidget {
  final List<String> lines;

  const StatusIndicator({super.key, required this.lines});

  @override
  Widget build(BuildContext context) {
    final textStyle = Theme.of(context).textTheme.labelMedium?.copyWith(
          fontWeight: FontWeight.w600,
          fontSize: 15,
          fontFeatures: const [
            FontFeature.tabularFigures(),
          ],
        );

    return Material(
      elevation: 3,
      borderRadius: BorderRadius.circular(4),
      color: Theme.of(context).colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            for (final line in lines)
              Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Flexible(
                    child: Text(
                      line,
                      textAlign: TextAlign.right,
                      style: textStyle,
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}