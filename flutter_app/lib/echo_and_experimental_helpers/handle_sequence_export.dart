// Excel export of every handle sequence on one or more slats (triggered from the 'Zoom In on Handles' dialog).
//
// Output mirrors the input plate 'All Data' format, prefixed with slat name/side/position columns.
// Each slat contributes one row per position per side (64 rows for a standard slat); positions without an
// assigned sequence are still listed, with their handle columns filled with 'N/A'. Slats are separated by a blank row.
// Sequences are colored as in the handle inspector (core black, tt linker grey, unique tail in the category color),
// and rows of handles marked as manual (pipetted by hand) are filled orange across all columns.
import 'dart:convert';
import 'dart:typed_data';

import 'package:archive/archive.dart';
import 'package:excel/excel.dart';
import 'package:flutter/material.dart' show Color, Colors;
import 'package:xml/xml.dart';

import '../graphics/handle_sequence_text.dart' show handleLinkerColor, plateCategoryDisplayColor, splitHandleSequence;

import '../crisscross_core/handle_plates.dart';
import '../crisscross_core/slats.dart';
import 'echo_category_colors.dart';
import 'echo_plate_constants.dart';

/// Column headers of the exported handle sequence sheet.
const List<String> handleSequenceExportHeaders = [
  'Slat Name', 'Slat Side', 'Slat Position', 'Name', 'Sequence', 'Plate Name', 'Plate Concentration (uM)', 'Plate Well', 'Description', 'Compatibility',
];

/// Row fill for manually pipetted handles (matches the orange used for manual positions in the zoom-in dialog).
final CellStyle _manualHandleStyle = CellStyle(backgroundColorHex: '#FFB74D'.excelColor);

/// Placeholder written for any unavailable handle value.
const String _notAvailable = 'N/A';

/// Builds an Excel workbook listing all h2 then h5 handles of each slat in [slats], in the given order.
///
/// [plateStack] is used to recover the plate-only columns (name, description, compatibility) that are not
/// stored on the slat handles themselves. [layerMap] and [allSlats] are needed to generate slat display names.
/// [manualHandles] maps slat IDs to their manual (helix, position) set; those rows are highlighted orange.
Uint8List generateHandleSequenceExcel({
  required List<Slat> slats,
  required Map<String, Map<String, dynamic>> layerMap,
  required Map<String, Slat> allSlats,
  required PlateLibrary plateStack,
  Map<String, Set<(int, int)>> manualHandles = const {},
}) {
  final excel = Excel.createExcel();
  const sheetName = 'All Data';
  excel.rename(excel.getDefaultSheet()!, sheetName);
  final sheet = excel[sheetName];

  // Longest text (in characters) per column, used to size columns to their content
  final colWidths = <int, int>{};
  void writeCell(int col, int row, dynamic val, {CellStyle? style}) {
    _setCell(sheet, col, row, val, style: style);
    final len = val.toString().length;
    if (len > (colWidths[col] ?? 0)) colWidths[col] = len;
  }

  for (var col = 0; col < handleSequenceExportHeaders.length; col++) {
    writeCell(col, 0, handleSequenceExportHeaders[col]);
  }

  // Unique-tail highlight color per exported sequence, applied to the saved workbook afterwards
  final sequenceHighlights = <String, Color>{};

  var row = 1;
  for (var i = 0; i < slats.length; i++) {
    // One empty line separates consecutive slats
    if (i > 0) row++;
    final slat = slats[i];
    final slatName = slatDisplayName(slat, layerMap, slats: allSlats);
    final manualPositions = manualHandles[slat.id] ?? const <(int, int)>{};
    for (final side in const [2, 5]) {
      final handles = side == 2 ? slat.h2Handles : slat.h5Handles;
      for (var pos = 1; pos <= slat.maxLength; pos++) {
        final handle = handles[pos];
        final values = [slatName, 'h$side', pos, ..._handleColumns(handle, plateStack)];
        final sequence = handle?['sequence']?.toString() ?? '';
        if (sequence.isNotEmpty) {
          sequenceHighlights.putIfAbsent(sequence, () => plateCategoryDisplayColor(effectiveEchoHandleCategory(handle) ?? ''));
        }
        for (var col = 0; col < values.length; col++) {
          writeCell(col, row, values[col], style: manualPositions.contains((side, pos)) ? _manualHandleStyle : null);
        }
        row++;
      }
    }
  }

  // Same sizing rule as the plate sheets in design_export.dart (padding + scale for proportional fonts/bold text)
  for (final entry in colWidths.entries) {
    sheet.setColumnWidth(entry.key, (entry.value + 2) * 1.2);
  }

  return _colorSequenceStrings(Uint8List.fromList(excel.encode()!), sequenceHighlights);
}

/// Rewrites the plain shared strings for handle sequences in [xlsxBytes] as colored rich-text runs.
///
/// The excel package only writes plain text (rich TextSpans are flattened on save), so the colored runs are
/// injected directly into `sharedStrings.xml`. Sequences without a linker are left untouched (plain black).
Uint8List _colorSequenceStrings(Uint8List xlsxBytes, Map<String, Color> sequenceHighlights) {
  final archive = ZipDecoder().decodeBytes(xlsxBytes);
  final output = Archive();
  var modified = false;
  for (final file in archive.files) {
    if (!file.isFile || !file.name.endsWith('sharedStrings.xml')) {
      output.addFile(file);
      continue;
    }
    final document = XmlDocument.parse(utf8.decode(file.content as List<int>));
    for (final si in document.findAllElements('si')) {
      final text = si.innerText;
      final highlight = sequenceHighlights[text];
      final parts = highlight == null ? null : splitHandleSequence(text);
      if (parts == null) continue;
      si.children
        ..clear()
        ..addAll([
          _richRun(parts.core, Colors.black),
          _richRun(parts.linker, handleLinkerColor),
          _richRun(parts.unique, highlight!, bold: true),
        ]);
      modified = true;
    }
    final bytes = utf8.encode(document.toXmlString());
    output.addFile(ArchiveFile(file.name, bytes.length, bytes));
  }
  if (!modified) return xlsxBytes;
  return Uint8List.fromList(ZipEncoder().encode(output)!);
}

/// Builds a shared-string rich-text run (`<r>`) with the given text [color] and optional bold weight.
XmlElement _richRun(String text, Color color, {bool bold = false}) {
  final argb = color.toARGB32().toRadixString(16).padLeft(8, '0').toUpperCase();
  return XmlElement(XmlName('r'), [], [
    XmlElement(XmlName('rPr'), [], [
      if (bold) XmlElement(XmlName('b')),
      XmlElement(XmlName('color'), [XmlAttribute(XmlName('rgb'), argb)]),
      XmlElement(XmlName('sz'), [XmlAttribute(XmlName('val'), '11')]),
      XmlElement(XmlName('rFont'), [XmlAttribute(XmlName('val'), 'Calibri')]),
    ]),
    // preserve keeps the spaces of an uppercase ' TT ' linker
    XmlElement(XmlName('t'), [XmlAttribute(XmlName('space', 'xml'), 'preserve')], [XmlText(text)]),
  ]);
}

/// Returns the Name, Sequence, Plate Name, Plate Concentration, Plate Well, Description and Compatibility values
/// for a single handle, or 'N/A' for all of them if the handle is missing or has no sequence (e.g. a placeholder).
List<dynamic> _handleColumns(Map<String, dynamic>? handle, PlateLibrary plateStack) {
  final sequence = handle?['sequence']?.toString() ?? '';
  if (handle == null || sequence.isEmpty) return List.filled(7, _notAvailable);

  final plateName = handle['plate']?.toString() ?? '';
  final well = handle['well']?.toString() ?? '';
  final plateRow = plateStack.plates[plateName]?.rawRowForWell(well);

  // Plate headers are matched case-insensitively, as in the plate reader
  dynamic plateValue(String key) {
    if (plateRow == null) return null;
    for (final entry in plateRow.entries) {
      if (entry.key.trim().toLowerCase() == key) return entry.value;
    }
    return null;
  }

  String orNa(dynamic value) => (value == null || value.toString().isEmpty) ? _notAvailable : value.toString();

  return [
    orNa(plateValue('name')),
    sequence,
    orNa(plateName),
    handle['concentration'] ?? _notAvailable,
    orNa(well),
    orNa(plateValue('description')),
    // A blank compatibility means the default staple in plate files, so it is kept blank rather than 'N/A'
    plateRow == null ? _notAvailable : (plateValue('compatibility')?.toString() ?? ''),
  ];
}

/// Writes [val] into the cell at ([col], [row]), preserving numeric types and applying [style] if given.
/// Empty strings leave the cell value blank (the style is still applied so highlighted rows stay continuous).
void _setCell(Sheet sheet, int col, int row, dynamic val, {CellStyle? style}) {
  final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row));
  if (val is int) {
    cell.value = IntCellValue(val);
  } else if (val is double) {
    cell.value = DoubleCellValue(val);
  } else if (val.toString().isNotEmpty) {
    cell.value = TextCellValue(val.toString());
  }
  // Must come after the value: setting a value replaces the cell data and drops any earlier style
  if (style != null) cell.cellStyle = style;
}
