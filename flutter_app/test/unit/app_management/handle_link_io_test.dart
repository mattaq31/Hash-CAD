import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:flutter_test/flutter_test.dart';

import 'package:hash_cad/app_management/design_io/handle_link_io.dart';
import 'package:hash_cad/app_management/design_state_mixins/design_state_handle_link_mixin.dart';
import 'package:hash_cad/crisscross_core/slats.dart';

void main() {
  late Map<String, Slat> slats;
  late Map<String, Map<String, dynamic>> layerMap;

  setUp(() {
    layerMap = {
      '1': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2'},
      '2': {'order': 1, 'top_helix': 'H2', 'bottom_helix': 'H5'},
    };
    slats = {
      '1-I1': Slat(1, '1-I1', '1', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)}),
      '1-I2': Slat(2, '1-I2', '1', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 1)}),
      '2-I1': Slat(1, '2-I1', '2', {for (int i = 1; i <= 32; i++) i: Offset(0, i.toDouble())}),
    };
  });

  group('writeHandleLinksToExcel → extractHandleLinksFromExcel round-trip', () {
    test('linked groups survive Excel round-trip', () {
      final original = HandleLinkManager();
      original.addLink(('1-I1', 1, 5), ('1-I1', 2, 5));
      original.addLink(('1-I1', 5, 5), ('1-I2', 5, 5));

      final excel = Excel.createExcel();
      writeHandleLinksToExcel(excel, slats, original, layerMap);

      final reimported = HandleLinkManager();
      final error = extractHandleLinksFromExcel(excel, slats, layerMap, reimported);

      expect(error, isNull);
      expect(reimported.handleLinkToGroup[('1-I1', 1, 5)], equals(reimported.handleLinkToGroup[('1-I1', 2, 5)]));
      expect(reimported.handleLinkToGroup[('1-I1', 5, 5)], equals(reimported.handleLinkToGroup[('1-I2', 5, 5)]));
      expect(reimported.handleLinkToGroup[('1-I1', 1, 5)], isNot(equals(reimported.handleLinkToGroup[('1-I1', 5, 5)])));
    });

    test('enforced values survive Excel round-trip', () {
      final original = HandleLinkManager();
      original.addLink(('1-I1', 1, 5), ('1-I1', 2, 5));
      original.setEnforcedValue(('1-I1', 1, 5), 42);
      original.setEnforcedValue(('1-I1', 3, 5), 99);

      final excel = Excel.createExcel();
      writeHandleLinksToExcel(excel, slats, original, layerMap);

      final reimported = HandleLinkManager();
      final error = extractHandleLinksFromExcel(excel, slats, layerMap, reimported);

      expect(error, isNull);
      expect(reimported.getEnforceValue(('1-I1', 1, 5)), equals(42));
      expect(reimported.getEnforceValue(('1-I1', 2, 5)), equals(42));
      expect(reimported.getEnforceValue(('1-I1', 3, 5)), equals(99));
    });

    test('blocked handles survive Excel round-trip', () {
      final original = HandleLinkManager();
      original.addBlock(('1-I1', 4, 5));
      original.addBlock(('1-I2', 10, 2));

      final excel = Excel.createExcel();
      writeHandleLinksToExcel(excel, slats, original, layerMap);

      final reimported = HandleLinkManager();
      final error = extractHandleLinksFromExcel(excel, slats, layerMap, reimported);

      expect(error, isNull);
      expect(reimported.handleBlocks, contains(('1-I1', 4, 5)));
      expect(reimported.handleBlocks, contains(('1-I2', 10, 2)));
    });

    test('mixed constraints survive Excel round-trip', () {
      final original = HandleLinkManager();
      original.addLink(('1-I1', 1, 5), ('1-I2', 1, 5));
      original.setEnforcedValue(('1-I1', 1, 5), 42);
      original.setEnforcedValue(('1-I1', 3, 5), 77);
      original.addBlock(('1-I1', 4, 5));
      original.addBlock(('2-I1', 8, 2));

      final excel = Excel.createExcel();
      writeHandleLinksToExcel(excel, slats, original, layerMap);

      final reimported = HandleLinkManager();
      final error = extractHandleLinksFromExcel(excel, slats, layerMap, reimported);

      expect(error, isNull);

      expect(reimported.handleLinkToGroup[('1-I1', 1, 5)], equals(reimported.handleLinkToGroup[('1-I2', 1, 5)]));
      expect(reimported.getEnforceValue(('1-I1', 1, 5)), equals(42));
      expect(reimported.getEnforceValue(('1-I1', 3, 5)), equals(77));
      expect(reimported.handleBlocks, contains(('1-I1', 4, 5)));
      expect(reimported.handleBlocks, contains(('2-I1', 8, 2)));
    });

    test('multiple Excel round-trips maintain consistency', () {
      var manager = HandleLinkManager();
      manager.addLink(('1-I1', 1, 5), ('1-I1', 2, 5));
      manager.setEnforcedValue(('1-I1', 1, 5), 42);
      manager.setEnforcedValue(('1-I1', 3, 5), 99);
      manager.addBlock(('1-I1', 4, 5));

      for (int i = 0; i < 3; i++) {
        final excel = Excel.createExcel();
        writeHandleLinksToExcel(excel, slats, manager, layerMap);

        manager = HandleLinkManager();
        final error = extractHandleLinksFromExcel(excel, slats, layerMap, manager);
        expect(error, isNull, reason: 'Round-trip $i failed');
      }

      expect(manager.handleLinkToGroup[('1-I1', 1, 5)], equals(manager.handleLinkToGroup[('1-I1', 2, 5)]));
      expect(manager.getEnforceValue(('1-I1', 1, 5)), equals(42));
      expect(manager.getEnforceValue(('1-I1', 3, 5)), equals(99));
      expect(manager.handleBlocks, contains(('1-I1', 4, 5)));
    });
  });

  group('extractHandleLinksFromExcel edge cases', () {
    test('returns null when no link sheet exists (backwards compatibility)', () {
      final excel = Excel.createExcel();
      final manager = HandleLinkManager();

      final error = extractHandleLinksFromExcel(excel, slats, layerMap, manager);

      expect(error, isNull);
      expect(manager.handleLinkToGroup, isEmpty);
    });

    test('empty manager still writes slat rows but no link data', () {
      final manager = HandleLinkManager();
      final excel = Excel.createExcel();
      writeHandleLinksToExcel(excel, slats, manager, layerMap);

      final reimported = HandleLinkManager();
      final error = extractHandleLinksFromExcel(excel, slats, layerMap, reimported);

      expect(error, isNull);
      expect(reimported.handleLinkToGroup, isEmpty);
      expect(reimported.handleBlocks, isEmpty);
    });
  });

  group('slat name conversion round-trip', () {
    test('dart name → python name → dart name for single-digit layer', () {
      final dartName = '1-I1';
      final pythonName = dartToPythonSlatNameConvert(dartName, layerMap);
      expect(pythonName, equals('layer1-slat1'));

      final backToDart = pythonToDartSlatNameConvert(pythonName, layerMap);
      expect(backToDart, equals(dartName));
    });

    test('dart name → python name → dart name for second layer', () {
      final dartName = '2-I1';
      final pythonName = dartToPythonSlatNameConvert(dartName, layerMap);
      expect(pythonName, equals('layer2-slat1'));

      final backToDart = pythonToDartSlatNameConvert(pythonName, layerMap);
      expect(backToDart, equals(dartName));
    });
  });
}
