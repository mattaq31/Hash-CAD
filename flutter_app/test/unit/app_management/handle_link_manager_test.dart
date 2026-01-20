import 'package:flutter_test/flutter_test.dart';

import 'package:hash_cad/app_management/design_state_mixins/design_state_handle_link_mixin.dart';
import 'package:hash_cad/crisscross_core/slats.dart';

/// Unit tests for HandleLinkManager - verifying numeric-only group IDs.
void main() {
  group('HandleLinkManager - Basic Operations', () {
    late HandleLinkManager manager;

    setUp(() {
      manager = HandleLinkManager();
    });

    test('addLink creates numeric group for two unlinked handles', () {
      final key1 = ('A-I1', 1, 5);
      final key2 = ('A-I2', 1, 5);

      manager.addLink(key1, key2);

      expect(manager.handleLinkToGroup.containsKey(key1), isTrue);
      expect(manager.handleLinkToGroup.containsKey(key2), isTrue);
      expect(manager.handleLinkToGroup[key1], isA<int>());
      expect(manager.handleLinkToGroup[key2], isA<int>());
      expect(manager.handleLinkToGroup[key1], equals(manager.handleLinkToGroup[key2]));
    });

    test('addLink joins existing group when one handle already linked', () {
      final key1 = ('A-I1', 1, 5);
      final key2 = ('A-I2', 1, 5);
      final key3 = ('A-I3', 1, 5);

      manager.addLink(key1, key2);
      final originalGroup = manager.handleLinkToGroup[key1];

      manager.addLink(key2, key3);

      expect(manager.handleLinkToGroup[key3], equals(originalGroup));
      expect(manager.handleGroupToLink[originalGroup]!.length, equals(3));
    });

    test('addLink merges groups when both handles already in different groups', () {
      final key1 = ('A-I1', 1, 5);
      final key2 = ('A-I2', 1, 5);
      final key3 = ('A-I3', 1, 5);
      final key4 = ('A-I4', 1, 5);

      manager.addLink(key1, key2);
      manager.addLink(key3, key4);
      final group1 = manager.handleLinkToGroup[key1];

      manager.addLink(key2, key3);

      // All should be in the same group (group1)
      expect(manager.handleLinkToGroup[key1], equals(group1));
      expect(manager.handleLinkToGroup[key2], equals(group1));
      expect(manager.handleLinkToGroup[key3], equals(group1));
      expect(manager.handleLinkToGroup[key4], equals(group1));
    });

    test('removeLink removes handle from group', () {
      final key1 = ('A-I1', 1, 5);
      final key2 = ('A-I2', 1, 5);
      final key3 = ('A-I3', 1, 5);

      manager.addLink(key1, key2);
      manager.addLink(key2, key3);
      final group = manager.handleLinkToGroup[key1];

      manager.removeLink(key2);

      expect(manager.handleLinkToGroup.containsKey(key2), isFalse);
      expect(manager.handleGroupToLink[group]!.length, equals(2));
      expect(manager.handleGroupToLink[group], contains(key1));
      expect(manager.handleGroupToLink[group], contains(key3));
    });

    test('removeLink deletes empty group', () {
      final key1 = ('A-I1', 1, 5);
      final key2 = ('A-I2', 1, 5);

      manager.addLink(key1, key2);
      final group = manager.handleLinkToGroup[key1];

      manager.removeLink(key1);
      manager.removeLink(key2);

      expect(manager.handleGroupToLink.containsKey(group), isFalse);
    });

    test('setEnforcedValue creates numeric group for unlinked handle', () {
      final key = ('A-I1', 1, 5);

      manager.setEnforcedValue(key, 42);

      expect(manager.handleLinkToGroup.containsKey(key), isTrue);
      expect(manager.handleLinkToGroup[key], isA<int>());
      expect(manager.handleGroupToValue[manager.handleLinkToGroup[key]], equals(42));
    });

    test('setEnforcedValue updates existing group enforced value', () {
      final key1 = ('A-I1', 1, 5);
      final key2 = ('A-I2', 1, 5);

      manager.addLink(key1, key2);
      manager.setEnforcedValue(key1, 42);

      expect(manager.handleGroupToValue[manager.handleLinkToGroup[key1]], equals(42));

      manager.setEnforcedValue(key2, 99);

      expect(manager.handleGroupToValue[manager.handleLinkToGroup[key2]], equals(99));
    });

    test('clearAll resets all state including maxGroupId', () {
      final key1 = ('A-I1', 1, 5);
      final key2 = ('A-I2', 1, 5);

      manager.addLink(key1, key2);
      manager.setEnforcedValue(key1, 42);
      manager.addBlock(('A-I3', 1, 5));

      manager.clearAll();

      expect(manager.handleLinkToGroup.isEmpty, isTrue);
      expect(manager.handleGroupToLink.isEmpty, isTrue);
      expect(manager.handleGroupToValue.isEmpty, isTrue);
      expect(manager.handleBlocks.isEmpty, isTrue);
      expect(manager.maxGroupId, equals(0));
    });
  });

  group('HandleLinkManager - Numeric-Only Groups', () {
    late HandleLinkManager manager;

    setUp(() {
      manager = HandleLinkManager();
    });

    test('all created groups are integers', () {
      // Create groups via addLink
      manager.addLink(('A-I1', 1, 5), ('A-I2', 1, 5));

      // Create groups via setEnforcedValue on unlinked handle
      manager.setEnforcedValue(('A-I3', 1, 5), 10);
      manager.setEnforcedValue(('A-I4', 1, 5), 20);

      // Verify all groups are integers
      for (final group in manager.handleGroupToLink.keys) {
        expect(group, isA<int>(), reason: 'Group ID $group should be int, not ${group.runtimeType}');
      }
      for (final group in manager.handleLinkToGroup.values) {
        expect(group, isA<int>(), reason: 'Group ID $group should be int, not ${group.runtimeType}');
      }
    });

    test('maxGroupId tracks highest group ID correctly', () {
      manager.addLink(('A-I1', 1, 5), ('A-I2', 1, 5)); // creates group 1
      expect(manager.maxGroupId, equals(1));

      manager.addLink(('A-I3', 1, 5), ('A-I4', 1, 5)); // creates group 2
      expect(manager.maxGroupId, equals(2));

      manager.setEnforcedValue(('A-I5', 1, 5), 10); // creates group 3
      expect(manager.maxGroupId, equals(3));
    });

    test('new groups increment from maxGroupId', () {
      manager.addLink(('A-I1', 1, 5), ('A-I2', 1, 5));
      final group1 = manager.handleLinkToGroup[('A-I1', 1, 5)];

      manager.addLink(('A-I3', 1, 5), ('A-I4', 1, 5));
      final group2 = manager.handleLinkToGroup[('A-I3', 1, 5)];

      expect(group2, equals(group1! + 1));
    });
  });

  group('HandleLinkManager - Import (Two-Pass Algorithm)', () {
    late HandleLinkManager manager;
    late Map<String, Slat> slats;
    late Map<String, Map<String, dynamic>> layerMap;

    setUp(() {
      manager = HandleLinkManager();
      // Create simple layer map for testing
      layerMap = {
        '1': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2'},
        '2': {'order': 1, 'top_helix': 'H2', 'bottom_helix': 'H5'},
      };
      // Create simple slats for testing
      slats = {
        '1-I1': Slat(1, '1-I1', '1', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)}),
        '1-I2': Slat(2, '1-I2', '1', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 1)}),
      };
    });

    /// Helper to create Excel data format
    /// Each slat has 6 rows: [slat_name, Position, h5-val, h5-link-group, h2-val, h2-link-group]
    List<List<dynamic>> createExcelData({
      required String slatName,
      required int maxLen,
      Map<int, int?>? h5Values,
      Map<int, int?>? h5Groups,
      Map<int, int?>? h2Values,
      Map<int, int?>? h2Groups,
    }) {
      // Row 0: slat name
      final row0 = <dynamic>[slatName, ...List.filled(maxLen, null)];
      // Row 1: positions
      final row1 = <dynamic>['Position', ...List.generate(maxLen, (i) => i + 1)];
      // Row 2: h5 values
      final row2 = <dynamic>['h5-val', ...List.generate(maxLen, (i) => h5Values?[i + 1] ?? '')];
      // Row 3: h5 groups
      final row3 = <dynamic>['h5-link-group', ...List.generate(maxLen, (i) => h5Groups?[i + 1] ?? '')];
      // Row 4: h2 values
      final row4 = <dynamic>['h2-val', ...List.generate(maxLen, (i) => h2Values?[i + 1] ?? '')];
      // Row 5: h2 groups
      final row5 = <dynamic>['h2-link-group', ...List.generate(maxLen, (i) => h2Groups?[i + 1] ?? '')];

      return [row0, row1, row2, row3, row4, row5];
    }

    test('import finds max group ID in first pass', () {
      // Create data with groups 5 and 10
      final data = [
        ...createExcelData(
          slatName: 'layer1-slat1',
          maxLen: 32,
          h5Values: {1: 42, 5: 99},
          h5Groups: {1: 5, 5: 10},
        ),
        ...createExcelData(
          slatName: 'layer1-slat2',
          maxLen: 32,
          h5Values: {1: 42},
          h5Groups: {1: 5}, // Same group 5
        ),
      ];

      manager.importFromExcelData(data, slats, layerMap);

      // maxGroupId should be 10 (the highest group found)
      expect(manager.maxGroupId, equals(10));
    });

    test('import assigns new IDs to enforced-only values without collision', () {
      // Create data with group 5, and an enforced-only value (no group)
      final data = createExcelData(
        slatName: 'layer1-slat1',
        maxLen: 32,
        h5Values: {1: 42, 5: 99}, // position 1 has group, position 5 is enforced-only
        h5Groups: {1: 5}, // only position 1 has a group
      );

      manager.importFromExcelData(data, slats, layerMap);

      // The enforced-only value at position 5 should get a new numeric group ID > 5
      final key5 = ('1-I1', 5, 5);
      expect(manager.handleLinkToGroup.containsKey(key5), isTrue);
      expect(manager.handleLinkToGroup[key5], isA<int>());
      expect((manager.handleLinkToGroup[key5] as int) > 5, isTrue);
      expect(manager.handleGroupToValue[manager.handleLinkToGroup[key5]], equals(99));
    });

    test('import handles enforced value with existing group', () {
      final data = createExcelData(
        slatName: 'layer1-slat1',
        maxLen: 32,
        h5Values: {1: 42},
        h5Groups: {1: 5},
      );

      manager.importFromExcelData(data, slats, layerMap);

      final key = ('1-I1', 1, 5);
      expect(manager.handleLinkToGroup[key], equals(5));
      expect(manager.handleGroupToValue[5], equals(42));
    });

    test('import handles blocked values (value=0)', () {
      final data = createExcelData(
        slatName: 'layer1-slat1',
        maxLen: 32,
        h5Values: {1: 0}, // blocked
      );

      manager.importFromExcelData(data, slats, layerMap);

      final key = ('1-I1', 1, 5);
      expect(manager.handleBlocks, contains(key));
      expect(manager.handleLinkToGroup.containsKey(key), isFalse);
    });

    test('import handles mixed data: groups, enforced-only, blocked', () {
      final data = createExcelData(
        slatName: 'layer1-slat1',
        maxLen: 32,
        h5Values: {1: 42, 2: 99, 3: 0}, // pos1: grouped, pos2: enforced-only, pos3: blocked
        h5Groups: {1: 5}, // only pos1 has group
      );

      manager.importFromExcelData(data, slats, layerMap);

      // Position 1: in group 5 with value 42
      final key1 = ('1-I1', 1, 5);
      expect(manager.handleLinkToGroup[key1], equals(5));
      expect(manager.handleGroupToValue[5], equals(42));

      // Position 2: enforced-only, should have new numeric group > 5
      final key2 = ('1-I1', 2, 5);
      expect(manager.handleLinkToGroup.containsKey(key2), isTrue);
      expect(manager.handleLinkToGroup[key2], isA<int>());
      expect((manager.handleLinkToGroup[key2] as int) > 5, isTrue);
      expect(manager.handleGroupToValue[manager.handleLinkToGroup[key2]], equals(99));

      // Position 3: blocked
      final key3 = ('1-I1', 3, 5);
      expect(manager.handleBlocks, contains(key3));
    });
  });

  group('HandleLinkManager - Export', () {
    late HandleLinkManager manager;
    late Map<String, Slat> slats;
    late Map<String, Map<String, dynamic>> layerMap;

    setUp(() {
      manager = HandleLinkManager();
      layerMap = {
        '1': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2'},
      };
      slats = {
        '1-I1': Slat(1, '1-I1', '1', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)}),
      };
    });

    test('export includes all groups (no type filtering)', () {
      // Create linked handles and enforced-only handles
      manager.addLink(('1-I1', 1, 5), ('1-I1', 2, 5));
      manager.setEnforcedValue(('1-I1', 3, 5), 99);

      final exported = manager.exportToExcelData(slats, layerMap);

      // Find h5-link-group row (row index 3 for the first slat)
      final groupRow = exported[3];

      // Position 1 and 2 should have group IDs
      expect(groupRow[1], isA<int>());
      expect(groupRow[2], isA<int>());
      expect(groupRow[1], equals(groupRow[2])); // same group

      // Position 3 (enforced-only) should also have a group ID now
      expect(groupRow[3], isA<int>());
    });

    test('export preserves group IDs correctly', () {
      manager.addLink(('1-I1', 1, 5), ('1-I1', 2, 5));
      final groupId = manager.handleLinkToGroup[('1-I1', 1, 5)];

      final exported = manager.exportToExcelData(slats, layerMap);
      final groupRow = exported[3];

      expect(groupRow[1], equals(groupId));
      expect(groupRow[2], equals(groupId));
    });

    test('export preserves enforced values', () {
      manager.addLink(('1-I1', 1, 5), ('1-I1', 2, 5));
      manager.setEnforcedValue(('1-I1', 1, 5), 42);

      final exported = manager.exportToExcelData(slats, layerMap);
      final valRow = exported[2]; // h5-val row

      expect(valRow[1], equals(42));
      expect(valRow[2], equals(42)); // should be same since linked
    });

    test('export handles blocked values', () {
      manager.addBlock(('1-I1', 1, 5));

      final exported = manager.exportToExcelData(slats, layerMap);
      final valRow = exported[2]; // h5-val row

      expect(valRow[1], equals(0));
    });
  });

  group('HandleLinkManager - Round-Trip', () {
    late Map<String, Slat> slats;
    late Map<String, Map<String, dynamic>> layerMap;

    setUp(() {
      layerMap = {
        '1': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2'},
      };
      slats = {
        '1-I1': Slat(1, '1-I1', '1', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 0)}),
        '1-I2': Slat(2, '1-I2', '1', {for (int i = 1; i <= 32; i++) i: Offset(i.toDouble(), 1)}),
      };
    });

    test('export then import preserves all link groups', () {
      final original = HandleLinkManager();
      original.addLink(('1-I1', 1, 5), ('1-I1', 2, 5));
      original.addLink(('1-I1', 5, 5), ('1-I2', 5, 5));

      final exported = original.exportToExcelData(slats, layerMap);

      final reimported = HandleLinkManager();
      reimported.importFromExcelData(exported, slats, layerMap);

      // Verify the link structure is preserved
      expect(reimported.handleLinkToGroup[('1-I1', 1, 5)], equals(reimported.handleLinkToGroup[('1-I1', 2, 5)]));
      expect(reimported.handleLinkToGroup[('1-I1', 5, 5)], equals(reimported.handleLinkToGroup[('1-I2', 5, 5)]));
      // Two different groups
      expect(reimported.handleLinkToGroup[('1-I1', 1, 5)], isNot(equals(reimported.handleLinkToGroup[('1-I1', 5, 5)])));
    });

    test('export then import preserves enforced-only values', () {
      final original = HandleLinkManager();
      original.setEnforcedValue(('1-I1', 1, 5), 42);
      original.setEnforcedValue(('1-I1', 2, 5), 99);

      final exported = original.exportToExcelData(slats, layerMap);

      final reimported = HandleLinkManager();
      reimported.importFromExcelData(exported, slats, layerMap);

      // Verify enforced values are preserved
      expect(reimported.getEnforceValue(('1-I1', 1, 5)), equals(42));
      expect(reimported.getEnforceValue(('1-I1', 2, 5)), equals(99));
    });

    test('multiple export/import cycles maintain consistency', () {
      var manager = HandleLinkManager();
      manager.addLink(('1-I1', 1, 5), ('1-I1', 2, 5));
      manager.setEnforcedValue(('1-I1', 1, 5), 42);
      manager.setEnforcedValue(('1-I1', 3, 5), 99);
      manager.addBlock(('1-I1', 4, 5));

      // Do 3 round-trips
      for (int i = 0; i < 3; i++) {
        final exported = manager.exportToExcelData(slats, layerMap);
        manager = HandleLinkManager();
        manager.importFromExcelData(exported, slats, layerMap);
      }

      // Verify everything is still correct
      expect(manager.handleLinkToGroup[('1-I1', 1, 5)], equals(manager.handleLinkToGroup[('1-I1', 2, 5)]));
      expect(manager.getEnforceValue(('1-I1', 1, 5)), equals(42));
      expect(manager.getEnforceValue(('1-I1', 3, 5)), equals(99));
      expect(manager.handleBlocks, contains(('1-I1', 4, 5)));
    });
  });
}
