import 'package:flutter/material.dart';
import '../crisscross_core/slats.dart';
import 'plate_layout_state.dart' show WellConfig;

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
const double echoMaxWellVolumeNl = 25000;

const List<String> plateRows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
const List<int> plateCols = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

/// Color mode for echo well outlines — local to the echo plate window.
enum EchoWellColorMode { natural, layer, group }

int wellRow(String well) => plateRows.indexOf(well[0]);
int wellCol(String well) => int.parse(well.substring(1)) - 1;
String wellName(int row, int col) => '${plateRows[row]}${col + 1}';

/// Compute design color for a slat based on unique color or layer color (legacy).
Color? designColorFor(Slat? slat, Map<String, Map<String, dynamic>> layerMap) {
  if (slat == null) return null;
  return slat.uniqueColor ?? layerMap[slat.layer]?['color'] as Color?;
}

/// Computes the well outline color based on the selected echo color mode.
Color? echoDesignColorFor(
  Slat? slat,
  Map<String, Map<String, dynamic>> layerMap,
  EchoWellColorMode colorMode,
  Color? Function(String slatId)? resolveGroupColor,
) {
  if (slat == null) return null;
  switch (colorMode) {
    case EchoWellColorMode.natural:
      return slat.uniqueColor ?? layerMap[slat.layer]?['color'] as Color?;
    case EchoWellColorMode.layer:
      return layerMap[slat.layer]?['color'] as Color?;
    case EchoWellColorMode.group:
      return resolveGroupColor?.call(slat.id) ?? layerMap[slat.layer]?['color'] as Color?;
  }
}

/// Returns a human-readable display name for a slat in the format `L{layer}-{number}`.
///
/// The layer number is 1-indexed (derived from the layer's `order` field in [layerMap]).
/// For example, a slat with `numericID` 9 on the second layer (order 1) becomes `L2-9`.
String slatDisplayName(Slat slat, Map<String, Map<String, dynamic>> layerMap, {Map<String, Slat>? slats}) {
  final layerOrder = (layerMap[slat.layer]?['order'] as int? ?? 0) + 1;
  if (slat.phantomParent != null && slats != null) {
    final parent = slats[slat.phantomParent];
    if (parent != null) {
      final parentLayerOrder = (layerMap[parent.layer]?['order'] as int? ?? 0) + 1;
      return 'P${slat.numericID}|L$parentLayerOrder-${parent.numericID}';
    }
  }
  return 'L$layerOrder-${slat.numericID}';
}

/// Returns a CSV-friendly component name for a slat in the format `layer{N}-slat{number}`.
///
/// Used only in Echo CSV output. For example, a slat with `numericID` 9 on the second
/// layer (order 1) becomes `layer2-slat9`.
String slatCsvName(Slat slat, Map<String, Map<String, dynamic>> layerMap) {
  final layerOrder = (layerMap[slat.layer]?['order'] as int? ?? 0) + 1;
  return 'layer$layerOrder-slat${slat.numericID}';
}

/// Rounds a raw volume in nL up to the nearest Echo-compatible 25 nL increment.
int echoRoundedVolumeNl(double materialPerHandle, double concentration) {
  final volumeNl = (materialPerHandle / concentration) * 1000;
  return (volumeNl / 25).ceil() * 25;
}

/// Computes the total rounded transfer volume (nL) for a slat given a well config.
double slatTotalVolumeNl(Slat slat, WellConfig config) {
  double total = 0;
  for (var handles in [slat.h2Handles, slat.h5Handles]) {
    for (var handle in handles.values) {
      final conc = (handle['concentration'] as num?)?.toDouble();
      if (conc != null && conc > 0) total += echoRoundedVolumeNl(config.materialPerHandle, conc);
    }
  }
  return total;
}

/// Computes warning state for a well: placeholder handles and/or volume exceeded.
///
/// Placeholders that are also in [manualPositions] do not count as incomplete.
({bool incomplete, bool exceedsVolume}) wellWarningState(Slat slat, WellConfig? config, {double? maxVolumeNl, Set<(int, int)> manualPositions = const {}}) {
  final incomplete = slat.placeholderList.any((entry) {
    final parts = entry.split('-');
    if (parts.length < 3) return true;
    final position = int.tryParse(parts[1]);
    final helix = int.tryParse(parts[2].replaceFirst('h', ''));
    if (position == null || helix == null) return true;
    return !manualPositions.contains((helix, position));
  });
  bool exceedsVolume = false;
  if (!incomplete && config != null) {
    exceedsVolume = slatTotalVolumeNl(slat, config) > (maxVolumeNl ?? echoMaxWellVolumeNl);
  }
  return (incomplete: incomplete, exceedsVolume: exceedsVolume);
}
