import 'package:flutter/material.dart';
import '../crisscross_core/slats.dart';
import 'echo_barcode_painter.dart';
import 'echo_plate_constants.dart';

// ---------------------------------------------------------------------------
// SlatSidebar — unassigned slats list with auto-assign button
// ---------------------------------------------------------------------------

class SlatSidebar extends StatelessWidget {
  final List<String> unassignedSlats;
  final Map<String, Slat> slats;
  final Map<String, Map<String, dynamic>> layerMap;
  final VoidCallback onAutoAssign;
  final void Function(int fromPlate, String fromWell) onReturnToSidebar;
  final bool columnsThreeToTenOnly;
  final ValueChanged<bool> onColumnsThreeToTenOnlyChanged;
  final bool overwriteExisting;
  final ValueChanged<bool> onOverwriteExistingChanged;
  final bool splitSlatTypes;
  final ValueChanged<bool> onSplitSlatTypesChanged;
  final bool splitSlatLayers;
  final ValueChanged<bool> onSplitSlatLayersChanged;
  final bool splitSlatGroups;
  final bool splitSlatGroupsEnabled;
  final ValueChanged<bool> onSplitSlatGroupsChanged;
  final EchoWellColorMode echoColorMode;
  final Color? Function(String slatId)? resolveGroupColor;
  final Set<String> selectedSlatIds;
  final void Function(String slatId, int index) onSlatTapped;
  final VoidCallback onClearSelection;

  const SlatSidebar({
    super.key,
    required this.unassignedSlats,
    required this.slats,
    required this.layerMap,
    required this.onAutoAssign,
    required this.onReturnToSidebar,
    required this.columnsThreeToTenOnly,
    required this.onColumnsThreeToTenOnlyChanged,
    required this.overwriteExisting,
    required this.onOverwriteExistingChanged,
    required this.splitSlatTypes,
    required this.onSplitSlatTypesChanged,
    required this.splitSlatLayers,
    required this.onSplitSlatLayersChanged,
    required this.splitSlatGroups,
    required this.splitSlatGroupsEnabled,
    required this.onSplitSlatGroupsChanged,
    this.echoColorMode = EchoWellColorMode.natural,
    this.resolveGroupColor,
    this.selectedSlatIds = const {},
    required this.onSlatTapped,
    required this.onClearSelection,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: echoSidebarWidth,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onAutoAssign,
                icon: const Icon(Icons.auto_fix_high, size: 16),
                label: const Text('Auto-Assign', style: TextStyle(fontSize: 12)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueGrey,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(left: 30, right: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: Checkbox(
                    value: columnsThreeToTenOnly,
                    onChanged: (v) => onColumnsThreeToTenOnlyChanged(v ?? false),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  ),
                ),
                const SizedBox(width: 4),
                Text('Center cols', style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
              ],
            ),
          ),
          const SizedBox(height: 2),
          Padding(
            padding: const EdgeInsets.only(left: 30, right: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: Checkbox(
                    value: overwriteExisting,
                    onChanged: (v) => onOverwriteExistingChanged(v ?? false),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  ),
                ),
                const SizedBox(width: 4),
                Text('Overwrite', style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
              ],
            ),
          ),
          const SizedBox(height: 2),
          Padding(
            padding: const EdgeInsets.only(left: 30, right: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: Checkbox(
                    value: splitSlatTypes,
                    onChanged: (v) => onSplitSlatTypesChanged(v ?? false),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  ),
                ),
                const SizedBox(width: 4),
                Text('Split types', style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
              ],
            ),
          ),
          const SizedBox(height: 2),
          Padding(
            padding: const EdgeInsets.only(left: 30, right: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: Checkbox(
                    value: splitSlatLayers,
                    onChanged: (v) => onSplitSlatLayersChanged(v ?? false),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  ),
                ),
                const SizedBox(width: 4),
                Text('Split layers', style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
              ],
            ),
          ),
          const SizedBox(height: 2),
          Padding(
            padding: const EdgeInsets.only(left: 30, right: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: Checkbox(
                    value: splitSlatGroups,
                    onChanged: splitSlatGroupsEnabled ? (v) => onSplitSlatGroupsChanged(v ?? false) : null,
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  ),
                ),
                const SizedBox(width: 4),
                Text('Split groups',
                    style: TextStyle(fontSize: 11, color: splitSlatGroupsEnabled ? Colors.grey.shade700 : Colors.grey.shade400)),
              ],
            ),
          ),
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: Text(
              selectedSlatIds.isEmpty
                  ? '${unassignedSlats.length} unassigned'
                  : '${selectedSlatIds.length} sel. / ${unassignedSlats.length} total',
              style: TextStyle(fontSize: 10, color: selectedSlatIds.isEmpty ? Colors.grey.shade600 : Colors.blue.shade700),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(height: 4),
          Expanded(
            child: DragTarget<Map<String, dynamic>>(
              onWillAcceptWithDetails: (details) {
                return details.data['source'] == 'plate';
              },
              onAcceptWithDetails: (details) {
                final data = details.data;
                onReturnToSidebar(data['plateIndex'] as int, data['wellName'] as String);
              },
              builder: (context, candidateData, rejectedData) {
                final isHovered = candidateData.isNotEmpty;
                return Container(
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  decoration: BoxDecoration(
                    color: isHovered ? Colors.blue.shade50 : Colors.grey.shade50,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: isHovered ? Colors.blue.shade300 : Colors.grey.shade200,
                      width: isHovered ? 2 : 1,
                    ),
                  ),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(4),
                    itemCount: unassignedSlats.length,
                    itemBuilder: (context, index) {
                      final slatId = unassignedSlats[index];
                      final slat = slats[slatId];
                      if (slat == null) return const SizedBox.shrink();
                      final isSelected = selectedSlatIds.contains(slatId);
                      return SidebarSlatTile(
                        slatId: slatId,
                        slat: slat,
                        displayName: slatDisplayName(slat, layerMap),
                        designColor: echoDesignColorFor(slat, layerMap, echoColorMode, resolveGroupColor),
                        isSelected: isSelected,
                        selectedSlatIds: selectedSlatIds,
                        unassignedSlats: unassignedSlats,
                        onTap: () => onSlatTapped(slatId, index),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// SidebarSlatTile — draggable slat tile in the sidebar with multi-select
// ---------------------------------------------------------------------------

class SidebarSlatTile extends StatelessWidget {
  final String slatId;
  final Slat slat;
  final String displayName;
  final Color? designColor;
  final bool isSelected;
  final Set<String> selectedSlatIds;
  final List<String> unassignedSlats;
  final VoidCallback onTap;

  const SidebarSlatTile({
    super.key,
    required this.slatId,
    required this.slat,
    required this.displayName,
    this.designColor,
    this.isSelected = false,
    this.selectedSlatIds = const {},
    this.unassignedSlats = const [],
    required this.onTap,
  });

  Widget _buildTileContent({double opacity = 1.0}) {
    final borderColor = isSelected ? Colors.blue : (designColor ?? Colors.grey.shade300);
    final borderWidth = isSelected ? 2.0 : (designColor != null ? 1.5 : 1.0);
    final bgColor = isSelected ? Colors.blue.shade50 : Colors.white;
    return Opacity(
      opacity: opacity,
      child: Container(
        margin: const EdgeInsets.only(bottom: 3),
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 3),
        decoration: BoxDecoration(
          color: bgColor,
          border: Border.all(color: borderColor, width: borderWidth),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              displayName,
              style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w600),
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
            ),
            const SizedBox(height: 2),
            SizedBox(
              width: double.infinity,
              height: 14,
              child: CustomPaint(
                painter: HandleBarcodePainter(
                  h2Handles: slat.h2Handles,
                  h5Handles: slat.h5Handles,
                  maxLength: slat.maxLength,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // When this tile is selected and part of a multi-selection, drag all selected
    final bool draggingMultiple = isSelected && selectedSlatIds.length > 1;
    final dragSlatIds = draggingMultiple
        ? unassignedSlats.where((id) => selectedSlatIds.contains(id)).toList()
        : [slatId];

    final dragData = <String, dynamic>{
      'source': 'sidebar',
      'slatId': slatId,
      'slatIds': dragSlatIds,
    };

    return GestureDetector(
      onTap: onTap,
      child: Draggable<Map<String, dynamic>>(
        data: dragData,
        feedback: Material(
          elevation: 4,
          borderRadius: BorderRadius.circular(4),
          child: SizedBox(
            width: echoSidebarWidth - 16,
            child: draggingMultiple
                ? Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Opacity(opacity: 0.85, child: _buildTileContent()),
                      Text(
                        '+ ${dragSlatIds.length - 1} more',
                        style: const TextStyle(fontSize: 9, color: Colors.blue, fontWeight: FontWeight.w600),
                      ),
                    ],
                  )
                : Opacity(opacity: 0.85, child: _buildTileContent()),
          ),
        ),
        childWhenDragging: Opacity(opacity: 0.3, child: _buildTileContent()),
        child: _buildTileContent(),
      ),
    );
  }
}
