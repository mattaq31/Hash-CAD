import 'package:flutter/material.dart';

class StatusIndicator extends StatelessWidget {
  final List<String> lines;
  final Widget? additionalContent;

  const StatusIndicator({super.key, required this.lines, this.additionalContent});

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
        child: Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                for (final line in lines)
                  Text(
                    line,
                    textAlign: TextAlign.right,
                    style: textStyle,
                  ),
              ],
            ),
            if (additionalContent != null) ...[
              const SizedBox(width: 12),
              additionalContent!,
            ],
          ],
        ),
      ),
    );
  }
}
