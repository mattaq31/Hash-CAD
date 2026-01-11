import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/slats.dart';

/// Creates test slat coordinates for a horizontal slat at given origin.
/// Returns Map with positions 1 through length.
Map<int, Offset> createTestSlatCoordinates(Offset origin, {int length = 32}) {
  final coords = <int, Offset>{};
  for (int i = 1; i <= length; i++) {
    coords[i] = Offset(origin.dx + i - 1, origin.dy);
  }
  return coords;
}

/// Builds a map of slat coordinates suitable for addSlats().
/// Each origin in [origins] becomes a separate slat.
Map<int, Map<int, Offset>> buildSlatCoordinatesMap(List<Offset> origins, {int slatLength = 32}) {
  final result = <int, Map<int, Offset>>{};
  for (int i = 0; i < origins.length; i++) {
    final coords = <int, Offset>{};
    for (int pos = 1; pos <= slatLength; pos++) {
      coords[pos] = Offset(origins[i].dx + pos - 1, origins[i].dy);
    }
    result[i] = coords;
  }
  return result;
}

/// Verifies that occupancy maps are consistent with slat data.
/// Every slat coordinate should be in occupiedGridPoints, and vice versa.
void verifyOccupancyConsistency({
  required Map<String, Slat> slats,
  required Map<String, Map<Offset, String>> occupiedGridPoints,
}) {
  // Every slat coordinate should be in occupiedGridPoints
  for (var slatEntry in slats.entries) {
    final slat = slatEntry.value;
    for (var coord in slat.slatPositionToCoordinate.values) {
      expect(
        occupiedGridPoints[slat.layer]?[coord],
        equals(slat.id),
        reason: 'Slat ${slat.id} coordinate $coord should be in occupiedGridPoints',
      );
    }
  }

  // Every entry in occupiedGridPoints (except SEED) should correspond to a slat
  for (var layerEntry in occupiedGridPoints.entries) {
    for (var entry in layerEntry.value.entries) {
      if (entry.value != 'SEED') {
        expect(
          slats.containsKey(entry.value),
          isTrue,
          reason: 'OccupiedGridPoints entry ${entry.value} at ${entry.key} should have corresponding slat',
        );
      }
    }
  }
}

/// Counts total occupied positions across all layers.
int countTotalOccupiedPositions(Map<String, Map<Offset, String>> occupiedGridPoints) {
  int count = 0;
  for (var layer in occupiedGridPoints.values) {
    count += layer.length;
  }
  return count;
}
