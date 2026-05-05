// Sidebar panel for the slat grouping system.
//
// Provides UI for managing group configurations (independent grouping schemes),
// creating/editing groups, and assigning slats to groups. Works in tandem with
// the "color by group" mode on the 2D/3D canvases.
import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:provider/provider.dart';

import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import '../app_management/design_state_mixins/design_state_grouping_mixin.dart';
import 'layer_manager.dart';

class GroupingTools extends StatefulWidget {
  const GroupingTools({super.key});

  @override
  State<GroupingTools> createState() => _GroupingToolsState();
}

class _GroupingToolsState extends State<GroupingTools> {
  final TextEditingController _groupSizeController = TextEditingController(text: '8');
  // Tracks which group is currently "focused" — persists until another group is selected
  String? _focusedGroupId;

  @override
  void dispose() {
    _groupSizeController.dispose();
    super.dispose();
  }

  /// Dialog for auto-grouping: partitions all slats into groups of N.
  void _showAutoGroupDialog(BuildContext context, DesignState appState, ActionState actionState) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Auto-Group Slats'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Group all slats into groups of:'),
            const SizedBox(height: 12),
            SizedBox(
              width: 80,
              child: TextField(
                controller: _groupSizeController,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.center,
                decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              int? size = int.tryParse(_groupSizeController.text);
              if (size != null && size > 0) {
                appState.autoGroupSlats(size);
                actionState.setSlatColorMode(SlatColorMode.group);
              }
              Navigator.pop(context);
            },
            child: const Text('Group'),
          ),
        ],
      ),
    );
  }

  /// Inline rename dialog for configurations.
  void _showConfigRenameDialog(BuildContext context, DesignState appState, String configId, String currentName) {
    TextEditingController controller = TextEditingController(text: currentName);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Rename Configuration'),
        content: TextField(controller: controller, autofocus: true, decoration: const InputDecoration(border: OutlineInputBorder())),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              if (controller.text.isNotEmpty) appState.renameGroupConfiguration(configId, controller.text);
              Navigator.pop(context);
            },
            child: const Text('Rename'),
          ),
        ],
      ),
    );
  }

  /// Inline rename dialog for groups.
  void _showGroupRenameDialog(BuildContext context, DesignState appState, String groupId, String currentName) {
    TextEditingController controller = TextEditingController(text: currentName);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Rename Group'),
        content: TextField(controller: controller, autofocus: true, decoration: const InputDecoration(border: OutlineInputBorder())),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              if (controller.text.isNotEmpty) appState.renameGroup(groupId, controller.text);
              Navigator.pop(context);
            },
            child: const Text('Rename'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    final colorScheme = Theme.of(context).colorScheme;
    final activeConfig = appState.activeGroupConfig;

    // Clear focused group if it no longer exists in the active config
    if (_focusedGroupId != null && (activeConfig == null || !activeConfig.groups.containsKey(_focusedGroupId))) {
      _focusedGroupId = null;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text("Slat Grouping", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),

        // Configuration selector with scrollbar
        Text("Configurations", style: TextStyle(fontSize: 14, color: Colors.grey.shade600)),
        const SizedBox(height: 6),
        _buildConfigSelector(context, appState),
        const SizedBox(height: 4),

        Divider(thickness: 2, color: Colors.grey.shade300),

        // Group actions (only shown when a configuration is active)
        if (activeConfig != null) ...[
          Text("Group Actions", style: TextStyle(fontSize: 14, color: Colors.grey.shade600)),
          const SizedBox(height: 8),
          ...[
            // Row 1: Group Selected + Update Group
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                FilledButton.icon(
                  onPressed: appState.selectedSlats.isEmpty ? null : () => appState.createGroupFromSelection(),
                  icon: const Icon(Icons.group_add, size: 16),
                  label: const Text("Group Selected"),
                  style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8), textStyle: const TextStyle(fontSize: 13)),
                ),
                const SizedBox(width: 6),
                FilledButton.icon(
                  onPressed: (_focusedGroupId != null && appState.selectedSlats.isNotEmpty && appState.selectedGroupId != _focusedGroupId)
                      ? () => appState.updateGroupToSelection(_focusedGroupId!)
                      : null,
                  icon: const Icon(Icons.update, size: 16),
                  label: const Text("Update Group"),
                  style: FilledButton.styleFrom(
                    backgroundColor: Colors.orange.shade600,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    textStyle: const TextStyle(fontSize: 13),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            // Row 2: Auto-Group + Clear All
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                FilledButton.icon(
                  onPressed: () => _showAutoGroupDialog(context, appState, actionState),
                  icon: const Icon(Icons.auto_awesome, size: 16),
                  label: const Text("Auto-Group"),
                  style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8), textStyle: const TextStyle(fontSize: 13)),
                ),
                const SizedBox(width: 6),
                FilledButton.icon(
                  onPressed: activeConfig.groups.isEmpty ? null : () => appState.clearAllGroups(),
                  icon: const Icon(Icons.clear_all, size: 16),
                  label: const Text("Clear All"),
                  style: FilledButton.styleFrom(
                    backgroundColor: Colors.red.shade400,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    textStyle: const TextStyle(fontSize: 13),
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 8),
          Divider(thickness: 2, color: Colors.grey.shade300),

          // Group list header with count badge
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text("Groups", style: TextStyle(fontSize: 14, color: Colors.grey.shade600)),
              const SizedBox(width: 6),
              if (activeConfig.groups.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(color: colorScheme.primary.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
                  child: Text('${activeConfig.groups.length}', style: TextStyle(fontSize: 12, color: colorScheme.primary, fontWeight: FontWeight.bold)),
                ),
            ],
          ),
          const SizedBox(height: 6),

          // Group list
          if (activeConfig.groups.isEmpty)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text("No groups yet.\nSelect slats and tap 'Group Selected'.", textAlign: TextAlign.center, style: TextStyle(color: Colors.grey.shade500, fontSize: 13)),
            )
          else
            ...activeConfig.groups.values.map((group) => _buildGroupCard(context, appState, group, isHighlighted: _focusedGroupId == group.id)),
        ],

        if (activeConfig == null)
          Padding(
            padding: const EdgeInsets.all(20),
            child: Text("Create a configuration to start grouping slats.", textAlign: TextAlign.center, style: TextStyle(color: Colors.grey.shade500, fontSize: 13)),
          ),

        SizedBox(height: 10),
        Divider(thickness: 2, color: Colors.grey.shade300),
        LayerManagerWidget(
          appState: appState,
          actionState: actionState,
        ),
        SizedBox(height: 10),
        Divider(thickness: 2, color: Colors.grey.shade300),
      ],
    );
  }

  /// Configuration selector: horizontal scrollable chip list with a visible scrollbar.
  /// Each chip shows the config name with a pencil icon (rename) and X icon (delete).
  /// Active config is indicated by color change only (no check mark).
  Widget _buildConfigSelector(BuildContext context, DesignState appState) {
    final scrollController = ScrollController();
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Scrollbar(
              controller: scrollController,
              thumbVisibility: true,
              child: SingleChildScrollView(
                controller: scrollController,
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.only(bottom: 10),
                child: Row(
                  children: [
                    ...appState.groupConfigurations.values.map((config) {
                      bool isActive = config.id == appState.activeGroupConfigId;
                      return Padding(
                        padding: const EdgeInsets.only(right: 4),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            InputChip(
                              label: Text(config.name, style: const TextStyle(fontSize: 12)),
                              showCheckmark: false,
                              selected: isActive,
                              onPressed: () => appState.setActiveGroupConfiguration(config.id),
                              visualDensity: VisualDensity.compact,
                              deleteIcon: const Icon(Icons.close, size: 14),
                              onDeleted: () => appState.deleteGroupConfiguration(config.id),
                            ),
                            // Pencil icon for renaming — separate from chip so it's always tappable
                            InkWell(
                              onTap: () => _showConfigRenameDialog(context, appState, config.id, config.name),
                              borderRadius: BorderRadius.circular(12),
                              child: const Padding(
                                padding: EdgeInsets.all(4),
                                child: Icon(Icons.edit, size: 14),
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ),
          ),
        ),
        IconButton(
          icon: const Icon(Icons.add_circle_outline, size: 20),
          tooltip: 'New Configuration',
          onPressed: () => appState.createGroupConfiguration(),
          visualDensity: VisualDensity.compact,
        ),
      ],
    );
  }

  /// Individual group card with color swatch, name, slat count, and action icons.
  /// Highlighted when the group's slats are currently selected on the canvas.
  Widget _buildGroupCard(BuildContext context, DesignState appState, SlatGroup group, {bool isHighlighted = false}) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 3, horizontal: 2),
      color: isHighlighted ? Colors.blue.shade50 : null,
      shape: isHighlighted
          ? RoundedRectangleBorder(borderRadius: BorderRadius.circular(8), side: BorderSide(color: Colors.blue.shade300, width: 1.5))
          : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 10),
        child: Row(
          children: [
            // Color swatch — opens the full ColorPicker (same as layer colors)
            PopupMenuButton(
              constraints: const BoxConstraints(minWidth: 200, maxWidth: 780),
              offset: const Offset(0, 40),
              itemBuilder: (context) {
                return [
                  PopupMenuItem(
                    child: ColorPicker(
                      hexInputBar: true,
                      pickerColor: group.color,
                      onColorChanged: (color) {
                        appState.recolorGroup(group.id, color);
                      },
                      pickerAreaHeightPercent: 0.5,
                    ),
                  ),
                ];
              },
              child: Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(color: group.color, shape: BoxShape.circle, border: Border.all(color: Colors.grey.shade400, width: 1.5)),
              ),
            ),
            const SizedBox(width: 8),

            // Group name + slat count
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(group.name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                  Text('${group.slatIds.length} slats', style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
                ],
              ),
            ),

            // Rename button
            IconButton(
              icon: const Icon(Icons.edit, size: 16),
              tooltip: 'Rename group',
              onPressed: () => _showGroupRenameDialog(context, appState, group.id, group.name),
              visualDensity: VisualDensity.compact,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            ),

            // Select group slats on canvas and focus this group
            IconButton(
              icon: const Icon(Icons.select_all, size: 18),
              tooltip: 'Select group slats',
              onPressed: () {
                appState.selectGroupSlats(group.id);
                setState(() => _focusedGroupId = group.id);
              },
              visualDensity: VisualDensity.compact,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            ),

            // Delete group
            IconButton(
              icon: Icon(Icons.close, size: 18, color: Colors.red.shade400),
              tooltip: 'Delete group',
              onPressed: () => appState.deleteGroup(group.id),
              visualDensity: VisualDensity.compact,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            ),
          ],
        ),
      ),
    );
  }

}
