// Dialog for marking handle positions as manual (pipetted by human, not Echo).
//
// Displays a simplified tube-style slat view with H5 and H2 rows (32 positions each).
// Users toggle positions to mark them as manual. Applied to all currently selected slats.
// When a single slat is selected, buttons are colored by handle category, cargo positions show
// the cargo's short name, and hovering a position shows its handle details beneath the view.
// An 'Export Handle Sequences' button (top right) exports all handles of the selected slats to Excel.
import 'package:flutter/material.dart';
import '../crisscross_core/cargo.dart';
import '../graphics/handle_sequence_text.dart';
import 'echo_barcode_painter.dart';
import 'echo_category_colors.dart';

/// Shows the manual handle marking dialog and returns the selected positions.
///
/// Returns null if the user cancels, otherwise the set of (helix, position) tuples
/// representing manual handles.
///
/// When [h5Handles] and [h2Handles] are provided (single-slat mode), buttons are
/// colored by their handle category. When [multipleSlatsSelected] is true, coloring
/// is disabled and a warning is shown. [cargoPalette] supplies the short names shown on cargo positions.
/// [onExportHandleSequences], if provided, is triggered by the top-right export button (dialog stays open) and
/// receives the dialog's current (possibly unapplied) manual positions.
Future<Set<(int, int)>?> showManualHandleDialog(
  BuildContext context, {
  required Set<(int, int)> currentManualPositions,
  required bool mixedConfig,
  int maxLength = 32,
  Map<int, Map<String, dynamic>>? h5Handles,
  Map<int, Map<String, dynamic>>? h2Handles,
  bool multipleSlatsSelected = false,
  String? slatName,
  Map<String, Cargo>? cargoPalette,
  void Function(Set<(int, int)> pendingManualPositions)? onExportHandleSequences,
}) {
  return showDialog<Set<(int, int)>>(
    context: context,
    builder: (context) => _ManualHandleDialog(
      currentManualPositions: currentManualPositions,
      mixedConfig: mixedConfig,
      maxLength: maxLength,
      h5Handles: h5Handles,
      h2Handles: h2Handles,
      multipleSlatsSelected: multipleSlatsSelected,
      slatName: slatName,
      cargoPalette: cargoPalette,
      onExportHandleSequences: onExportHandleSequences,
    ),
  );
}

class _ManualHandleDialog extends StatefulWidget {
  final Set<(int, int)> currentManualPositions;
  final bool mixedConfig;
  final int maxLength;
  final Map<int, Map<String, dynamic>>? h5Handles;
  final Map<int, Map<String, dynamic>>? h2Handles;
  final bool multipleSlatsSelected;
  final String? slatName;
  final Map<String, Cargo>? cargoPalette;
  final void Function(Set<(int, int)> pendingManualPositions)? onExportHandleSequences;

  const _ManualHandleDialog({
    required this.currentManualPositions,
    required this.mixedConfig,
    required this.maxLength,
    this.h5Handles,
    this.h2Handles,
    this.multipleSlatsSelected = false,
    this.slatName,
    this.cargoPalette,
    this.onExportHandleSequences,
  });

  @override
  State<_ManualHandleDialog> createState() => _ManualHandleDialogState();
}

class _ManualHandleDialogState extends State<_ManualHandleDialog> {
  late Set<(int, int)> _manualPositions;

  // Last hovered (helix, position); kept after the pointer leaves so its details stay readable/copyable.
  (int, int)? _inspectedPosition;

  @override
  void initState() {
    super.initState();
    _manualPositions = Set<(int, int)>.from(widget.currentManualPositions);
  }

  void _togglePosition(int helix, int position) {
    setState(() {
      final key = (helix, position);
      if (_manualPositions.contains(key)) {
        _manualPositions.remove(key);
      } else {
        _manualPositions.add(key);
      }
    });
  }

  void _selectAllHelix(int helix) {
    setState(() {
      for (var pos = 1; pos <= widget.maxLength; pos++) {
        _manualPositions.add((helix, pos));
      }
    });
  }

  void _clearAllHelix(int helix) {
    setState(() {
      _manualPositions.removeWhere((p) => p.$1 == helix);
    });
  }

  void _clearAll() {
    setState(() => _manualPositions.clear());
  }

  void _selectAll() {
    setState(() {
      for (var pos = 1; pos <= widget.maxLength; pos++) {
        _manualPositions.add((5, pos));
        _manualPositions.add((2, pos));
      }
    });
  }

  /// Whether category coloring is available (single slat with handle data).
  bool get _hasCategoryColoring =>
      !widget.multipleSlatsSelected &&
      widget.h5Handles != null &&
      widget.h2Handles != null;

  /// Records the hovered position so the details bar below the view can display it.
  void _inspectPosition(int helix, int position) {
    if (_inspectedPosition == (helix, position)) return;
    setState(() => _inspectedPosition = (helix, position));
  }

  /// Builds the handle details bar (name, sequence, concentration), formatted like the input plate view.
  Widget _buildInspectedHandleInfo() {
    final infoStyle = TextStyle(fontSize: 12, color: Colors.grey.shade600);
    if (_inspectedPosition == null) {
      return Text('Hover over a position to inspect its handle.', style: infoStyle);
    }
    final (helix, position) = _inspectedPosition!;
    final handle = (helix == 5 ? widget.h5Handles : widget.h2Handles)![position];
    if (handle == null) {
      return Text('H$helix, pos $position: no handle assigned.', style: infoStyle);
    }
    final sequence = handle['sequence'] as String?;
    // Placeholder handles have a value but haven't been matched to a plate, so there is no sequence yet.
    if (sequence == null || sequence.isEmpty) {
      return Text('H$helix, pos $position (${handle['value']}): no sequence assigned — handle not found in any loaded plate.', style: infoStyle);
    }

    final category = HandleBarcodePainter.effectiveCategoryForHandle(handle) ?? '';
    final highlight = plateCategoryDisplayColor(category);
    // FLAT staples have no meaningful handle name, so it is omitted for them (as in the plate view).
    final isFlat = category.toUpperCase() == 'FLAT';
    return CopyableHandleSequenceText(
      sequence: sequence,
      highlight: highlight,
      prefix: [
        const TextSpan(text: 'Selected handle: '),
        TextSpan(text: 'H$helix, pos $position', style: const TextStyle(fontWeight: FontWeight.bold)),
        const TextSpan(text: '  ('),
        if (!isFlat) ...[
          TextSpan(text: '${handle['value']}', style: TextStyle(color: highlight, fontWeight: FontWeight.bold)),
          const TextSpan(text: ', '),
        ],
        TextSpan(text: 'conc ${handle['concentration']} µM, plate ${handle['plate']}, well ${handle['well']}): '),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Container(
        width: 900,
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header — shows slat name or 'Multiple Slats'
            Row(
              children: [
                const Icon(Icons.zoom_in, size: 22, color: Colors.deepPurple),
                const SizedBox(width: 8),
                Text(
                  widget.multipleSlatsSelected
                      ? 'Multiple Slats'
                      : (widget.slatName ?? 'Handle View'),
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                if (widget.onExportHandleSequences != null)
                  ElevatedButton.icon(
                    onPressed: () => widget.onExportHandleSequences!(Set.of(_manualPositions)),
                    icon: const Icon(Icons.download, size: 16),
                    label: const Text('Export Handle Sequences'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      textStyle: const TextStyle(fontSize: 12),
                    ),
                  ),
              ],
            ),

            // Warning for mixed configs
            if (widget.mixedConfig) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.amber.shade300),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, size: 18, color: Colors.amber.shade800),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'WARNING: NOT ALL SELECTED SLATS HAVE THE SAME MANUAL HANDLE CONFIG',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                            color: Colors.amber.shade900),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // Warning for multiple slats selected (category coloring disabled)
            if (widget.multipleSlatsSelected) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.blue.shade300),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, size: 18, color: Colors.blue.shade800),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Multiple slats selected — handle category coloring is disabled',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600,
                            color: Colors.blue.shade900),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 16),

            // Convenience buttons with descriptor
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text('Manual handle assignment:',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                        color: Colors.grey.shade700)),
                const SizedBox(width: 12),
                _ConvenienceButton(label: 'Select All', onTap: _selectAll),
                const SizedBox(width: 8),
                _ConvenienceButton(label: 'Select All H5', onTap: () => _selectAllHelix(5)),
                const SizedBox(width: 8),
                _ConvenienceButton(label: 'Select All H2', onTap: () => _selectAllHelix(2)),
                const SizedBox(width: 8),
                _ConvenienceButton(label: 'Clear All H5', onTap: () => _clearAllHelix(5)),
                const SizedBox(width: 8),
                _ConvenienceButton(label: 'Clear All H2', onTap: () => _clearAllHelix(2)),
                const SizedBox(width: 8),
                _ConvenienceButton(label: 'Clear All', onTap: _clearAll, color: Colors.red),
              ],
            ),

            const SizedBox(height: 16),

            // H5 row
            _HandleRow(
              label: 'H5',
              helix: 5,
              maxLength: widget.maxLength,
              manualPositions: _manualPositions,
              onToggle: _togglePosition,
              handles: _hasCategoryColoring ? widget.h5Handles : null,
              cargoPalette: widget.cargoPalette,
              inspectedPosition: _inspectedPosition,
              onHover: _hasCategoryColoring ? _inspectPosition : null,
            ),

            const SizedBox(height: 8),

            // H2 row
            _HandleRow(
              label: 'H2',
              helix: 2,
              maxLength: widget.maxLength,
              manualPositions: _manualPositions,
              onToggle: _togglePosition,
              handles: _hasCategoryColoring ? widget.h2Handles : null,
              cargoPalette: widget.cargoPalette,
              inspectedPosition: _inspectedPosition,
              onHover: _hasCategoryColoring ? _inspectPosition : null,
            ),

            // Handle details for the hovered position (single-slat mode only, as handle data is needed)
            if (_hasCategoryColoring) ...[
              const SizedBox(height: 12),
              const Divider(height: 8),
              SizedBox(height: 40, child: Center(child: _buildInspectedHandleInfo())),
            ],

            const SizedBox(height: 20),

            // Action buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(null),
                  child: const Text('Cancel'),
                ),
                const SizedBox(width: 12),
                ElevatedButton(
                  onPressed: () => Navigator.of(context).pop(_manualPositions),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.deepPurple),
                  child: const Text('Apply', style: TextStyle(color: Colors.white)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _HandleRow extends StatelessWidget {
  final String label;
  final int helix;
  final int maxLength;
  final Set<(int, int)> manualPositions;
  final void Function(int helix, int position) onToggle;
  final Map<int, Map<String, dynamic>>? handles;
  final Map<String, Cargo>? cargoPalette;
  final (int, int)? inspectedPosition;
  final void Function(int helix, int position)? onHover;

  const _HandleRow({
    required this.label,
    required this.helix,
    required this.maxLength,
    required this.manualPositions,
    required this.onToggle,
    this.handles,
    this.cargoPalette,
    this.inspectedPosition,
    this.onHover,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 28,
          child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
        ),
        for (var pos = 1; pos <= maxLength; pos++) ...[
          _HandlePositionButton(
            position: pos,
            isManual: manualPositions.contains((helix, pos)),
            onTap: () => onToggle(helix, pos),
            categoryColor: _resolveCategoryColor(pos),
            cargoLabel: _resolveCargoLabel(pos),
            isInspected: inspectedPosition == (helix, pos),
            onHover: onHover == null ? null : () => onHover!(helix, pos),
          ),
        ],
      ],
    );
  }

  /// Resolves the background color for a position based on handle category.
  Color? _resolveCategoryColor(int position) {
    if (handles == null) return null;
    final handle = handles![position];
    if (handle == null) return null;
    final category = HandleBarcodePainter.effectiveCategoryForHandle(handle);
    if (category == null) return null;
    return categoryColor(category);
  }

  /// Returns the cargo short name (as set in the cargo window) for cargo positions, or null otherwise.
  String? _resolveCargoLabel(int position) {
    final handle = handles?[position];
    if (handle == null || handle['category'] != 'CARGO') return null;
    final cargoName = handle['value'].toString();
    return cargoPalette?[cargoName]?.shortName ?? cargoName;
  }
}

class _HandlePositionButton extends StatefulWidget {
  final int position;
  final bool isManual;
  final VoidCallback onTap;
  final Color? categoryColor;
  final String? cargoLabel;
  final bool isInspected;
  final VoidCallback? onHover;

  const _HandlePositionButton({
    required this.position,
    required this.isManual,
    required this.onTap,
    this.categoryColor,
    this.cargoLabel,
    this.isInspected = false,
    this.onHover,
  });

  @override
  State<_HandlePositionButton> createState() => _HandlePositionButtonState();
}

class _HandlePositionButtonState extends State<_HandlePositionButton> {
  bool _hovering = false;

  @override
  Widget build(BuildContext context) {
    // Manual override always uses orange
    final Color bgColor;
    final Color textColor;
    if (widget.isManual) {
      bgColor = Colors.orange.shade300;
      textColor = Colors.orange.shade900;
    } else if (widget.categoryColor != null) {
      bgColor = widget.categoryColor!.withValues(alpha: 0.4);
      textColor = HSLColor.fromColor(widget.categoryColor!).withLightness(0.3).toColor();
    } else {
      bgColor = Colors.grey.shade200;
      textColor = Colors.grey.shade600;
    }

    // The inspected position keeps a purple outline so the details bar can be traced back to it
    final highlighted = _hovering || widget.isInspected;
    final borderColor = highlighted
        ? Colors.deepPurple
        : (widget.isManual ? Colors.orange.shade700 : (widget.categoryColor ?? Colors.grey.shade400));

    return Padding(
      padding: const EdgeInsets.all(1),
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        onEnter: (_) {
          setState(() => _hovering = true);
          widget.onHover?.call();
        },
        onExit: (_) => setState(() => _hovering = false),
        child: GestureDetector(
          onTap: widget.onTap,
          child: Container(
            width: 24,
            height: 30,
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(3),
              border: Border.all(color: borderColor, width: highlighted ? 2 : 1),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '${widget.position}',
                  style: TextStyle(
                    fontSize: 9,
                    color: textColor,
                    fontWeight: widget.isManual ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
                // Cargo short name; scaled down so longer abbreviations still fit the narrow button
                if (widget.cargoLabel != null)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 1),
                    child: FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(widget.cargoLabel!, style: TextStyle(fontSize: 7, fontStyle: FontStyle.italic, color: textColor)),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ConvenienceButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final Color? color;

  const _ConvenienceButton({required this.label, required this.onTap, this.color});

  @override
  Widget build(BuildContext context) {
    final c = color ?? Colors.deepPurple;
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        foregroundColor: c,
        side: BorderSide(color: c.withValues(alpha: 0.5)),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 15),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        textStyle: const TextStyle(fontSize: 11),
      ),
      child: Text(label),
    );
  }
}
