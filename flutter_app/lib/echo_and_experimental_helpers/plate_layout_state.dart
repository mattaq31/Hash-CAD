import '../app_management/design_io_constants.dart';
import '../crisscross_core/slats.dart';
import 'echo_export.dart' show generatePlateLayout96;
import 'echo_plate_constants.dart';

final List<String> _plate96Wells = generatePlateLayout96();

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

  PlateLayoutState({
    List<String>? unassignedSlats,
    Map<int, Map<String, String?>>? plateAssignments,
    Map<String, Set<String>>? duplicateGroups,
    Map<String, int>? duplicateCounters,
    Map<int, String>? plateNames,
  })  : unassignedSlats = unassignedSlats ?? [],
        plateAssignments = plateAssignments ?? {},
        duplicateGroups = duplicateGroups ?? {},
        _duplicateCounters = duplicateCounters ?? {},
        plateNames = plateNames ?? {};

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

  /// Creates a new state with all non-phantom slats unassigned and one empty plate.
  factory PlateLayoutState.fromSlats(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap) {
    final sorted = sortSlatsForPlateAssignment(slats, layerMap);
    return PlateLayoutState(
      unassignedSlats: sorted.map((e) => e.key).toList(),
      plateAssignments: {0: {for (var w in _plate96Wells) w: null}},
      plateNames: {0: 'Plate'},
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

    // Clear all duplicate tracking
    duplicateGroups.clear();
    _duplicateCounters.clear();

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
  void autoAssign(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap,
      {bool columnsThreeToTenOnly = false}) {
    if (unassignedSlats.isEmpty) return;

    // Sort unassigned slats using the standard ordering
    final sortedAll = sortSlatsForPlateAssignment(slats, layerMap);
    final unassignedSet = unassignedSlats.toSet();
    final toAssign = sortedAll.where((e) => unassignedSet.contains(e.key)).map((e) => e.key).toList();

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
    for (var slatId in toAssign) {
      // Add new plates as needed
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
      wellIdx++;
    }

    unassignedSlats.clear();
  }

  /// Exports each plate as a human-readable 9×13 grid (header row + A-H, label col + 1-12).
  /// Returns a map from plate index to a record containing the plate name and grid data.
  Map<int, ({String name, List<List<dynamic>> grid})> exportPlateGrids() {
    final result = <int, ({String name, List<List<dynamic>> grid})>{};
    for (var plateEntry in plateAssignments.entries) {
      final plateIndex = plateEntry.key;
      final plate = plateEntry.value;
      final grid = <List<dynamic>>[];
      // Header row: ["", 1, 2, ..., 12]
      grid.add(['', ...List.generate(12, (i) => i + 1)]);
      // Data rows: ["A", slatId_or_empty, ...]
      for (var r = 0; r < 8; r++) {
        final row = <dynamic>[plateRows[r]];
        for (var c = 0; c < 12; c++) {
          final well = wellName(r, c);
          row.add(plate[well] ?? '');
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
    );
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
  /// New copies are placed in the first fully empty row (across all plates),
  /// preserving their original column positions.
  /// Returns the new well keys (format: "plate:well") for selection.
  Set<String> duplicateSlats(Set<String> selectedKeys) {
    if (selectedKeys.isEmpty) return {};

    // Parse selected wells and collect slat info with row + col
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

    // Compute relative row offsets from the minimum row
    final minRow = toDuplicate.map((e) => e.row).reduce((a, b) => a < b ? a : b);
    final rowSpan = toDuplicate.map((e) => e.row).reduce((a, b) => a > b ? a : b) - minRow + 1;

    // Generate new duplicate IDs, preserving relative row/col
    final newSlats = <({String newId, int dRow, int col})>[];
    for (var item in toDuplicate) {
      final base = baseSlatId(item.slatId);
      final counter = (_duplicateCounters[base] ?? 1) + 1;
      _duplicateCounters[base] = counter;
      final newId = '$base~$counter';

      // Register in duplicate group
      final group = duplicateGroups.putIfAbsent(base, () => {base});
      group.add(item.slatId); // ensure original is tracked
      group.add(newId);

      newSlats.add((newId: newId, dRow: item.row - minRow, col: item.col));
    }

    // Find a contiguous block of `rowSpan` fully empty rows on one plate
    ({int plate, int startRow})? targetBlock;

    for (var plateIndex in plateAssignments.keys.toList()..sort()) {
      for (var r = 0; r <= 8 - rowSpan; r++) {
        bool blockEmpty = true;
        for (var dr = 0; dr < rowSpan && blockEmpty; dr++) {
          for (var c = 0; c < 12; c++) {
            if (plateAssignments[plateIndex]![wellName(r + dr, c)] != null) {
              blockEmpty = false;
              break;
            }
          }
        }
        if (blockEmpty) {
          targetBlock = (plate: plateIndex, startRow: r);
          break;
        }
      }
      if (targetBlock != null) break;
    }

    // If no block found, create a new plate
    if (targetBlock == null) {
      final newPlateIndex = plateAssignments.isEmpty ? 0 : (plateAssignments.keys.toList()..sort()).last + 1;
      plateAssignments[newPlateIndex] = {for (var w in _plate96Wells) w: null};
      plateNames[newPlateIndex] = 'Plate';
      targetBlock = (plate: newPlateIndex, startRow: 0);
    }

    // Place duplicates preserving relative row and column positions
    final target = targetBlock;
    final newKeys = <String>{};
    for (var item in newSlats) {
      final well = wellName(target.startRow + item.dRow, item.col);
      plateAssignments[target.plate]![well] = item.newId;
      newKeys.add('${target.plate}:$well');
    }

    return newKeys;
  }
}
