// Unit tests for the per-slat handle sequence Excel export (Zoom In on Handles dialog).
import 'dart:convert';

import 'package:archive/archive.dart';
import 'package:excel/excel.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/handle_plates.dart';
import 'package:hash_cad/crisscross_core/slats.dart';
import 'package:hash_cad/echo_and_experimental_helpers/handle_sequence_export.dart';

import '../../helpers/test_helpers.dart';

/// Converts a cell to a comparable Dart value (String/int/double), or null for an empty cell.
dynamic _cellValue(Data? cell) {
  final v = cell?.value;
  if (v == null) return null;
  if (v is IntCellValue) return v.value;
  if (v is DoubleCellValue) return v.value;
  return v.toString();
}

/// Decodes the exported bytes into a list of row value lists from the 'All Data' sheet.
List<List<dynamic>> _decodeRows(List<int> bytes) {
  final sheet = Excel.decodeBytes(bytes).tables['All Data']!;
  return sheet.rows.map((r) => r.map(_cellValue).toList()).toList();
}

void main() {
  final layerMap = <String, Map<String, dynamic>>{'A': {'order': 0}};

  /// Plate library with one plate holding a flat staple (A1) and a compatibility-tagged staple (A2).
  PlateLibrary buildPlates() {
    final library = PlateLibrary();
    library.readPlatesFromRawData({
      'plateX': [
        ['well', 'name', 'sequence', 'description', 'concentration', 'compatibility'],
        ['A1', 'FLAT-BLANK-h2-position_1', 'AAAA', 'Flat Staple 1', 500, null],
        ['A2', 'FLAT-BLANK-h5-position_3', 'CCCC', 'Flat Staple 3', 200, 'special'],
      ],
    });
    return library;
  }

  test('single slat exports header plus 64 rows with N/A for missing handles', () {
    final slat = Slat(1, 'A-I1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
    slat.setHandle(1, 2, 'AAAA', 'A1', 'plateX', 'BLANK', 'FLAT', 500);
    slat.setHandle(3, 5, 'CCCC', 'A2', 'plateX', 'BLANK', 'FLAT', 200);

    final rows = _decodeRows(generateHandleSequenceExcel(slats: [slat], layerMap: layerMap, allSlats: {slat.id: slat}, plateStack: buildPlates()));

    expect(rows.first, handleSequenceExportHeaders);
    expect(rows.length, 65);
    expect(rows[1], ['L1-1', 'h2', 1, 'FLAT-BLANK-h2-position_1', 'AAAA', 'plateX', 500, 'A1', 'Flat Staple 1', null]);
    expect(rows[2], ['L1-1', 'h2', 2, 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A']);
    // h5 rows follow the 32 h2 rows
    expect(rows[35], ['L1-1', 'h5', 3, 'FLAT-BLANK-h5-position_3', 'CCCC', 'plateX', 200, 'A2', 'Flat Staple 3', 'special']);
  });

  test('multiple slats are separated by a single empty row', () {
    final s1 = Slat(1, 'A-I1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
    final s2 = Slat(2, 'A-I2', 'A', createTestSlatCoordinates(const Offset(0, 1)));

    final rows = _decodeRows(generateHandleSequenceExcel(slats: [s1, s2], layerMap: layerMap, allSlats: {s1.id: s1, s2.id: s2}, plateStack: PlateLibrary()));

    expect(rows.length, 1 + 64 + 1 + 64);
    expect(rows[64].first, 'L1-1');
    expect(rows[65].every((v) => v == null), isTrue);
    expect(rows[66].sublist(0, 3), ['L1-2', 'h2', 1]);
  });

  test('sequences with a tt linker are written as colored rich-text runs', () {
    final slat = Slat(1, 'A-I1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
    slat.setHandle(1, 2, 'CCCCttGGGG', 'A1', 'plateX', '12', 'ASSEMBLY_HANDLE', 500);
    slat.setHandle(2, 2, 'AAAA TT CCCC', 'A2', 'plateX', '13', 'ASSEMBLY_HANDLE', 500);

    final bytes = generateHandleSequenceExcel(slats: [slat], layerMap: layerMap, allSlats: {slat.id: slat}, plateStack: PlateLibrary());

    // Cell text is still the full, unmodified sequence
    final rows = _decodeRows(bytes);
    expect(rows[1][4], 'CCCCttGGGG');
    expect(rows[2][4], 'AAAA TT CCCC');

    final sharedStrings = ZipDecoder().decodeBytes(bytes).files.firstWhere((f) => f.name.endsWith('sharedStrings.xml'));
    final xml = utf8.decode(sharedStrings.content as List<int>);
    expect(xml, contains('<t xml:space="preserve">tt</t>'));
    expect(xml, contains('<t xml:space="preserve"> TT </t>'));
    expect(xml, contains('<b/>'));
  });

  test('manual handle rows are filled orange across all columns', () {
    final slat = Slat(1, 'A-I1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
    slat.setHandle(1, 2, 'AAAA', 'A1', 'plateX', 'BLANK', 'FLAT', 500);

    final bytes = generateHandleSequenceExcel(slats: [slat], layerMap: layerMap, allSlats: {slat.id: slat}, plateStack: buildPlates(), manualHandles: {slat.id: {(2, 1), (5, 4)}});
    final sheet = Excel.decodeBytes(bytes).tables['All Data']!;

    String? fill(int row, int col) => sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).cellStyle?.backgroundColor.colorHex;
    for (var col = 0; col < handleSequenceExportHeaders.length; col++) {
      expect(fill(1, col), 'FFFFB74D'); // h2 position 1 (with handle)
      expect(fill(36, col), 'FFFFB74D'); // h5 position 4 (N/A row)
    }
    expect(fill(2, 0), isNot('FFFFB74D'));
  });
}
