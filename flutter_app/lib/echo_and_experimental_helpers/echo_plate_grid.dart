import 'package:flutter/material.dart';
import '../crisscross_core/slats.dart';
import 'echo_plate_constants.dart';
import 'echo_plate_painters.dart';
import 'echo_plate_well.dart';
import 'plate_layout_state.dart' show PlateLayoutState, WellConfig, baseSlatId;

// ---------------------------------------------------------------------------
// PlateGrid — renders one 96-well plate with chamfered borders
// ---------------------------------------------------------------------------

class PlateGrid extends StatelessWidget {
  final int plateIndex;
  final Map<String, String?> assignments;
  final Map<String, Slat> slats;
  final Map<String, Map<String, dynamic>> layerMap;
  final void Function(int fromPlate, String fromWell, int toPlate, String toWell) onWellToWell;
  final void Function(String slatId, int toPlate, String toWell) onSidebarToWell;
  final GlobalKey<WellWidgetState> Function(int plate, String well) wellKeyFor;
  final Set<String> selectedWells;
  final void Function(int plate, String well) onWellClick;
  final void Function(int plate, String well) onWellRightClick;
  final bool isGroupDragging;
  final void Function(int plate, String well) onGroupDragStart;
  final void Function(int plate, String well) onGroupDragHover;
  final ({bool isValid, String? ghostSlatId})? Function(int plate, String well) ghostStateFor;
  final bool Function(int plate, String well) isSourceWellDuringGroupDrag;
  final PlateLayoutState layoutState;
  final VoidCallback? onRemovePlate;
  final String plateName;
  final int plateDisplayNumber;
  final VoidCallback? onRenamePlate;
  final VoidCallback? onConfigPlate;
  final bool showMetricView;
  final Map<String, WellConfig>? plateWellConfigs;

  const PlateGrid({
    super.key,
    required this.plateIndex,
    required this.assignments,
    required this.slats,
    required this.layerMap,
    required this.onWellToWell,
    required this.onSidebarToWell,
    required this.wellKeyFor,
    required this.selectedWells,
    required this.onWellClick,
    required this.onWellRightClick,
    required this.isGroupDragging,
    required this.onGroupDragStart,
    required this.onGroupDragHover,
    required this.ghostStateFor,
    required this.isSourceWellDuringGroupDrag,
    required this.layoutState,
    required this.plateName,
    required this.plateDisplayNumber,
    this.onRemovePlate,
    this.onRenamePlate,
    this.onConfigPlate,
    this.showMetricView = false,
    this.plateWellConfigs,
  });

  @override
  Widget build(BuildContext context) {
    const plateContentWidth = echoHeaderCellSize + (echoWellWidth * 12) + 16;
    const plateContentHeight = echoHeaderCellSize + (echoWellHeight * 8) + 16;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                plateName,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(width: 4),
              Text(
                '($plateDisplayNumber)',
                style: TextStyle(fontSize: 13, color: Colors.grey.shade500),
              ),
              if (onRenamePlate != null) ...[
                const SizedBox(width: 4),
                _HoverableIconButton(onTap: onRenamePlate!, icon: Icons.edit, hoverColor: Colors.blue),
              ],
              if (onConfigPlate != null) ...[
                const SizedBox(width: 4),
                _HoverableIconButton(onTap: onConfigPlate!, icon: Icons.tune, hoverColor: Colors.teal.shade700),
              ],
              if (onRemovePlate != null) ...[
                const SizedBox(width: 4),
                _HoverableIconButton(onTap: onRemovePlate!, icon: Icons.close, hoverColor: Colors.red),
              ],
            ],
          ),
        ),
        SizedBox(
          width: plateContentWidth,
          height: plateContentHeight,
          child: CustomPaint(
            foregroundPainter: PlateBorderPainter(color: Colors.grey.shade600, strokeWidth: 2),
            child: ClipPath(
              clipper: PlateChamferClipper(),
              child: Container(
                color: Colors.white,
                padding: const EdgeInsets.all(8),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Column headers row
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const SizedBox(width: echoHeaderCellSize),
                        for (var col in plateCols)
                          SizedBox(
                            width: echoWellWidth,
                            height: echoHeaderCellSize,
                            child: Center(
                              child: Text('$col',
                                  style:
                                      TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
                            ),
                          ),
                      ],
                    ),
                    // Plate rows
                    for (var row in plateRows)
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: echoHeaderCellSize,
                            height: echoWellHeight,
                            child: Center(
                              child: Text(row,
                                  style:
                                      TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
                            ),
                          ),
                          for (var col in plateCols) _buildWell(row, col),
                        ],
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildWell(String row, int col) {
    final well = '$row$col';
    final slatId = assignments[well];
    // For duplicates, look up the real Slat using the base ID
    final lookupId = slatId != null ? baseSlatId(slatId) : null;
    final slat = lookupId != null ? slats[lookupId] : null;
    final wellKey = '$plateIndex:$well';
    final isSelected = selectedWells.contains(wellKey);
    final ghostState = ghostStateFor(plateIndex, well);
    final isSource = isSourceWellDuringGroupDrag(plateIndex, well);
    final color = designColorFor(slat, layerMap);
    final isInDupGroup = slatId != null && layoutState.duplicateGroups.containsKey(baseSlatId(slatId));
    final displayName = slat != null ? slatDisplayName(slat, layerMap) : null;

    return WellWidget(
      key: wellKeyFor(plateIndex, well),
      wellName: well,
      slatId: slatId,
      displayName: displayName,
      slat: slat,
      plateIndex: plateIndex,
      designColor: color,
      isSelected: isSelected,
      ghostState: ghostState,
      isDimmedSource: isSource && isGroupDragging,
      isInDuplicateGroup: isInDupGroup,
      showMetricView: showMetricView,
      wellConfig: plateWellConfigs?[well],
      slatType: slat?.slatType,
      onWellToWell: onWellToWell,
      onSidebarToWell: onSidebarToWell,
      onWellClick: () => onWellClick(plateIndex, well),
      onRightClick: () => onWellRightClick(plateIndex, well),
      isGroupDragging: isGroupDragging,
      onGroupDragStart: () => onGroupDragStart(plateIndex, well),
      onGroupDragHover: () => onGroupDragHover(plateIndex, well),
    );
  }
}

class _HoverableIconButton extends StatefulWidget {
  final VoidCallback onTap;
  final IconData icon;
  final Color hoverColor;
  const _HoverableIconButton({required this.onTap, required this.icon, required this.hoverColor});

  @override
  State<_HoverableIconButton> createState() => _HoverableIconButtonState();
}

class _HoverableIconButtonState extends State<_HoverableIconButton> {
  bool _hovering = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hovering = true),
      onExit: (_) => setState(() => _hovering = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: Padding(
          padding: const EdgeInsets.all(2),
          child: Icon(widget.icon, size: 16, color: _hovering ? widget.hoverColor : Colors.grey.shade400),
        ),
      ),
    );
  }
}
