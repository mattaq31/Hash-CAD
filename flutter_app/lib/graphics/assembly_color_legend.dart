import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import '../app_management/shared_app_state.dart';

/// A single clickable color swatch for the assembly handle legend
class ColorLegendItem extends StatelessWidget {
  final String label;
  final Color color;
  final ValueChanged<Color> onColorChanged;
  final double width;

  const ColorLegendItem({
    super.key,
    required this.label,
    required this.color,
    required this.onColorChanged,
    this.width = 52,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: PopupMenuButton<Color>(
        constraints: const BoxConstraints(minWidth: 200, maxWidth: 780),
        offset: const Offset(0, 40),
        tooltip: '$label (click to change)',
        itemBuilder: (context) {
          return [
            PopupMenuItem(
              enabled: false,
              child: ColorPicker(
                hexInputBar: true,
                pickerColor: color,
                onColorChanged: (newColor) {
                  onColorChanged(newColor);
                },
                pickerAreaHeightPercent: 0.5,
              ),
            ),
          ];
        },
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: color,
                border: Border.all(color: Colors.black54, width: 1),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 3),
            Flexible(
              child: Text(
                label,
                style: const TextStyle(fontSize: 9),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Assembly handle color legend with clickable swatches in a 2x3 grid with reset button on side
class AssemblyColorLegend extends StatelessWidget {
  final DesignState appState;

  const AssemblyColorLegend({super.key, required this.appState});

  @override
  Widget build(BuildContext context) {
    const double itemWidth = 58;

    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Color grid (2 rows x 3 columns)
        Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Row 1: Handle, Phantom, Linked
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                ColorLegendItem(
                  label: '+ Handle',
                  color: appState.assemblyHandleHandleColor,
                  onColorChanged: (color) => appState.setAssemblyHandleColor('handle', color),
                  width: itemWidth,
                ),
                ColorLegendItem(
                  label: '+ Phan.',
                  color: appState.assemblyHandlePhantomColor,
                  onColorChanged: (color) => appState.setAssemblyHandleColor('phantom', color),
                  width: itemWidth,
                ),
                ColorLegendItem(
                  label: 'Linked',
                  color: appState.assemblyHandleLinkedColor,
                  onColorChanged: (color) => appState.setAssemblyHandleColor('linked', color),
                  width: itemWidth,
                ),
              ],
            ),
            const SizedBox(height: 3),
            // Row 2: AntiHandle, PhantomAnti, Blocked
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                ColorLegendItem(
                  label: '- Handle',
                  color: appState.assemblyHandleAntiHandleColor,
                  onColorChanged: (color) => appState.setAssemblyHandleColor('antiHandle', color),
                  width: itemWidth,
                ),
                ColorLegendItem(
                  label: '- Phan.',
                  color: appState.assemblyHandlePhantomAntiColor,
                  onColorChanged: (color) => appState.setAssemblyHandleColor('phantomAnti', color),
                  width: itemWidth,
                ),
                ColorLegendItem(
                  label: 'Blocked',
                  color: appState.assemblyHandleBlockedColor,
                  onColorChanged: (color) => appState.setAssemblyHandleColor('blocked', color),
                  width: itemWidth,
                ),
              ],
            ),
          ],
        ),
        const SizedBox(width: 4),
        // Vertical reset button on the side
        Tooltip(
          message: 'Reset colors to defaults',
          child: Material(
            color: Theme.of(context).colorScheme.primary,
            borderRadius: BorderRadius.circular(3),
            child: InkWell(
              onTap: () => appState.resetAssemblyHandleColors(),
              borderRadius: BorderRadius.circular(3),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 6),
                child: RotatedBox(
                  quarterTurns: 1,
                  child: const Text(
                    'Reset',
                    style: TextStyle(
                      fontSize: 9,
                      color: Colors.white,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
