// Dialog for mass-applying fluorophore assignments across slats matching criteria.
// Follows the same visual style as mass_manual_handle_dialog.dart.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../crisscross_core/slats.dart';
import '../crisscross_core/fluorophore.dart';

/// Result of a mass fluorophore edit operation.
class MassFluorophoreEditResult {
  /// Per-slat handle positions to be affected by the operation.
  final Map<String, Set<(int helix, int position)>> perSlatPositions;
  /// Fluorophore name to assign, or null to clear from affected handles.
  final String? fluorophoreName;
  /// When true, clears all fluorophore assignments in the entire design.
  final bool clearAll;

  const MassFluorophoreEditResult({this.perSlatPositions = const {}, this.fluorophoreName, this.clearAll = false});
}

/// Shows the mass fluorophore edit dialog.
Future<MassFluorophoreEditResult?> showMassFluorophoreDialog(
  BuildContext context, {
  required Map<String, Slat> slats,
  required Map<String, Fluorophore> fluorophorePalette,
  required String? activeFluorophore,
}) {
  return showDialog<MassFluorophoreEditResult>(
    context: context,
    builder: (context) => _MassFluorophoreDialog(
      slats: slats,
      fluorophorePalette: fluorophorePalette,
      activeFluorophore: activeFluorophore,
    ),
  );
}

enum _FluorophoreEditMode { byPosition, byHandleValue }

class _MassFluorophoreDialog extends StatefulWidget {
  final Map<String, Slat> slats;
  final Map<String, Fluorophore> fluorophorePalette;
  final String? activeFluorophore;

  const _MassFluorophoreDialog({required this.slats, required this.fluorophorePalette, required this.activeFluorophore});

  @override
  State<_MassFluorophoreDialog> createState() => _MassFluorophoreDialogState();
}

class _MassFluorophoreDialogState extends State<_MassFluorophoreDialog> {
  _FluorophoreEditMode _mode = _FluorophoreEditMode.byPosition;
  bool _clearAllPending = false;

  // By position mode
  int _selectedHelix = 5;
  int _selectedPosition = 1;
  String _selectedSlatType = 'all';

  // By handle value mode
  String? _selectedHandleValue;
  int _valueHelix = 5;
  bool _allPositions = true;
  int _valuePosition = 1;

  late List<String> _availableSlatTypes;
  late List<String> _availableHandleValues;

  @override
  void initState() {
    super.initState();
    _availableSlatTypes = _computeAvailableSlatTypes();
    _availableHandleValues = _computeAvailableHandleValues();
    if (_availableHandleValues.isNotEmpty) {
      _selectedHandleValue = _availableHandleValues.first;
    }
  }

  List<String> _computeAvailableSlatTypes() {
    final types = <String>{};
    for (var slat in _nonPhantomSlats()) {
      types.add(slat.slatType);
    }
    return types.toList()..sort();
  }

  List<String> _computeAvailableHandleValues() {
    final values = <String>{};
    for (var slat in _nonPhantomSlats()) {
      for (var handle in slat.h2Handles.values) {
        if (_isAssemblyHandle(handle) && handle['value'] != null && handle['value'] != '0') {
          values.add(handle['value'] as String);
        }
      }
      for (var handle in slat.h5Handles.values) {
        if (_isAssemblyHandle(handle) && handle['value'] != null && handle['value'] != '0') {
          values.add(handle['value'] as String);
        }
      }
    }
    final sorted = values.toList();
    sorted.sort((a, b) {
      final ia = int.tryParse(a);
      final ib = int.tryParse(b);
      if (ia != null && ib != null) return ia.compareTo(ib);
      return a.compareTo(b);
    });
    return sorted;
  }

  bool _isAssemblyHandle(Map<String, dynamic> handle) {
    final cat = handle['category'] as String?;
    return cat != null && cat.contains('ASSEMBLY');
  }

  Iterable<Slat> _nonPhantomSlats() => widget.slats.values.where((s) => s.phantomParent == null);

  Map<String, Set<(int, int)>> _computeByPositionResult() {
    final result = <String, Set<(int, int)>>{};
    for (var slat in _nonPhantomSlats()) {
      if (_selectedSlatType != 'all' && slat.slatType != _selectedSlatType) continue;
      final handleDict = _selectedHelix == 2 ? slat.h2Handles : slat.h5Handles;
      if (handleDict.containsKey(_selectedPosition)) {
        final handle = handleDict[_selectedPosition]!;
        if (_isAssemblyHandle(handle) && handle['value'] != '0') {
          result.putIfAbsent(slat.id, () => {}).add((_selectedHelix, _selectedPosition));
        }
      }
    }
    return result;
  }

  Map<String, Set<(int, int)>> _computeByHandleValueResult() {
    if (_selectedHandleValue == null) return {};
    final result = <String, Set<(int, int)>>{};
    for (var slat in _nonPhantomSlats()) {
      final handleDict = _valueHelix == 2 ? slat.h2Handles : slat.h5Handles;
      for (var entry in handleDict.entries) {
        if (_isAssemblyHandle(entry.value) &&
            entry.value['value'].toString() == _selectedHandleValue &&
            entry.value['value'] != '0') {
          if (_allPositions || entry.key == _valuePosition) {
            result.putIfAbsent(slat.id, () => {}).add((_valueHelix, entry.key));
          }
        }
      }
    }
    return result;
  }

  int _countAffected() {
    if (_clearAllPending) {
      int count = 0;
      for (var slat in _nonPhantomSlats()) {
        for (var h in slat.h2Handles.values) {
          if (h['fluorophore'] != null) count++;
        }
        for (var h in slat.h5Handles.values) {
          if (h['fluorophore'] != null) count++;
        }
      }
      return count;
    }
    switch (_mode) {
      case _FluorophoreEditMode.byPosition:
        return _computeByPositionResult().values.fold(0, (s, v) => s + v.length);
      case _FluorophoreEditMode.byHandleValue:
        return _computeByHandleValueResult().values.fold(0, (s, v) => s + v.length);
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
            // Title row with Clear All in top-right
            Row(
              children: [
                const Icon(Icons.highlight, size: 22, color: Colors.deepPurple),
                const SizedBox(width: 8),
                const Text('Mass Fluorophore Edit', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const Spacer(),
                TextButton.icon(
                  onPressed: () => setState(() => _clearAllPending = true),
                  icon: Icon(Icons.delete_forever, size: 18, color: Colors.red.shade700),
                  label: Text('Clear All',
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

            // Mode selector (chips)
            Row(
              children: [
                _ModeChip(
                  label: 'By Position',
                  selected: _mode == _FluorophoreEditMode.byPosition,
                  onTap: () => setState(() { _mode = _FluorophoreEditMode.byPosition; _clearAllPending = false; }),
                ),
                const SizedBox(width: 8),
                _ModeChip(
                  label: 'By Assembly Handle Value',
                  selected: _mode == _FluorophoreEditMode.byHandleValue,
                  onTap: () => setState(() { _mode = _FluorophoreEditMode.byHandleValue; _clearAllPending = false; }),
                ),
              ],
            ),
            const SizedBox(height: 16),

            if (!_clearAllPending) ...[
              if (_mode == _FluorophoreEditMode.byPosition) _buildPositionMode(),
              if (_mode == _FluorophoreEditMode.byHandleValue) _buildHandleValueMode(),

              const SizedBox(height: 16),
              // Info box
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
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            affected > 0
                                ? '$affected handle${affected == 1 ? '' : 's'} will be affected'
                                : 'No handles match the current criteria',
                            style: TextStyle(fontSize: 12,
                                color: affected > 0 ? Colors.deepPurple.shade700 : Colors.grey.shade600),
                          ),
                          if (widget.activeFluorophore != null)
                            Text('Assigning: ${widget.activeFluorophore}',
                                style: TextStyle(fontSize: 11, color: Colors.deepPurple.shade500)),
                          if (widget.activeFluorophore == null)
                            Text('No fluorophore selected — will clear from affected handles.',
                                style: TextStyle(fontSize: 11, color: Colors.orange.shade700)),
                        ],
                      ),
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
                    Expanded(
                      child: Text('All fluorophore assignments will be cleared ($affected tagged handle${affected == 1 ? '' : 's'}).',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.red.shade700)),
                    ),
                  ],
                ),
              ),
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
                  onPressed: (_clearAllPending || affected > 0) ? () {
                    if (_clearAllPending) {
                      Navigator.of(context).pop(const MassFluorophoreEditResult(clearAll: true));
                    } else {
                      final MassFluorophoreEditResult result;
                      switch (_mode) {
                        case _FluorophoreEditMode.byPosition:
                          result = MassFluorophoreEditResult(
                            perSlatPositions: _computeByPositionResult(),
                            fluorophoreName: widget.activeFluorophore,
                          );
                        case _FluorophoreEditMode.byHandleValue:
                          result = MassFluorophoreEditResult(
                            perSlatPositions: _computeByHandleValueResult(),
                            fluorophoreName: widget.activeFluorophore,
                          );
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
        Text('Assign fluorophore to a specific position across all matching slats.',
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
            // Position spinner
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

  Widget _buildHandleValueMode() {
    if (_availableHandleValues.isEmpty) {
      return Text('No assembly handle values found.',
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Assign fluorophore to positions with a specific assembly handle value.',
            style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
        const SizedBox(height: 12),
        Row(
          children: [
            // Handle value spinner
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

/// Mode chip matching the mass manual handle dialog style.
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

/// Numeric spinner with up/down arrows matching the mass manual handle dialog style.
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

/// Spinner for cycling through a list of string values.
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
