import '../app_management/design_io/design_io_constants.dart';
import '../crisscross_core/slats.dart';
import 'echo_export.dart' show generatePlateLayout96;
import 'echo_plate_constants.dart';
import 'master_mix_config.dart';
import 'peg_purification_config.dart';

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

  /// Serializes to a descriptive string for Excel storage: "r{ratio}_v{volume}_sc{scaffoldConc}".
  String toExcelString() => 'r${ratio}_v${volume}_sc$scaffoldConc';

  /// Parses a config string produced by [toExcelString].
  static WellConfig? fromExcelString(String s) {
    if (s.isEmpty) return null;
    final match = RegExp(r'^r([^_]+)_v([^_]+)_sc(.+)$').firstMatch(s);
    if (match == null) return null;
    final r = double.tryParse(match.group(1)!);
    final v = double.tryParse(match.group(2)!);
    final sc = double.tryParse(match.group(3)!);
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

  /// Per-slat manual handle markings: baseSlatId → set of (helix, position).
  /// Helix is 2 or 5, position is 1-based (1..maxLength).
  Map<String, Set<(int helix, int position)>> manualHandles;

  /// Tracks the next duplicate counter per base slat ID.
  Map<String, int> _duplicateCounters;

  /// User-assigned names for each plate (keyed by plate index).
  Map<int, String> plateNames;

  /// Per-well dispensing configuration: plateIndex → wellName → WellConfig.
  Map<int, Map<String, WellConfig>> wellConfigs;

  /// User-assigned experiment title, persisted with the design file.
  String experimentTitle;

  /// Master mix configuration, persisted with the design file.
  MasterMixConfig masterMixConfig;

  /// Export format flags, persisted with the design file.
  bool generatePdf;
  bool generateCsv;
  bool generateHelperSheets;
  bool generatePegSheet;
  bool normalizeVolumes;

  /// Maximum allowed handle volume per well (nL) — used for warnings.
  double maxWellVolumeNl;

  /// PEG purification configuration, persisted with the design file.
  PegPurificationConfig pegConfig;

  PlateLayoutState({
    List<String>? unassignedSlats,
    Map<int, Map<String, String?>>? plateAssignments,
    Map<String, Set<String>>? duplicateGroups,
    Map<String, int>? duplicateCounters,
    Map<int, String>? plateNames,
    Map<int, Map<String, WellConfig>>? wellConfigs,
    Map<String, Set<(int, int)>>? manualHandles,
    this.experimentTitle = 'Experiment',
    this.masterMixConfig = const MasterMixConfig(),
    this.generatePdf = true,
    this.generateCsv = true,
    this.generateHelperSheets = false,
    this.generatePegSheet = false,
    this.normalizeVolumes = false,
    this.maxWellVolumeNl = 25000,
    this.pegConfig = const PegPurificationConfig(),
  })  : unassignedSlats = unassignedSlats ?? [],
        plateAssignments = plateAssignments ?? {},
        duplicateGroups = duplicateGroups ?? {},
        _duplicateCounters = duplicateCounters ?? {},
        plateNames = plateNames ?? {},
        wellConfigs = wellConfigs ?? {},
        manualHandles = manualHandles ?? {};

  /// Returns the user-assigned name for a plate, defaulting to 'P{index+1}'.
  String plateName(int index) => plateNames[index] ?? 'P${index + 1}';

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

  /// Returns the manual handle positions for a slat (empty set if none marked).
  Set<(int, int)> getManualHandles(String slatId) {
    return manualHandles[baseSlatId(slatId)] ?? {};
  }

  /// Sets the manual handle positions for a slat, replacing any existing markings.
  void setManualHandles(String slatId, Set<(int, int)> positions) {
    final base = baseSlatId(slatId);
    if (positions.isEmpty) {
      manualHandles.remove(base);
    } else {
      manualHandles[base] = Set<(int, int)>.from(positions);
    }
  }

  /// Applies manual handle markings to all slats in the given selected well keys.
  void applyManualHandlesToSelected(Set<String> selectedKeys, Set<(int, int)> positions) {
    for (var key in selectedKeys) {
      final parts = key.split(':');
      final plate = int.parse(parts[0]);
      final well = parts[1];
      final slatId = plateAssignments[plate]?[well];
      if (slatId == null) continue;
      setManualHandles(slatId, positions);
    }
  }

  /// Returns true if all selected slats have identical manual handle configurations.
  bool selectedHaveSameManualConfig(Set<String> selectedKeys) {
    Set<(int, int)>? reference;
    for (var key in selectedKeys) {
      final parts = key.split(':');
      final plate = int.parse(parts[0]);
      final well = parts[1];
      final slatId = plateAssignments[plate]?[well];
      if (slatId == null) continue;
      final config = getManualHandles(slatId);
      if (reference == null) {
        reference = config;
      } else if (!_setsEqual(reference, config)) {
        return false;
      }
    }
    return true;
  }

  static bool _setsEqual(Set<(int, int)> a, Set<(int, int)> b) {
    if (a.length != b.length) return false;
    return a.containsAll(b);
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
      plateNames: {0: 'P1'},
      experimentTitle: experimentTitle,
    );
  }

  /// Adds a new empty plate at the end.
  void addPlate() {
    final newIndex = plateAssignments.isEmpty ? 0 : (plateAssignments.keys.toList()..sort()).last + 1;
    plateAssignments[newIndex] = {for (var w in _plate96Wells) w: null};
    plateNames[newIndex] = 'P${newIndex + 1}';
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
        plateNames[newPlateIndex] = 'P${newPlateIndex + 1}';
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

  /// Exports all plates into a single consolidated grid for the `output_echo_plates` sheet.
  ///
  /// Each plate block: title row, slat header, 8 data rows, blank, config header, 8 config rows,
  /// followed by 2 blank rows of spacing. After all plates, a manual handles section is appended.
  List<List<dynamic>> exportConsolidatedGrid() {
    final result = <List<dynamic>>[];
    final sortedKeys = plateAssignments.keys.toList()..sort();

    for (var plateIndex in sortedKeys) {
      final plate = plateAssignments[plateIndex]!;
      final name = plateName(plateIndex);

      // Title row
      result.add(['$echoConsolidatedTitlePrefix$name (index=$plateIndex)$echoConsolidatedTitleSuffix']);

      // Slat header row
      result.add([experimentTitle, ...List.generate(12, (i) => i + 1)]);
      // Slat data rows A-H
      for (var r = 0; r < 8; r++) {
        final row = <dynamic>[plateRows[r]];
        for (var c = 0; c < 12; c++) {
          row.add(plate[wellName(r, c)] ?? '');
        }
        result.add(row);
      }

      // Blank separator
      result.add(List.filled(13, ''));

      // Config header row
      result.add([experimentTitle, ...List.generate(12, (i) => i + 1)]);
      // Config data rows A-H
      final plateConfigs = wellConfigs[plateIndex] ?? {};
      for (var r = 0; r < 8; r++) {
        final row = <dynamic>[plateRows[r]];
        for (var c = 0; c < 12; c++) {
          final config = plateConfigs[wellName(r, c)];
          row.add(config?.toExcelString() ?? '');
        }
        result.add(row);
      }

      // 2 blank rows between plates
      result.add(List.filled(13, ''));
      result.add(List.filled(13, ''));
    }

    // Manual handles section
    if (manualHandles.isNotEmpty) {
      result.add([echoManualHandlesMarker]);
      result.add(['Slat ID', 'Positions']);
      for (var entry in manualHandles.entries) {
        if (entry.value.isEmpty) continue;
        result.add([entry.key, _serializeManualPositions(entry.value)]);
      }
    }

    return result;
  }

  /// Serializes manual handle positions to compact string format: "2:1,3,5|5:2,4,6".
  static String _serializeManualPositions(Set<(int, int)> positions) {
    final h2 = positions.where((p) => p.$1 == 2).map((p) => p.$2).toList()..sort();
    final h5 = positions.where((p) => p.$1 == 5).map((p) => p.$2).toList()..sort();
    final parts = <String>[];
    if (h2.isNotEmpty) parts.add('2:${h2.join(',')}');
    if (h5.isNotEmpty) parts.add('5:${h5.join(',')}');
    return parts.join('|');
  }

  /// Parses compact string format "2:1,3,5|5:2,4,6" into a set of (helix, position) tuples.
  static Set<(int, int)> _parseManualPositions(String s) {
    final result = <(int, int)>{};
    if (s.isEmpty) return result;
    for (var part in s.split('|')) {
      final colonIdx = part.indexOf(':');
      if (colonIdx < 0) continue;
      final helix = int.tryParse(part.substring(0, colonIdx));
      if (helix == null) continue;
      for (var posStr in part.substring(colonIdx + 1).split(',')) {
        final pos = int.tryParse(posStr.trim());
        if (pos != null) result.add((helix, pos));
      }
    }
    return result;
  }

  /// Exports all export settings and master mix config as key-value pairs
  /// for writing to the lab_metadata sheet.
  Map<String, String> exportLabMetadata() {
    return {
      'experiment_title': experimentTitle,
      'generate_pdf': generatePdf.toString(),
      'generate_csv': generateCsv.toString(),
      'generate_helper_sheets': generateHelperSheets.toString(),
      'generate_peg_sheet': generatePegSheet.toString(),
      'normalize_volumes': normalizeVolumes.toString(),
      'max_well_volume_nl': maxWellVolumeNl.toString(),
      ...masterMixConfig.toMap(),
      ...pegConfig.toMap(),
    };
  }

  /// Reconstructs a PlateLayoutState from the consolidated `output_echo_plates` sheet.
  ///
  /// Scans rows for title markers to separate plate blocks, then parses
  /// slat data and config data from each block. Returns null if no plates found.
  static PlateLayoutState? fromConsolidatedSheet(
    List<List<dynamic>> rows,
    Map<String, Slat> slats,
    Map<String, Map<String, dynamic>> layerMap, {
    Map<String, String>? labMetadata,
  }) {
    if (rows.isEmpty) return null;

    final plateAssignments = <int, Map<String, String?>>{};
    final parsedPlateNames = <int, String>{};
    final parsedWellConfigs = <int, Map<String, WellConfig>>{};
    final parsedManualHandles = <String, Set<(int, int)>>{};
    String parsedExperimentTitle = 'Experiment';
    final allPlacedIds = <String>[];

    // Regex to extract plate name and index from title row
    final titleRegex = RegExp(
      r'^' + RegExp.escape(echoConsolidatedTitlePrefix) + r'(.+?) \(index=(\d+)\)' +
      RegExp.escape(echoConsolidatedTitleSuffix) + r'$',
    );

    int i = 0;
    while (i < rows.length) {
      final firstCell = rows[i].isNotEmpty ? rows[i][0].toString() : '';

      // Check for manual handles section
      if (firstCell == echoManualHandlesMarker) {
        i += 2; // skip marker + header row
        while (i < rows.length && rows[i].isNotEmpty) {
          final row = rows[i];
          if (row.length >= 2 && row[0] != null && row[0].toString().isNotEmpty) {
            final slatId = row[0].toString();
            final positions = _parseManualPositions(row[1].toString());
            if (positions.isNotEmpty) parsedManualHandles[slatId] = positions;
          }
          i++;
        }
        break;
      }

      // Check for plate title row
      final titleMatch = titleRegex.firstMatch(firstCell);
      if (titleMatch == null) {
        i++;
        continue;
      }

      final pName = titleMatch.group(1)!;
      final plateIndex = int.parse(titleMatch.group(2)!);
      final plateMap = <String, String?>{for (var w in _plate96Wells) w: null};
      i++; // move past title row

      // Parse slat header (row i) and data rows (i+1 to i+8)
      if (i < rows.length) {
        // Experiment title from the header row
        final headerCell = rows[i].isNotEmpty ? rows[i][0]?.toString() : null;
        if (headerCell != null && headerCell.isNotEmpty) {
          parsedExperimentTitle = headerCell;
        }
        i++; // skip header row
      }

      // 8 data rows (A-H)
      for (var r = 0; r < 8 && i < rows.length; r++, i++) {
        final row = rows[i];
        for (var c = 1; c < row.length && c <= 12; c++) {
          final cellValue = row[c];
          if (cellValue != null && cellValue.toString().isNotEmpty) {
            final slatId = cellValue.toString();
            plateMap[wellName(r, c - 1)] = slatId;
            allPlacedIds.add(slatId);
          }
        }
      }

      plateAssignments[plateIndex] = plateMap;
      parsedPlateNames[plateIndex] = pName;

      // Skip blank separator row
      if (i < rows.length) i++;

      // Parse config header + 8 config data rows
      if (i < rows.length) i++; // skip config header
      final plateConfigMap = <String, WellConfig>{};
      for (var r = 0; r < 8 && i < rows.length; r++, i++) {
        final row = rows[i];
        for (var c = 1; c < row.length && c <= 12; c++) {
          final cellValue = row[c];
          if (cellValue != null && cellValue.toString().isNotEmpty) {
            final config = WellConfig.fromExcelString(cellValue.toString());
            if (config != null) {
              plateConfigMap[wellName(r, c - 1)] = config;
            }
          }
        }
      }
      if (plateConfigMap.isNotEmpty) {
        parsedWellConfigs[plateIndex] = plateConfigMap;
      }

      // Skip 2 blank spacer rows between plates
      while (i < rows.length && rows[i].every((c) => c == null || c.toString().isEmpty)) {
        i++;
      }
    }

    if (plateAssignments.isEmpty) return null;

    // Parse lab metadata (master mix config + export settings)
    final m = labMetadata ?? {};
    final parsedMixConfig = MasterMixConfig.fromMap(m);
    final labExperimentTitle = m['experiment_title'];
    final parsedGeneratePdf = m['generate_pdf'] != 'false';
    final parsedGenerateCsv = m['generate_csv'] != 'false';
    final parsedGenerateHelper = m['generate_helper_sheets'] == 'true';
    final parsedGeneratePeg = m['generate_peg_sheet'] == 'true';
    final parsedPegConfig = PegPurificationConfig.fromMap(m);
    final parsedNormalize = m['normalize_volumes'] == 'true';
    final parsedMaxWellVolume = double.tryParse(m['max_well_volume_nl'] ?? '') ?? 25000;

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
      manualHandles: parsedManualHandles,
      experimentTitle: labExperimentTitle ?? parsedExperimentTitle,
      masterMixConfig: parsedMixConfig,
      generatePdf: parsedGeneratePdf,
      generateCsv: parsedGenerateCsv,
      generateHelperSheets: parsedGenerateHelper,
      generatePegSheet: parsedGeneratePeg,
      normalizeVolumes: parsedNormalize,
      maxWellVolumeNl: parsedMaxWellVolume,
      pegConfig: parsedPegConfig,
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
      manualHandles: {
        for (var e in manualHandles.entries) e.key: Set<(int, int)>.from(e.value),
      },
      experimentTitle: experimentTitle,
      masterMixConfig: masterMixConfig,
      generatePdf: generatePdf,
      generateCsv: generateCsv,
      generateHelperSheets: generateHelperSheets,
      generatePegSheet: generatePegSheet,
      normalizeVolumes: normalizeVolumes,
      maxWellVolumeNl: maxWellVolumeNl,
      pegConfig: pegConfig,
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

      // Clean up duplicate groups and manual handles
      for (var baseId in deletedIds) {
        duplicateGroups.remove(baseId);
        _duplicateCounters.remove(baseId);
        manualHandles.remove(baseId);
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
    plateNames[newPlateIndex] = 'P${newPlateIndex + 1}';
    final well = wellName(0, 0);
    plateAssignments[newPlateIndex]![well] = slatId;
    wellConfigs.putIfAbsent(newPlateIndex, () => {}).putIfAbsent(well, () => const WellConfig());
    occupiedThisRound.add('$newPlateIndex:$well');
    return '$newPlateIndex:$well';
  }
}
