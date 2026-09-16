import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/slats.dart';
import 'package:hash_cad/app_management/design_state_mixins/design_state_handle_link_mixin.dart';
import 'package:hash_cad/crisscross_core/common_utilities.dart';

import '../../helpers/design_state_test_factory.dart';

/// Unit tests for blocked handle behavior with the new value='0' implementation.
void main() {
  group('Blocked Handles - Value 0 on Slat', () {
    test('slat setPlaceholderHandle with value 0 creates blocked handle', () {
      final slat = Slat(1, 'A-I1', 'A', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)});
      slat.setPlaceholderHandle(1, 5, '0', 'ASSEMBLY_HANDLE');

      expect(slat.h5Handles[1]?['category'], equals('ASSEMBLY_HANDLE'));
      expect(slat.h5Handles[1]?['value'], equals('0'));
    });

    test('blocked handle passes ASSEMBLY category check', () {
      final slat = Slat(1, 'A-I1', 'A', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)});
      slat.setPlaceholderHandle(1, 5, '0', 'ASSEMBLY_HANDLE');

      final category = slat.h5Handles[1]?['category']?.toString() ?? '';
      expect(category.contains('ASSEMBLY'), isTrue);
    });

    test('blocking ANTIHANDLE preserves ANTIHANDLE category', () {
      final slat = Slat(1, 'A-I1', 'A', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)});
      slat.setPlaceholderHandle(1, 2, '0', 'ASSEMBLY_ANTIHANDLE');

      expect(slat.h2Handles[1]?['category'], equals('ASSEMBLY_ANTIHANDLE'));
      expect(slat.h2Handles[1]?['value'], equals('0'));
    });

    test('removeHandle removes handle data entirely', () {
      final slat = Slat(1, 'A-I1', 'A', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)});
      slat.setPlaceholderHandle(1, 5, '0', 'ASSEMBLY_HANDLE');

      // Verify handle exists
      expect(slat.h5Handles[1], isNotNull);

      // Remove it
      slat.removeHandle(1, 5);

      // Verify handle is gone
      expect(slat.h5Handles[1], isNull);
    });

    test('blocked handle value can be detected as 0', () {
      final slat = Slat(1, 'A-I1', 'A', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)});
      slat.setPlaceholderHandle(1, 5, '0', 'ASSEMBLY_HANDLE');

      final value = slat.h5Handles[1]?['value'];
      final isBlocked = value == '0' || value == 0;
      expect(isBlocked, isTrue);
    });

    test('non-blocked handle value is not 0', () {
      final slat = Slat(1, 'A-I1', 'A', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)});
      slat.setPlaceholderHandle(1, 5, '42', 'ASSEMBLY_HANDLE');

      final value = slat.h5Handles[1]?['value'];
      final isBlocked = value == '0' || value == 0;
      expect(isBlocked, isFalse);
    });
  });

  group('HandleLinkManager - Block Synchronization', () {
    test('handleBlocks list tracks blocked handles', () {
      final manager = HandleLinkManager();
      final key = ('A-I1', 1, 5);

      manager.addBlock(key);

      expect(manager.handleBlocks, contains(key));
      expect(manager.getEnforceValue(key), equals(0));
    });

    test('removeBlock removes from handleBlocks list', () {
      final manager = HandleLinkManager();
      final key = ('A-I1', 1, 5);

      manager.addBlock(key);
      manager.removeBlock(key);

      expect(manager.handleBlocks, isNot(contains(key)));
    });

    test('blocked handle returns 0 from getEnforceValue', () {
      final manager = HandleLinkManager();
      final key = ('A-I1', 1, 5);

      manager.addBlock(key);

      expect(manager.getEnforceValue(key), equals(0));
    });

    test('non-blocked handle without group returns null from getEnforceValue', () {
      final manager = HandleLinkManager();
      final key = ('A-I1', 1, 5);

      expect(manager.getEnforceValue(key), isNull);
    });

    test('updateKey preserves blocked status', () {
      final manager = HandleLinkManager();
      final oldKey = ('A-I1', 1, 5);
      final newKey = ('A-I2', 2, 5);

      manager.addBlock(oldKey);

      manager.updateKey(oldKey, newKey);

      expect(manager.handleBlocks, isNot(contains(oldKey)));
      expect(manager.handleBlocks, contains(newKey));
    });
  });

  group('Blocked Handles - Import/Export', () {
    late Map<String, Slat> slats;
    late Map<String, Map<String, dynamic>> layerMap;

    setUp(() {
      layerMap = {
        '1': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2'},
      };
      slats = {
        '1-I1': Slat(1, '1-I1', '1', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)}),
      };
    });

    test('import blocked value creates entry in handleBlocks', () {
      final data = [
        ['layer1-slat1', ...List.filled(32, null)],
        ['Position', ...List.generate(32, (i) => i + 1)],
        ['h5-val', 0, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ['h5-link-group', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ['h2-val', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        ['h2-link-group', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
      ];

      final manager = HandleLinkManager();
      manager.importFromExcelData(data, slats, layerMap);

      expect(manager.handleBlocks, contains(('1-I1', 1, 5)));
    });

    test('export blocked handle produces value 0', () {
      final manager = HandleLinkManager();
      manager.addBlock(('1-I1', 1, 5));

      final exported = manager.exportToExcelData(slats, layerMap);

      // Find h5-val row (row index 2 for the first slat)
      final valRow = exported[2];
      expect(valRow[1], equals(0));
    });

    test('import then export preserves blocked handles', () {
      final original = HandleLinkManager();
      original.addBlock(('1-I1', 1, 5));
      original.addBlock(('1-I1', 5, 2));

      final exported = original.exportToExcelData(slats, layerMap);

      final reimported = HandleLinkManager();
      reimported.importFromExcelData(exported, slats, layerMap);

      expect(reimported.handleBlocks, contains(('1-I1', 1, 5)));
      expect(reimported.handleBlocks, contains(('1-I1', 5, 2)));
    });
  });

  group('DesignState.clearAllHandleLinks', () {
    test('removes links and enforced values but keeps blocks', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 1);
      final slat = state.slats.values.single;
      final side = getSlatSideFromLayer(state.layerMap, 'A', 'top');
      state.smartSetHandle(slat, 1, side, '7', 'ASSEMBLY_HANDLE');
      state.smartSetHandle(slat, 2, side, '7', 'ASSEMBLY_HANDLE');
      state.linkHandlesAndPropagate([(slat.id, 1, side), (slat.id, 2, side)]);
      state.setHandleEnforcedValue((slat.id, 1, side), 7);
      state.toggleHandleBlockAndApply((slat.id, 5, side));

      state.clearAllHandleLinks();

      expect(state.assemblyLinkManager.handleLinkToGroup, isEmpty);
      expect(state.assemblyLinkManager.handleGroupToValue, isEmpty);
      // block stays registered and on the slat, so the two representations stay in sync
      expect(state.assemblyLinkManager.handleBlocks, contains((slat.id, 5, side)));
      expect(getHandleDict(slat, side)[5]!['value'], '0');
      // handle values themselves are untouched
      expect(getHandleDict(slat, side)[1]!['value'], '7');
    });
  });

  group('DesignState.clearAssemblyHandles', () {
    test('also clears handle links, enforced values and blocks', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 1);
      final slat = state.slats.values.single;
      final side = getSlatSideFromLayer(state.layerMap, 'A', 'top');
      state.smartSetHandle(slat, 1, side, '7', 'ASSEMBLY_HANDLE');
      state.smartSetHandle(slat, 2, side, '7', 'ASSEMBLY_HANDLE');
      state.linkHandlesAndPropagate([(slat.id, 1, side), (slat.id, 2, side)]);
      state.setHandleEnforcedValue((slat.id, 1, side), 7);
      state.toggleHandleBlockAndApply((slat.id, 5, side));

      state.clearAssemblyHandles();

      expect(getHandleDict(slat, side), isEmpty);
      expect(state.assemblyLinkManager.handleLinkToGroup, isEmpty);
      expect(state.assemblyLinkManager.handleGroupToValue, isEmpty);
      expect(state.assemblyLinkManager.handleBlocks, isEmpty);
    });
  });
}
