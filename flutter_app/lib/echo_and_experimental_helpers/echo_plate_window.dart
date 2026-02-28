import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../2d_painters/drag_box_painter.dart';
import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import 'echo_plate_bars.dart';
import 'echo_plate_constants.dart';
import 'echo_plate_grid.dart';
import 'echo_plate_pdf_export.dart';
import 'echo_plate_sidebar.dart';
import 'echo_plate_well.dart';
import 'plate_layout_state.dart';
import 'plate_undo_stack.dart';

import 'save_file_web.dart' if (dart.library.io) '../echo_and_experimental_helpers/save_file_desktop.dart';

// ---------------------------------------------------------------------------
// EchoPlateWindow — top-level overlay container
// ---------------------------------------------------------------------------

class EchoPlateWindow extends StatefulWidget {
  const EchoPlateWindow({super.key});

  @override
  State<EchoPlateWindow> createState() => _EchoPlateWindowState();
}

class _EchoPlateWindowState extends State<EchoPlateWindow> {
  PlateLayoutState? _layoutState;
  final PlateUndoStack _undoStack = PlateUndoStack();
  final Map<String, GlobalKey<WellWidgetState>> _wellKeys = {};
  final GlobalKey _rubberBandOverlayKey = GlobalKey();

  // Collapse
  bool _isCollapsed = false;
  bool _isHeaderHovered = false;
  bool _animationComplete = true;

  // Multi-select
  Set<String> _selectedWells = {};
  Offset? _rubberBandStart;
  Offset? _rubberBandCurrent;
  bool _isRubberBanding = false;
  bool _modifierHeld = false;

  // Auto-assign options
  bool _columnsThreeToTenOnly = false;
  bool _overwriteExisting = false;

  // Group drag
  String? _groupDragAnchor;
  List<({int dRow, int dCol})>? _groupDragOffsets;
  ({int plate, String well})? _groupDragHoverWell;

  @override
  void initState() {
    super.initState();
    HardwareKeyboard.instance.addHandler(_handleKeyEvent);
  }

  @override
  void dispose() {
    HardwareKeyboard.instance.removeHandler(_handleKeyEvent);
    super.dispose();
  }

  bool _handleKeyEvent(KeyEvent event) {
    final pressed = HardwareKeyboard.instance.logicalKeysPressed;
    final held = pressed.any((k) =>
        k == LogicalKeyboardKey.metaLeft ||
        k == LogicalKeyboardKey.metaRight ||
        k == LogicalKeyboardKey.controlLeft ||
        k == LogicalKeyboardKey.controlRight);
    if (held != _modifierHeld) {
      setState(() => _modifierHeld = held);
    }

    // Only consume undo/redo/delete when the echo window is active and not collapsed
    final active = _layoutState != null && !_isCollapsed;

    // Delete/Backspace to remove selected wells
    if (event is KeyDownEvent &&
        (event.logicalKey == LogicalKeyboardKey.backspace || event.logicalKey == LogicalKeyboardKey.delete)) {
      if (active && _selectedWells.isNotEmpty) {
        _handleDeleteSelected();
        return true;
      }
    }

    // Undo: Ctrl/Cmd-Z (without Shift)
    if (event is KeyDownEvent && event.logicalKey == LogicalKeyboardKey.keyZ && held) {
      final shiftHeld = pressed.contains(LogicalKeyboardKey.shiftLeft) ||
          pressed.contains(LogicalKeyboardKey.shiftRight);
      if (active) {
        if (shiftHeld) {
          _performRedo();
        } else {
          _performUndo();
        }
        return true;
      }
    }

    // Redo: Ctrl/Cmd-Y
    if (event is KeyDownEvent && event.logicalKey == LogicalKeyboardKey.keyY && held) {
      if (active) {
        _performRedo();
        return true;
      }
    }

    return false;
  }

  GlobalKey<WellWidgetState> _keyFor(int plate, String well) {
    final id = '$plate:$well';
    return _wellKeys.putIfAbsent(id, () => GlobalKey<WellWidgetState>());
  }

  void _initialize(DesignState appState) {
    _layoutState = PlateLayoutState.fromSlats(appState.slats, appState.layerMap);
    _wellKeys.clear();
    _selectedWells = {};
    _groupDragAnchor = null;
    _groupDragOffsets = null;
    _groupDragHoverWell = null;
    _undoStack.clear();
    _undoStack.saveState(_layoutState!);
  }

  void _saveUndoState() {
    _undoStack.saveState(_layoutState!);
  }

  void _performUndo() {
    final restored = _undoStack.undo();
    if (restored != null) {
      setState(() {
        _layoutState = restored;
        _selectedWells.clear();
      });
    }
  }

  void _performRedo() {
    final restored = _undoStack.redo();
    if (restored != null) {
      setState(() {
        _layoutState = restored;
        _selectedWells.clear();
      });
    }
  }

  void _handleSidebarToWell(String slatId, int toPlate, String toWell) {
    setState(() {
      _layoutState!.moveSlatFromSidebarToWell(slatId, toPlate, toWell);
    });
    _saveUndoState();
  }

  void _handleWellToSidebar(int fromPlate, String fromWell) {
    setState(() {
      _layoutState!.moveSlatFromWellToSidebar(fromPlate, fromWell);
    });
    _saveUndoState();
  }

  void _handleWellToWell(int fromPlate, String fromWell, int toPlate, String toWell) {
    _keyFor(fromPlate, fromWell).currentState?.triggerFlash(sourceWell: true);
    setState(() {
      _layoutState!.moveSlatBetweenWells(fromPlate, fromWell, toPlate, toWell);
    });
    _saveUndoState();
  }

  void _handleAutoAssign(DesignState appState) {
    setState(() {
      if (_overwriteExisting) {
        _layoutState!.removeAll(appState.slats, appState.layerMap);
      }
      _layoutState!.autoAssign(appState.slats, appState.layerMap, columnsThreeToTenOnly: _columnsThreeToTenOnly);
    });
    _saveUndoState();
  }

  void _handleRemoveAll(DesignState appState) {
    setState(() {
      _layoutState!.removeAll(appState.slats, appState.layerMap);
      _selectedWells.clear();
    });
    _saveUndoState();
  }

  void _handleDeleteSelected() {
    setState(() {
      _layoutState!.removeSelected(_selectedWells);
      _selectedWells.clear();
    });
    _saveUndoState();
  }

  void _handleDuplicateSelected() {
    setState(() {
      final newKeys = _layoutState!.duplicateSlats(_selectedWells);
      _selectedWells = newKeys;
    });
    _saveUndoState();
  }

  void _handleAddPlate() {
    setState(() {
      _layoutState!.addPlate();
    });
    _saveUndoState();
  }

  void _handleRemovePlate(int plateIndex) {
    setState(() {
      // Clear selections that reference this plate or plates that will be renumbered
      _selectedWells.clear();
      _layoutState!.removePlate(plateIndex);
      _wellKeys.clear();
    });
    _saveUndoState();
  }

  void _handleWellRightClick(int plate, String well) {
    final slatId = _layoutState!.plateAssignments[plate]?[well];
    if (slatId == null) return;

    final siblings = _layoutState!.getDuplicateSiblings(slatId);

    // Find all wells containing any sibling across all plates
    final newSelection = <String>{};
    for (var pEntry in _layoutState!.plateAssignments.entries) {
      for (var wEntry in pEntry.value.entries) {
        if (wEntry.value != null && siblings.contains(wEntry.value)) {
          newSelection.add('${pEntry.key}:${wEntry.key}');
        }
      }
    }

    setState(() {
      _selectedWells = newSelection;
    });
  }

  Future<void> _exportPdf(DesignState appState) async {
    final pdfBytes = await buildPlateLayoutPdf(_layoutState!.plateAssignments, appState.slats);
    await saveFileBytes(
      pdfBytes,
      '${appState.designName}_plate_layout.pdf',
      'pdf',
    );
  }

  // --- Selection helpers ---

  void _handleWellClick(int plate, String well) {
    final key = '$plate:$well';
    final isOccupied = _layoutState!.plateAssignments[plate]?[well] != null;
    final isShiftHeld = HardwareKeyboard.instance.logicalKeysPressed.contains(LogicalKeyboardKey.shiftLeft) ||
        HardwareKeyboard.instance.logicalKeysPressed.contains(LogicalKeyboardKey.shiftRight);

    setState(() {
      if (isShiftHeld) {
        if (isOccupied) {
          if (_selectedWells.contains(key)) {
            _selectedWells.remove(key);
          } else {
            _selectedWells.add(key);
          }
        }
      } else {
        _selectedWells.clear();
        if (isOccupied) {
          _selectedWells.add(key);
        }
      }
    });
  }

  void _clearSelection() {
    if (_selectedWells.isNotEmpty) {
      setState(() => _selectedWells.clear());
    }
  }

  // --- Group drag helpers ---

  void _startGroupDrag(int plate, String well) {
    final key = '$plate:$well';
    if (!_selectedWells.contains(key)) return;

    final anchorRow = wellRow(well);
    final anchorCol = wellCol(well);

    final offsets = <({int dRow, int dCol})>[];
    for (var sel in _selectedWells) {
      final parts = sel.split(':');
      final p = int.parse(parts[0]);
      if (p != plate) continue;
      final w = parts[1];
      offsets.add((dRow: wellRow(w) - anchorRow, dCol: wellCol(w) - anchorCol));
    }

    setState(() {
      _groupDragAnchor = key;
      _groupDragOffsets = offsets;
      _groupDragHoverWell = (plate: plate, well: well);
    });
  }

  void _updateGroupDragHover(int plate, String well) {
    final newHover = (plate: plate, well: well);
    if (_groupDragHoverWell != newHover) {
      setState(() => _groupDragHoverWell = newHover);
    }
  }

  void _endGroupDrag(int targetPlate, String targetWell) {
    if (_groupDragAnchor == null || _groupDragOffsets == null) {
      _cancelGroupDrag();
      return;
    }

    final targetRow = wellRow(targetWell);
    final targetCol = wellCol(targetWell);

    final moves = <({int plate, String well}), ({int plate, String well})>{};
    final anchorParts = _groupDragAnchor!.split(':');
    final anchorPlate = int.parse(anchorParts[0]);
    final anchorWell = anchorParts[1];
    final anchorRow = wellRow(anchorWell);
    final anchorCol = wellCol(anchorWell);

    for (var offset in _groupDragOffsets!) {
      final srcRow = anchorRow + offset.dRow;
      final srcCol = anchorCol + offset.dCol;
      final dstRow = targetRow + offset.dRow;
      final dstCol = targetCol + offset.dCol;

      if (dstRow < 0 || dstRow >= 8 || dstCol < 0 || dstCol >= 12) {
        _cancelGroupDrag();
        return;
      }

      moves[(plate: anchorPlate, well: wellName(srcRow, srcCol))] =
          (plate: targetPlate, well: wellName(dstRow, dstCol));
    }

    setState(() {
      _layoutState!.moveGroupToWells(moves);
      for (var target in moves.values) {
        _keyFor(target.plate, target.well).currentState?.triggerFlash();
      }
      for (var source in moves.keys) {
        if (!moves.values.any((t) => t.plate == source.plate && t.well == source.well)) {
          _keyFor(source.plate, source.well).currentState?.triggerFlash(sourceWell: true);
        }
      }
      _selectedWells = moves.values.map((t) => '${t.plate}:${t.well}').toSet();
      _groupDragAnchor = null;
      _groupDragOffsets = null;
      _groupDragHoverWell = null;
    });
    _saveUndoState();
  }

  void _endGroupDragAtCurrentHover() {
    if (_groupDragHoverWell == null) {
      _cancelGroupDrag();
      return;
    }
    _endGroupDrag(_groupDragHoverWell!.plate, _groupDragHoverWell!.well);
  }

  void _cancelGroupDrag() {
    setState(() {
      _groupDragAnchor = null;
      _groupDragOffsets = null;
      _groupDragHoverWell = null;
    });
  }

  ({bool isValid, String? ghostSlatId})? _ghostStateFor(int plate, String well) {
    if (_groupDragAnchor == null || _groupDragOffsets == null || _groupDragHoverWell == null) return null;
    if (plate != _groupDragHoverWell!.plate) return null;

    final hoverRow = wellRow(_groupDragHoverWell!.well);
    final hoverCol = wellCol(_groupDragHoverWell!.well);
    final wellRow_ = wellRow(well);
    final wellCol_ = wellCol(well);

    final anchorParts = _groupDragAnchor!.split(':');
    final anchorPlate = int.parse(anchorParts[0]);
    final anchorWell = anchorParts[1];
    final anchorRow = wellRow(anchorWell);
    final anchorCol = wellCol(anchorWell);

    for (var offset in _groupDragOffsets!) {
      final ghostRow = hoverRow + offset.dRow;
      final ghostCol = hoverCol + offset.dCol;
      if (ghostRow == wellRow_ && ghostCol == wellCol_) {
        bool allValid = true;
        for (var o in _groupDragOffsets!) {
          final r = hoverRow + o.dRow;
          final c = hoverCol + o.dCol;
          if (r < 0 || r >= 8 || c < 0 || c >= 12) {
            allValid = false;
            break;
          }
        }

        final srcRow = anchorRow + offset.dRow;
        final srcCol = anchorCol + offset.dCol;
        final srcWell = wellName(srcRow, srcCol);
        final slatId = _layoutState!.plateAssignments[anchorPlate]?[srcWell];

        return (isValid: allValid, ghostSlatId: slatId);
      }
    }
    return null;
  }

  bool _isSourceWellDuringGroupDrag(int plate, String well) {
    if (_groupDragAnchor == null) return false;
    final anchorPlate = int.parse(_groupDragAnchor!.split(':')[0]);
    if (plate != anchorPlate) return false;
    return _selectedWells.contains('$plate:$well');
  }

  /// During a group drag, only wells on the anchor plate should appear selected.
  Set<String> _effectiveSelectedWells(int plateIndex) {
    if (_groupDragAnchor == null) return _selectedWells;
    final anchorPlate = int.parse(_groupDragAnchor!.split(':')[0]);
    if (plateIndex != anchorPlate) return {};
    return _selectedWells;
  }

  // --- Rubber band selection ---

  void _onRubberBandStart(DragStartDetails details) {
    setState(() {
      _isRubberBanding = true;
      _rubberBandStart = details.localPosition;
      _rubberBandCurrent = details.localPosition;
    });
  }

  void _onRubberBandUpdate(DragUpdateDetails details) {
    if (!_isRubberBanding) return;
    setState(() {
      _rubberBandCurrent = details.localPosition;
      _updateRubberBandSelection();
    });
  }

  void _onRubberBandEnd(DragEndDetails details) {
    if (!_isRubberBanding) return;
    setState(() {
      _isRubberBanding = false;
      _rubberBandStart = null;
      _rubberBandCurrent = null;
    });
  }

  void _updateRubberBandSelection() {
    if (_rubberBandStart == null || _rubberBandCurrent == null) return;
    final bandRect = Rect.fromPoints(_rubberBandStart!, _rubberBandCurrent!);

    final overlayBox = _rubberBandOverlayKey.currentContext?.findRenderObject() as RenderBox?;
    if (overlayBox == null) return;

    final newSelection = <String>{};
    for (var entry in _wellKeys.entries) {
      final key = entry.key;
      final globalKey = entry.value;
      final renderBox = globalKey.currentContext?.findRenderObject() as RenderBox?;
      if (renderBox == null || !renderBox.hasSize) continue;

      final wellSize = renderBox.size;
      final wellCenterGlobal = renderBox.localToGlobal(Offset(wellSize.width / 2, wellSize.height / 2));
      final wellCenterLocal = overlayBox.globalToLocal(wellCenterGlobal);

      if (bandRect.contains(wellCenterLocal)) {
        final parts = key.split(':');
        final plate = int.parse(parts[0]);
        final well = parts[1];
        if (_layoutState!.plateAssignments[plate]?[well] != null) {
          newSelection.add(key);
        }
      }
    }
    _selectedWells = newSelection;
  }

  // --- Build ---

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();

    // Keep undo routing flag in sync: true when echo window owns undo/redo
    actionState.echoPlateUndoActive =
        actionState.echoPlateWindowActive && _layoutState != null && !_isCollapsed;

    if (!actionState.echoPlateWindowActive) {
      // Sync when hidden so state is correct when reopened
      _layoutState?.syncWithDesign(appState.slats, appState.layerMap);
      return const SizedBox.shrink();
    }

    if (_layoutState == null) {
      _initialize(appState);
      actionState.echoPlateUndoActive = true;
    } else {
      // Sync with design on every rebuild (picks up added/removed slats)
      _layoutState!.syncWithDesign(appState.slats, appState.layerMap);
    }

    final screenWidth = MediaQuery.of(context).size.width;
    final screenHeight = MediaQuery.of(context).size.height;
    final fullHeight = screenHeight * 0.8;

    final showContent = !_isCollapsed && _animationComplete;

    return AnimatedPositioned(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      top: 60,
      left: (screenWidth - echoWindowWidth) / 2,
      width: echoWindowWidth,
      height: _isCollapsed ? echoCollapsedHeight : fullHeight,
      onEnd: () {
        setState(() {
          _animationComplete = !_isCollapsed;
        });
      },
      child: Material(
        elevation: 8,
        borderRadius: BorderRadius.circular(12),
        clipBehavior: Clip.antiAlias,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade300),
          ),
          child: Column(
            children: [
              PlateHeaderBar(
                onClose: () => actionState.deactivateEchoPlateWindow(),
                onExport: () => _exportPdf(appState),
                onToggleCollapse: () {
                  setState(() {
                    _isCollapsed = !_isCollapsed;
                    if (_isCollapsed) _animationComplete = false;
                  });
                },
                isHovered: _isHeaderHovered,
                onHoverChanged: (hovered) => setState(() => _isHeaderHovered = hovered),
              ),
              if (showContent) ...[
                PlateActionBar(
                  onRemoveAll: () => _handleRemoveAll(appState),
                  onDeleteSelected: _handleDeleteSelected,
                  onDuplicateSelected: _handleDuplicateSelected,
                  hasSelection: _selectedWells.isNotEmpty,
                ),
                Expanded(
                  child: Row(
                    children: [
                      SlatSidebar(
                        unassignedSlats: _layoutState!.unassignedSlats,
                        slats: appState.slats,
                        layerMap: appState.layerMap,
                        onAutoAssign: () => _handleAutoAssign(appState),
                        onReturnToSidebar: _handleWellToSidebar,
                        columnsThreeToTenOnly: _columnsThreeToTenOnly,
                        onColumnsThreeToTenOnlyChanged: (v) => setState(() => _columnsThreeToTenOnly = v),
                        overwriteExisting: _overwriteExisting,
                        onOverwriteExistingChanged: (v) => setState(() => _overwriteExisting = v),
                      ),
                      const VerticalDivider(width: 1, thickness: 1),
                      Expanded(
                        child: _buildPlateScrollArea(appState),
                      ),
                    ],
                  ),
                ),
                const PlateColorKeyBar(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPlateScrollArea(DesignState appState) {
    return Listener(
      onPointerUp: (_) {
        if (_groupDragAnchor != null) {
          _endGroupDragAtCurrentHover();
        }
      },
      child: Stack(
        children: [
          // Base scroll content with plates
          GestureDetector(
            behavior: HitTestBehavior.translucent,
            onTap: _clearSelection,
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: echoGridPadding, vertical: 12),
              child: Column(
                children: [
                  for (int p = 0; p < _layoutState!.plateAssignments.length; p++) ...[
                    if (p > 0) const SizedBox(height: 20),
                    PlateGrid(
                      plateIndex: p,
                      assignments: _layoutState!.plateAssignments[p]!,
                      slats: appState.slats,
                      layerMap: appState.layerMap,
                      onWellToWell: _handleWellToWell,
                      onSidebarToWell: _handleSidebarToWell,
                      wellKeyFor: _keyFor,
                      selectedWells: _effectiveSelectedWells(p),
                      onWellClick: _handleWellClick,
                      onWellRightClick: _handleWellRightClick,
                      isGroupDragging: _groupDragAnchor != null,
                      onGroupDragStart: _startGroupDrag,
                      onGroupDragHover: _updateGroupDragHover,
                      ghostStateFor: _ghostStateFor,
                      isSourceWellDuringGroupDrag: _isSourceWellDuringGroupDrag,
                      layoutState: _layoutState!,
                      onRemovePlate: _layoutState!.plateAssignments.length > 1
                          ? () => _handleRemovePlate(p)
                          : null,
                    ),
                  ],
                  const SizedBox(height: 16),
                  TextButton.icon(
                    onPressed: _handleAddPlate,
                    icon: Icon(Icons.add, size: 18, color: Colors.blueGrey.shade600),
                    label: Text('Add Plate', style: TextStyle(fontSize: 13, color: Colors.blueGrey.shade600)),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    ),
                  ),
                ],
              ),
            ),
          ),
          // Rubber band gesture overlay — opaque when modifier held or rubber banding,
          // so it captures pan gestures above the wells (including occupied ones)
          if (_modifierHeld || _isRubberBanding)
            Positioned.fill(
              child: GestureDetector(
                key: _rubberBandOverlayKey,
                behavior: HitTestBehavior.opaque,
                onPanStart: _onRubberBandStart,
                onPanUpdate: _onRubberBandUpdate,
                onPanEnd: _onRubberBandEnd,
                child: const SizedBox.expand(),
              ),
            ),
          // Rubber band visual
          if (_isRubberBanding && _rubberBandStart != null && _rubberBandCurrent != null)
            Positioned.fill(
              child: IgnorePointer(
                child: CustomPaint(
                  painter: DragPainter(_rubberBandStart, _rubberBandCurrent, true),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
