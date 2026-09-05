// Dialogs for inspecting a loaded input (source) plate:
//  * displayPlateInfo — the detailed per-entry slat pictograph view, with an
//    interactive rod whose arms reveal each handle's sequence/concentration.
//  * the "Plate Layout" window (opened from the detailed view) — a read-only
//    384-well plate map whose filled wells can be clicked to inspect the oligo.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../crisscross_core/handle_plates.dart';
import '../echo_and_experimental_helpers/echo_category_colors.dart';

// Colors used to mark staple availability in the detailed pictograph view.
const Color _defaultPlateCompatibilityColor = Colors.green;
const Color _specialPlateCompatibilityColor = Colors.orange;

/// Returns the display color for a plate handle [category].
///
/// [categoryColor] maps FLAT to a very light grey that is almost invisible as
/// text or against empty wells, so FLAT is darkened here for legibility.
Color _plateCategoryDisplayColor(String category) {
  if (category.toUpperCase() == 'FLAT') return Colors.grey.shade700;
  return categoryColor(category);
}

/// Splits a stored handle sequence (`core + tt + unique`) into colored spans:
/// the core in black, the `tt` / ` TT ` linker in grey, and the unique tail in
/// [highlight]. If no linker is present the whole sequence is shown in black.
List<TextSpan> _buildSequenceSpans(String fullSequence, Color highlight) {
  // Prefer the last linker occurrence: lowercase 'tt' or an uppercase ' TT '
  // flanked by spaces.
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
  if (linkerIndex < 0) {
    // No linker present: show the whole sequence in plain black.
    return [TextSpan(text: fullSequence, style: const TextStyle(color: Colors.black))];
  }
  final core = fullSequence.substring(0, linkerIndex);
  final linker = fullSequence.substring(linkerIndex, linkerIndex + linkerLen); // preserves 'tt' vs ' TT '
  final unique = fullSequence.substring(linkerIndex + linkerLen);
  return [
    TextSpan(text: core, style: const TextStyle(color: Colors.black)),
    TextSpan(text: linker, style: TextStyle(color: Colors.grey.shade500)),
    TextSpan(text: unique, style: TextStyle(color: highlight, fontWeight: FontWeight.bold)),
  ];
}

/// Copies [sequence] to the clipboard and confirms with a short SnackBar.
void _copySequenceToClipboard(BuildContext context, String sequence) {
  Clipboard.setData(ClipboardData(text: sequence));
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content: Text('Sequence copied to clipboard'), duration: Duration(seconds: 1)),
  );
}

/// Shows the detailed plate view: one interactive slat pictograph per entry,
/// plus a "Plate Layout" button that opens the 384-well plate map.
void displayPlateInfo(BuildContext context, String plateName, HashCadPlate plate) {
  final entries = plate.displayEntries;

  showDialog(
    context: context,
    builder: (_) {
      return AlertDialog(
        title: Text('Detailed Plate View: $plateName'),
        // Trim the default bottom padding so the button sits close to the actions.
        contentPadding: const EdgeInsets.fromLTRB(24, 20, 24, 4),
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
              const SizedBox(height: 12),
              // Opens the well-map layout window; centered beneath the legend.
              Center(
                child: FilledButton.icon(
                  onPressed: () => _showPlateLayoutDialog(context, plateName, plate),
                  icon: const Icon(Icons.grid_on, size: 18),
                  label: const Text('Plate Layout'),
                ),
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

/// Builds a single colored-swatch + label item for the compatibility legend.
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

  /// Builds the sequence label shown under the pictograph for the selected arm.
  ///
  /// Nothing is shown until an arm is selected. The full stored sequence is
  /// colored via [_buildSequenceSpans]. Tapping the label copies the full sequence.
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

    // Concentration of the selected oligo, shown alongside position in the label.
    final concentration = widget.plate.getConcentrationByComponents(
      widget.entry.category,
      _selectedPos!,
      _selectedSide!,
      widget.entry.id,
      compatibility: widget.entry.compatibility,
    );

    final categoryHighlight = _plateCategoryDisplayColor(widget.entry.category);

    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Tooltip(
        message: 'Click to copy',
        child: MouseRegion(
          cursor: SystemMouseCursors.click,
          child: GestureDetector(
            onTap: () => _copySequenceToClipboard(context, fullSequence),
            child: SizedBox(
              width: _rodWidth,
              child: Text.rich(
                TextSpan(
                  style: const TextStyle(fontSize: 11, fontFamily: 'monospace'),
                  children: [
                    TextSpan(text: 'Sequence (H$_selectedSide, pos $_selectedPos, conc $concentration µM): ', style: const TextStyle(color: Colors.black)),
                    ..._buildSequenceSpans(fullSequence, categoryHighlight),
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

/// Paints a diagonal cross-hatch over a cell to mark it as selected
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

/// Opens the read-only 384-well plate-layout window for [plate].
void _showPlateLayoutDialog(BuildContext context, String plateName, HashCadPlate plate) {
  showDialog(
    context: context,
    builder: (_) => _PlateLayoutView(plateName: plateName, plate: plate),
  );
}

/// Immutable summary of the oligo occupying a single well.
class _WellInfo {
  final String sequence;
  final dynamic concentration;
  final String category;
  final String id;
  final int position;
  final int side;
  // True when this well holds a special-compatibility staple (i.e. not the
  // default tube-compatible variant); used to mark it with an orange border.
  final bool isSpecialCompatibility;
  // Human-readable compatibility label, shown in the selected-well caption.
  final String compatibilityLabel;

  const _WellInfo({
    required this.sequence,
    required this.concentration,
    required this.category,
    required this.id,
    required this.position,
    required this.side,
    required this.isSpecialCompatibility,
    required this.compatibilityLabel,
  });
}

/// Read-only 384-well plate map. Filled wells are colored by handle category;
/// clicking a filled well highlights it (cross-hatch) and shows its oligo
/// sequence/concentration in a bar above the plate.
class _PlateLayoutView extends StatefulWidget {
  final String plateName;
  final HashCadPlate plate;

  const _PlateLayoutView({required this.plateName, required this.plate});

  @override
  State<_PlateLayoutView> createState() => _PlateLayoutViewState();
}

class _PlateLayoutViewState extends State<_PlateLayoutView> {
  // Standard 384-well geometry: 16 rows (A–P) × 24 columns (1–24).
  static const int _rowCount = 16;
  static const int _colCount = 24;
  static const double _cellSize = 26.0;
  static const double _headerSize = 22.0;
  static const double _cellMargin = 1.0;

  // Reverse lookup from a well id (e.g. 'A1') to the oligo it holds.
  late final Map<String, _WellInfo> _wellMap;

  // Currently highlighted well, or null when nothing is selected.
  String? _selectedWell;

  @override
  void initState() {
    super.initState();
    _wellMap = _buildWellMap();
  }

  /// Builds a well -> oligo map by inverting the plate's variant-key data.
  ///
  /// `wells`, `sequences` and `concentrations` all share the same variant key
  /// (`category|position|side|id|compatibility`), so each well can be resolved
  /// back to its sequence/concentration and parsed metadata.
  Map<String, _WellInfo> _buildWellMap() {
    final map = <String, _WellInfo>{};
    for (final entry in widget.plate.wells.entries) {
      final parts = entry.key.split('|');
      if (parts.length < 4) continue;
      // Compatibility is the 5th key segment; absent keys default to tube-compatible.
      final compatibility = parts.length >= 5 ? parts[4] : defaultPlateCompatibility;
      final info = _WellInfo(
        sequence: widget.plate.sequences[entry.key] ?? '',
        concentration: widget.plate.concentrations[entry.key],
        category: parts[0],
        position: int.tryParse(parts[1]) ?? 0,
        side: int.tryParse(parts[2]) ?? 0,
        id: parts[3],
        isSpecialCompatibility: !isDefaultPlateCompatibility(compatibility),
        // Default-compatible wells read simply as 'default'; special ones show
        // their raw compatibility token.
        compatibilityLabel: isDefaultPlateCompatibility(compatibility) ? 'default' : compatibility,
      );
      for (final well in entry.value) {
        map[well] = info;
      }
    }
    return map;
  }

  /// The well id for grid coordinates (0-based row/col), e.g. (0,0) -> 'A1'.
  String _wellName(int row, int col) => '${String.fromCharCode(65 + row)}${col + 1}';

  /// Builds the info bar shown above the plate for the selected well.
  Widget _buildSelectedInfo() {
    if (_selectedWell == null) {
      return Text('Click a colored well to inspect its sequence.',
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600));
    }
    final info = _wellMap[_selectedWell]!;
    final highlight = _plateCategoryDisplayColor(info.category);
    // FLAT staples have no meaningful handle name, so it is omitted for them.
    final isFlat = info.category.toUpperCase() == 'FLAT';
    return Tooltip(
      message: 'Click to copy',
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: GestureDetector(
          onTap: () => _copySequenceToClipboard(context, info.sequence),
          child: Text.rich(
            TextSpan(
              style: const TextStyle(fontSize: 12, fontFamily: 'monospace', color: Colors.black),
              children: [
                const TextSpan(text: 'Selected well: '),
                TextSpan(text: '$_selectedWell', style: const TextStyle(fontWeight: FontWeight.bold)),
                const TextSpan(text: '  ('),
                // Exact handle name (e.g. antiBArt), colored to match its category.
                if (!isFlat) ...[
                  TextSpan(text: info.id, style: TextStyle(color: highlight, fontWeight: FontWeight.bold)),
                  const TextSpan(text: ', '),
                ],
                TextSpan(text: 'H${info.side}, pos ${info.position}, conc ${info.concentration} µM, compat: ${info.compatibilityLabel}): '),
                ..._buildSequenceSpans(info.sequence, highlight),
              ],
            ),
            textAlign: TextAlign.center,
            softWrap: true,
          ),
        ),
      ),
    );
  }

  /// Builds one well square. Filled wells are colored and clickable; empty
  /// wells are light grey and inert.
  Widget _buildWell(int row, int col) {
    final name = _wellName(row, col);
    final info = _wellMap[name];
    final present = info != null;
    final selected = name == _selectedWell;
    final fill = present ? _plateCategoryDisplayColor(info.category) : Colors.grey.shade200;
    // Special-compatibility wells get an orange marker border.
    final special = present && info.isSpecialCompatibility;

    final cell = Container(
      width: _cellSize,
      height: _cellSize,
      margin: const EdgeInsets.all(_cellMargin),
      decoration: BoxDecoration(
        color: fill,
        borderRadius: BorderRadius.circular(3),
        border: Border.all(color: selected ? Colors.black : Colors.white, width: 0.5),
      ),
      child: Stack(
        fit: StackFit.expand,
        children: [
          // Inner orange border for special-compatibility wells. Drawn as an
          // overlay inset from the edges so it stays inside the well square
          // rather than spilling out of it.
          if (special)
            Positioned.fill(
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(2),
                  border: Border.all(color: _specialPlateCompatibilityColor, width: 2),
                ),
              ),
            ),
          // Cross-hatch overlay marks the selected well.
          if (selected)
            ClipRRect(borderRadius: BorderRadius.circular(3), child: CustomPaint(painter: _HatchPainter())),
        ],
      ),
    );

    if (!present) return cell;
    return Tooltip(
      message: name,
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: GestureDetector(
          onTap: () => setState(() => _selectedWell = selected ? null : name),
          child: cell,
        ),
      ),
    );
  }

  /// Builds the full plate grid: a column header row of numbers, then one row
  /// per plate row prefixed by its letter label.
  Widget _buildGrid() {
    const headerStyle = TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.black54);
    final cellSpan = _cellSize + 2 * _cellMargin;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Column headers (1–24) with a leading corner spacer.
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(width: _headerSize),
            for (int c = 0; c < _colCount; c++)
              SizedBox(width: cellSpan, child: Center(child: Text('${c + 1}', style: headerStyle))),
          ],
        ),
        for (int r = 0; r < _rowCount; r++)
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Row letter header (A–P).
              SizedBox(
                width: _headerSize,
                height: cellSpan,
                child: Center(child: Text(String.fromCharCode(65 + r), style: headerStyle)),
              ),
              for (int c = 0; c < _colCount; c++) _buildWell(r, c),
            ],
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Plate Layout: ${widget.plateName}'),
      content: SizedBox(
        width: 780,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Selected-well info bar, shown on top of the plate.
            SizedBox(height: 40, child: Center(child: _buildSelectedInfo())),
            const Divider(height: 8),
            // Center the plate horizontally; scale down if it would overflow.
            Center(
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: _buildGrid(),
              ),
            ),
            const SizedBox(height: 6),
            Text('Colored wells contain a staple (color = category); grey wells are empty.',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
          ],
        ),
      ),
      actions: [
        TextButton(
          child: const Text('Close'),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ],
    );
  }
}
