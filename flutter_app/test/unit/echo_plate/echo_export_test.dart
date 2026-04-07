import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/slats.dart';
import 'package:hash_cad/echo_and_experimental_helpers/echo_export.dart';
import 'package:hash_cad/echo_and_experimental_helpers/echo_plate_constants.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';
import '../../helpers/test_helpers.dart';

/// Parses CSV output into lines, filtering empty trailing lines.
List<String> _parseCsvLines(EchoCsvResult result) {
  return utf8.decode(result.csvBytes).split('\n').where((l) => l.isNotEmpty).toList();
}

/// Creates a minimal plate assignments map with one plate and given well→slatId entries.
Map<int, Map<String, String?>> _makePlateAssignments(Map<String, String?> wellMap) {
  final wells = generatePlateLayout96();
  final plate = <String, String?>{for (var w in wells) w: null};
  plate.addAll(wellMap);
  return {0: plate};
}

/// Standard layer map for testing (one layer 'A' at order 0).
final Map<String, Map<String, dynamic>> _testLayerMap = {
  'A': {'order': 0, 'color': const Color(0xFF0000FF)},
};

void main() {
  group('WellConfig', () {
    test('default values', () {
      const config = WellConfig();
      expect(config.ratio, 15);
      expect(config.volume, 50);
      expect(config.scaffoldConc, 50);
    });

    test('materialPerHandle = 37.5 for defaults', () {
      const config = WellConfig();
      expect(config.materialPerHandle, 37.5);
    });

    test('totalSlatQuantity = 2.5 for defaults', () {
      const config = WellConfig();
      expect(config.totalSlatQuantity, 2.5);
    });

    test('toExcelString/fromExcelString round-trip', () {
      const config = WellConfig(ratio: 20, volume: 100, scaffoldConc: 75);
      final serialized = config.toExcelString();
      final restored = WellConfig.fromExcelString(serialized);
      expect(restored, isNotNull);
      expect(restored!.ratio, 20);
      expect(restored.volume, 100);
      expect(restored.scaffoldConc, 75);
    });

    test('fromExcelString returns null for empty input', () {
      expect(WellConfig.fromExcelString(''), isNull);
    });

    test('fromExcelString returns null for malformed input', () {
      expect(WellConfig.fromExcelString('abc'), isNull);
      expect(WellConfig.fromExcelString('1_s2'), isNull); // only 2 parts
    });

    test('copyWith preserves unset fields', () {
      const config = WellConfig(ratio: 20, volume: 100, scaffoldConc: 75);
      final copied = config.copyWith(ratio: 30);
      expect(copied.ratio, 30);
      expect(copied.volume, 100);
      expect(copied.scaffoldConc, 75);
    });
  });

  group('generateEchoCsv', () {
    test('correct CSV header row', () {
      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {},
        layerMap: _testLayerMap,
      );
      final lines = _parseCsvLines(result);
      expect(lines.first, contains('Component'));
      expect(lines.first, contains('Source Plate Name'));
      expect(lines.first, contains('Source Well'));
      expect(lines.first, contains('Destination Well'));
      expect(lines.first, contains('Transfer Volume'));
      expect(lines.first, contains('Destination Plate Name'));
      expect(lines.first, contains('Source Plate Type'));
    });

    test('one row per handle (5 handles → 5 data rows)', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      for (int i = 1; i <= 3; i++) {
        slat.setHandle(i, 2, 'ATCG', 'A$i', 'Source_Plate_1_extra', 'val', 'ASSEMBLY', 200);
      }
      for (int i = 1; i <= 2; i++) {
        slat.setHandle(i, 5, 'ATCG', 'B$i', 'Source_Plate_2_extra', 'val', 'ASSEMBLY', 200);
      }

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
      );
      final lines = _parseCsvLines(result);
      // 1 header + 5 data rows
      expect(lines.length, 6);
    });

    test('skips handles with null or zero concentration', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat.setPlaceholderHandle(2, 2, 'val', 'ASSEMBLY'); // no concentration
      slat.h2Handles[3] = {'sequence': 'ATCG', 'well': 'A3', 'plate': 'P_1', 'value': 'v', 'category': 'ASSEMBLY', 'concentration': 0};

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
      );
      final lines = _parseCsvLines(result);
      // 1 header + 1 valid handle
      expect(lines.length, 2);
    });

    test('correct transfer volume (echoRoundedVolumeNl applied)', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
      );
      final lines = _parseCsvLines(result);
      // Transfer volume should be echoRoundedVolumeNl(37.5, 200) = 200
      expect(lines[1], contains(',200,'));
    });

    test('source plate name is sanitized', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1_extra_stuff', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
      );
      final lines = _parseCsvLines(result);
      // sanitizePlateMap('Plate_1_extra_stuff') → 'Plate_1'
      expect(lines[1], contains('Plate_1'));
      expect(lines[1], isNot(contains('extra_stuff')));
    });

    test('component name follows slatCsvName format', () {
      final slat = Slat(5, 'slat-5', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-5'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-5': slat},
        layerMap: _testLayerMap,
      );
      final lines = _parseCsvLines(result);
      // slatCsvName for layer 'A' (order 0) → 'layer1-slat5'
      expect(lines[1], contains('layer1-slat5_h2_staple_1'));
    });
  });

  group('generateEchoCsv — volume warnings', () {
    test('warning when well exceeds echoMaxWellVolumeNl', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      // 32 h2 handles at conc=25 → 1500 nL each → 48000 total
      for (int i = 1; i <= 32; i++) {
        slat.setHandle(i, 2, 'ATCG', 'A$i', 'Plate_1', 'val', 'ASSEMBLY', 25);
      }

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
      );
      expect(result.warnings, isNotEmpty);
      expect(result.warnings.first, contains('25 µL'));
    });

    test('no warning when under limit', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat},
        layerMap: _testLayerMap,
      );
      expect(result.warnings, isEmpty);
    });

    test('warning lists up to 5 wells, then "and N more"', () {
      // Create 7 slats each exceeding the limit
      final slats = <String, Slat>{};
      final wellMap = <String, String?>{};
      final wells = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7'];

      for (int s = 0; s < 7; s++) {
        final id = 'slat-${s + 1}';
        final slat = Slat(s + 1, id, 'A', createTestSlatCoordinates(Offset(0, s.toDouble())));
        for (int i = 1; i <= 32; i++) {
          slat.setHandle(i, 2, 'ATCG', 'A$i', 'Plate_1', 'val', 'ASSEMBLY', 25);
        }
        slats[id] = slat;
        wellMap[wells[s]] = id;
      }

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments(wellMap),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: slats,
        layerMap: _testLayerMap,
      );
      expect(result.warnings, isNotEmpty);
      expect(result.warnings.first, contains('and 2 more'));
    });
  });

  group('generateEchoCsv — volume normalization', () {
    test('adds water rows when normalizeVolumes=true and wells have different totals', () {
      // Two slats with different handle counts → different volumes
      final slat1 = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat1.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat1.setHandle(2, 2, 'ATCG', 'A2', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final slat2 = Slat(2, 'slat-2', 'A', createTestSlatCoordinates(const Offset(0, 1)));
      slat2.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat1, 'slat-2': slat2},
        layerMap: _testLayerMap,
        normalizeVolumes: true,
      );

      final lines = _parseCsvLines(result);
      // Should have water row(s) for the well with less volume
      final waterLines = lines.where((l) => l.contains('WATER_PLATE')).toList();
      expect(waterLines, isNotEmpty);
    });

    test('water deficit rounded to nearest 25 nL', () {
      final slat1 = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat1.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat1.setHandle(2, 2, 'ATCG', 'A2', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final slat2 = Slat(2, 'slat-2', 'A', createTestSlatCoordinates(const Offset(0, 1)));
      slat2.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat1, 'slat-2': slat2},
        layerMap: _testLayerMap,
        normalizeVolumes: true,
      );

      // slat-1: 2 handles * 200 nL = 400 nL
      // slat-2: 1 handle * 200 nL = 200 nL
      // deficit = 400 - 200 = 200, ceil(200/25)*25 = 200
      final lines = _parseCsvLines(result);
      final waterLine = lines.firstWhere((l) => l.contains('WATER_PLATE'));
      expect(waterLine, contains(',200,'));
    });

    test('totalWaterNl and waterWellsUsed populated correctly', () {
      final slat1 = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat1.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat1.setHandle(2, 2, 'ATCG', 'A2', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final slat2 = Slat(2, 'slat-2', 'A', createTestSlatCoordinates(const Offset(0, 1)));
      slat2.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat1, 'slat-2': slat2},
        layerMap: _testLayerMap,
        normalizeVolumes: true,
      );

      expect(result.totalWaterNl, 200);
      expect(result.waterWellsUsed, 1);
    });

    test('water source plate = WATER_PLATE', () {
      final slat1 = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat1.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat1.setHandle(2, 2, 'ATCG', 'A2', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final slat2 = Slat(2, 'slat-2', 'A', createTestSlatCoordinates(const Offset(0, 1)));
      slat2.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat1, 'slat-2': slat2},
        layerMap: _testLayerMap,
        normalizeVolumes: true,
      );

      final lines = _parseCsvLines(result);
      final waterLine = lines.firstWhere((l) => l.contains('WATER_PLATE'));
      expect(waterLine, contains('WATER_PLATE'));
    });

    test('no water rows when normalizeVolumes=false', () {
      final slat1 = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat1.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat1.setHandle(2, 2, 'ATCG', 'A2', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final slat2 = Slat(2, 'slat-2', 'A', createTestSlatCoordinates(const Offset(0, 1)));
      slat2.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = generateEchoCsv(
        plateAssignments: _makePlateAssignments({'A1': 'slat-1', 'A2': 'slat-2'}),
        wellConfigs: {},
        plateNames: {0: 'Plate'},
        slats: {'slat-1': slat1, 'slat-2': slat2},
        layerMap: _testLayerMap,
        normalizeVolumes: false,
      );

      expect(result.totalWaterNl, isNull);
      expect(result.waterWellsUsed, isNull);
      final lines = _parseCsvLines(result);
      expect(lines.where((l) => l.contains('WATER_PLATE')), isEmpty);
    });
  });
}
