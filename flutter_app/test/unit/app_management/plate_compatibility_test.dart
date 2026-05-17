// Unit tests for compatibility-aware source plate parsing and sequence assignment.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:hash_cad/app_management/shared_app_state.dart';
import 'package:hash_cad/crisscross_core/handle_plates.dart';
import 'package:hash_cad/crisscross_core/slats.dart';

List<List<dynamic>> _withCompatibilityHeader(List<List<dynamic>> rows) {
  return [
    ['well', 'name', 'sequence', 'description', 'concentration', 'compatibility'],
    ...rows,
  ];
}

List<dynamic> _plateRow({
  required String well,
  required String category,
  required String id,
  required int side,
  required int position,
  required String sequence,
  String compatibility = '',
}) {
  return [well, '$category-$id-H$side-pos_$position', sequence, '', 100, compatibility];
}

Slat _buildLinearSlat({required int numericId, required String id, required String layer, required String slatType}) {
  final coordinates = <int, Offset>{
    for (int i = 1; i <= 32; i++) i: Offset((i - 1).toDouble(), 0),
  };
  return Slat(numericId, id, layer, coordinates, slatType: slatType);
}

void main() {
  group('PlateLibrary compatibility parsing', () {
    test('legacy source plates without compatibility header are treated as default-compatible', () {
      final library = PlateLibrary();
      library.readPlatesFromRawData({
        'LegacyPlate': [
          ['well', 'name', 'sequence', 'description', 'concentration'],
          ['A1', 'FLAT-BLANK-H2-pos_16', 'AAAA', '', 100],
        ],
      });

      expect(library.contains('FLAT', 16, 2, 'BLANK'), isTrue);
      expect(library.availableCompatibilities('FLAT', 16, 2, 'BLANK'), equals({defaultPlateCompatibility}));
    });

    test('plate display entries split default and special compatibility variants', () {
      final plate = HashCadPlate.fromParsedData(
        [
          {'well': 'A1', 'name': 'FLAT-BLANK-H2-pos_16', 'sequence': 'AAAA', 'description': '', 'concentration': 100, 'compatibility': ''},
          {'well': 'A2', 'name': 'FLAT-BLANK-H2-pos_16', 'sequence': 'CCCC', 'description': '', 'concentration': 100, 'compatibility': 'db'},
        ],
        'TestPlate',
      );

      expect(plate.contains('FLAT', 16, 2, 'BLANK'), isTrue);
      expect(plate.contains('FLAT', 16, 2, 'BLANK', compatibility: 'db'), isTrue);
      expect(plate.getSequenceByComponents('FLAT', 16, 2, 'BLANK'), equals('AAAA'));
      expect(plate.getSequenceByComponents('FLAT', 16, 2, 'BLANK', compatibility: 'db'), equals('CCCC'));
      expect(plate.displayEntries.length, equals(2));
      expect(plate.displayEntries.where((entry) => entry.isDefaultCompatibility).length, equals(1));
      expect(plate.displayEntries.where((entry) => entry.compatibility == 'db').length, equals(1));
    });
  });

  group('DesignState plate assignment compatibility', () {
    test('tube slats use the default-compatible staple at position 16', () {
      final appState = DesignState();
      final slat = _buildLinearSlat(numericId: 1, id: 'A-I1', layer: 'A', slatType: 'tube');
      slat.setPlaceholderHandle(16, 2, '7', 'ASSEMBLY_HANDLE');
      appState.slats = {slat.id: slat};

      appState.plateStack.readPlatesFromRawData({
        'AssemblyPlate': _withCompatibilityHeader([
          _plateRow(well: 'A1', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 16, sequence: 'TUBESEQ'),
          _plateRow(well: 'A2', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 16, sequence: 'DBSEQ', compatibility: 'db'),
        ]),
      });

      appState.plateAssignAllHandles();

      expect(slat.h2Handles[16]!['sequence'], equals('TUBESEQ'));
      expect(appState.plateCompatibilityWarning, isNull);
    });

    test('double-barrel slats use the db-compatible staple at position 16', () {
      final appState = DesignState();
      final slat = _buildLinearSlat(numericId: 1, id: 'A-I1', layer: 'A', slatType: 'DB-L-120');
      slat.setPlaceholderHandle(16, 2, '7', 'ASSEMBLY_HANDLE');
      appState.slats = {slat.id: slat};

      appState.plateStack.readPlatesFromRawData({
        'AssemblyPlate': _withCompatibilityHeader([
          _plateRow(well: 'A1', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 16, sequence: 'TUBESEQ'),
          _plateRow(well: 'A2', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 16, sequence: 'DBSEQ', compatibility: 'db'),
        ]),
      });

      appState.plateAssignAllHandles();

      expect(slat.h2Handles[16]!['sequence'], equals('DBSEQ'));
      expect(appState.plateCompatibilityWarning, isNull);
    });

    test('90-degree double-barrel slats also use the db-compatible staple at position 16', () {
      for (final slatType in ['DB-L', 'DB-R']) {
        final appState = DesignState();
        final slat = _buildLinearSlat(numericId: 1, id: 'A-I1', layer: 'A', slatType: slatType);
        slat.setPlaceholderHandle(16, 2, '7', 'ASSEMBLY_HANDLE');
        appState.slats = {slat.id: slat};

        appState.plateStack.readPlatesFromRawData({
          'AssemblyPlate': _withCompatibilityHeader([
            _plateRow(well: 'A1', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 16, sequence: 'TUBESEQ'),
            _plateRow(well: 'A2', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 16, sequence: 'DBSEQ', compatibility: 'db'),
          ]),
        });

        appState.plateAssignAllHandles();

        expect(slat.h2Handles[16]!['sequence'], equals('DBSEQ'));
        expect(appState.plateCompatibilityWarning, isNull);
      }
    });

    test('double-barrel slats fall back to the default staple outside special positions', () {
      final appState = DesignState();
      final slat = _buildLinearSlat(numericId: 1, id: 'A-I1', layer: 'A', slatType: 'DB-R-60');
      slat.setPlaceholderHandle(15, 2, '7', 'ASSEMBLY_HANDLE');
      appState.slats = {slat.id: slat};

      appState.plateStack.readPlatesFromRawData({
        'AssemblyPlate': _withCompatibilityHeader([
          _plateRow(well: 'A1', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 15, sequence: 'DEFAULT15'),
          _plateRow(well: 'A2', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 15, sequence: 'DB15', compatibility: 'db'),
        ]),
      });

      appState.plateAssignAllHandles();

      expect(slat.h2Handles[15]!['sequence'], equals('DEFAULT15'));
      expect(appState.plateCompatibilityWarning, isNull);
    });

    test('blocked assembly handles use compatibility-aware flat staples', () {
      final appState = DesignState();
      final slat = _buildLinearSlat(numericId: 1, id: 'A-I1', layer: 'A', slatType: 'DB-R-120');
      slat.setPlaceholderHandle(16, 2, '0', 'ASSEMBLY_HANDLE');
      appState.slats = {slat.id: slat};

      appState.plateStack.readPlatesFromRawData({
        'FlatPlate': _withCompatibilityHeader([
          _plateRow(well: 'A1', category: 'FLAT', id: 'BLANK', side: 2, position: 16, sequence: 'DEFAULTFLAT'),
          _plateRow(well: 'A2', category: 'FLAT', id: 'BLANK', side: 2, position: 16, sequence: 'DBFLAT', compatibility: 'db'),
        ]),
      });

      appState.plateAssignAllHandles();

      expect(slat.h2Handles[16]!['sequence'], equals('DBFLAT'));
      expect(slat.h2Handles[16]!['value'], equals('0'));
      expect(slat.h2Handles[16]!['category'], equals('ASSEMBLY_HANDLE'));
    });

    test('sequence assignment warns when only incompatible variants are available', () {
      final appState = DesignState();
      final slat = _buildLinearSlat(numericId: 1, id: 'A-I1', layer: 'A', slatType: 'tube');
      slat.setPlaceholderHandle(16, 2, '7', 'ASSEMBLY_HANDLE');
      appState.slats = {slat.id: slat};

      appState.plateStack.readPlatesFromRawData({
        'AssemblyPlate': _withCompatibilityHeader([
          _plateRow(well: 'A2', category: 'ASSEMBLY_HANDLE_v1', id: '7', side: 2, position: 16, sequence: 'DBSEQ', compatibility: 'db'),
        ]),
      });

      appState.plateAssignAllHandles();

      expect(slat.h2Handles[16]!['sequence'], isNull);
      expect(appState.plateCompatibilityWarning, contains('1 staple(s) could not be assigned'));
    });
  });
}
