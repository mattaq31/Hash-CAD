import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';

import '../../helpers/design_state_test_factory.dart';

/// Helper: creates a layout with [slatCount] slats auto-assigned to plates.
PlateLayoutState _autoAssignedLayout(int slatCount) {
  final state = DesignStateTestFactory.createWithSlats(slatCount: slatCount);
  final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
  layout.autoAssign(state.slats, state.layerMap);
  return layout;
}

/// Helper: finds the well key ("plate:well") for a given slatId.
String? _findWellKey(PlateLayoutState layout, String slatId) {
  for (var pEntry in layout.plateAssignments.entries) {
    for (var wEntry in pEntry.value.entries) {
      if (wEntry.value == slatId) return '${pEntry.key}:${wEntry.key}';
    }
  }
  return null;
}

/// Helper: counts total occupied wells across all plates.
int _occupiedCount(PlateLayoutState layout) {
  int count = 0;
  for (var plate in layout.plateAssignments.values) {
    count += plate.values.where((v) => v != null).length;
  }
  return count;
}

void main() {
  group('baseSlatId / isDuplicateSlatId', () {
    test('baseSlatId strips ~N suffix', () {
      expect(baseSlatId('A-I1~2'), 'A-I1');
      expect(baseSlatId('A-I1~99'), 'A-I1');
    });

    test('baseSlatId returns original when no suffix', () {
      expect(baseSlatId('A-I1'), 'A-I1');
    });

    test('isDuplicateSlatId detects tilde', () {
      expect(isDuplicateSlatId('A-I1~2'), isTrue);
      expect(isDuplicateSlatId('A-I1'), isFalse);
    });
  });

  group('PlateLayoutState — duplicateSlats', () {
    test('duplicates a single well into an empty row', () {
      final layout = _autoAssignedLayout(5);
      // All 5 slats are in row A (A1-A5). Rows B-H are empty.
      final slatId = layout.plateAssignments[0]!['A1']!;
      final newKeys = layout.duplicateSlats({'0:A1'});

      expect(newKeys.length, 1);
      final newKey = newKeys.first;
      final parts = newKey.split(':');
      final newWell = parts[1];
      // Should be in column 1 (same column as A1), but a different row
      expect(newWell.substring(1), '1'); // same column
      expect(newWell[0], isNot('A')); // different row

      // The new well should contain a duplicate ID
      final newSlatId = layout.plateAssignments[int.parse(parts[0])]![newWell]!;
      expect(newSlatId, contains('~'));
      expect(baseSlatId(newSlatId), baseSlatId(slatId));

      // Original should still be in place
      expect(layout.plateAssignments[0]!['A1'], slatId);
    });

    test('duplicates preserve column positions across multiple columns', () {
      final layout = _autoAssignedLayout(5);
      // Slats are in A1..A5. Select A2 and A4.
      final newKeys = layout.duplicateSlats({'0:A2', '0:A4'});

      expect(newKeys.length, 2);
      final newWells = newKeys.map((k) => k.split(':')[1]).toSet();
      final newCols = newWells.map((w) => w.substring(1)).toSet();
      expect(newCols, containsAll(['2', '4']));

      // Both should be in the same row (since originals are in the same row)
      final newRows = newWells.map((w) => w[0]).toSet();
      expect(newRows.length, 1);
    });

    test('duplicates across multiple rows preserve relative row layout', () {
      final layout = _autoAssignedLayout(20);
      // 20 slats fill A1-A12 (12) + B1-B8 (8). Select one from row A and one from row B.
      final keyA3 = '0:A3';
      final keyB2 = '0:B2';
      final newKeys = layout.duplicateSlats({keyA3, keyB2});

      expect(newKeys.length, 2);
      final wellsByKey = <String, String>{};
      for (var k in newKeys) {
        final parts = k.split(':');
        wellsByKey[k] = parts[1];
      }

      // Find the wells and check relative row offset is preserved
      final newWells = wellsByKey.values.toList()..sort();
      final rows = newWells.map((w) => w[0]).toList();
      final cols = newWells.map((w) => int.parse(w.substring(1))).toList();

      // Original A3 and B2 differ by 1 row; duplicates should too
      final rowIndices = rows.map((r) => 'ABCDEFGH'.indexOf(r)).toList()..sort();
      expect(rowIndices[1] - rowIndices[0], 1);
      // Columns should match originals
      expect(cols.toSet(), containsAll([2, 3]));
    });

    test('registers duplicate group correctly', () {
      final layout = _autoAssignedLayout(3);
      final slatId = layout.plateAssignments[0]!['A1']!;
      final base = baseSlatId(slatId);

      expect(layout.duplicateGroups, isEmpty);

      layout.duplicateSlats({'0:A1'});

      expect(layout.duplicateGroups.containsKey(base), isTrue);
      expect(layout.duplicateGroups[base]!.length, 2); // original + copy
      expect(layout.duplicateGroups[base]!, contains(slatId));
    });

    test('multiple duplications increment counter', () {
      final layout = _autoAssignedLayout(3);
      final slatId = layout.plateAssignments[0]!['A1']!;
      final base = baseSlatId(slatId);

      final keys1 = layout.duplicateSlats({'0:A1'});
      final keys2 = layout.duplicateSlats({'0:A1'});

      // Should have 3 members: original + two copies
      expect(layout.duplicateGroups[base]!.length, 3);

      // The duplicate IDs should be distinct
      final id1 = layout.plateAssignments[0]![keys1.first.split(':')[1]]!;
      final id2 = layout.plateAssignments[0]![keys2.first.split(':')[1]]!;
      expect(id1, isNot(id2));
    });

    test('creates new plate when no empty rows available', () {
      final layout = _autoAssignedLayout(96);
      // Plate 0 is completely full
      expect(layout.plateAssignments.length, 1);

      final newKeys = layout.duplicateSlats({'0:A1'});
      expect(newKeys.length, 1);
      // Should have created a second plate
      expect(layout.plateAssignments.length, 2);
      expect(newKeys.first.startsWith('1:'), isTrue);
    });

    test('empty selection returns empty set', () {
      final layout = _autoAssignedLayout(3);
      final newKeys = layout.duplicateSlats({});
      expect(newKeys, isEmpty);
    });

    test('selection on empty well is skipped', () {
      final layout = _autoAssignedLayout(3);
      final newKeys = layout.duplicateSlats({'0:H12'});
      expect(newKeys, isEmpty);
    });

    test('total occupied wells increases by number of duplicates', () {
      final layout = _autoAssignedLayout(10);
      final beforeCount = _occupiedCount(layout);
      layout.duplicateSlats({'0:A1', '0:A3', '0:A5'});
      expect(_occupiedCount(layout), beforeCount + 3);
    });
  });

  group('PlateLayoutState — getDuplicateSiblings', () {
    test('returns singleton set for non-duplicated slat', () {
      final layout = _autoAssignedLayout(3);
      final slatId = layout.plateAssignments[0]!['A1']!;
      final siblings = layout.getDuplicateSiblings(slatId);
      expect(siblings, {slatId});
    });

    test('returns all siblings after duplication', () {
      final layout = _autoAssignedLayout(3);
      final slatId = layout.plateAssignments[0]!['A1']!;
      final newKeys = layout.duplicateSlats({'0:A1'});
      final newWell = newKeys.first.split(':')[1];
      final dupId = layout.plateAssignments[0]![newWell]!;

      final siblings = layout.getDuplicateSiblings(slatId);
      expect(siblings, contains(slatId));
      expect(siblings, contains(dupId));

      // Getting siblings from the duplicate returns the same group
      expect(layout.getDuplicateSiblings(dupId), siblings);
    });
  });

  group('PlateLayoutState — duplicate-aware removal', () {
    test('removing a duplicate copy does not add it to shelf', () {
      final layout = _autoAssignedLayout(3);
      final slatId = layout.plateAssignments[0]!['A1']!;
      final newKeys = layout.duplicateSlats({'0:A1'});
      final newKeyParts = newKeys.first.split(':');
      final dupPlate = int.parse(newKeyParts[0]);
      final dupWell = newKeyParts[1];

      final shelfBefore = layout.unassignedSlats.length;
      layout.moveSlatFromWellToSidebar(dupPlate, dupWell);

      // Duplicate disappears — shelf should NOT grow (original still on plate)
      expect(layout.unassignedSlats.length, shelfBefore);
      expect(layout.plateAssignments[dupPlate]![dupWell], isNull);
      // Original should still be on plate
      expect(layout.plateAssignments[0]!['A1'], slatId);
    });

    test('removing the last copy returns base ID to shelf', () {
      final layout = _autoAssignedLayout(3);
      final slatId = layout.plateAssignments[0]!['A1']!;
      final base = baseSlatId(slatId);
      final newKeys = layout.duplicateSlats({'0:A1'});
      final newKeyParts = newKeys.first.split(':');
      final dupPlate = int.parse(newKeyParts[0]);
      final dupWell = newKeyParts[1];

      // Remove the original
      layout.moveSlatFromWellToSidebar(0, 'A1');
      // Duplicate still on plate — original just disappears
      expect(layout.unassignedSlats, isNot(contains(base)));

      // Now remove the last copy
      layout.moveSlatFromWellToSidebar(dupPlate, dupWell);
      // Base ID should return to shelf
      expect(layout.unassignedSlats, contains(base));
      // Duplicate group should be cleaned up
      expect(layout.duplicateGroups.containsKey(base), isFalse);
    });

    test('removeSelected with duplicates applies same logic', () {
      final layout = _autoAssignedLayout(3);
      final slatId = layout.plateAssignments[0]!['A1']!;
      final newKeys = layout.duplicateSlats({'0:A1'});

      final shelfBefore = layout.unassignedSlats.length;
      // Remove only the duplicate via removeSelected
      layout.removeSelected(newKeys);

      // Duplicate gone, original still in place, shelf unchanged
      expect(layout.unassignedSlats.length, shelfBefore);
      expect(layout.plateAssignments[0]!['A1'], slatId);
    });

    test('removeAll collapses duplicates to base IDs', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      // Duplicate two slats
      layout.duplicateSlats({'0:A1', '0:A2'});
      expect(_occupiedCount(layout), 7); // 5 originals + 2 copies

      layout.removeAll(state.slats, state.layerMap);

      // All wells empty, only base IDs on shelf (no ~N suffixes)
      expect(_occupiedCount(layout), 0);
      expect(layout.unassignedSlats.length, 5);
      for (var id in layout.unassignedSlats) {
        expect(isDuplicateSlatId(id), isFalse);
      }
      expect(layout.duplicateGroups, isEmpty);
    });

    test('removeAll re-sorts shelf by layer order then numericID', () {
      final state = DesignStateTestFactory.createWithMultiLayerSlats(
        slatsPerLayer: {'A': 3, 'B': 3},
      );
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      layout.removeAll(state.slats, state.layerMap);

      // Verify sorted: all layer A before layer B, numeric order within
      final slats = state.slats;
      for (int i = 1; i < layout.unassignedSlats.length; i++) {
        final prev = slats[layout.unassignedSlats[i - 1]]!;
        final curr = slats[layout.unassignedSlats[i]]!;
        final orderPrev = state.layerMap[prev.layer]?['order'] ?? 0;
        final orderCurr = state.layerMap[curr.layer]?['order'] ?? 0;
        if (orderPrev == orderCurr) {
          expect(prev.numericID, lessThanOrEqualTo(curr.numericID));
        } else {
          expect(orderPrev, lessThan(orderCurr));
        }
      }
    });
  });

  group('PlateLayoutState — removeSelected', () {
    test('removes selected wells and returns slats to shelf', () {
      final layout = _autoAssignedLayout(5);
      final slatA1 = layout.plateAssignments[0]!['A1']!;
      final slatA3 = layout.plateAssignments[0]!['A3']!;

      layout.removeSelected({'0:A1', '0:A3'});

      expect(layout.plateAssignments[0]!['A1'], isNull);
      expect(layout.plateAssignments[0]!['A3'], isNull);
      expect(layout.unassignedSlats, contains(slatA1));
      expect(layout.unassignedSlats, contains(slatA3));
      // Other slats unaffected
      expect(layout.plateAssignments[0]!['A2'], isNotNull);
    });

    test('ignores empty wells in selection', () {
      final layout = _autoAssignedLayout(3);
      final shelfBefore = layout.unassignedSlats.length;
      layout.removeSelected({'0:H12'}); // empty well
      expect(layout.unassignedSlats.length, shelfBefore);
    });
  });

  group('PlateLayoutState — autoAssign columnsThreeToTenOnly', () {
    test('only fills columns 3-10 when flag is set', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 10);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap, columnsThreeToTenOnly: true);

      for (var plate in layout.plateAssignments.values) {
        for (var entry in plate.entries) {
          if (entry.value != null) {
            final col = int.parse(entry.key.substring(1));
            expect(col, greaterThanOrEqualTo(3));
            expect(col, lessThanOrEqualTo(10));
          }
        }
      }
    });

    test('columns 1, 2, 11, 12 remain empty with flag', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 10);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap, columnsThreeToTenOnly: true);

      for (var plate in layout.plateAssignments.values) {
        for (var entry in plate.entries) {
          final col = int.parse(entry.key.substring(1));
          if (col < 3 || col > 10) {
            expect(entry.value, isNull, reason: 'Column $col should be empty');
          }
        }
      }
    });
  });
}
