import 'package:flutter/material.dart';
import '../crisscross_core/slats.dart';

// ---------------------------------------------------------------------------
// Shared constants for the Echo Plate Layout window
// ---------------------------------------------------------------------------

const double echoWellWidth = 78.0;
const double echoWellHeight = 55.0;
const double echoHeaderCellSize = 24.0;
const double echoGridPadding = 16.0;
const double echoSidebarWidth = 160.0;
const double echoChamferSize = 12.0;
const double echoWindowWidth = 1200.0;
const double echoCollapsedHeight = 53.0;

const List<String> plateRows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
const List<int> plateCols = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

int wellRow(String well) => plateRows.indexOf(well[0]);
int wellCol(String well) => int.parse(well.substring(1)) - 1;
String wellName(int row, int col) => '${plateRows[row]}${col + 1}';

/// Compute design color for a slat based on unique color or layer color.
Color? designColorFor(Slat? slat, Map<String, Map<String, dynamic>> layerMap) {
  if (slat == null) return null;
  return slat.uniqueColor ?? layerMap[slat.layer]?['color'] as Color?;
}

/// Returns a human-readable display name for a slat in the format `L{layer}-{number}`.
///
/// The layer number is 1-indexed (derived from the layer's `order` field in [layerMap]).
/// For example, a slat with `numericID` 9 on the second layer (order 1) becomes `L2-9`.
String slatDisplayName(Slat slat, Map<String, Map<String, dynamic>> layerMap) {
  final layerOrder = (layerMap[slat.layer]?['order'] as int? ?? 0) + 1;
  return 'L$layerOrder-${slat.numericID}';
}
