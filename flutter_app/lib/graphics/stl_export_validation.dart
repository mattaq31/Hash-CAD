// Validates that all slats in a design are connected via assembly handles,
// ensuring the structure can be exported as a single 3D-printable piece.

import 'dart:collection';
import 'dart:ui';

import '../crisscross_core/slats.dart';
import '../crisscross_core/common_utilities.dart';

/// Returns null if all slats form a single connected component via assembly
/// handles, or an error message listing disconnected slats.
///
/// Two slats are considered "connected" if they share a grid coordinate on
/// adjacent layers and BOTH have non-zero assembly handles at that crossing.
String? validateFullConnectivity({
  required Map<String, Slat> slats,
  required Map<String, Map<Offset, String>> occupiedGridPoints,
  required Map<String, Map<String, dynamic>> layerMap,
}) {
  if (slats.isEmpty) {
    return 'No slats in design.';
  }

  if (slats.length == 1) {
    return 'Only one slat in design — need at least two connected slats to export.';
  }

  // Build adjacency graph via assembly handle crossings
  final Map<String, Set<String>> adjacency = {for (var id in slats.keys) id: {}};

  for (final slat in slats.values) {
    // Check both helix sides for assembly handle connections
    for (final side in [2, 5]) {
      final handleDict = getHandleDict(slat, side);
      final int direction = getLayerOffsetForSide(layerMap, slat.layer, side);
      final int adjacentOrder = layerMap[slat.layer]!['order'] + direction;
      final String? adjacentLayer = getLayerByOrder(layerMap, adjacentOrder);

      if (adjacentLayer == null) continue;

      final int opposingSide = getOpposingSide(layerMap, adjacentLayer, direction);

      for (final entry in handleDict.entries) {
        final int position = entry.key;
        final Map<String, dynamic> handleData = entry.value;

        // Only count non-zero assembly handles as connections
        if (!_isActiveAssemblyHandle(handleData)) continue;

        final Offset? coordinate = slat.slatPositionToCoordinate[position];
        if (coordinate == null) continue;

        // Find the slat at this coordinate on the adjacent layer
        final String? adjacentSlatId = occupiedGridPoints[adjacentLayer]?[coordinate];
        if (adjacentSlatId == null || adjacentSlatId == 'SEED') continue;
        if (!slats.containsKey(adjacentSlatId)) continue;

        // Check that the adjacent slat also has a non-zero assembly handle at this crossing
        final Slat adjacentSlat = slats[adjacentSlatId]!;
        final int? adjacentPosition = adjacentSlat.slatCoordinateToPosition[coordinate];
        if (adjacentPosition == null) continue;

        final Map<int, Map<String, dynamic>> adjacentHandleDict = getHandleDict(adjacentSlat, opposingSide);
        final Map<String, dynamic>? adjacentHandleData = adjacentHandleDict[adjacentPosition];

        if (adjacentHandleData != null && _isActiveAssemblyHandle(adjacentHandleData)) {
          adjacency[slat.id]!.add(adjacentSlatId);
          adjacency[adjacentSlatId]!.add(slat.id);
        }
      }
    }
  }

  // BFS to find connected component from the first slat
  final String startId = slats.keys.first;
  final Set<String> visited = {};
  final Queue<String> queue = Queue();
  queue.add(startId);
  visited.add(startId);

  while (queue.isNotEmpty) {
    final String current = queue.removeFirst();
    for (final neighbor in adjacency[current]!) {
      if (!visited.contains(neighbor)) {
        visited.add(neighbor);
        queue.add(neighbor);
      }
    }
  }

  if (visited.length == slats.length) {
    return null; // All slats connected
  }

  // Identify disconnected slats
  final Set<String> disconnected = slats.keys.toSet().difference(visited);
  return 'Cannot export: ${disconnected.length} slat(s) are not connected to the main structure via assembly handles:\n'
      '${disconnected.take(10).join(", ")}${disconnected.length > 10 ? " ...and ${disconnected.length - 10} more" : ""}';
}

/// Returns true if the handle data represents an active (non-zero, non-null)
/// assembly handle.
bool _isActiveAssemblyHandle(Map<String, dynamic> handleData) {
  final category = handleData['category'];
  if (category == null || !category.toString().contains('ASSEMBLY')) return false;
  final value = handleData['value'];
  if (value == null || value.toString() == '0' || value.toString().isEmpty) return false;
  return true;
}
