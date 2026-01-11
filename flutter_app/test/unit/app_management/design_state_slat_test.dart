import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/app_management/shared_app_state.dart';

import '../../helpers/test_helpers.dart';
import '../../helpers/design_state_test_factory.dart';

void main() {
  group('DesignState - Slat Addition', () {
    late DesignState state;

    setUp(() {
      state = DesignStateTestFactory.create();
    });

    test('addSlats adds single slat to empty layer', () {
      // Arrange
      const layer = 'A';
      final coordinates = buildSlatCoordinatesMap([const Offset(0, 0)]);

      // Act
      state.addSlats(layer, coordinates);

      // Assert - Slat creation
      expect(state.slats.length, equals(1));
      expect(state.slats.containsKey('A-I1'), isTrue);

      final slat = state.slats['A-I1']!;
      expect(slat.layer, equals('A'));
      expect(slat.numericID, equals(1));
      expect(slat.slatPositionToCoordinate.length, equals(32));
    });

    test('addSlats updates occupiedGridPoints correctly', () {
      // Arrange
      const layer = 'A';
      final origin = const Offset(0, 0);
      final coordinates = buildSlatCoordinatesMap([origin]);

      // Act
      state.addSlats(layer, coordinates);

      // Assert - Occupancy map
      expect(state.occupiedGridPoints.containsKey('A'), isTrue);
      expect(state.occupiedGridPoints['A']!.length, equals(32));

      // Verify each position is tracked
      for (int i = 0; i < 32; i++) {
        final coord = Offset(origin.dx + i, origin.dy);
        expect(state.occupiedGridPoints['A']![coord], equals('A-I1'));
      }
    });

    test('addSlats updates layer metadata', () {
      // Arrange
      const layer = 'A';
      final coordinates = buildSlatCoordinatesMap([const Offset(0, 0)]);
      final nextIdBefore = state.layerMap['A']!['next_slat_id'] as int;
      final slatCountBefore = state.layerMap['A']!['slat_count'] as int;

      // Act
      state.addSlats(layer, coordinates);

      // Assert
      expect(state.layerMap['A']!['next_slat_id'], equals(nextIdBefore + 1));
      expect(state.layerMap['A']!['slat_count'], equals(slatCountBefore + 1));
    });

    test('addSlats adds multiple slats with correct IDs', () {
      // Arrange
      const layer = 'A';
      final coordinates = buildSlatCoordinatesMap([
        const Offset(0, 0),
        const Offset(0, 35),
        const Offset(0, 70),
      ]);

      // Act
      state.addSlats(layer, coordinates);

      // Assert
      expect(state.slats.length, equals(3));
      expect(state.slats.containsKey('A-I1'), isTrue);
      expect(state.slats.containsKey('A-I2'), isTrue);
      expect(state.slats.containsKey('A-I3'), isTrue);
      expect(state.layerMap['A']!['slat_count'], equals(3));
    });

    test('addSlats sets hammingValueValid to false', () {
      // Arrange
      state.hammingValueValid = true;
      final coordinates = buildSlatCoordinatesMap([const Offset(0, 0)]);

      // Act
      state.addSlats('A', coordinates);

      // Assert
      expect(state.hammingValueValid, isFalse);
    });

    test('addSlats to different layers maintains separate tracking', () {
      // Arrange
      final coordsA = buildSlatCoordinatesMap([const Offset(0, 0)]);
      final coordsB = buildSlatCoordinatesMap([const Offset(0, 35)]);

      // Act
      state.addSlats('A', coordsA);
      state.addSlats('B', coordsB);

      // Assert
      expect(state.slats.length, equals(2));
      expect(state.slats['A-I1']!.layer, equals('A'));
      expect(state.slats['B-I1']!.layer, equals('B'));
      expect(state.occupiedGridPoints['A']!.length, equals(32));
      expect(state.occupiedGridPoints['B']!.length, equals(32));
    });

    test('addSlats applies slatAdditionType to created slats', () {
      // Arrange
      state.slatAdditionType = 'double_barrel';
      final coordinates = buildSlatCoordinatesMap([const Offset(0, 0)]);

      // Act
      state.addSlats('A', coordinates);

      // Assert
      expect(state.slats['A-I1']!.slatType, equals('double_barrel'));
    });

    test('slat has correct bidirectional coordinate mapping', () {
      // Arrange
      final coordinates = buildSlatCoordinatesMap([const Offset(0, 0)]);

      // Act
      state.addSlats('A', coordinates);

      // Assert
      final slat = state.slats['A-I1']!;
      for (var entry in slat.slatPositionToCoordinate.entries) {
        final position = entry.key;
        final coord = entry.value;
        expect(slat.slatCoordinateToPosition[coord], equals(position));
      }
    });

    test('slat center coordinate is calculated correctly', () {
      // Arrange
      final origin = const Offset(0, 0);
      final coordinates = buildSlatCoordinatesMap([origin]);

      // Act
      state.addSlats('A', coordinates);

      // Assert - center of positions 0-31 should be at x=15.5
      final slat = state.slats['A-I1']!;
      expect(slat.centerCoordinate.dx, equals(15.5));
      expect(slat.centerCoordinate.dy, equals(0.0));
    });
  });

  group('DesignState - Slat Deletion', () {
    late DesignState state;

    setUp(() {
      state = DesignStateTestFactory.createWithSlats(slatCount: 3);
    });

    test('removeSlat removes slat from slats map', () {
      // Arrange
      expect(state.slats.containsKey('A-I1'), isTrue);

      // Act
      state.removeSlat('A-I1');

      // Assert
      expect(state.slats.containsKey('A-I1'), isFalse);
      expect(state.slats.length, equals(2));
    });

    test('removeSlat clears occupiedGridPoints entries', () {
      // Arrange
      final slat = state.slats['A-I1']!;
      final slatCoords = slat.slatPositionToCoordinate.values.toList();

      // Verify occupancy before deletion
      for (var coord in slatCoords) {
        expect(state.occupiedGridPoints['A']![coord], equals('A-I1'));
      }

      // Act
      state.removeSlat('A-I1');

      // Assert - all positions should be cleared
      for (var coord in slatCoords) {
        expect(state.occupiedGridPoints['A']!.containsKey(coord), isFalse);
      }
    });

    test('removeSlat updates layer slat_count', () {
      // Arrange
      expect(state.layerMap['A']!['slat_count'], equals(3));

      // Act
      state.removeSlat('A-I1');

      // Assert
      expect(state.layerMap['A']!['slat_count'], equals(2));
    });

    test('removeSlat does not affect next_slat_id', () {
      // Arrange
      final nextIdBefore = state.layerMap['A']!['next_slat_id'];

      // Act
      state.removeSlat('A-I1');

      // Assert - next_slat_id should remain unchanged (IDs are not reused)
      expect(state.layerMap['A']!['next_slat_id'], equals(nextIdBefore));
    });

    test('removeSlat sets hammingValueValid to false', () {
      // Arrange
      state.hammingValueValid = true;

      // Act
      state.removeSlat('A-I1');

      // Assert
      expect(state.hammingValueValid, isFalse);
    });

    test('removeSlat clears selection', () {
      // Arrange
      state.selectedSlats = ['A-I1', 'A-I2'];

      // Act
      state.removeSlat('A-I1');

      // Assert - selection should be cleared
      expect(state.selectedSlats.isEmpty, isTrue);
    });

    test('removeSlats removes multiple slats', () {
      // Arrange
      expect(state.slats.length, equals(3));

      // Act
      state.removeSlats(['A-I1', 'A-I2']);

      // Assert
      expect(state.slats.length, equals(1));
      expect(state.slats.containsKey('A-I3'), isTrue);
      expect(state.layerMap['A']!['slat_count'], equals(1));
    });

    test('removeSlats with empty list does nothing', () {
      // Arrange
      final slatCountBefore = state.slats.length;

      // Act
      state.removeSlats([]);

      // Assert
      expect(state.slats.length, equals(slatCountBefore));
    });

    test('removing all slats leaves empty occupancy map', () {
      // Act
      state.removeSlats(['A-I1', 'A-I2', 'A-I3']);

      // Assert
      expect(state.slats.isEmpty, isTrue);
      expect(state.occupiedGridPoints['A']?.isEmpty ?? true, isTrue);
      expect(state.layerMap['A']!['slat_count'], equals(0));
    });
  });

  group('DesignState - Occupancy Map Consistency', () {
    late DesignState state;

    setUp(() {
      state = DesignStateTestFactory.create();
    });

    test('add then delete maintains consistent occupancy', () {
      // Arrange & Act - add slats
      final coords = buildSlatCoordinatesMap([
        const Offset(0, 0),
        const Offset(0, 35),
      ]);
      state.addSlats('A', coords);

      // Verify consistency after add
      verifyOccupancyConsistency(
        slats: state.slats,
        occupiedGridPoints: state.occupiedGridPoints,
      );

      // Act - delete one slat
      state.removeSlat('A-I1');

      // Assert consistency after delete
      verifyOccupancyConsistency(
        slats: state.slats,
        occupiedGridPoints: state.occupiedGridPoints,
      );
    });

    test('multiple add/delete cycles maintain consistency', () {
      // Cycle 1: Add
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 0)]));

      // Cycle 2: Add more
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 35)]));

      // Cycle 3: Delete first
      state.removeSlat('A-I1');

      // Cycle 4: Add another
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 70)]));

      // Final verification
      verifyOccupancyConsistency(
        slats: state.slats,
        occupiedGridPoints: state.occupiedGridPoints,
      );

      // Should have slats A-I2 and A-I3 (A-I1 was deleted)
      expect(state.slats.length, equals(2));
      expect(state.slats.containsKey('A-I1'), isFalse);
      expect(state.slats.containsKey('A-I2'), isTrue);
      expect(state.slats.containsKey('A-I3'), isTrue);
    });

    test('cross-layer operations maintain separate occupancy', () {
      // Add to layer A
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 0)]));

      // Add to layer B at same coordinates (physically possible in 3D)
      state.addSlats('B', buildSlatCoordinatesMap([const Offset(0, 0)]));

      // Delete from layer A
      state.removeSlat('A-I1');

      // Layer B should still have its slat
      expect(state.occupiedGridPoints['B']!.length, equals(32));
      expect(state.occupiedGridPoints['A']?.isEmpty ?? true, isTrue);
    });

    test('occupancy count matches slat position count', () {
      // Arrange
      state.addSlats('A', buildSlatCoordinatesMap([
        const Offset(0, 0),
        const Offset(0, 35),
      ]));
      state.addSlats('B', buildSlatCoordinatesMap([const Offset(0, 70)]));

      // Assert
      // 2 slats in A (64 positions) + 1 slat in B (32 positions) = 96 total
      final totalOccupied = countTotalOccupiedPositions(state.occupiedGridPoints);
      expect(totalOccupied, equals(96));
    });
  });

  group('DesignState - Slat ID Sequencing', () {
    test('slat IDs increment correctly after deletion', () {
      final state = DesignStateTestFactory.create();

      // Add slat -> A-I1
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 0)]));
      expect(state.slats.containsKey('A-I1'), isTrue);

      // Delete it
      state.removeSlat('A-I1');

      // Add another -> should be A-I2, not A-I1
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 35)]));
      expect(state.slats.containsKey('A-I1'), isFalse);
      expect(state.slats.containsKey('A-I2'), isTrue);
    });

    test('different layers have independent ID sequences', () {
      final state = DesignStateTestFactory.create();

      // Add to both layers
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 0)]));
      state.addSlats('B', buildSlatCoordinatesMap([const Offset(0, 0)]));
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 35)]));

      // Assert
      expect(state.slats.containsKey('A-I1'), isTrue);
      expect(state.slats.containsKey('A-I2'), isTrue);
      expect(state.slats.containsKey('B-I1'), isTrue);
      expect(state.layerMap['A']!['next_slat_id'], equals(3));
      expect(state.layerMap['B']!['next_slat_id'], equals(2));
    });
  });

  group('DesignState - Edge Cases', () {
    test('adding slat to fresh state works correctly', () {
      final state = DesignState();

      // Verify initial state
      expect(state.slats.isEmpty, isTrue);
      expect(state.layerMap['A']!['next_slat_id'], equals(1));
      expect(state.layerMap['A']!['slat_count'], equals(0));

      // Add slat
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 0)]));

      // Verify
      expect(state.slats.length, equals(1));
      expect(state.layerMap['A']!['slat_count'], equals(1));
    });

    test('slat default type is tube', () {
      final state = DesignStateTestFactory.create();
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 0)]));

      expect(state.slats['A-I1']!.slatType, equals('tube'));
    });

    test('slat is initialized with empty handle maps', () {
      final state = DesignStateTestFactory.create();
      state.addSlats('A', buildSlatCoordinatesMap([const Offset(0, 0)]));

      final slat = state.slats['A-I1']!;
      expect(slat.h2Handles.isEmpty, isTrue);
      expect(slat.h5Handles.isEmpty, isTrue);
      expect(slat.placeholderList.isEmpty, isTrue);
    });
  });
}
