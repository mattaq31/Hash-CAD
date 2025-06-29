import 'package:flutter/material.dart';
import '../app_management/shared_app_state.dart';


class TogglePanel extends StatefulWidget {
  final ActionState actionState;
  const TogglePanel({super.key, required this.actionState});

  @override
  State<TogglePanel> createState() => _TogglePanelState();
}

class _TogglePanelState extends State<TogglePanel> {
  bool showPanel = false;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return AnimatedPositioned(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      bottom: 20,
      left: widget.actionState.isSideBarCollapsed ? 72 + 15 : 72 + 330 + 10,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Always-visible settings button
          FloatingActionButton.small(
            foregroundColor: colorScheme.onPrimary,
            backgroundColor: colorScheme.primary,
            child: Icon(showPanel ? Icons.close : Icons.tune),
            onPressed: () => setState(() => showPanel = !showPanel),
          ),
          const SizedBox(width: 8),

          // Toggle buttons expanding to the right
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 150),
            switchInCurve: Curves.easeOut,
            switchOutCurve: Curves.easeIn,
            transitionBuilder: (child, animation) {
              final offset = Tween<Offset>(
                begin: const Offset(0, 0),
                end: Offset.zero,
              ).animate(animation);

              return SlideTransition(
                position: offset,
                child: FadeTransition(opacity: animation, child: child),
              );
            },
            child: showPanel
                ? Row(
              key: const ValueKey('expanded'),
              children: [
                const SizedBox(width: 8),
                buildFabIcon(
                  icon: Icons.border_inner,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Border',
                  value: widget.actionState.displayBorder,
                  onChanged: widget.actionState.setBorderDisplay,
                ),
                buildFabIcon(
                  icon: Icons.grid_on,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Grid',
                  value: widget.actionState.displayGrid,
                  onChanged: widget.actionState.setGridDisplay,
                ),
                buildFabIcon(
                  icon: Icons.edit_square,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Drawing Aids',
                  value: widget.actionState.drawingAids,
                  onChanged: widget.actionState.setDrawingAidsDisplay,
                ),
                buildFabIcon(
                  icon: Icons.pin,
                  tooltip: 'Slat Coordinates',
                  color: Theme.of(context).colorScheme.primary,
                  value: widget.actionState.slatNumbering,
                  onChanged: widget.actionState.setSlatNumberingDisplay,
                ),
                buildFabIcon(
                  icon: Icons.developer_board,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Assembly Handles',
                  value: widget.actionState.displayAssemblyHandles,
                  onChanged: widget.actionState.setAssemblyHandleDisplay,
                ),
                buildFabIcon(
                  icon: Icons.warehouse,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Cargo Handles',
                  value: widget.actionState.displayCargoHandles,
                  onChanged: widget.actionState.setCargoHandleDisplay,
                ),
                buildFabIcon(
                  icon: Icons.spa,
                  color: Theme.of(context).colorScheme.primary,

                  tooltip: 'Seeds',
                  value: widget.actionState.displaySeeds,
                  onChanged: widget.actionState.setSeedDisplay,
                ),
                buildFabIcon(
                  icon: Icons.label_important,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Slat IDs',
                  value: widget.actionState.displaySlatIDs,
                  onChanged: widget.actionState.setSlatIDDisplay,
                ),
                buildFabIcon(
                  icon: Icons.verified_user,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Plate Validation',
                  value: widget.actionState.plateValidation,
                  onChanged: widget.actionState.setPlateValidation,
                ),
              ],
            )
                : const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }

}

Widget buildFabIcon({
  required IconData icon,
  required String tooltip,
  required bool value,
  required Color color,
  required ValueChanged<bool> onChanged,
}) {
  return Tooltip(
    message: tooltip,
    child: Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FloatingActionButton.small(
        backgroundColor: value
            ? color
            : Colors.grey[300],
        foregroundColor: value ? Colors.white : Colors.black87,
        onPressed: () => onChanged(!value),
        child: Icon(icon),
      ),
    ),
  );
}

Widget buildToggleSwitch({
  required String label,
  required bool value,
  required void Function(bool) onChanged,
}) {
  return Row(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.center,
    children: [
      SizedBox(
        width: 115, // Fixed width for label column
        child: Text(
          label,
          style: const TextStyle(fontSize: 12),
          overflow: TextOverflow.ellipsis,
        ),
      ),
      Transform.scale(
        scale: 0.75,
        child: Switch(
          value: value,
          onChanged: onChanged,
        ),
      ),
    ],
  );
}


Widget buildFreeToggleSwitch({
  required String label,
  required bool value,
  required void Function(bool) onChanged,
}) {
  return Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Text(label, style: const TextStyle(fontSize: 12)),
      Transform.scale(
        scale: 0.75, // Scale down the switch
        child: Switch(
          value: value,
          onChanged: onChanged,
        ),
      ),
    ],
  );
}