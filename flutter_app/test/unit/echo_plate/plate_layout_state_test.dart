import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';

import '../../helpers/design_state_test_factory.dart';

void main() {
  group('PlateLayoutState — autoAssign', () {
    test('distributes slats across plates filling 96 wells per plate', () {
      final state = DesignStateTestFactory.createWithMultiLayerSlats(
        slatsPerLayer: {'A': 50, 'B': 50},
      );

      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      expect(layout.unassignedSlats.length, 100);
      expect(layout.plateAssignments.length, 1); // starts with 1 empty plate

      layout.autoAssign(state.slats, state.layerMap);

      expect(layout.unassignedSlats, isEmpty);
      // 100 slats → 96 on plate 0, 4 on plate 1
      expect(layout.plateAssignments.length, 2);

      // Count assigned slats
      int assignedCount = 0;
      for (var plate in layout.plateAssignments.values) {
        assignedCount += plate.values.where((v) => v != null).length;
      }
      expect(assignedCount, 100);
    });

    test('creates correct plate count for exactly 96 slats', () {
      final state = DesignStateTestFactory.createWithMultiLayerSlats(
        slatsPerLayer: {'A': 48, 'B': 48},
      );

      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      layout.autoAssign(state.slats, state.layerMap);

      expect(layout.plateAssignments.length, 1);
      expect(layout.unassignedSlats, isEmpty);
    });

    test('handles empty slats', () {
      final state = DesignStateTestFactory.create();

      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      expect(layout.unassignedSlats, isEmpty);

      layout.autoAssign(state.slats, state.layerMap);
      expect(layout.unassignedSlats, isEmpty);
      expect(layout.plateAssignments.length, 1);
    });
  });

  group('PlateLayoutState — moveSlatFromSidebarToWell', () {
    test('moves slat to empty well', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 3);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      final slatId = layout.unassignedSlats.first;
      layout.moveSlatFromSidebarToWell(slatId, 0, 'A1');

      expect(layout.unassignedSlats, isNot(contains(slatId)));
      expect(layout.plateAssignments[0]!['A1'], slatId);
    });

    test('displaces existing slat back to sidebar when target is occupied', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 3);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      final firstSlat = layout.unassignedSlats[0];
      final secondSlat = layout.unassignedSlats[1];

      layout.moveSlatFromSidebarToWell(firstSlat, 0, 'A1');
      layout.moveSlatFromSidebarToWell(secondSlat, 0, 'A1');

      expect(layout.plateAssignments[0]!['A1'], secondSlat);
      expect(layout.unassignedSlats, contains(firstSlat));
      expect(layout.unassignedSlats, isNot(contains(secondSlat)));
    });
  });

  group('PlateLayoutState — moveSlatFromWellToSidebar', () {
    test('returns slat to sidebar and clears well', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 2);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      final slatId = layout.unassignedSlats.first;
      layout.moveSlatFromSidebarToWell(slatId, 0, 'B3');
      expect(layout.plateAssignments[0]!['B3'], slatId);

      layout.moveSlatFromWellToSidebar(0, 'B3');
      expect(layout.plateAssignments[0]!['B3'], isNull);
      expect(layout.unassignedSlats, contains(slatId));
    });

    test('no-op on empty well', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 1);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
      final countBefore = layout.unassignedSlats.length;

      layout.moveSlatFromWellToSidebar(0, 'H12');
      expect(layout.unassignedSlats.length, countBefore);
    });
  });

  group('PlateLayoutState — moveSlatBetweenWells', () {
    test('swaps contents of two wells', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 2);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      final slatA = layout.unassignedSlats[0];
      final slatB = layout.unassignedSlats[1];
      layout.moveSlatFromSidebarToWell(slatA, 0, 'A1');
      layout.moveSlatFromSidebarToWell(slatB, 0, 'A2');

      layout.moveSlatBetweenWells(0, 'A1', 0, 'A2');
      expect(layout.plateAssignments[0]!['A1'], slatB);
      expect(layout.plateAssignments[0]!['A2'], slatA);
    });

    test('moves slat to empty well leaving source empty', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 1);
      final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);

      final slatId = layout.unassignedSlats.first;
      layout.moveSlatFromSidebarToWell(slatId, 0, 'A1');

      layout.moveSlatBetweenWells(0, 'A1', 0, 'C5');
      expect(layout.plateAssignments[0]!['A1'], isNull);
      expect(layout.plateAssignments[0]!['C5'], slatId);
    });
  });
}
