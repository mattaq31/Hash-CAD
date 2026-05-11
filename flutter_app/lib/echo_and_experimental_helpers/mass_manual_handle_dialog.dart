// Dialog for mass-applying manual handle markings across all slats matching a criteria.
//
// Mode 1: By position + side + slat type — marks a specific position/side combo as manual
// for all slats of the given type.
// Mode 2: By assembly handle value + position — marks all positions with a specific handle
// value as manual.
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../crisscross_core/slats.dart';
import 'plate_layout_state.dart' show PlateLayoutState, baseSlatId;

/// Result of a mass manual edit operation.
class MassManualEditResult {
  /// Per-slat positions to mark as manual — each slat gets only the positions relevant to it.
  final Map<String, Set<(int helix, int position)>> perSlatPositions;
  final bool clearAll;

  const MassManualEditResult({this.perSlatPositions = const {}, this.clearAll = false});
}

/// Shows the mass manual edit dialog.
///
/// Returns null if cancelled, otherwise a result describing what to apply.
Future<MassManualEditResult?> showMassManualHandleDialog(
  BuildContext context, {
  required Map<String, Slat> slats,
  required PlateLayoutState layoutState,
}) {
  return showDialog<MassManualEditResult>(
    context: context,
    builder: (context) => _MassManualHandleDialog(slats: slats, layoutState: layoutState),
  );
}

class _MassManualHandleDialog extends StatefulWidget {
  final Map<String, Slat> slats;
  final PlateLayoutState layoutState;

  const _MassManualHandleDialog({required this.slats, required this.layoutState});

  @override
  State<_MassManualHandleDialog> createState() => _MassManualHandleDialogState();
}

enum _MassEditMode { byPosition, byAssemblyHandleValue, byCargoValue }

class _MassManualHandleDialogState extends State<_MassManualHandleDialog> {
  _MassEditMode _mode = _MassEditMode.byPosition;
  bool _clearAllPending = false;

  // Mode 1: By position
  int _selectedHelix = 5;
  int _selectedPosition = 1;
  String _selectedSlatType = 'all';

  // Mode 2: By assembly handle value
  String? _selectedHandleValue;
  int _valueHelix = 5;
  int _valuePosition = 1;
  bool _allPositions = true;

  // Mode 3: By cargo value
  String? _selectedCargoValue;

  late List<String> _availableSlatTypes;
  late List<String> _availableHandleValues;
  late List<String> _availableCargoValues;

  @override
  void initState() {
    super.initState();
    _availableSlatTypes = _computeAvailableSlatTypes();
    _availableHandleValues = _computeAvailableHandleValues();
    _availableCargoValues = _computeAvailableCargoValues();
    if (_availableHandleValues.isNotEmpty) {
      _selectedHandleValue = _availableHandleValues.first;
    }
    if (_availableCargoValues.isNotEmpty) {
      _selectedCargoValue = _availableCargoValues.first;
    }
  }

  List<String> _computeAvailableSlatTypes() {
    final types = <String>{};
    for (var slat in _allAssignedSlats()) {
      types.add(slat.slatType);
    }
    return types.toList()..sort();
  }

  /// Collects unique handle values from assigned slats matching a category predicate.
  List<String> _collectHandleValues(bool Function(Map<String, dynamic>) predicate, {bool numericSort = false}) {
    final values = <String>{};
    for (var slat in _allAssignedSlats()) {
      for (var handle in slat.h2Handles.values) {
        if (predicate(handle) && handle['value'] != null && handle['value'] != '0') {
          values.add(handle['value'] as String);
        }
      }
      for (var handle in slat.h5Handles.values) {
        if (predicate(handle) && handle['value'] != null && handle['value'] != '0') {
          values.add(handle['value'] as String);
        }
      }
    }
    final sorted = values.toList();
    if (numericSort) {
      sorted.sort((a, b) {
        final ia = int.tryParse(a);
        final ib = int.tryParse(b);
        if (ia != null && ib != null) return ia.compareTo(ib);
        return a.compareTo(b);
      });
    } else {
      sorted.sort();
    }
    return sorted;
  }

  List<String> _computeAvailableHandleValues() => _collectHandleValues(_isAssemblyHandle, numericSort: true);

  List<String> _computeAvailableCargoValues() => _collectHandleValues(_isCargoHandle);

  bool _isAssemblyHandle(Map<String, dynamic> handle) {
    final cat = handle['category'] as String?;
    return cat != null && cat.contains('ASSEMBLY');
  }

  bool _isCargoHandle(Map<String, dynamic> handle) {
    final cat = handle['category'] as String?;
    return cat == 'CARGO';
  }

  /// All unique non-phantom slats currently assigned to plates (deduplicated by base ID).
  Iterable<(String, Slat)> _uniqueAssignedSlats() sync* {
    final seen = <String>{};
    for (var plateMap in widget.layoutState.plateAssignments.values) {
      for (var slatId in plateMap.values) {
        if (slatId == null) continue;
        final base = baseSlatId(slatId);
        if (!seen.add(base)) continue;
        final slat = widget.slats[base];
        if (slat != null) yield (base, slat);
      }
    }
  }

  /// Convenience: yields just the Slat objects (used by value-collection helpers).
  Iterable<Slat> _allAssignedSlats() => _uniqueAssignedSlats().map((e) => e.$2);

  /// Computes the result for Mode 1: by position/side/slat type.
  MassManualEditResult? _computeByPositionResult() {
    final perSlat = <String, Set<(int, int)>>{};
    final pos = {(_selectedHelix, _selectedPosition)};
    for (var (base, slat) in _uniqueAssignedSlats()) {
      if (_selectedSlatType != 'all' && slat.slatType != _selectedSlatType) continue;
      perSlat[base] = pos;
    }
    if (perSlat.isEmpty) return null;
    return MassManualEditResult(perSlatPositions: perSlat);
  }

  /// Computes the result for Mode 2: by assembly handle value + position.
  MassManualEditResult? _computeByHandleValueResult() {
    if (_selectedHandleValue == null) return null;

    final perSlat = <String, Set<(int, int)>>{};

    for (var (base, slat) in _uniqueAssignedSlats()) {
      final slatPositions = <(int, int)>{};
      final handles = _valueHelix == 2 ? slat.h2Handles : slat.h5Handles;
      if (_allPositions) {
        for (var entry in handles.entries) {
          if (_isAssemblyHandle(entry.value) && entry.value['value'] == _selectedHandleValue) {
            slatPositions.add((_valueHelix, entry.key));
          }
        }
      } else {
        final handle = handles[_valuePosition];
        if (handle != null && _isAssemblyHandle(handle) && handle['value'] == _selectedHandleValue) {
          slatPositions.add((_valueHelix, _valuePosition));
        }
      }
      if (slatPositions.isNotEmpty) perSlat[base] = slatPositions;
    }

    if (perSlat.isEmpty) return null;
    return MassManualEditResult(perSlatPositions: perSlat);
  }

  /// Computes the result for Mode 3: by cargo value (all positions on all sides).
  MassManualEditResult? _computeByCargoValueResult() {
    if (_selectedCargoValue == null) return null;

    final perSlat = <String, Set<(int, int)>>{};

    for (var (base, slat) in _uniqueAssignedSlats()) {
      final slatPositions = <(int, int)>{};
      for (var entry in slat.h2Handles.entries) {
        if (_isCargoHandle(entry.value) && entry.value['value'] == _selectedCargoValue) {
          slatPositions.add((2, entry.key));
        }
      }
      for (var entry in slat.h5Handles.entries) {
        if (_isCargoHandle(entry.value) && entry.value['value'] == _selectedCargoValue) {
          slatPositions.add((5, entry.key));
        }
      }
      if (slatPositions.isNotEmpty) perSlat[base] = slatPositions;
    }

    if (perSlat.isEmpty) return null;
    return MassManualEditResult(perSlatPositions: perSlat);
  }

  int _countAffected() {
    switch (_mode) {
      case _MassEditMode.byPosition:
        return _computeByPositionResult()?.perSlatPositions.length ?? 0;
      case _MassEditMode.byAssemblyHandleValue:
        return _computeByHandleValueResult()?.perSlatPositions.length ?? 0;
      case _MassEditMode.byCargoValue:
        return _computeByCargoValueResult()?.perSlatPositions.length ?? 0;
    }
  }

  @override
  Widget build(BuildContext context) {
    final affected = _countAffected();

    return Dialog(
      child: Container(
        width: 520,
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.auto_fix_high, size: 22, color: Colors.deepPurple),
                const SizedBox(width: 8),
                const Text('Mass Manual Edit', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const Spacer(),
                TextButton.icon(
                  onPressed: () => setState(() => _clearAllPending = true),
                  icon: Icon(Icons.delete_forever, size: 18, color: Colors.red.shade700),
                  label: Text('Clear All Manual Markings',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.red.shade700)),
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Mode selector
            Row(
              children: [
                _ModeChip(
                  label: 'By Position',
                  selected: _mode == _MassEditMode.byPosition,
                  onTap: () => setState(() => _mode = _MassEditMode.byPosition),
                ),
                const SizedBox(width: 8),
                _ModeChip(
                  label: 'By Assembly Handle Value',
                  selected: _mode == _MassEditMode.byAssemblyHandleValue,
                  onTap: () => setState(() => _mode = _MassEditMode.byAssemblyHandleValue),
                ),
                const SizedBox(width: 8),
                _ModeChip(
                  label: 'By Cargo Value',
                  selected: _mode == _MassEditMode.byCargoValue,
                  onTap: () => setState(() => _mode = _MassEditMode.byCargoValue),
                ),
              ],
            ),
            const SizedBox(height: 16),

            if (!_clearAllPending) ...[
              if (_mode == _MassEditMode.byPosition) _buildPositionMode(),
              if (_mode == _MassEditMode.byAssemblyHandleValue) _buildHandleValueMode(),
              if (_mode == _MassEditMode.byCargoValue) _buildCargoValueMode(),

              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: affected > 0 ? Colors.deepPurple.shade50 : Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: affected > 0 ? Colors.deepPurple.shade200 : Colors.grey.shade300),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, size: 16,
                        color: affected > 0 ? Colors.deepPurple.shade700 : Colors.grey.shade600),
                    const SizedBox(width: 8),
                    Text(
                      affected > 0
                          ? '$affected slat${affected == 1 ? '' : 's'} will be affected'
                          : 'No slats match the current criteria',
                      style: TextStyle(fontSize: 12,
                          color: affected > 0 ? Colors.deepPurple.shade700 : Colors.grey.shade600),
                    ),
                  ],
                ),
              ),
            ],
            if (_clearAllPending) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.red.shade300),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, size: 16, color: Colors.red.shade700),
                    const SizedBox(width: 8),
                    Text('All manual handle markings will be cleared.',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.red.shade700)),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(null),
                  child: const Text('Cancel'),
                ),
                const SizedBox(width: 12),
                ElevatedButton(
                  onPressed: (_clearAllPending || affected > 0) ? () {
                    if (_clearAllPending) {
                      Navigator.of(context).pop(const MassManualEditResult(clearAll: true));
                    } else {
                      final MassManualEditResult? result;
                      switch (_mode) {
                        case _MassEditMode.byPosition:
                          result = _computeByPositionResult();
                        case _MassEditMode.byAssemblyHandleValue:
                          result = _computeByHandleValueResult();
                        case _MassEditMode.byCargoValue:
                          result = _computeByCargoValueResult();
                      }
                      Navigator.of(context).pop(result);
                    }
                  } : null,
                  style: ElevatedButton.styleFrom(
                      backgroundColor: _clearAllPending ? Colors.red : Colors.deepPurple),
                  child: Text(_clearAllPending ? 'Confirm Clear' : 'Apply',
                      style: const TextStyle(color: Colors.white)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPositionMode() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Mark a specific position as manual for all matching slats.',
            style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
        const SizedBox(height: 12),
        Row(
          children: [
            // Side selector
            SizedBox(
              width: 80,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Side', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
                  const SizedBox(height: 4),
                  DropdownButton<int>(
                    value: _selectedHelix,
                    isExpanded: true,
                    isDense: true,
                    items: const [
                      DropdownMenuItem(value: 5, child: Text('H5', style: TextStyle(fontSize: 12))),
                      DropdownMenuItem(value: 2, child: Text('H2', style: TextStyle(fontSize: 12))),
                    ],
                    onChanged: (v) => setState(() => _selectedHelix = v!),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 16),
            // Position selector
            _PositionSpinner(
              label: 'Position',
              value: _selectedPosition,
              min: 1,
              max: 32,
              onChanged: (v) => setState(() => _selectedPosition = v),
            ),
            const SizedBox(width: 16),
            // Slat type selector
            SizedBox(
              width: 140,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Slat Type', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
                  const SizedBox(height: 4),
                  DropdownButton<String>(
                    value: _selectedSlatType,
                    isExpanded: true,
                    isDense: true,
                    items: [
                      const DropdownMenuItem(value: 'all', child: Text('All Types', style: TextStyle(fontSize: 12))),
                      for (var t in _availableSlatTypes)
                        DropdownMenuItem(value: t, child: Text(t, style: const TextStyle(fontSize: 12))),
                    ],
                    onChanged: (v) => setState(() => _selectedSlatType = v!),
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildCargoValueMode() {
    if (_availableCargoValues.isEmpty) {
      return Text('No cargo values found in assigned slats.',
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Mark all positions with a specific cargo value as manual (all sides).',
            style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
        const SizedBox(height: 12),
        Row(
          children: [
            SizedBox(
              width: 200,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Cargo Value', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
                  const SizedBox(height: 4),
                  DropdownButton<String>(
                    value: _selectedCargoValue,
                    isExpanded: true,
                    isDense: true,
                    items: [
                      for (var v in _availableCargoValues)
                        DropdownMenuItem(value: v, child: Text(v, style: const TextStyle(fontSize: 12))),
                    ],
                    onChanged: (v) => setState(() => _selectedCargoValue = v),
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildHandleValueMode() {
    if (_availableHandleValues.isEmpty) {
      return Text('No assembly handle values found in assigned slats.',
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Mark positions with a specific assembly handle value as manual.',
            style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
        const SizedBox(height: 12),
        Row(
          children: [
            // Assembly handle value selector
            _ValueSpinner(
              label: 'Assembly Handle Value',
              value: _selectedHandleValue ?? '',
              availableValues: _availableHandleValues,
              onChanged: (v) => setState(() => _selectedHandleValue = v),
            ),
            const SizedBox(width: 16),
            // Side selector
            SizedBox(
              width: 80,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Side', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
                  const SizedBox(height: 4),
                  DropdownButton<int>(
                    value: _valueHelix,
                    isExpanded: true,
                    isDense: true,
                    items: const [
                      DropdownMenuItem(value: 5, child: Text('H5', style: TextStyle(fontSize: 12))),
                      DropdownMenuItem(value: 2, child: Text('H2', style: TextStyle(fontSize: 12))),
                    ],
                    onChanged: (v) => setState(() => _valueHelix = v!),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 16),
            // All positions or specific
            SizedBox(
              width: 160,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Position', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      SizedBox(
                        width: 20,
                        height: 20,
                        child: Checkbox(
                          value: _allPositions,
                          onChanged: (v) => setState(() => _allPositions = v ?? true),
                          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          visualDensity: VisualDensity.compact,
                        ),
                      ),
                      const SizedBox(width: 4),
                      const Text('All', style: TextStyle(fontSize: 11)),
                      const SizedBox(width: 8),
                      if (!_allPositions)
                        _PositionSpinner(
                          value: _valuePosition,
                          min: 1,
                          max: 32,
                          onChanged: (v) => setState(() => _valuePosition = v),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _ModeChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _ModeChip({required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: selected ? Colors.deepPurple.shade50 : Colors.grey.shade100,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: selected ? Colors.deepPurple : Colors.grey.shade300),
        ),
        child: Text(label, style: TextStyle(
          fontSize: 12,
          fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
          color: selected ? Colors.deepPurple : Colors.grey.shade700,
        )),
      ),
    );
  }
}

/// Numeric spinner with up/down arrows and a text input field for position values.
class _PositionSpinner extends StatefulWidget {
  final String? label;
  final int value;
  final int min;
  final int max;
  final ValueChanged<int> onChanged;

  const _PositionSpinner({this.label, required this.value, required this.min, required this.max, required this.onChanged});

  @override
  State<_PositionSpinner> createState() => _PositionSpinnerState();
}

class _PositionSpinnerState extends State<_PositionSpinner> {
  late TextEditingController _controller;
  late FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: '${widget.value}');
    _focusNode = FocusNode();
    _focusNode.addListener(() {
      if (!_focusNode.hasFocus) _commitValue();
    });
  }

  @override
  void didUpdateWidget(_PositionSpinner oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value && !_focusNode.hasFocus) {
      _controller.text = '${widget.value}';
    }
  }

  @override
  void dispose() {
    _focusNode.dispose();
    _controller.dispose();
    super.dispose();
  }

  void _commitValue() {
    final parsed = int.tryParse(_controller.text);
    if (parsed != null && parsed >= widget.min && parsed <= widget.max) {
      widget.onChanged(parsed);
    } else if (parsed != null && parsed < widget.min) {
      widget.onChanged(widget.min);
    } else if (parsed != null && parsed > widget.max) {
      widget.onChanged(widget.max);
    }
    _controller.text = '${widget.value}';
  }

  void _increment() {
    if (widget.value < widget.max) widget.onChanged(widget.value + 1);
    _controller.text = '${widget.value + (widget.value < widget.max ? 1 : 0)}';
  }

  void _decrement() {
    if (widget.value > widget.min) widget.onChanged(widget.value - 1);
    _controller.text = '${widget.value - (widget.value > widget.min ? 1 : 0)}';
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 80,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (widget.label != null)
            Text(widget.label!, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
          if (widget.label != null) const SizedBox(height: 4),
          Row(
            children: [
              SizedBox(
                width: 50,
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  keyboardType: TextInputType.number,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12),
                  decoration: const InputDecoration(
                    contentPadding: EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                    isDense: true,
                    border: OutlineInputBorder(),
                  ),
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  onSubmitted: (_) => _commitValue(),
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _SpinButton(icon: Icons.arrow_drop_up, onTap: _increment),
                  _SpinButton(icon: Icons.arrow_drop_down, onTap: _decrement),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Spinner for cycling through a list of string values (assembly handle values).
class _ValueSpinner extends StatefulWidget {
  final String? label;
  final String value;
  final List<String> availableValues;
  final ValueChanged<String> onChanged;

  const _ValueSpinner({this.label, required this.value, required this.availableValues, required this.onChanged});

  @override
  State<_ValueSpinner> createState() => _ValueSpinnerState();
}

class _ValueSpinnerState extends State<_ValueSpinner> {
  late TextEditingController _controller;
  late FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.value);
    _focusNode = FocusNode();
    _focusNode.addListener(() {
      if (!_focusNode.hasFocus) _commitValue();
    });
  }

  @override
  void didUpdateWidget(_ValueSpinner oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value && !_focusNode.hasFocus) {
      _controller.text = widget.value;
    }
  }

  @override
  void dispose() {
    _focusNode.dispose();
    _controller.dispose();
    super.dispose();
  }

  void _commitValue() {
    final text = _controller.text.trim();
    if (widget.availableValues.contains(text)) {
      widget.onChanged(text);
    } else {
      _controller.text = widget.value;
    }
  }

  void _increment() {
    final idx = widget.availableValues.indexOf(widget.value);
    if (idx < widget.availableValues.length - 1) {
      widget.onChanged(widget.availableValues[idx + 1]);
    }
  }

  void _decrement() {
    final idx = widget.availableValues.indexOf(widget.value);
    if (idx > 0) {
      widget.onChanged(widget.availableValues[idx - 1]);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 150,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (widget.label != null)
            Text(widget.label!, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey.shade700)),
          if (widget.label != null) const SizedBox(height: 4),
          Row(
            children: [
              SizedBox(
                width: 60,
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12),
                  decoration: const InputDecoration(
                    contentPadding: EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                    isDense: true,
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _commitValue(),
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _SpinButton(icon: Icons.arrow_drop_up, onTap: _increment),
                  _SpinButton(icon: Icons.arrow_drop_down, onTap: _decrement),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SpinButton extends StatefulWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _SpinButton({required this.icon, required this.onTap});

  @override
  State<_SpinButton> createState() => _SpinButtonState();
}

class _SpinButtonState extends State<_SpinButton> {
  bool _hovering = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hovering = true),
      onExit: (_) => setState(() => _hovering = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: SizedBox(
          height: 14,
          child: Icon(widget.icon, size: 18, color: _hovering ? Colors.deepPurple : Colors.grey.shade600),
        ),
      ),
    );
  }
}
