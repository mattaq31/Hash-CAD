import '../app_management/design_io_constants.dart';
import '../crisscross_core/slats.dart';
import 'echo_export.dart' show generatePlateLayout96;
import 'echo_plate_constants.dart';

final List<String> _plate96Wells = generatePlateLayout96();

/// Per-well configuration for Echo liquid handler dispensing parameters.
class WellConfig {
  final double ratio;
  final double volume;
  final double scaffoldConc;

  const WellConfig({this.ratio = 15, this.volume = 50, this.scaffoldConc = 50});

  /// Material per handle in pmol: scaffoldConc * ratio * volume / 1000.
  double get materialPerHandle => scaffoldConc * ratio * volume / 1000;

  /// Total slat quantity in pmol: scaffoldConc * volume / 1000.
  double get totalSlatQuantity => scaffoldConc * volume / 1000;

  /// Serializes to a compact string for Excel storage: "ratio_sVolume_sScaffoldConc".
  String toExcelString() => '${ratio}_s${volume}_s$scaffoldConc';

  /// Parses a config string produced by [toExcelString].
  static WellConfig? fromExcelString(String s) {
    if (s.isEmpty) return null;
    final parts = s.split('_s');
    if (parts.length != 3) return null;
    final r = double.tryParse(parts[0]);
    final v = double.tryParse(parts[1]);
    final sc = double.tryParse(parts[2]);
    if (r == null || v == null || sc == null) return null;
    return WellConfig(ratio: r, volume: v, scaffoldConc: sc);
  }

  WellConfig copyWith({double? ratio, double? volume, double? scaffoldConc}) {
    return WellConfig(
      ratio: ratio ?? this.ratio,
      volume: volume ?? this.volume,
      scaffoldConc: scaffoldConc ?? this.scaffoldConc,
    );
  }

  WellConfig copy() => WellConfig(ratio: ratio, volume: volume, scaffoldConc: scaffoldConc);
}

/// Sorts slats for plate assignment: excludes phantoms, orders by layer then numericID.
List<MapEntry<String, Slat>> sortSlatsForPlateAssignment(
    Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap) {
  return slats.entries.where((e) => e.value.phantomParent == null).toList()
    ..sort((a, b) {
      final orderA = layerMap[a.value.layer]?['order'] ?? 0;
      final orderB = layerMap[b.value.layer]?['order'] ?? 0;
      if (orderA != orderB) return orderA.compareTo(orderB);
      return a.value.numericID.compareTo(b.value.numericID);
    });
}

/// Returns the base slat ID by stripping the `~N` duplicate suffix.
String baseSlatId(String id) {
  final tildeIndex = id.indexOf('~');
  return tildeIndex < 0 ? id : id.substring(0, tildeIndex);
}

/// Returns true if the slat ID is a duplicate (has `~N` suffix).
bool isDuplicateSlatId(String id) => id.contains('~');

/// Manages the assignment of slats to 96-well plates.
///
/// Slats start in [unassignedSlats] and can be moved to plate wells
/// via drag-drop or auto-assignment.
class PlateLayoutState {
  List<String> unassignedSlats;
  Map<int, Map<String, String?>> plateAssignments;

  /// Maps a base slat ID to all IDs in its duplicate group (including the base).
  Map<String, Set<String>> duplicateGroups;

  /// Tracks the next duplicate counter per base slat ID.
  Map<String, int> _duplicateCounters;

  /// User-assigned names for each plate (keyed by plate index).
  Map<int, String> plateNames;

  /// Per-well dispensing configuration: plateIndex → wellName → WellConfig.
  Map<int, Map<String, WellConfig>> wellConfigs;

  /// User-assigned experiment title, persisted with the design file.
  String experimentTitle;

  PlateLayoutState({
    List<String>? unassignedSlats,
    Map<int, Map<String, String?>>? plateAssignments,
    Map<String, Set<String>>? duplicateGroups,
    Map<String, int>? duplicateCounters,
    Map<int, String>? plateNames,
    Map<int, Map<String, WellConfig>>? wellConfigs,
    this.experimentTitle = 'Experiment',
  })  : unassignedSlats = unassignedSlats ?? [],
        plateAssignments = plateAssignments ?? {},
        duplicateGroups = duplicateGroups ?? {},
        _duplicateCounters = duplicateCounters ?? {},
        plateNames = plateNames ?? {},
        wellConfigs = wellConfigs ?? {};

  /// Returns the user-assigned name for a plate, defaulting to 'Plate'.
  String plateName(int index) => plateNames[index] ?? 'Plate';

  /// Renames a plate. Name must be max 25 chars, alphanumeric + underscore only.
  void renamePlate(int index, String name) {
    plateNames[index] = name;
  }

  /// Validates a plate name: max 25 chars, alphanumeric + underscore only.
  static bool isValidPlateName(String name) {
    if (name.isEmpty || name.length > 25) return false;
    return RegExp(r'^[a-zA-Z0-9_]+$').hasMatch(name);
  }

  /// Returns the [WellConfig] for a specific well, or a default if none is set.
  WellConfig getWellConfig(int plateIndex, String well) {
    return wellConfigs[plateIndex]?[well] ?? const WellConfig();
  }

  /// Sets the [WellConfig] for a specific well.
  void setWellConfig(int plateIndex, String well, WellConfig config) {
    wellConfigs.putIfAbsent(plateIndex, () => {})[well] = config;
  }

  /// Applies a [WellConfig] to every occupied well on a single plate.
  void applyConfigToPlate(int plateIndex, WellConfig config) {
    final plate = plateAssignments[plateIndex];
    if (plate == null) return;
    for (var wellEntry in plate.entries) {
      if (wellEntry.value != null) {
        wellConfigs.putIfAbsent(plateIndex, () => {})[wellEntry.key] = config.copy();
      }
    }
  }

  /// Applies a [WellConfig] to every occupied well across all plates.
  void applyConfigToAll(WellConfig config) {
    for (var plateEntry in plateAssignments.entries) {
      for (var wellEntry in plateEntry.value.entries) {
        if (wellEntry.value != null) {
          wellConfigs.putIfAbsent(plateEntry.key, () => {})[wellEntry.key] = config.copy();
        }
      }
    }
  }

  /// Ensures every occupied well has a [WellConfig] entry (fills in defaults where missing).
  void ensureDefaultConfigs() {
    for (var plateEntry in plateAssignments.entries) {
      for (var wellEntry in plateEntry.value.entries) {
        if (wellEntry.value != null) {
          final plateConfigs = wellConfigs.putIfAbsent(plateEntry.key, () => {});
          plateConfigs.putIfAbsent(wellEntry.key, () => const WellConfig());
        }
      }
    }
  }

  /// Applies a [WellConfig] to the given selected well keys (format: "plate:well").
  void applyConfigToSelected(Set<String> keys, WellConfig config) {
    for (var key in keys) {
      final parts = key.split(':');
      final plate = int.parse(parts[0]);
      final well = parts[1];
      if (plateAssignments[plate]?[well] != null) {
        wellConfigs.putIfAbsent(plate, () => {})[well] = config.copy();
      }
    }
  }

  /// Creates a new state with all non-phantom slats unassigned and one empty plate.
  factory PlateLayoutState.fromSlats(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap,
      {String experimentTitle = 'Experiment'}) {
    final sorted = sortSlatsForPlateAssignment(slats, layerMap);
    return PlateLayoutState(
      unassignedSlats: sorted.map((e) => e.key).toList(),
      plateAssignments: {0: {for (var w in _plate96Wells) w: null}},
      plateNames: {0: 'Plate'},
      experimentTitle: experimentTitle,
    );
  }

  /// Adds a new empty plate at the end.
  void addPlate() {
    final newIndex = plateAssignments.isEmpty ? 0 : (plateAssignments.keys.toList()..sort()).last + 1;
    plateAssignments[newIndex] = {for (var w in _plate96Wells) w: null};
    plateNames[newIndex] = 'Plate';
  }

  /// Removes a plate, returning any assigned slats to the sidebar.
  /// Renumbers remaining plates to be sequential starting from 0.
  void removePlate(int plateIndex) {
    final plate = plateAssignments[plateIndex];
    if (plate == null) return;

    // Return all slats on this plate to sidebar
    for (var well in plate.keys) {
      final slatId = plate[well];
      if (slatId != null) {
        _returnSlatToSidebar(slatId);
      }
    }

    plateAssignments.remove(plateIndex);
    plateNames.remove(plateIndex);
    wellConfigs.remove(plateIndex);
  }

  /// Returns all IDs sharing the same base (siblings + self).
  Set<String> getDuplicateSiblings(String slatId) {
    final base = baseSlatId(slatId);
    return duplicateGroups[base] ?? {slatId};
  }

  /// Moves a slat from the unassigned sidebar into a plate well.
  /// If the target well is occupied, the displaced slat goes back to the sidebar.
  void moveSlatFromSidebarToWell(String slatId, int toPlate, String toWell) {
    if (!unassignedSlats.contains(slatId)) return;

    final existing = plateAssignments[toPlate]?[toWell];
    if (existing != null) {
      _returnSlatToSidebar(existing);
    }

    unassignedSlats.remove(slatId);
    plateAssignments[toPlate]![toWell] = slatId;
    wellConfigs.putIfAbsent(toPlate, () => {}).putIfAbsent(toWell, () => const WellConfig());
  }

  /// Moves a slat from a plate well back to the unassigned sidebar.
  void moveSlatFromWellToSidebar(int fromPlate, String fromWell) {
    final slatId = plateAssignments[fromPlate]?[fromWell];
    if (slatId == null) return;

    plateAssignments[fromPlate]![fromWell] = null;
    _returnSlatToSidebar(slatId);
  }

  /// Internal helper: returns a slat to the sidebar with duplicate-awareness.
  /// If the slat is a duplicate and other copies remain on plates, the removed
  /// copy simply disappears. If it's the last copy, the base ID returns to shelf.
  void _returnSlatToSidebar(String slatId) {
    final base = baseSlatId(slatId);
    final group = duplicateGroups[base];

    if (group == null) {
      // Not in any duplicate group — simple return
      unassignedSlats.add(slatId);
      return;
    }

    // Remove this ID from the group
    group.remove(slatId);

    // Count how many group members remain on plates
    final onPlates = group.where((id) {
      for (var plate in plateAssignments.values) {
        if (plate.values.contains(id)) return true;
      }
      return false;
    });

    if (onPlates.isNotEmpty) {
      // Dissolve group if only 1 copy remains (no longer a "duplicate")
      if (onPlates.length <= 1) {
        final lastCopy = onPlates.first;
        // Rename the remaining copy back to the base ID on its plate
        if (lastCopy != base) {
          for (var plate in plateAssignments.values) {
            for (var well in plate.keys) {
              if (plate[well] == lastCopy) {
                plate[well] = base;
                break;
              }
            }
          }
        }
        duplicateGroups.remove(base);
      }
      return;
    }

    // No copies remain on plates — return the base ID to shelf
    duplicateGroups.remove(base);
    _duplicateCounters.remove(base);

    // Don't add if base is already unassigned
    if (!unassignedSlats.contains(base)) {
      unassignedSlats.add(base);
    }
  }

  /// Swaps the contents of two wells (either or both may be empty).
  void moveSlatBetweenWells(int fromPlate, String fromWell, int toPlate, String toWell) {
    final movingSlat = plateAssignments[fromPlate]?[fromWell];
    final targetSlat = plateAssignments[toPlate]?[toWell];

    plateAssignments[fromPlate]![fromWell] = targetSlat;
    plateAssignments[toPlate]![toWell] = movingSlat;
  }

  /// Moves all placed slats back to [unassignedSlats] and clears every well.
  /// Collapses all duplicate groups so only base IDs return to the shelf.
  void removeAll(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap) {
    // Collect base IDs already on the shelf
    final baseIdsOnShelf = unassignedSlats.toSet();

    for (var plate in plateAssignments.values) {
      for (var well in plate.keys) {
        final slatId = plate[well];
        if (slatId != null) {
          final base = baseSlatId(slatId);
          if (!baseIdsOnShelf.contains(base)) {
            baseIdsOnShelf.add(base);
            unassignedSlats.add(base);
          }
          plate[well] = null;
        }
      }
    }

    // Clear all duplicate tracking and well configs
    duplicateGroups.clear();
    _duplicateCounters.clear();
    wellConfigs.clear();

    // Re-sort using the standard ordering
    final sortedAll = sortSlatsForPlateAssignment(slats, layerMap);
    final unassignedSet = unassignedSlats.toSet();
    unassignedSlats = sortedAll.where((e) => unassignedSet.contains(e.key)).map((e) => e.key).toList();
  }

  /// Removes slats at the given selected well keys (format: "plate:well")
  /// and returns them to the shelf.
  void removeSelected(Set<String> keys) {
    for (var key in keys) {
      final parts = key.split(':');
      final plate = int.parse(parts[0]);
      final well = parts[1];
      final slatId = plateAssignments[plate]?[well];
      if (slatId == null) continue;

      plateAssignments[plate]![well] = null;
      wellConfigs[plate]?.remove(well);
      _returnSlatToSidebar(slatId);
    }
  }

  /// Atomically moves a group of slats between wells.
  ///
  /// [moves] maps (sourcePlate, sourceWell) → (targetPlate, targetWell).
  /// If any target is out-of-bounds or invalid the entire move is cancelled.
  /// Non-group slats displaced by the move are returned to [unassignedSlats].
  void moveGroupToWells(Map<({int plate, String well}), ({int plate, String well})> moves) {
    // Validate every target exists
    for (var target in moves.values) {
      if (plateAssignments[target.plate] == null) return;
      if (!plateAssignments[target.plate]!.containsKey(target.well)) return;
    }

    // Collect slats being moved (from source wells)
    final movingSlatIds = <({int plate, String well}), String>{};
    for (var source in moves.keys) {
      final slatId = plateAssignments[source.plate]?[source.well];
      if (slatId == null) return; // source must have a slat
      movingSlatIds[source] = slatId;
    }

    final groupSlatIdSet = movingSlatIds.values.toSet();
    final targetSet = moves.values.toSet();

    // Displace any non-group slats at target wells
    for (var target in targetSet) {
      final existing = plateAssignments[target.plate]![target.well];
      if (existing != null && !groupSlatIdSet.contains(existing)) {
        unassignedSlats.add(existing);
      }
    }

    // Clear source wells
    for (var source in moves.keys) {
      plateAssignments[source.plate]![source.well] = null;
    }

    // Place slats at target wells
    for (var entry in moves.entries) {
      plateAssignments[entry.value.plate]![entry.value.well] = movingSlatIds[entry.key]!;
    }
  }

  /// Auto-assigns all unassigned slats onto plates in sorted order.
  /// Any already-assigned slats remain in place; unassigned slats fill empty wells.
  /// When [columnsThreeToTenOnly] is true, only wells in columns 3-10 (0-indexed 2-9) are used.
  /// When [splitSlatTypes] is true, different slat types are placed on separate plates.
  void autoAssign(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap,
      {bool columnsThreeToTenOnly = false, bool splitSlatTypes = false, bool splitSlatLayers = false}) {
    if (unassignedSlats.isEmpty) return;

    // Sort unassigned slats using the standard ordering
    final sortedAll = sortSlatsForPlateAssignment(slats, layerMap);
    final unassignedSet = unassignedSlats.toSet();
    final toAssign = sortedAll.where((e) => unassignedSet.contains(e.key)).toList();

    if (splitSlatTypes) {
      // Group slats by type, preserving sorted order within each group
      final groupsByType = <String, List<String>>{};
      for (var entry in toAssign) {
        final slatType = slats[entry.key]?.slatType ?? 'tube';
        groupsByType.putIfAbsent(slatType, () => []).add(entry.key);
      }

      for (var typeGroup in groupsByType.values) {
        _autoAssignGroup(typeGroup, columnsThreeToTenOnly: columnsThreeToTenOnly, startOnNewPlate: true);
      }
    } else if (splitSlatLayers) {
      // Group slats by layer, preserving sorted order within each group
      final groupsByLayer = <String, List<String>>{};
      for (var entry in toAssign) {
        final layer = slats[entry.key]?.layer ?? '';
        groupsByLayer.putIfAbsent(layer, () => []).add(entry.key);
      }

      for (var layerGroup in groupsByLayer.values) {
        _autoAssignGroup(layerGroup, columnsThreeToTenOnly: columnsThreeToTenOnly, startOnNewPlate: true);
      }
    } else {
      _autoAssignGroup(toAssign.map((e) => e.key).toList(), columnsThreeToTenOnly: columnsThreeToTenOnly);
    }

    unassignedSlats.clear();
  }

  /// Internal helper: assigns a list of slat IDs to empty wells.
  /// When [startOnNewPlate] is true, skips to a fresh plate before filling.
  void _autoAssignGroup(List<String> slatIds,
      {bool columnsThreeToTenOnly = false, bool startOnNewPlate = false}) {
    if (slatIds.isEmpty) return;

    // Collect empty wells across existing plates
    final emptyWells = <({int plate, String well})>[];
    for (var plateIndex in plateAssignments.keys.toList()..sort()) {
      for (var well in _plate96Wells) {
        if (plateAssignments[plateIndex]![well] == null) {
          if (columnsThreeToTenOnly) {
            final col = wellCol(well);
            if (col < 2 || col > 9) continue;
          }
          emptyWells.add((plate: plateIndex, well: well));
        }
      }
    }

    int wellIdx = 0;

    // When starting on a new plate, skip past wells on plates that already have content
    if (startOnNewPlate && emptyWells.isNotEmpty) {
      // Find which plates already have occupied wells
      final occupiedPlates = <int>{};
      for (var plateIndex in plateAssignments.keys) {
        if (plateAssignments[plateIndex]!.values.any((v) => v != null)) {
          occupiedPlates.add(plateIndex);
        }
      }
      // Skip to first well on a completely empty plate
      while (wellIdx < emptyWells.length && occupiedPlates.contains(emptyWells[wellIdx].plate)) {
        wellIdx++;
      }
    }

    for (var slatId in slatIds) {
      if (wellIdx >= emptyWells.length) {
        final newPlateIndex = (plateAssignments.keys.toList()..sort()).last + 1;
        plateAssignments[newPlateIndex] = {for (var w in _plate96Wells) w: null};
        plateNames[newPlateIndex] = 'Plate';
        for (var w in _plate96Wells) {
          if (columnsThreeToTenOnly) {
            final col = wellCol(w);
            if (col < 2 || col > 9) continue;
          }
          emptyWells.add((plate: newPlateIndex, well: w));
        }
      }

      final target = emptyWells[wellIdx];
      plateAssignments[target.plate]![target.well] = slatId;
      wellConfigs.putIfAbsent(target.plate, () => {}).putIfAbsent(target.well, () => const WellConfig());
      wellIdx++;
    }
  }

  /// Exports each plate as a human-readable 9×13 grid (header row + A-H, label col + 1-12)
  /// followed by a blank separator row and a 9×13 config grid.
  /// Returns a map from plate index to a record containing the plate name and grid data.
  Map<int, ({String name, List<List<dynamic>> grid})> exportPlateGrids() {
    final result = <int, ({String name, List<List<dynamic>> grid})>{};
    for (var plateEntry in plateAssignments.entries) {
      final plateIndex = plateEntry.key;
      final plate = plateEntry.value;
      final grid = <List<dynamic>>[];
      // Header row: [experimentTitle, 1, 2, ..., 12]
      grid.add([experimentTitle, ...List.generate(12, (i) => i + 1)]);
      // Data rows: ["A", slatId_or_empty, ...]
      for (var r = 0; r < 8; r++) {
        final row = <dynamic>[plateRows[r]];
        for (var c = 0; c < 12; c++) {
          final well = wellName(r, c);
          row.add(plate[well] ?? '');
        }
        grid.add(row);
      }
      // Blank separator row (row 9)
      grid.add(List.filled(13, ''));
      // Config header row (row 10): [experimentTitle, 1, 2, ..., 12]
      grid.add([experimentTitle, ...List.generate(12, (i) => i + 1)]);
      // Config data rows (rows 11-18): ["A", configString_or_empty, ...]
      final plateConfigs = wellConfigs[plateIndex] ?? {};
      for (var r = 0; r < 8; r++) {
        final row = <dynamic>[plateRows[r]];
        for (var c = 0; c < 12; c++) {
          final well = wellName(r, c);
          final config = plateConfigs[well];
          row.add(config?.toExcelString() ?? '');
        }
        grid.add(row);
      }
      result[plateIndex] = (name: plateName(plateIndex), grid: grid);
    }
    return result;
  }

  /// Reconstructs a PlateLayoutState from echo plate sheets in a design file.
  /// Returns null if no echo plate sheets are found.
  static PlateLayoutState? fromExcelSheets(
    Map<String, List<List<dynamic>>> sheets,
    Map<String, Slat> slats,
    Map<String, Map<String, dynamic>> layerMap,
  ) {
    // Find echo plate sheets with format p{N}_{name}
    final plateSheetRegex = RegExp(r'^' + echoPlateSheetPrefix + r'(\d+)_(.+)$');
    final plateSheetNames = sheets.keys.where((k) => plateSheetRegex.hasMatch(k)).toList()
      ..sort((a, b) {
        final numA = int.parse(plateSheetRegex.firstMatch(a)!.group(1)!);
        final numB = int.parse(plateSheetRegex.firstMatch(b)!.group(1)!);
        return numA.compareTo(numB);
      });

    if (plateSheetNames.isEmpty) return null;

    final plateAssignments = <int, Map<String, String?>>{};
    final parsedPlateNames = <int, String>{};
    final parsedWellConfigs = <int, Map<String, WellConfig>>{};
    String parsedExperimentTitle = 'Experiment';
    final allPlacedIds = <String>[];

    for (var sheetName in plateSheetNames) {
      final match = plateSheetRegex.firstMatch(sheetName)!;
      final plateIndex = int.parse(match.group(1)!);
      final pName = match.group(2)!;
      final rows = sheets[sheetName]!;
      final plateMap = <String, String?>{for (var w in _plate96Wells) w: null};

      // rows[0] is the header row; rows 1-8 are data rows A-H
      for (var r = 1; r < rows.length && r <= 8; r++) {
        final row = rows[r];
        for (var c = 1; c < row.length && c <= 12; c++) {
          final cellValue = row[c];
          final well = wellName(r - 1, c - 1);
          if (cellValue != null && cellValue.toString().isNotEmpty) {
            final slatId = cellValue.toString();
            plateMap[well] = slatId;
            allPlacedIds.add(slatId);
          }
        }
      }
      plateAssignments[plateIndex] = plateMap;
      parsedPlateNames[plateIndex] = pName;

      // Parse config grid (rows 10-18) if present
      if (rows.length > 10) {
        final expTitleCell = rows[10][0];
        if (expTitleCell != null && expTitleCell.toString().isNotEmpty) {
          parsedExperimentTitle = expTitleCell.toString();
        }
        final plateConfigMap = <String, WellConfig>{};
        for (var r = 11; r < rows.length && r <= 18; r++) {
          final row = rows[r];
          for (var c = 1; c < row.length && c <= 12; c++) {
            final cellValue = row[c];
            if (cellValue != null && cellValue.toString().isNotEmpty) {
              final config = WellConfig.fromExcelString(cellValue.toString());
              if (config != null) {
                final well = wellName(r - 11, c - 1);
                plateConfigMap[well] = config;
              }
            }
          }
        }
        if (plateConfigMap.isNotEmpty) {
          parsedWellConfigs[plateIndex] = plateConfigMap;
        }
      }
    }

    // Rebuild duplicateGroups and counters in a single pass
    final duplicateGroups = <String, Set<String>>{};
    final duplicateCounters = <String, int>{};
    for (var id in allPlacedIds) {
      final base = baseSlatId(id);
      if (isDuplicateSlatId(id)) {
        duplicateGroups.putIfAbsent(base, () => {base});
        duplicateGroups[base]!.add(id);
        final suffix = int.tryParse(id.substring(id.indexOf('~') + 1)) ?? 0;
        final current = duplicateCounters[base] ?? 0;
        if (suffix > current) duplicateCounters[base] = suffix;
      } else if (duplicateGroups.containsKey(base)) {
        // Base ID placed without suffix but has duplicates — track it
        duplicateGroups[base]!.add(id);
      }
    }

    // Compute unassigned slats: all non-phantom design slat IDs not placed
    final placedBaseIds = allPlacedIds.map(baseSlatId).toSet();
    final sorted = sortSlatsForPlateAssignment(slats, layerMap);
    final unassigned = sorted.where((e) => !placedBaseIds.contains(e.key)).map((e) => e.key).toList();

    return PlateLayoutState(
      unassignedSlats: unassigned,
      plateAssignments: plateAssignments,
      duplicateGroups: duplicateGroups,
      duplicateCounters: duplicateCounters,
      plateNames: parsedPlateNames,
      wellConfigs: parsedWellConfigs,
      experimentTitle: parsedExperimentTitle,
    )..ensureDefaultConfigs();
  }

  /// Creates a deep copy of this state.
  PlateLayoutState copy() {
    return PlateLayoutState(
      unassignedSlats: List<String>.from(unassignedSlats),
      plateAssignments: {
        for (var e in plateAssignments.entries) e.key: Map<String, String?>.from(e.value),
      },
      duplicateGroups: {
        for (var e in duplicateGroups.entries) e.key: Set<String>.from(e.value),
      },
      duplicateCounters: Map<String, int>.from(_duplicateCounters),
      plateNames: Map<int, String>.from(plateNames),
      wellConfigs: {
        for (var e in wellConfigs.entries)
          e.key: {for (var w in e.value.entries) w.key: w.value.copy()},
      },
      experimentTitle: experimentTitle,
    );
  }

  /// Syncs this state with the current design slats.
  ///
  /// New non-phantom slats are added to [unassignedSlats] in sorted order.
  /// Deleted slats are removed from wells and [unassignedSlats].
  /// Returns `true` if any changes were made.
  bool syncWithDesign(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap) {
    // Build set of valid base IDs (non-phantom slats from design)
    final validBaseIds = <String>{};
    for (var entry in slats.entries) {
      if (entry.value.phantomParent == null) {
        validBaseIds.add(entry.key);
      }
    }

    // Build set of tracked base IDs (from unassigned + wells)
    final trackedBaseIds = <String>{};
    for (var id in unassignedSlats) {
      trackedBaseIds.add(baseSlatId(id));
    }
    for (var plate in plateAssignments.values) {
      for (var slatId in plate.values) {
        if (slatId != null) {
          trackedBaseIds.add(baseSlatId(slatId));
        }
      }
    }

    bool changed = false;

    // Add new slats to unassigned list
    final newIds = validBaseIds.difference(trackedBaseIds);
    if (newIds.isNotEmpty) {
      changed = true;
      // Sort new slats using standard ordering, then append
      final sorted = sortSlatsForPlateAssignment(slats, layerMap);
      for (var entry in sorted) {
        if (newIds.contains(entry.key)) {
          unassignedSlats.add(entry.key);
        }
      }
    }

    // Remove deleted slats
    final deletedIds = trackedBaseIds.difference(validBaseIds);
    if (deletedIds.isNotEmpty) {
      changed = true;

      // Remove from unassigned
      unassignedSlats.removeWhere((id) => deletedIds.contains(baseSlatId(id)));

      // Remove from wells
      for (var plate in plateAssignments.values) {
        for (var well in plate.keys) {
          final slatId = plate[well];
          if (slatId != null && deletedIds.contains(baseSlatId(slatId))) {
            plate[well] = null;
          }
        }
      }

      // Clean up duplicate groups
      for (var baseId in deletedIds) {
        duplicateGroups.remove(baseId);
        _duplicateCounters.remove(baseId);
      }
    }

    return changed;
  }

  /// Duplicates slats at the given selected well keys.
  /// New copies are placed as close as possible to the originals,
  /// filling adjacent empty wells on the same plate first.
  /// Returns the new well keys (format: "plate:well") for selection.
  Set<String> duplicateSlats(Set<String> selectedKeys) {
    if (selectedKeys.isEmpty) return {};

    // Parse selected wells and collect slat info
    final toDuplicate = <({int plate, String well, String slatId, int row, int col})>[];
    for (var key in selectedKeys) {
      final parts = key.split(':');
      final plate = int.parse(parts[0]);
      final well = parts[1];
      final slatId = plateAssignments[plate]?[well];
      if (slatId == null) continue;
      toDuplicate.add((plate: plate, well: well, slatId: slatId, row: wellRow(well), col: wellCol(well)));
    }
    if (toDuplicate.isEmpty) return {};

    // Generate new duplicate IDs
    final newSlats = <({String newId, int origPlate, String origWell, int origRow, int origCol})>[];
    for (var item in toDuplicate) {
      final base = baseSlatId(item.slatId);
      final counter = (_duplicateCounters[base] ?? 1) + 1;
      _duplicateCounters[base] = counter;
      final newId = '$base~$counter';

      // Register in duplicate group
      final group = duplicateGroups.putIfAbsent(base, () => {base});
      group.add(item.slatId); // ensure original is tracked
      group.add(newId);

      newSlats.add((newId: newId, origPlate: item.plate, origWell: item.well, origRow: item.row, origCol: item.col));
    }

    // Place each duplicate as close as possible to its original
    final newKeys = <String>{};
    final occupiedThisRound = <String>{}; // track wells claimed during this operation

    for (var item in newSlats) {
      final placed = _placeNearby(item.newId, item.origPlate, item.origRow, item.origCol, occupiedThisRound);
      if (placed != null) {
        newKeys.add(placed);
        // Copy well config from source well to the new duplicate well
        final sourceConfig = wellConfigs[item.origPlate]?[item.origWell];
        if (sourceConfig != null) {
          final parts = placed.split(':');
          final destPlate = int.parse(parts[0]);
          final destWell = parts[1];
          wellConfigs.putIfAbsent(destPlate, () => {})[destWell] = sourceConfig.copy();
        }
      }
    }

    return newKeys;
  }

  /// Places a single slat as close as possible to (origRow, origCol) on origPlate.
  /// Searches outward in Manhattan distance, preferring the same plate.
  /// Falls back to other plates, then creates a new plate if needed.
  /// [occupiedThisRound] tracks wells claimed during the current batch operation.
  /// Returns the well key "plate:well" or null on failure.
  String? _placeNearby(String slatId, int origPlate, int origRow, int origCol, Set<String> occupiedThisRound) {
    // Try the origin plate first, then other plates in sorted order
    final sortedPlates = plateAssignments.keys.toList()..sort();
    final orderedPlates = [origPlate, ...sortedPlates.where((p) => p != origPlate)];

    for (var plateIndex in orderedPlates) {
      final plate = plateAssignments[plateIndex]!;
      final refRow = plateIndex == origPlate ? origRow : 0;
      final refCol = plateIndex == origPlate ? origCol : 0;

      // Search outward by Manhattan distance from reference point
      for (var dist = 1; dist < 20; dist++) {
        for (var dr = -dist; dr <= dist; dr++) {
          final dcAbs = dist - dr.abs();
          for (var dc in dcAbs == 0 ? [0] : [-dcAbs, dcAbs]) {
            final r = refRow + dr;
            final c = refCol + dc;
            if (r < 0 || r >= 8 || c < 0 || c >= 12) continue;
            final well = wellName(r, c);
            final wellKey = '$plateIndex:$well';
            if (plate[well] == null && !occupiedThisRound.contains(wellKey)) {
              plate[well] = slatId;
              wellConfigs.putIfAbsent(plateIndex, () => {}).putIfAbsent(well, () => const WellConfig());
              occupiedThisRound.add(wellKey);
              return wellKey;
            }
          }
        }
      }
    }

    // No space found — create a new plate
    final newPlateIndex = plateAssignments.isEmpty ? 0 : (plateAssignments.keys.toList()..sort()).last + 1;
    plateAssignments[newPlateIndex] = {for (var w in _plate96Wells) w: null};
    plateNames[newPlateIndex] = 'Plate';
    final well = wellName(0, 0);
    plateAssignments[newPlateIndex]![well] = slatId;
    wellConfigs.putIfAbsent(newPlateIndex, () => {}).putIfAbsent(well, () => const WellConfig());
    occupiedThisRound.add('$newPlateIndex:$well');
    return '$newPlateIndex:$well';
  }
}
