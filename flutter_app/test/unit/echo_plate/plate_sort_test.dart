import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/slats.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';

import '../../helpers/design_state_test_factory.dart';
import '../../helpers/test_helpers.dart';

void main() {
  group('sortSlatsForPlateAssignment', () {
    test('excludes phantom slats', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 3);

      // Make one slat a phantom
      final phantomId = state.slats.keys.first;
      state.slats[phantomId]!.setPhantom('some-parent');

      final sorted = sortSlatsForPlateAssignment(state.slats, state.layerMap);
      final ids = sorted.map((e) => e.key).toList();

      expect(ids, isNot(contains(phantomId)));
      expect(ids.length, 2);
    });

    test('sorts by layer order first then numericID', () {
      final state = DesignStateTestFactory.createWithMultiLayerSlats(
        slatsPerLayer: {'A': 3, 'B': 2},
      );

      final sorted = sortSlatsForPlateAssignment(state.slats, state.layerMap);
      final ids = sorted.map((e) => e.key).toList();

      // Layer A (order 0) should come before layer B (order 1)
      final layerAIds = ids.where((id) => id.startsWith('A-')).toList();
      final layerBIds = ids.where((id) => id.startsWith('B-')).toList();

      // All A slats before B slats
      final lastAIndex = ids.lastIndexOf(layerAIds.last);
      final firstBIndex = ids.indexOf(layerBIds.first);
      expect(lastAIndex, lessThan(firstBIndex));

      // Within each layer, sorted by numericID
      for (int i = 1; i < layerAIds.length; i++) {
        final prevSlat = state.slats[layerAIds[i - 1]]!;
        final currSlat = state.slats[layerAIds[i]]!;
        expect(prevSlat.numericID, lessThan(currSlat.numericID));
      }
    });

    test('handles empty slat map', () {
      final sorted = sortSlatsForPlateAssignment({}, {});
      expect(sorted, isEmpty);
    });

    test('handles single slat', () {
      final coords = createTestSlatCoordinates(const Offset(0, 0));
      final slat = Slat(1, 'A-I1', 'A', coords);
      final slats = {'A-I1': slat};
      final layerMap = {
        'A': {'order': 0}
      };

      final sorted = sortSlatsForPlateAssignment(slats, layerMap as Map<String, Map<String, dynamic>>);
      expect(sorted.length, 1);
      expect(sorted.first.key, 'A-I1');
    });
  });
}
