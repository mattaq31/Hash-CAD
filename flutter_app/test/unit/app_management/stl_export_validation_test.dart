// Tests for STL export connectivity validation.
//
// Verifies that the guard-rail correctly identifies whether all slats
// form a single connected component via assembly handles before allowing
// 3D export.

import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/slats.dart';
import 'package:hash_cad/graphics/stl_export_validation.dart';

/// Helper to create a horizontal slat (incrementing x) at a given y position.
Slat _createHorizontalSlat(String id, String layer, double y, {int length = 32, double startX = 0}) {
  final coords = <int, Offset>{};
  for (int i = 1; i <= length; i++) {
    coords[i] = Offset(startX + i - 1, y);
  }
  return Slat(int.parse(id.split('I').last), id, layer, coords, maxLength: length);
}

/// Helper to create a vertical slat (incrementing y) at a given x position.
Slat _createVerticalSlat(String id, String layer, double x, {int length = 32, double startY = 0}) {
  final coords = <int, Offset>{};
  for (int i = 1; i <= length; i++) {
    coords[i] = Offset(x, startY + i - 1);
  }
  return Slat(int.parse(id.split('I').last), id, layer, coords, maxLength: length);
}

/// Builds occupiedGridPoints from a map of slats.
Map<String, Map<Offset, String>> _buildOccupiedGridPoints(Map<String, Slat> slats) {
  final Map<String, Map<Offset, String>> occupiedGridPoints = {};
  for (final slat in slats.values) {
    occupiedGridPoints.putIfAbsent(slat.layer, () => {});
    for (final coord in slat.slatPositionToCoordinate.values) {
      occupiedGridPoints[slat.layer]![coord] = slat.id;
    }
  }
  return occupiedGridPoints;
}

/// Standard two-layer layerMap where H5 is top on layer A and H2 is top on layer B.
Map<String, Map<String, dynamic>> _twoLayerMap() => {
  'A': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2', 'direction': 0},
  'B': {'order': 1, 'top_helix': 'H2', 'bottom_helix': 'H5', 'direction': 90},
};

/// Three-layer layerMap for chain-connectivity tests.
Map<String, Map<String, dynamic>> _threeLayerMap() => {
  'A': {'order': 0, 'top_helix': 'H5', 'bottom_helix': 'H2', 'direction': 0},
  'B': {'order': 1, 'top_helix': 'H2', 'bottom_helix': 'H5', 'direction': 90},
  'C': {'order': 2, 'top_helix': 'H5', 'bottom_helix': 'H2', 'direction': 0},
};

void main() {
  group('STL Export Validation - Empty/Minimal Cases', () {
    test('returns error for empty design', () {
      final result = validateFullConnectivity(
        slats: {},
        occupiedGridPoints: {},
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('No slats'));
    });

    test('returns error for single slat', () {
      final slat = _createHorizontalSlat('A-I1', 'A', 0);
      final slats = {'A-I1': slat};
      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: _buildOccupiedGridPoints(slats),
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('Only one slat'));
    });
  });

  group('STL Export Validation - Two Layers, Crossing Slats', () {
    late Slat slatA;
    late Slat slatB;
    late Map<String, Slat> slats;
    late Map<String, Map<Offset, String>> occupiedGridPoints;

    setUp(() {
      // Horizontal slat on layer A at y=5, vertical slat on layer B at x=5
      // They cross at coordinate (5, 5)
      slatA = _createHorizontalSlat('A-I1', 'A', 5);
      slatB = _createVerticalSlat('B-I1', 'B', 5);
      slats = {'A-I1': slatA, 'B-I1': slatB};
      occupiedGridPoints = _buildOccupiedGridPoints(slats);
    });

    test('returns error when no assembly handles are present', () {
      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('not connected'));
    });

    test('returns error when only one slat has a handle at the crossing', () {
      // Layer A has H5 as top_helix, so H5 side points upward toward layer B
      // Place an assembly handle on slatA at position 6 (coordinate (5,5)), side H5
      slatA.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_HANDLE');

      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('not connected'));
    });

    test('returns null when both slats have assembly handles at the crossing', () {
      // slatA position 6 → coordinate (5, 5), H5 side points up to layer B
      slatA.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_HANDLE');
      // slatB at coordinate (5, 5) → position 6, H5 side (bottom_helix of B) points down to A
      slatB.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_ANTIHANDLE');

      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: _twoLayerMap(),
      );
      expect(result, isNull);
    });

    test('returns error when handle value is 0 (blocked)', () {
      slatA.setPlaceholderHandle(6, 5, '0', 'ASSEMBLY_HANDLE');
      slatB.setPlaceholderHandle(6, 5, '0', 'ASSEMBLY_ANTIHANDLE');

      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('not connected'));
    });

    test('returns error when handle category is not ASSEMBLY', () {
      slatA.setPlaceholderHandle(6, 5, '1', 'CARGO');
      slatB.setPlaceholderHandle(6, 5, '1', 'CARGO');

      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('not connected'));
    });
  });

  group('STL Export Validation - Three Layers, Chain Connectivity', () {
    test('returns null when A-B and B-C are connected forming a chain', () {
      // Layer A: horizontal at y=5
      // Layer B: vertical at x=5 (crosses A at (5,5))
      // Layer C: horizontal at y=5 (crosses B at (5,5))
      final slatA = _createHorizontalSlat('A-I1', 'A', 5);
      final slatB = _createVerticalSlat('B-I1', 'B', 5);
      final slatC = _createHorizontalSlat('C-I1', 'C', 5);

      // A connects to B at (5,5)
      // A's H5 (top) points up → layer B; B's H2 (top on B) points down → layer A
      // Layer B top_helix = H2, so H2 points up. bottom_helix = H5, so H5 points down.
      // getOpposingSide(layerMap, 'B', 1) → bottom_helix of B → H5
      slatA.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_HANDLE');
      slatB.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_ANTIHANDLE');

      // B connects to C at (5,5)
      // B's H2 (top) points up → layer C; C's H2 (bottom on C) points down → layer B
      // getLayerOffsetForSide for B, side 2: top_helix of B is H2, side==2 → 1 (up)
      // getOpposingSide(layerMap, 'C', 1) → bottom_helix of C → H2
      slatB.setPlaceholderHandle(6, 2, '2', 'ASSEMBLY_HANDLE');
      slatC.setPlaceholderHandle(6, 2, '2', 'ASSEMBLY_ANTIHANDLE');

      final slats = {'A-I1': slatA, 'B-I1': slatB, 'C-I1': slatC};
      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: _buildOccupiedGridPoints(slats),
        layerMap: _threeLayerMap(),
      );
      expect(result, isNull);
    });

    test('returns error when C is disconnected from A-B', () {
      final slatA = _createHorizontalSlat('A-I1', 'A', 5);
      final slatB = _createVerticalSlat('B-I1', 'B', 5);
      final slatC = _createHorizontalSlat('C-I1', 'C', 5);

      // Only A-B connected
      slatA.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_HANDLE');
      slatB.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_ANTIHANDLE');
      // No handles between B and C

      final slats = {'A-I1': slatA, 'B-I1': slatB, 'C-I1': slatC};
      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: _buildOccupiedGridPoints(slats),
        layerMap: _threeLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('C-I1'));
    });
  });

  group('STL Export Validation - Multiple Slats Per Layer', () {
    test('returns null when all slats are connected via multiple crossings', () {
      // Layer A: two horizontal slats at y=3 and y=7
      // Layer B: one vertical slat at x=5 crossing both A slats
      final slatA1 = _createHorizontalSlat('A-I1', 'A', 3);
      final slatA2 = _createHorizontalSlat('A-I2', 'A', 7);
      final slatB1 = _createVerticalSlat('B-I1', 'B', 5);

      // A1 crosses B1 at (5, 3) → A1 position 6, B1 position 4
      slatA1.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_HANDLE');
      slatB1.setPlaceholderHandle(4, 5, '1', 'ASSEMBLY_ANTIHANDLE');

      // A2 crosses B1 at (5, 7) → A2 position 6, B1 position 8
      slatA2.setPlaceholderHandle(6, 5, '2', 'ASSEMBLY_HANDLE');
      slatB1.setPlaceholderHandle(8, 5, '2', 'ASSEMBLY_ANTIHANDLE');

      final slats = {'A-I1': slatA1, 'A-I2': slatA2, 'B-I1': slatB1};
      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: _buildOccupiedGridPoints(slats),
        layerMap: _twoLayerMap(),
      );
      expect(result, isNull);
    });

    test('returns error when one slat has no handle connections', () {
      // Same setup but A2 has no handles
      final slatA1 = _createHorizontalSlat('A-I1', 'A', 3);
      final slatA2 = _createHorizontalSlat('A-I2', 'A', 7);
      final slatB1 = _createVerticalSlat('B-I1', 'B', 5);

      // Only A1-B1 connected
      slatA1.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_HANDLE');
      slatB1.setPlaceholderHandle(4, 5, '1', 'ASSEMBLY_ANTIHANDLE');

      final slats = {'A-I1': slatA1, 'A-I2': slatA2, 'B-I1': slatB1};
      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: _buildOccupiedGridPoints(slats),
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('A-I2'));
    });
  });

  group('STL Export Validation - Edge Cases', () {
    test('handles slats that do not physically cross (no shared coordinates)', () {
      // Two parallel horizontal slats on different layers that never intersect
      final slatA = _createHorizontalSlat('A-I1', 'A', 0);
      final slatB = _createHorizontalSlat('B-I1', 'B', 50); // far away

      slatA.setPlaceholderHandle(1, 5, '1', 'ASSEMBLY_HANDLE');
      slatB.setPlaceholderHandle(1, 5, '1', 'ASSEMBLY_ANTIHANDLE');

      final slats = {'A-I1': slatA, 'B-I1': slatB};
      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: _buildOccupiedGridPoints(slats),
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('not connected'));
    });

    test('SEED entries in occupiedGridPoints are ignored', () {
      // Layer A has a slat, layer B coordinate is occupied by SEED not a slat
      final slatA = _createHorizontalSlat('A-I1', 'A', 5);
      final slatB = _createVerticalSlat('B-I1', 'B', 10); // doesn't cross A

      slatA.setPlaceholderHandle(6, 5, '1', 'ASSEMBLY_HANDLE');

      final slats = {'A-I1': slatA, 'B-I1': slatB};
      final occupiedGridPoints = _buildOccupiedGridPoints(slats);
      // Place a SEED at the crossing point so it blocks connection
      occupiedGridPoints['B']![const Offset(5, 5)] = 'SEED';

      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: _twoLayerMap(),
      );
      expect(result, isNotNull);
      expect(result, contains('not connected'));
    });

    test('connection works with ASSEMBLY_ANTIHANDLE category', () {
      // Both sides use ANTIHANDLE — should still count as connected
      final slatA = _createHorizontalSlat('A-I1', 'A', 5);
      final slatB = _createVerticalSlat('B-I1', 'B', 5);

      slatA.setPlaceholderHandle(6, 5, '3', 'ASSEMBLY_ANTIHANDLE');
      slatB.setPlaceholderHandle(6, 5, '3', 'ASSEMBLY_HANDLE');

      final slats = {'A-I1': slatA, 'B-I1': slatB};
      final result = validateFullConnectivity(
        slats: slats,
        occupiedGridPoints: _buildOccupiedGridPoints(slats),
        layerMap: _twoLayerMap(),
      );
      expect(result, isNull);
    });
  });
}
