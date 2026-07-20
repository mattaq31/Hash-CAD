// Dialog for editing the per-design fluorophore library.

import 'dart:math';

import 'package:flutter/material.dart';

import '../crisscross_core/fluorophore.dart';

/// Widget mapping for fluorophore shapes.
Widget fluorophoreShapeIcon(FluorophoreShape shape, {double size = 16}) {
  switch (shape) {
    case FluorophoreShape.square:
      return Icon(Icons.square, size: size);
    case FluorophoreShape.dot:
      return Icon(Icons.circle, size: size);
    case FluorophoreShape.diamond:
      return Transform.rotate(
        angle: pi / 4,
        child: Icon(Icons.square, size: size * 0.8),
      );
    case FluorophoreShape.star:
      return SizedBox(
        width: size,
        height: size,
        child: CustomPaint(painter: _FourPointStarPainter()),
      );
  }
}

/// Paints a 4-pointed star matching the 2D canvas rendering.
class _FourPointStarPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final outerRadius = size.width * 0.45;
    final innerRadius = outerRadius * 0.45;
    final paint = Paint()..color = Colors.black..style = PaintingStyle.fill;

    final path = Path();
    for (int j = 0; j < 8; j++) {
      final radius = j.isEven ? outerRadius : innerRadius;
      final angle = (j * pi / 4) - pi / 2;
      final x = center.dx + radius * cos(angle);
      final y = center.dy + radius * sin(angle);
      if (j == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    path.close();
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Result returned from the fluorophore library editor dialog.
class FluorophoreLibraryEditResult {
  /// Final fluorophore palette after all edits are applied.
  final Map<String, Fluorophore> palette;

  /// Mapping of original names to their edited names for existing entries.
  final Map<String, String> renamedNames;

  /// Creates a fluorophore library edit result.
  const FluorophoreLibraryEditResult({required this.palette, this.renamedNames = const {}});
}

class _FluorophoreDraft {
  final String? originalName;
  final TextEditingController controller;
  FluorophoreShape shape;

  _FluorophoreDraft({required String initialName, required this.shape, this.originalName})
      : controller = TextEditingController(text: initialName);

  void dispose() {
    controller.dispose();
  }
}

/// Shows the fluorophore library editor dialog and returns the updated palette.
/// Returns null if the user cancels.
Future<FluorophoreLibraryEditResult?> showFluorophoreLibraryDialog(
    BuildContext context, Map<String, Fluorophore> currentPalette) {
  return showDialog<FluorophoreLibraryEditResult>(
    context: context,
    builder: (ctx) => _FluorophoreLibraryDialog(palette: Map.from(currentPalette)),
  );
}

class _FluorophoreLibraryDialog extends StatefulWidget {
  final Map<String, Fluorophore> palette;

  const _FluorophoreLibraryDialog({required this.palette});

  @override
  State<_FluorophoreLibraryDialog> createState() => _FluorophoreLibraryDialogState();
}

class _FluorophoreLibraryDialogState extends State<_FluorophoreLibraryDialog> {
  late List<_FluorophoreDraft> _entries;
  final _newNameController = TextEditingController();
  FluorophoreShape _newShape = FluorophoreShape.dot;
  String? _validationMessage;

  @override
  void initState() {
    super.initState();
    final sortedEntries = widget.palette.entries.toList()..sort((a, b) => a.key.compareTo(b.key));
    _entries = sortedEntries.map((entry) {
      return _FluorophoreDraft(initialName: entry.key, shape: entry.value.shape, originalName: entry.key);
    }).toList();
  }

  @override
  void dispose() {
    for (var entry in _entries) {
      entry.dispose();
    }
    _newNameController.dispose();
    super.dispose();
  }

  void _addFluorophore() {
    final name = _newNameController.text.trim();
    if (name.isEmpty) {
      setState(() {
        _validationMessage = 'Fluorophore names cannot be blank.';
      });
      return;
    }
    if (_entries.any((entry) => entry.controller.text.trim() == name)) {
      setState(() {
        _validationMessage = 'Fluorophore names must be unique.';
      });
      return;
    }
    setState(() {
      _entries.add(_FluorophoreDraft(initialName: name, shape: _newShape));
      _newNameController.clear();
      _validationMessage = null;
    });
  }

  void _deleteFluorophore(_FluorophoreDraft draft) {
    setState(() {
      _entries.remove(draft);
      draft.dispose();
      _validationMessage = null;
    });
  }

  FluorophoreLibraryEditResult? _buildResult() {
    final palette = <String, Fluorophore>{};
    final renamedNames = <String, String>{};

    for (var entry in _entries) {
      final name = entry.controller.text.trim();
      if (name.isEmpty) {
        setState(() {
          _validationMessage = 'Fluorophore names cannot be blank.';
        });
        return null;
      }
      if (palette.containsKey(name)) {
        setState(() {
          _validationMessage = 'Fluorophore names must be unique.';
        });
        return null;
      }

      palette[name] = Fluorophore(name: name, shape: entry.shape);
      if (entry.originalName != null && entry.originalName != name) {
        renamedNames[entry.originalName!] = name;
      }
    }

    setState(() {
      _validationMessage = null;
    });
    return FluorophoreLibraryEditResult(palette: palette, renamedNames: renamedNames);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Fluorophore Library'),
      content: SizedBox(
        width: 420,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_entries.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Text('No fluorophores defined yet.', style: TextStyle(color: Colors.grey)),
              ),
            if (_entries.isNotEmpty)
              ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 280),
                child: Scrollbar(
                  thumbVisibility: _entries.length > 4,
                  child: ListView.builder(
                    shrinkWrap: true,
                    itemCount: _entries.length,
                    itemBuilder: (context, index) {
                      final entry = _entries[index];
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Row(
                          children: [
                            fluorophoreShapeIcon(entry.shape, size: 20),
                            const SizedBox(width: 8),
                            Expanded(
                              child: TextField(
                                controller: entry.controller,
                                decoration: const InputDecoration(
                                  isDense: true,
                                  contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                                  border: OutlineInputBorder(),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            DropdownButton<FluorophoreShape>(
                              value: entry.shape,
                              underline: const SizedBox(),
                              isDense: true,
                              items: FluorophoreShape.values.map((shape) => DropdownMenuItem(
                                value: shape,
                                child: fluorophoreShapeIcon(shape),
                              )).toList(),
                              onChanged: (shape) {
                                if (shape == null) return;
                                setState(() {
                                  entry.shape = shape;
                                });
                              },
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete, size: 18),
                              onPressed: () => _deleteFluorophore(entry),
                              tooltip: 'Delete',
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ),
            if (_validationMessage != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(_validationMessage!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                ),
              ),
            const Divider(),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _newNameController,
                    decoration: const InputDecoration(
                      hintText: 'New fluorophore name',
                      isDense: true,
                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _addFluorophore(),
                  ),
                ),
                const SizedBox(width: 8),
                DropdownButton<FluorophoreShape>(
                  value: _newShape,
                  underline: const SizedBox(),
                  isDense: true,
                  items: FluorophoreShape.values.map((shape) => DropdownMenuItem(
                    value: shape,
                    child: fluorophoreShapeIcon(shape),
                  )).toList(),
                  onChanged: (shape) {
                    if (shape != null) {
                      setState(() {
                        _newShape = shape;
                      });
                    }
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.add, size: 20),
                  onPressed: _addFluorophore,
                  tooltip: 'Add',
                ),
              ],
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context, null), child: const Text('Cancel')),
        FilledButton(
          onPressed: () {
            final result = _buildResult();
            if (result != null) {
              Navigator.pop(context, result);
            }
          },
          child: const Text('Save'),
        ),
      ],
    );
  }
}
