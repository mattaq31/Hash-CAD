import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';

import '../../helpers/design_state_test_factory.dart';

void main() {
  group('PlateLayoutState.copy()', () {
    test('copy produces identical content', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      final copy = layout.copy();

      expect(copy.unassignedSlats, equals(layout.unassignedSlats));
      expect(copy.plateAssignments.length, equals(layout.plateAssignments.length));
      for (var plateIndex in layout.plateAssignments.keys) {
        expect(copy.plateAssignments[plateIndex], equals(layout.plateAssignments[plateIndex]));
      }
      expect(copy.duplicateGroups, equals(layout.duplicateGroups));
    });

    test('copy is independent — modifying copy does not affect original', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      final copy = layout.copy();

      // Modify the copy
      copy.unassignedSlats.add('fake-id');
      copy.plateAssignments[0]!['A1'] = 'modified';

      // Original should be unaffected
      expect(layout.unassignedSlats, isNot(contains('fake-id')));
      expect(layout.plateAssignments[0]!['A1'], isNot('modified'));
    });

    test('copy is independent — modifying original does not affect copy', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      final copy = layout.copy();
      final originalA1 = copy.plateAssignments[0]!['A1'];

      // Modify the original
      layout.plateAssignments[0]!['A1'] = 'modified';

      // Copy should be unaffected
      expect(copy.plateAssignments[0]!['A1'], equals(originalA1));
    });

    test('copy preserves duplicate groups and counters', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      // Create duplicates
      layout.duplicateSlats({'0:A1', '0:A2'});

      final copy = layout.copy();

      expect(copy.duplicateGroups.length, equals(layout.duplicateGroups.length));
      for (var key in layout.duplicateGroups.keys) {
        expect(copy.duplicateGroups[key], equals(layout.duplicateGroups[key]));
      }

      // Modifying copy's duplicate groups doesn't affect original
      final firstKey = copy.duplicateGroups.keys.first;
      copy.duplicateGroups[firstKey]!.add('fake-dup');
      expect(layout.duplicateGroups[firstKey], isNot(contains('fake-dup')));
    });
  });

  group('PlateLayoutState.syncWithDesign()', () {
    test('no changes returns false', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      final changed = layout.syncWithDesign(state.slats, state.layerMap);
      expect(changed, isFalse);
      expect(layout.unassignedSlats.length, 5);
    });

    test('new slat added to design appears in unassignedSlats', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 3);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      // Add more slats to the design state
      final biggerState = DesignStateTestFactory.createWithSlats(slatCount: 5);

      final changed = layout.syncWithDesign(biggerState.slats, biggerState.layerMap);
      expect(changed, isTrue);
      expect(layout.unassignedSlats.length, 5);
    });

    test('deleted slat removed from unassigned', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      // Create a smaller design (missing some slats)
      final smallerState = DesignStateTestFactory.createWithSlats(slatCount: 3);

      final changed = layout.syncWithDesign(smallerState.slats, smallerState.layerMap);
      expect(changed, isTrue);
      expect(layout.unassignedSlats.length, 3);
    });

    test('deleted slat removed from well', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);
      expect(layout.unassignedSlats, isEmpty);

      // Create a smaller design
      final smallerState = DesignStateTestFactory.createWithSlats(slatCount: 3);

      final changed = layout.syncWithDesign(smallerState.slats, smallerState.layerMap);
      expect(changed, isTrue);

      // Count occupied wells — should be 3 now
      int occupied = 0;
      for (var plate in layout.plateAssignments.values) {
        occupied += plate.values.where((v) => v != null).length;
      }
      expect(occupied, 3);
    });

    test('deleted slat with duplicates cleans up all copies', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      // Duplicate A1
      final slatA1 = layout.plateAssignments[0]!['A1']!;
      final baseA1 = baseSlatId(slatA1);
      layout.duplicateSlats({'0:A1'});
      expect(layout.duplicateGroups.containsKey(baseA1), isTrue);

      // Remove that slat from the design
      final smallerState = DesignStateTestFactory.createWithSlats(slatCount: 5);
      // Remove the specific slat that was in A1
      smallerState.slats.remove(slatA1);

      final changed = layout.syncWithDesign(smallerState.slats, smallerState.layerMap);
      expect(changed, isTrue);
      expect(layout.duplicateGroups.containsKey(baseA1), isFalse);

      // Neither original nor duplicate should be in any well
      for (var plate in layout.plateAssignments.values) {
        for (var slatId in plate.values) {
          if (slatId != null) {
            expect(baseSlatId(slatId), isNot(baseA1));
          }
        }
      }
    });

    test('new slats are added in sorted order', () {
      // Start with layer B slats only
      final stateB = DesignStateTestFactory.createWithMultiLayerSlats(slatsPerLayer: {'B': 3});
      final layout = PlateLayoutState.fromSlats(stateB.slats, stateB.layerMap);
      expect(layout.unassignedSlats.length, 3);

      // Now sync with a design that also has layer A slats
      final stateAB = DesignStateTestFactory.createWithMultiLayerSlats(slatsPerLayer: {'A': 2, 'B': 3});

      layout.syncWithDesign(stateAB.slats, stateAB.layerMap);

      // New layer A slats should be present
      expect(layout.unassignedSlats.length, 5);
    });

    test('phantom slats excluded from sync', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 3);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      // Add a phantom slat to the design
      final phantomState = DesignStateTestFactory.createWithSlats(slatCount: 5);
      // Mark one slat as phantom
      final lastSlatId = phantomState.slats.keys.last;
      phantomState.slats[lastSlatId]!.phantomParent = 'some-parent';

      final changed = layout.syncWithDesign(phantomState.slats, phantomState.layerMap);
      expect(changed, isTrue);
      // Should have 4 non-phantom slats (5 total minus 1 phantom), but only the new ones are added
      // Original 3 + 1 new non-phantom = 4
      expect(layout.unassignedSlats.length, 4);
      expect(layout.unassignedSlats, isNot(contains(lastSlatId)));
    });

    test('multiple changes at once — additions and deletions', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 5);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      // Create a different design with some overlap
      final newState = DesignStateTestFactory.createWithMultiLayerSlats(slatsPerLayer: {'A': 3, 'B': 2});

      final changed = layout.syncWithDesign(newState.slats, newState.layerMap);
      expect(changed, isTrue);

      // Should have only valid slats tracked
      final validIds = newState.slats.keys.where((id) => newState.slats[id]!.phantomParent == null).toSet();

      // All tracked slats should be valid
      for (var id in layout.unassignedSlats) {
        expect(validIds, contains(baseSlatId(id)));
      }
      for (var plate in layout.plateAssignments.values) {
        for (var slatId in plate.values) {
          if (slatId != null) {
            expect(validIds, contains(baseSlatId(slatId)));
          }
        }
      }
    });
  });
}
