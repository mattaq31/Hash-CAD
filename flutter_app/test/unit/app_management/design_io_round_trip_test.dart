import 'dart:typed_data';
import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:hash_cad/app_management/design_io/design_io_constants.dart';
import 'package:hash_cad/app_management/design_io/design_export.dart';
import 'package:hash_cad/app_management/design_io/design_import.dart';
import 'package:hash_cad/app_management/design_io/excel_utilities.dart';

/// Builds a minimal valid #-CAD Excel workbook in memory.
///
/// Creates a two-layer design with two horizontal slats on layer 1 and
/// two vertical slats on layer 2, intersecting in a 32×32 grid.
/// This mirrors the structure that [exportDesign] produces.
Excel _buildMinimalDesign() {
  final excel = Excel.createExcel();

  final layerMap = {
    'A': {'order': 0, 'direction': 0, 'top_helix': 'H5', 'bottom_helix': 'H2', 'next_slat_id': 3, 'slat_count': 2, 'color': const Color(0xFFFF0000)},
    'B': {'order': 1, 'direction': 1, 'top_helix': 'H2', 'bottom_helix': 'H5', 'next_slat_id': 3, 'slat_count': 2, 'color': const Color(0xFF0000FF)},
  };

  // --- slat_layer_1: two horizontal slats (IDs 1 and 2) ---
  Sheet slatSheet1 = excel[slatLayerSheetName(0)];
  for (int row = 0; row < 32; row++) {
    for (int col = 0; col < 32; col++) {
      slatSheet1.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value = IntCellValue(0);
    }
  }
  for (int col = 0; col < 32; col++) {
    slatSheet1.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: 0)).value = TextCellValue('1-${col + 1}');
    slatSheet1.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: 1)).value = TextCellValue('2-${col + 1}');
  }

  // --- slat_layer_2: two vertical slats (IDs 1 and 2) ---
  Sheet slatSheet2 = excel[slatLayerSheetName(1)];
  for (int row = 0; row < 32; row++) {
    for (int col = 0; col < 32; col++) {
      slatSheet2.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value = IntCellValue(0);
    }
  }
  for (int row = 0; row < 32; row++) {
    slatSheet2.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: row)).value = TextCellValue('1-${row + 1}');
    slatSheet2.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: row)).value = TextCellValue('2-${row + 1}');
  }

  // --- handle_interface_1: all zeros ---
  Sheet handleSheet = excel[handleInterfaceSheetName(0)];
  for (int row = 0; row < 32; row++) {
    for (int col = 0; col < 32; col++) {
      handleSheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value = IntCellValue(0);
    }
  }

  // --- metadata ---
  Sheet meta = excel[metadataSheetName];
  meta.cell(CellIndex.indexByString('A1')).value = TextCellValue('Layer Interface Orientations');
  meta.cell(CellIndex.indexByString(metaCellLayerInterface)).value = TextCellValue('[2, (5, 5), 2]');
  meta.cell(CellIndex.indexByString('A2')).value = TextCellValue('Connection Angle');
  meta.cell(CellIndex.indexByString(metaCellGridMode)).value = TextCellValue('90');
  meta.cell(CellIndex.indexByString('A3')).value = TextCellValue('File Format');
  meta.cell(CellIndex.indexByString(metaCellFileFormat)).value = TextCellValue('#-CAD');
  meta.cell(CellIndex.indexByString('A4')).value = TextCellValue('Canvas Offset (Min)');
  meta.cell(CellIndex.indexByString(metaCellMinX)).value = DoubleCellValue(0.0);
  meta.cell(CellIndex.indexByString(metaCellMinY)).value = DoubleCellValue(0.0);
  meta.cell(CellIndex.indexByString('A5')).value = TextCellValue('Canvas Offset (Max)');
  meta.cell(CellIndex.indexByString(metaCellMaxX)).value = DoubleCellValue(31.0);
  meta.cell(CellIndex.indexByString(metaCellMaxY)).value = DoubleCellValue(31.0);

  // Layer info section
  meta.cell(CellIndex.indexByString('A6')).value = TextCellValue(metaSectionLayerInfo);

  meta.cell(CellIndex.indexByString('A7')).value = TextCellValue('ID');
  meta.cell(CellIndex.indexByString('B7')).value = TextCellValue('Default Rotation');
  meta.cell(CellIndex.indexByString('C7')).value = TextCellValue('Top Helix');
  meta.cell(CellIndex.indexByString('D7')).value = TextCellValue('Bottom Helix');
  meta.cell(CellIndex.indexByString('E7')).value = TextCellValue('Next Slat ID');
  meta.cell(CellIndex.indexByString('F7')).value = TextCellValue('Slat Count');
  meta.cell(CellIndex.indexByString('G7')).value = TextCellValue('Colour');

  int startRow = metaLayerStartRow;
  for (var entry in layerMap.entries) {
    int row = entry.value['order'] as int;
    meta.cell(CellIndex.indexByString('A${row + startRow}')).value = TextCellValue('Layer ${entry.key}');
    meta.cell(CellIndex.indexByString('B${row + startRow}')).value = IntCellValue(entry.value['direction'] as int);
    meta.cell(CellIndex.indexByString('C${row + startRow}')).value = TextCellValue(entry.value['top_helix'] as String);
    meta.cell(CellIndex.indexByString('D${row + startRow}')).value = TextCellValue(entry.value['bottom_helix'] as String);
    meta.cell(CellIndex.indexByString('E${row + startRow}')).value = IntCellValue(entry.value['next_slat_id'] as int);
    meta.cell(CellIndex.indexByString('F${row + startRow}')).value = IntCellValue(entry.value['slat_count'] as int);
    meta.cell(CellIndex.indexByString('G${row + startRow}')).value = TextCellValue('#FF0000');
  }

  // Cargo info section (empty but header present)
  int cargoStart = startRow + layerMap.length;
  meta.cell(CellIndex.indexByString('A$cargoStart')).value = TextCellValue(metaSectionCargoInfo);
  meta.cell(CellIndex.indexByString('A${cargoStart + 1}')).value = TextCellValue('ID');
  meta.cell(CellIndex.indexByString('B${cargoStart + 1}')).value = TextCellValue('Short Name');
  meta.cell(CellIndex.indexByString('C${cargoStart + 1}')).value = TextCellValue('Colour');

  // Unique slat colour section (empty but header present)
  int colorStart = cargoStart + 2;
  meta.cell(CellIndex.indexByString('A$colorStart')).value = TextCellValue(metaSectionSlatColorInfo);

  // --- slat_types ---
  Sheet slatTypes = excel[slatTypesSheetName];
  slatTypes.cell(CellIndex.indexByString('A1')).value = TextCellValue('Layer');
  slatTypes.cell(CellIndex.indexByString('B1')).value = TextCellValue('Slat ID');
  slatTypes.cell(CellIndex.indexByString('C1')).value = TextCellValue('Type');
  slatTypes.appendRow([IntCellValue(1), IntCellValue(1), TextCellValue('tube')]);
  slatTypes.appendRow([IntCellValue(1), IntCellValue(2), TextCellValue('tube')]);
  slatTypes.appendRow([IntCellValue(2), IntCellValue(1), TextCellValue('tube')]);
  slatTypes.appendRow([IntCellValue(2), IntCellValue(2), TextCellValue('tube')]);

  // Remove default Sheet1
  final firstReal = excel.sheets.keys.firstWhere((k) => k != 'Sheet1', orElse: () => 'Sheet1');
  if (firstReal != 'Sheet1') {
    excel.setDefaultSheet(firstReal);
    excel.delete('Sheet1');
  }

  return excel;
}

void main() {
  group('generateLayerString', () {
    test('two-layer design produces correct interface string', () {
      final layerMap = {
        'A': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2'},
        'B': {'order': 1, 'top_helix': 'H2', 'bottom_helix': 'H5'},
      };

      final result = generateLayerString(layerMap);

      expect(result, equals('[2, (5, 5), 2]'));
    });

    test('three-layer design produces correct interface string', () {
      final layerMap = {
        'A': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2'},
        'B': {'order': 1, 'top_helix': 'H2', 'bottom_helix': 'H5'},
        'C': {'order': 2, 'top_helix': 'H5', 'bottom_helix': 'H2'},
      };

      final result = generateLayerString(layerMap);

      expect(result, equals('[2, (5, 5), (2, 2), 5]'));
    });

    test('layers are sorted by order regardless of map key order', () {
      final layerMap = {
        'Z': {'order': 1, 'top_helix': 'H2', 'bottom_helix': 'H5'},
        'A': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2'},
      };

      final result = generateLayerString(layerMap);

      expect(result, equals('[2, (5, 5), 2]'));
    });
  });

  group('parseDesignInIsolate', () {
    test('parses minimal two-layer design without errors', () async {
      final excel = _buildMinimalDesign();
      final bytes = Uint8List.fromList(excel.encode()!);

      final result = await parseDesignInIsolate(bytes);

      expect(result.errorCode, isEmpty);
      expect(result.gridMode, equals('90'));
      expect(result.layerMap.length, equals(2));
      expect(result.layerMap.containsKey('A'), isTrue);
      expect(result.layerMap.containsKey('B'), isTrue);
    });

    test('recovers correct slat count per layer', () async {
      final excel = _buildMinimalDesign();
      final bytes = Uint8List.fromList(excel.encode()!);

      final result = await parseDesignInIsolate(bytes);

      final layerASlats = result.slats.values.where((s) => s.layer == 'A').length;
      final layerBSlats = result.slats.values.where((s) => s.layer == 'B').length;
      expect(layerASlats, equals(2));
      expect(layerBSlats, equals(2));
    });

    test('recovers correct slat positions', () async {
      final excel = _buildMinimalDesign();
      final bytes = Uint8List.fromList(excel.encode()!);

      final result = await parseDesignInIsolate(bytes);

      final slatA1 = result.slats['A-I1']!;
      expect(slatA1.maxLength, equals(32));
      expect(slatA1.slatPositionToCoordinate.length, equals(32));
      expect(slatA1.slatPositionToCoordinate[1], equals(const Offset(0, 0)));
      expect(slatA1.slatPositionToCoordinate[32], equals(const Offset(31, 0)));
    });

    test('recovers layer map properties', () async {
      final excel = _buildMinimalDesign();
      final bytes = Uint8List.fromList(excel.encode()!);

      final result = await parseDesignInIsolate(bytes);

      expect(result.layerMap['A']!['order'], equals(0));
      expect(result.layerMap['A']!['top_helix'], equals('H5'));
      expect(result.layerMap['A']!['bottom_helix'], equals('H2'));
      expect(result.layerMap['A']!['direction'], equals(0));
      expect(result.layerMap['B']!['order'], equals(1));
      expect(result.layerMap['B']!['top_helix'], equals('H2'));
      expect(result.layerMap['B']!['bottom_helix'], equals('H5'));
    });

    test('recovers slat types from slat_types sheet', () async {
      final excel = _buildMinimalDesign();
      final bytes = Uint8List.fromList(excel.encode()!);

      final result = await parseDesignInIsolate(bytes);

      for (var slat in result.slats.values) {
        expect(slat.slatType, equals('tube'));
      }
    });

    test('returns ERR_GENERAL for missing metadata sheet', () async {
      final excel = Excel.createExcel();
      excel['slat_layer_1'];
      final bytes = Uint8List.fromList(excel.encode()!);

      final result = await parseDesignInIsolate(bytes);

      expect(result.errorCode, equals('ERR_GENERAL'));
    });

    test('returns ERR_SLAT_SHEETS when no slat layers present', () async {
      final excel = Excel.createExcel();
      Sheet meta = excel[metadataSheetName];
      meta.cell(CellIndex.indexByString(metaCellGridMode)).value = TextCellValue('90');
      meta.cell(CellIndex.indexByString(metaCellMinX)).value = DoubleCellValue(0);
      meta.cell(CellIndex.indexByString(metaCellMinY)).value = DoubleCellValue(0);
      final bytes = Uint8List.fromList(excel.encode()!);

      final result = await parseDesignInIsolate(bytes);

      expect(result.errorCode, equals('ERR_SLAT_SHEETS'));
    });
  });

  group('design_io_constants consistency', () {
    test('sheet name builders use their respective prefixes', () {
      expect(slatLayerSheetName(0), startsWith(slatLayerPrefix));
      expect(slatLayerSheetName(0), equals('slat_layer_1'));
      expect(slatLayerSheetName(3), equals('slat_layer_4'));

      expect(handleInterfaceSheetName(0), startsWith(handleInterfacePrefix));
      expect(handleInterfaceSheetName(0), equals('handle_interface_1'));

      expect(cargoSheetName(0, 'lower', 'h2'), startsWith(cargoLayerPrefix));
      expect(cargoSheetName(0, 'lower', 'h2'), equals('cargo_layer_1_lower_h2'));

      expect(seedSheetName(0, 'upper', 'h5'), startsWith(seedLayerPrefix));
      expect(seedSheetName(0, 'upper', 'h5'), equals('seed_layer_1_upper_h5'));
    });

    test('side name mapping is symmetric', () {
      expect(sideToPositionalName('top'), equals('upper'));
      expect(sideToPositionalName('bottom'), equals('lower'));
      expect(positionalToSide('upper'), equals('top'));
      expect(positionalToSide('lower'), equals('bottom'));

      expect(positionalToSide(sideToPositionalName('top')), equals('top'));
      expect(positionalToSide(sideToPositionalName('bottom')), equals('bottom'));
      expect(sideToPositionalName(positionalToSide('upper')), equals('upper'));
      expect(sideToPositionalName(positionalToSide('lower')), equals('lower'));
    });

    test('encodePhantomCellValue matches expected format', () {
      expect(encodePhantomCellValue(3, 1, 5), equals('P3_1-5'));
      expect(encodePhantomCellValue(10, 2, 32), equals('P10_2-32'));
    });

    test('sideToHelixKey produces correct key for layer map lookup', () {
      expect(sideToHelixKey('top'), equals('top_helix'));
      expect(sideToHelixKey('bottom'), equals('bottom_helix'));
    });
  });
}
