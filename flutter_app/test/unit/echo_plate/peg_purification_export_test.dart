// Unit tests for PEG purification helper sheet Excel export.
import 'package:excel/excel.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/slats.dart';
import 'package:hash_cad/echo_and_experimental_helpers/peg_purification_config.dart';
import 'package:hash_cad/echo_and_experimental_helpers/peg_purification_export.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';

import '../../helpers/test_helpers.dart';

/// Extracts a numeric value from a cell regardless of whether it's Int or Double.
double _numericValue(CellValue? cell) {
  if (cell is IntCellValue) return cell.value.toDouble();
  if (cell is DoubleCellValue) return cell.value;
  throw Exception('Expected numeric cell, got: $cell');
}

/// Extracts a string value from a TextCellValue (TextSpan → String).
String _textValue(CellValue? cell) {
  if (cell is TextCellValue) return cell.value.toString();
  throw Exception('Expected text cell, got: $cell');
}

/// Creates a slat with all handles fully assigned (for MW calculation).
Slat _createFullSlat(int id, String layer) {
  final slat = Slat(id, 'slat-$id', layer, createTestSlatCoordinates(Offset(0, id.toDouble())));
  for (var pos = 1; pos <= 32; pos++) {
    slat.setHandle(pos, 2, 'ATCGATCGATCG', 'A$pos', 'Plate1', 'v$pos', 'ASSEMBLY', 200);
    slat.setHandle(pos, 5, 'GCTAGCTAGCTA', 'B$pos', 'Plate2', 'w$pos', 'ASSEMBLY', 200);
  }
  return slat;
}

/// Creates a slat without handle assignments (MW will fail).
Slat _createEmptySlat(int id, String layer) {
  return Slat(id, 'slat-$id', layer, createTestSlatCoordinates(Offset(0, id.toDouble())));
}

Map<int, Map<String, String?>> _makePlateAssignments(Map<String, String> wellToSlat) {
  final plate = <String, String?>{};
  for (var entry in wellToSlat.entries) {
    plate[entry.key] = entry.value;
  }
  return {0: plate};
}

/// Minimal layerMap for tests — layer 'A' at order 0.
final _testLayerMap = <String, Map<String, dynamic>>{
  'A': {'order': 0, 'color': 0xFF000000},
};

void main() {
  group('PegPurificationConfig serialization', () {
    test('toMap produces expected keys and values', () {
      const config = PegPurificationConfig(pegConcentration: 2);
      final map = config.toMap();
      expect(map['peg_concentration'], '2');
    });

    test('fromMap round-trips correctly', () {
      const original = PegPurificationConfig(pegConcentration: 2);
      final restored = PegPurificationConfig.fromMap(original.toMap());
      expect(restored.pegConcentration, 2);
    });

    test('fromMap with missing keys falls back to defaults', () {
      final config = PegPurificationConfig.fromMap({});
      expect(config.pegConcentration, 3);
    });
  });

  group('generatePegPurificationExcel — basic structure', () {
    test('generates non-empty bytes with valid groups', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'Group A': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {0: 'TestPlate'},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      expect(result.bytes.isNotEmpty, true);
    });

    test('output contains expected sheet name', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'Group A': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      expect(excel.tables.containsKey('PEG Purification'), true);
    });

    test('row 3 (slat count) matches actual group sizes', () {
      final slat1 = _createFullSlat(1, 'A');
      final slat2 = _createFullSlat(2, 'A');
      final slat3 = _createFullSlat(3, 'A');
      final result = generatePegPurificationExcel(
        groups: {
          'G1': ['slat-1', 'slat-2'],
          'G2': ['slat-3'],
        },
        slats: {'slat-1': slat1, 'slat-2': slat2, 'slat-3': slat3},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2', 'A3': 'slat-3'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      // Row 3 (0-indexed) = slat count. Column B=1, Column C=2
      final g1Count = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 3)).value;
      final g2Count = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 3)).value;
      expect(_numericValue(g1Count), 2);
      expect(_numericValue(g2Count), 1);
    });

    test('empty groups produces warning', () {
      final result = generatePegPurificationExcel(
        groups: {},
        slats: {},
        layerMap: _testLayerMap,
        plateAssignments: {},
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      expect(result.warnings, contains('No groups provided.'));
    });
  });

  group('generatePegPurificationExcel — molecular weight', () {
    test('groups with fully-assigned handles have valid MW in row 23', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final mwCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 23)).value;
      expect(_numericValue(mwCell), greaterThan(0));
      expect(result.warnings, isEmpty);
    });

    test('groups where all slats lack handles show N/A and add warning', () {
      final slat = _createEmptySlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final mwCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 23)).value;
      expect(_textValue(mwCell), 'N/A');
      expect(result.warnings.any((w) => w.contains('molecular weight')), true);
    });

    test('mixed group uses average of valid slats and warns', () {
      final fullSlat = _createFullSlat(1, 'A');
      final emptySlat = _createEmptySlat(2, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1', 'slat-2']},
        slats: {'slat-1': fullSlat, 'slat-2': emptySlat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final mwCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 23)).value;
      expect(_numericValue(mwCell), greaterThan(0));
      expect(result.warnings.any((w) => w.contains('1/2 slats')), true);
    });
  });

  group('generatePegPurificationExcel — volume resolution', () {
    test('uses WellConfig volume from plate assignments', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {0: {'A1': const WellConfig(volume: 75)}},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final volCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 2)).value;
      expect(_numericValue(volCell), 75.0);
    });

    test('group with all unassigned slats is excluded with warning', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: {},
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      expect(result.warnings.any((w) => w.contains('no slats on output plates')), true);
      expect(result.warnings.any((w) => w.contains('No slats assigned')), true);
    });

    test('partially assigned group only counts assigned slats', () {
      final slat1 = _createFullSlat(1, 'A');
      final slat2 = _createFullSlat(2, 'A');
      final slat3 = _createFullSlat(3, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1', 'slat-2', 'slat-3']},
        slats: {'slat-1': slat1, 'slat-2': slat2, 'slat-3': slat3},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final countCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 3)).value;
      expect(_numericValue(countCell), 2);
      expect(result.warnings.any((w) => w.contains('2/3 slats on output plates')), true);
    });

    test('group with no plate assignments is excluded while others remain', () {
      final slat1 = _createFullSlat(1, 'A');
      final slat2 = _createFullSlat(2, 'A');
      final result = generatePegPurificationExcel(
        groups: {
          'G1': ['slat-1'],
          'G2': ['slat-2'],
        },
        slats: {'slat-1': slat1, 'slat-2': slat2},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final headerB = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 0)).value;
      expect(_textValue(headerB), 'G1');
      // Only 1 group column
      final headerC = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 0)).value;
      expect(headerC, isNull);
      expect(result.warnings.any((w) => w.contains('G2') && w.contains('excluded')), true);
    });

    test('plate-assigned slats not in any group become leftover groups per layer', () {
      final slat1 = _createFullSlat(1, 'A');
      final slat2 = _createFullSlat(2, 'A');
      final slat3 = _createFullSlat(3, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat1, 'slat-2': slat2, 'slat-3': slat3},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2', 'A3': 'slat-3'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      // G1 in column B, leftover group in column C
      final headerB = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 0)).value;
      final headerC = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 0)).value;
      expect(_textValue(headerB), 'G1');
      expect(_textValue(headerC), 'Leftover L1 Slats');
      // Leftover group should have 2 slats
      final countC = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 3)).value;
      expect(_numericValue(countC), 2);
    });

    test('mixed volumes within group splits into subgroups', () {
      final slat1 = _createFullSlat(1, 'A');
      final slat2 = _createFullSlat(2, 'A');
      final slat3 = _createFullSlat(3, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1', 'slat-2', 'slat-3']},
        slats: {'slat-1': slat1, 'slat-2': slat2, 'slat-3': slat3},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2', 'A3': 'slat-3'}),
        wellConfigs: {
          0: {
            'A1': const WellConfig(volume: 50),
            'A2': const WellConfig(volume: 50),
            'A3': const WellConfig(volume: 100),
          }
        },
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      // Subgroup A (50 µL): 2 slats in column B
      final volCellA = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 2)).value;
      expect(_numericValue(volCellA), 50.0);
      final countA = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 3)).value;
      expect(_numericValue(countA), 2.0);
      // Subgroup B (100 µL): 1 slat in column C
      final volCellB = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 2)).value;
      expect(_numericValue(volCellB), 100.0);
      final countB = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 3)).value;
      expect(_numericValue(countB), 1.0);
      // Warning mentions split
      expect(result.warnings.any((w) => w.contains('mixed volumes')), true);
    });
  });

  group('generatePegPurificationExcel — PEG concentration', () {
    test('3x PEG gives target Mg of 15 mM', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(pegConcentration: 3),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final mgCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 8)).value;
      expect(_numericValue(mgCell), 15.0);
    });

    test('2x PEG gives target Mg of 20 mM', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(pegConcentration: 2),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final mgCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 8)).value;
      expect(_numericValue(mgCell), 20.0);
    });
  });

  group('generatePegPurificationExcel — formulas', () {
    test('row 4 contains total volume formula', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 4)).value;
      expect(cell, isA<FormulaCellValue>());
      expect((cell as FormulaCellValue).formula, 'B3*B4');
    });

    test('row 10 contains Mg addition formula', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 10)).value;
      expect(cell, isA<FormulaCellValue>());
      expect((cell as FormulaCellValue).formula, 'ROUND((B9-B8)*B5/(1000-B9),2)');
    });

    test('row 12 PEG formula uses correct divisor for 3x PEG', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {},
        pegConfig: const PegPurificationConfig(pegConcentration: 3),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 12)).value;
      expect(cell, isA<FormulaCellValue>());
      expect((cell as FormulaCellValue).formula, '(B11+B5)/2');
    });
  });

  group('generatePegPurificationExcel — slat reference table', () {
    test('all slats from all groups appear in reference rows', () {
      final slat1 = _createFullSlat(1, 'A');
      final slat2 = _createFullSlat(2, 'A');
      final result = generatePegPurificationExcel(
        groups: {
          'G1': ['slat-1'],
          'G2': ['slat-2'],
        },
        slats: {'slat-1': slat1, 'slat-2': slat2},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'B1': 'slat-2'}),
        wellConfigs: {},
        plateNames: {0: 'MyPlate'},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;

      // Reference table starts at row 38 (0-indexed)
      final slatIdsInTable = <String>[];
      for (var r = 38; r < sheet.maxRows; r++) {
        final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: r)).value;
        if (cell != null && cell is TextCellValue) {
          final text = cell.value.toString();
          if (text.isNotEmpty) slatIdsInTable.add(text);
        }
      }
      expect(slatIdsInTable, containsAll(['L1-1', 'L1-2']));
    });

    test('well and plate resolved from plate assignments', () {
      final slat = _createFullSlat(1, 'A');
      final result = generatePegPurificationExcel(
        groups: {'G1': ['slat-1']},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
        plateAssignments: _makePlateAssignments({'C3': 'slat-1'}),
        wellConfigs: {},
        plateNames: {0: 'SourcePlate'},
        pegConfig: const PegPurificationConfig(),
        experimentTitle: 'Test',
      );
      final excel = Excel.decodeBytes(result.bytes);
      final sheet = excel.tables['PEG Purification']!;
      // First reference row
      final wellCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 38)).value;
      final plateCell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 3, rowIndex: 38)).value;
      expect(_textValue(wellCell), 'C3');
      expect(_textValue(plateCell), 'SourcePlate');
    });
  });
}
