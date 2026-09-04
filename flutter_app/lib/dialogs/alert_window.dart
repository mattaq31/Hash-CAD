import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../crisscross_core/handle_plates.dart';
import '../crisscross_core/common_utilities.dart';
import '../app_management/shared_app_state.dart';
import '../echo_and_experimental_helpers/echo_category_colors.dart';


void showWarning(BuildContext context, String title, String message){
  showDialog<String>(
      context: context,
      builder: (BuildContext context) =>
          AlertDialog(
            title: Text(title),
            content: RichText(
              text: TextSpan(
                style: TextStyle(color: Colors.black87, fontSize: 16),
                children: [
                  TextSpan(text: message),
                ],
              ),
            ),
            actions: <Widget>[
              TextButton(
                onPressed: () =>
                    Navigator.pop(context, 'OK'),
                child: const Text('OK'),
              ),
            ],
          ));
}

/// Shows dialog for selecting seed handles with options for group or individual selection.
/// Returns 'group', 'single', or null (if cancelled).
Future<String?> showSeedHandleSelectionDialog(BuildContext context, String seedID) async {
  return showDialog<String>(
    context: context,
    builder: (BuildContext context) => AlertDialog(
      title: Text('Seed Handle Selection'),
      content: RichText(
        text: TextSpan(
          style: TextStyle(color: Colors.black87, fontSize: 16),
          children: [
            TextSpan(text: 'This handle belongs to Seed $seedID. How would you like to proceed?'),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context, 'group'),
          child: const Text('Select all seed handles'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, 'single'),
          child: const Text('Select just this handle'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, null),
          child: const Text('Cancel'),
        ),
      ],
    ),
  );
}

/// Shows dialog for deleting seed handles with options for group or individual deletion.
/// Returns 'group', 'single', or null (if cancelled).
Future<String?> showSeedHandleDeletionDialog(BuildContext context, String seedID) async {
  return showDialog<String>(
    context: context,
    builder: (BuildContext context) => AlertDialog(
      title: Text('Delete Seed Handle'),
      content: RichText(
        text: TextSpan(
          style: TextStyle(color: Colors.black87, fontSize: 16),
          children: [
            TextSpan(text: 'This handle belongs to Seed $seedID. How would you like to proceed?'),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context, 'group'),
          child: const Text('Delete entire seed'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, 'single'),
          child: const Text('Delete just this handle'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, null),
          child: const Text('Cancel'),
        ),
      ],
    ),
  );
}

void showKeyboardShortcutsDialog(BuildContext context) {
  showDialog(
    context: context,
    builder: (context) {
      return AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: Text(
          "Keyboard Shortcuts",
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _shortcutItem("'R'", "Rotate slat draw direction"),
              _shortcutItem("'F'", "Flip multi-slat draw direction"),
              _shortcutItem("'T'", "Transpose slat draw direction (only for straight slats in move mode)"),
              _shortcutItem("'Up/Down arrow keys'", "Change layer"),
              _shortcutItem("'A'", "Add new layer"),
              _shortcutItem("'1'", "Switch to 'Add' mode"),
              _shortcutItem("'2'", "Switch to 'Delete' mode"),
              _shortcutItem("'3'", "Switch to 'Edit' mode"),
              _shortcutItem("'E'", "Edit selected handles while in the Assembly Handles panel"),
              _shortcutItem("'L'", "Lock / unlock all edits"),
              _shortcutItem("'CMD/Ctrl-Z'", "Undo last action"),
              _shortcutItem("'CMD-Shift-Z/Ctrl-Y'", "Redo last action"),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text("Close"),
          ),
        ],
      );
    },
  );
}

Widget _shortcutItem(String key, String description) {
  return Padding(
    padding: const EdgeInsets.symmetric(vertical: 4.0),
    child: Text.rich(
      TextSpan(
        children: [
          TextSpan(
            text: "$key ",
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black),
          ),
          TextSpan(
            text: description,
            style: TextStyle(color: Colors.grey.shade700),
          ),
        ],
      ),
      style: TextStyle(fontSize: 14),
    ),
  );
}


void displayPlateInfo(BuildContext context, String plateName, HashCadPlate plate) {
  final entries = plate.displayEntries;

  showDialog(
    context: context,
    builder: (_) {
      return AlertDialog(
        title: Text('Detailed Plate View: $plateName'),
        content: SizedBox(
          width: 800,
          height: 500,
          child: Column(
            children: [
              Expanded(
                child: entries.isEmpty
                    ? Center(child: Text('No plate entries found.', style: TextStyle(color: Colors.grey.shade600)))
                    : ListView.builder(
                        itemCount: entries.length,
                        itemBuilder: (context, index) {
                          final entry = entries[index];
                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4.0),
                            child: _SlatPictograph(entry: entry, plate: plate),
                          );
                        },
                      ),
              ),
              Divider(height: 20),
              Wrap(
                alignment: WrapAlignment.center,
                spacing: 24,
                runSpacing: 8,
                children: [
                  _buildPlateLegendItem(_defaultPlateCompatibilityColor, 'Default / tube-compatible staple'),
                  _buildPlateLegendItem(_specialPlateCompatibilityColor, 'Special compatibility staple'),
                ],
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            child: Text('Close'),
            onPressed: () => Navigator.of(context).pop(),
          )
        ],
      );
    },
  );
}

const Color _defaultPlateCompatibilityColor = Colors.green;
const Color _specialPlateCompatibilityColor = Colors.orange;

Widget _buildPlateLegendItem(Color color, String label) {
  return Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(width: 14, height: 14, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3))),
      SizedBox(width: 6),
      Text(label, style: TextStyle(fontSize: 12)),
    ],
  );
}

/// Interactive slat pictograph for a single plate entry.
///
/// Renders the numbered rod with its top (H5 / side 5) and bottom (H2 / side 2)
/// arms. Each *available* arm is clickable: tapping it selects that specific
/// (position, side) and reveals its full DNA sequence beneath the pictograph.
/// Because the stored sequence differs per position/side, selection state is
/// held per pictograph rather than derived from the entry alone.
class _SlatPictograph extends StatefulWidget {
  final PlateDisplayEntry entry;
  final HashCadPlate plate;

  const _SlatPictograph({required this.entry, required this.plate});

  @override
  State<_SlatPictograph> createState() => _SlatPictographState();
}

class _SlatPictographState extends State<_SlatPictograph> {
  // Currently selected arm; both null when nothing is selected (no sequence shown).
  int? _selectedPos; // 1-based position along the rod
  int? _selectedSide; // 5 for H5 (top), 2 for H2 (bottom)

  // Layout constants for the pictograph geometry.
  static const int _armCount = 32;
  static const double _armWidth = 10.0;
  static const double _armSpacing = 5.0;
  static const double _rodWidth = _armCount * (_armWidth + _armSpacing);
  static const double _armHeight = 20.0;
  static const double _rodHeight = 25.0;
  static const double _labelWidth = 100.0;

  /// Whether a handle exists (is available) at [pos] (1-based) on the given side.
  bool _isArmAvailable(int pos, {required bool isTop}) {
    return widget.plate.contains(widget.entry.category, pos, isTop ? 5 : 2, widget.entry.id,
        compatibility: widget.entry.compatibility);
  }

  /// Toggles selection of the arm at [pos]/[side], clearing it if already selected.
  void _onArmTapped(int pos, int side) {
    setState(() {
      if (_selectedPos == pos && _selectedSide == side) {
        _selectedPos = null;
        _selectedSide = null;
      } else {
        _selectedPos = pos;
        _selectedSide = side;
      }
    });
  }

  /// Builds a horizontal strip of arms for one side (top = H5, bottom = H2).
  /// Available arms are colored and clickable; unavailable ones are greyed out.
  Widget _buildArms(bool isTop) {
    final side = isTop ? 5 : 2;
    final availabilityColor =
        widget.entry.isDefaultCompatibility ? _defaultPlateCompatibilityColor : _specialPlateCompatibilityColor;

    return SizedBox(
      width: _rodWidth,
      height: _armHeight,
      child: Row(
        children: [
          SizedBox(width: _armSpacing / 2),
          ...List.generate(_armCount, (i) {
            final pos = i + 1;
            final available = _isArmAvailable(pos, isTop: isTop);
            final selected = _selectedPos == pos && _selectedSide == side;

            // The colored cell, with a cross-hatch overlay when selected.
            final arm = Padding(
              padding: EdgeInsets.only(right: i == _armCount - 1 ? 0 : _armSpacing),
              child: SizedBox(
                width: _armWidth,
                height: _armHeight,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    Container(color: available ? availabilityColor : Colors.grey[400]),
                    if (selected) ClipRect(child: CustomPaint(painter: _HatchPainter())),
                  ],
                ),
              ),
            );

            // Only available arms are interactive (unavailable ones have no sequence).
            if (!available) return arm;
            return Tooltip(
              message: 'H$side · pos $pos · click for sequence',
              child: MouseRegion(
                cursor: SystemMouseCursors.click,
                child: GestureDetector(
                  onTap: () => _onArmTapped(pos, side),
                  child: arm,
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  /// Builds the black rod with the 1-based position number printed on each cell.
  Widget _buildRod() {
    return Stack(
      children: [
        Container(width: _rodWidth, height: _rodHeight, color: Colors.black),
        Positioned.fill(
          child: Row(
            children: List.generate(_armCount, (i) {
              return SizedBox(
                width: _armWidth + _armSpacing,
                child: Center(
                  child: Text('${i + 1}', style: TextStyle(fontSize: 8, color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              );
            }),
          ),
        ),
      ],
    );
  }

  /// Copies [sequence] to the clipboard and confirms with a short SnackBar.
  void _copySequence(String sequence) {
    Clipboard.setData(ClipboardData(text: sequence));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Sequence copied to clipboard'), duration: Duration(seconds: 1)),
    );
  }

  /// Builds the sequence label shown under the pictograph for the selected arm.
  ///
  /// Nothing is shown until an arm is selected. The full stored sequence is
  /// `core + tt + unique`; we color the core black, the `tt` linker grey, and the
  /// unique tail by handle category. Tapping the label copies the full sequence.
  Widget _buildSequenceLabel() {
    if (_selectedPos == null || _selectedSide == null) return const SizedBox.shrink();

    final fullSequence = widget.plate.getSequenceByComponents(
      widget.entry.category,
      _selectedPos!,
      _selectedSide!,
      widget.entry.id,
      compatibility: widget.entry.compatibility,
    );
    if (fullSequence.isEmpty) return const SizedBox.shrink();

    // The FLAT category color is a very light grey that is hard to read as text, so darken it.
    final categoryHighlight = widget.entry.category.toUpperCase() == 'FLAT'
        ? Colors.grey.shade700
        : categoryColor(widget.entry.category);

    // Split on the last linker: lowercase 'tt' or an uppercase ' TT ' flanked by spaces.
    final ttIndex = fullSequence.lastIndexOf('tt');
    final upperTtIndex = fullSequence.lastIndexOf(' TT ');
    final int linkerIndex;
    final int linkerLen;
    if (upperTtIndex > ttIndex) {
      linkerIndex = upperTtIndex;
      linkerLen = 4; // ' TT ' including the flanking spaces
    } else {
      linkerIndex = ttIndex;
      linkerLen = 2; // 'tt'
    }
    final List<TextSpan> sequenceSpans;
    if (linkerIndex < 0) {
      // No linker present: show the whole sequence in plain black.
      sequenceSpans = [TextSpan(text: fullSequence, style: const TextStyle(color: Colors.black))];
    } else {
      final core = fullSequence.substring(0, linkerIndex);
      final linker = fullSequence.substring(linkerIndex, linkerIndex + linkerLen); // preserves 'tt' vs ' TT '
      final unique = fullSequence.substring(linkerIndex + linkerLen);
      sequenceSpans = [
        TextSpan(text: core, style: const TextStyle(color: Colors.black)),
        TextSpan(text: linker, style: TextStyle(color: Colors.grey.shade500)),
        TextSpan(text: unique, style: TextStyle(color: categoryHighlight, fontWeight: FontWeight.bold)),
      ];
    }

    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Tooltip(
        message: 'Click to copy',
        child: MouseRegion(
          cursor: SystemMouseCursors.click,
          child: GestureDetector(
            onTap: () => _copySequence(fullSequence),
            child: SizedBox(
              width: _rodWidth,
              child: Text.rich(
                TextSpan(
                  style: const TextStyle(fontSize: 11, fontFamily: 'monospace'),
                  children: [
                    TextSpan(text: 'Sequence (H$_selectedSide, pos $_selectedPos): ', style: const TextStyle(color: Colors.black)),
                    ...sequenceSpans,
                  ],
                ),
                textAlign: TextAlign.center,
                softWrap: true,
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final entry = widget.entry;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Left label
              SizedBox(
                width: _labelWidth,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('H5', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                    Text('Handle ID:', style: TextStyle(fontSize: 10)),
                    Tooltip(
                      message: entry.id == "BLANK" ? "FLAT" : entry.id,
                      child: Text(
                        entry.id == "BLANK" ? "FLAT" : entry.id,
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                        softWrap: false,
                        overflow: TextOverflow.ellipsis,
                        maxLines: 1,
                      ),
                    ),
                    Text('H2', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
              SizedBox(width: 8),
              // Pictograph centered
              Column(
                children: [
                  _buildArms(true),
                  _buildRod(),
                  _buildArms(false),
                ],
              ),
              SizedBox(width: 8),
              // Right label
              SizedBox(
                width: _labelWidth,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('H5', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                    RichText(
                      textAlign: TextAlign.start,
                      text: TextSpan(
                        style: TextStyle(fontSize: 10, color: Colors.black),
                        children: [
                          TextSpan(text: 'Total Staples: '),
                          TextSpan(text: '${widget.plate.countDisplayEntryPositions(entry)}', style: TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                    Tooltip(
                      message: entry.category,
                      child: SizedBox(
                        width: 100,
                        child: Text.rich(
                          TextSpan(
                            style: TextStyle(fontSize: 10, color: Colors.black),
                            children: [
                              TextSpan(text: 'Category: '),
                              TextSpan(text: entry.category, style: TextStyle(fontWeight: FontWeight.bold)),
                            ],
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          softWrap: false,
                        ),
                      ),
                    ),
                    Tooltip(
                      message: entry.compatibilityLabel,
                      child: SizedBox(
                        width: 100,
                        child: Text.rich(
                          TextSpan(
                            style: TextStyle(fontSize: 10, color: Colors.black),
                            children: [
                              TextSpan(text: 'Compat: '),
                              TextSpan(text: entry.compatibilityLabel, style: TextStyle(fontWeight: FontWeight.bold)),
                            ],
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          softWrap: true,
                        ),
                      ),
                    ),
                    Text('H2', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ],
          ),
          // Sequence for the selected arm (hidden until an arm is clicked).
          _buildSequenceLabel(),
        ],
      ),
    );
  }
}

/// Paints a diagonal cross-hatch over an arm to mark it as selected
/// (used instead of a border, which looked too heavy).
class _HatchPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black54
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;
    const step = 4.0;
    // Draw lines in both diagonal directions to form the cross-hatch.
    for (double d = -size.height; d < size.width; d += step) {
      canvas.drawLine(Offset(d, 0), Offset(d + size.height, size.height), paint);
      canvas.drawLine(Offset(d + size.height, 0), Offset(d, size.height), paint);
    }
  }

  @override
  bool shouldRepaint(covariant _HatchPainter oldDelegate) => false;
}

/// Shows dialog for editing assembly handle value and enforce status.
/// Returns a map with:
/// - 'value' (int): The new handle value (ignored if enforceInPlace is true)
/// - 'enforce' (bool): Whether to enforce the value
/// - 'enforceInPlace' (bool): If true, enforce current values without changing them
/// Returns null if cancelled.
Future<Map<String, dynamic>?> showAssemblyHandleEditDialog(
  BuildContext context,
  DesignState appState,
  String currentValue,
  HandleKey handleKey,
) async {
  final controller = TextEditingController(text: currentValue);
  bool enforce = appState.assemblyLinkManager.getEnforceValue(handleKey) != null &&
      appState.assemblyLinkManager.getEnforceValue(handleKey)! > 0;
  bool enforceInPlace = false;

  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (context, setDialogState) => AlertDialog(
        title: const Text('Edit Assembly Handle'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: controller,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              decoration: const InputDecoration(
                labelText: 'Handle Value (1-999)',
                border: OutlineInputBorder(),
              ),
              autofocus: true,
              enabled: !enforceInPlace,
            ),
            const SizedBox(height: 16),
            CheckboxListTile(
              title: const Text('Enforce this value'),
              subtitle: const Text('Lock this handle to the specified value'),
              value: enforceInPlace || enforce,
              onChanged: enforceInPlace
                  ? null
                  : (value) {
                      setDialogState(() => enforce = value ?? false);
                    },
            ),
            const SizedBox(height: 16),
            CheckboxListTile(
              title: const Text('Enforce in-place'),
              subtitle: const Text('Lock selected handles to their current values'),
              value: enforceInPlace,
              onChanged: (value) {
                setDialogState(() => enforceInPlace = value ?? false);
              },
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              if (enforceInPlace) {
                Navigator.pop(ctx, {'value': 0, 'enforce': true, 'enforceInPlace': true});
              } else {
                int? val = int.tryParse(controller.text);
                if (val != null && val > 0 && val <= 999) {
                  Navigator.pop(ctx, {'value': val, 'enforce': enforce, 'enforceInPlace': false});
                }
              }
            },
            child: const Text('Apply'),
          ),
        ],
      ),
    ),
  );
}