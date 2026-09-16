// Mixin for recording, naming and placing reusable assembly handle patterns.

import 'package:flutter/material.dart';

import '../../crisscross_core/assembly_handle_pattern.dart';
import '../../crisscross_core/common_utilities.dart' hide getLayerByOrder;
import 'design_state_contract.dart';

/// Monotonic counter used to generate session-unique pattern ids (ids are never saved to file).
int _patternIdCounter = 0;

/// Mixin containing assembly handle pattern management for DesignState.
///
/// A pattern is a pre-configured group of assembly handles (values and blocks) stored as offsets relative to its
/// top-left handle. Placement validity is not checked here - the grid canvas reuses the multi-handle move validity
/// check and only calls [placeAssemblyHandlePattern] when the whole pattern fits.
mixin DesignStateAssemblyPatternMixin on ChangeNotifier, DesignStateContract {

  /// Generates a fresh session-unique pattern id.
  String _generatePatternId() => 'P${++_patternIdCounter}';

  /// Returns the first unused default name of the form 'Pattern N'.
  String _nextDefaultPatternName() {
    final existingNames = assemblyHandlePatterns.values.map((p) => p.name).toSet();
    int n = 1;
    while (existingNames.contains('Pattern $n')) {
      n++;
    }
    return 'Pattern $n';
  }

  /// Records the currently selected assembly handles on [layerKey]/[attachMode] as a new pattern.
  ///
  /// Only positions holding an assembly handle are recorded; blocked handles are kept as blocked entries.
  /// [includeHandles] / [includeBlocks] restrict recording to regular valued handles or blocks respectively.
  /// Returns the new pattern id, or null if nothing in the selection matched.
  @override
  String? recordAssemblyHandlePattern(String layerKey, String attachMode,
      {bool includeHandles = true, bool includeBlocks = true}) {
    final occupiedPoints = occupiedGridPoints[layerKey];
    if (occupiedPoints == null) return null;
    final side = getSlatSideFromLayer(layerMap, layerKey, attachMode);

    // absolute coordinates are collected first, as offsets can only be computed once the anchor is known
    final recorded = <({Offset coord, String value, bool blocked})>[];
    for (var coord in selectedAssemblyPositions) {
      final slatId = occupiedPoints[coord];
      if (slatId == null) continue;
      final slat = slats[slatId];
      final position = slat?.slatCoordinateToPosition[coord];
      if (slat == null || position == null) continue;

      final handle = getHandleDict(slat, side)[position];
      if (handle == null || !handle['category'].toString().contains('ASSEMBLY')) continue;

      // blocks are registered against the phantom parent (if any), matching the canvas click logic. A value of '0'
      // also counts as a block, consistent with the slat painter which draws any '0' assembly handle as blocked.
      final key = (slat.phantomParent ?? slat.id, position, side);
      final blocked = assemblyLinkManager.handleBlocks.contains(key) || handle['value'].toString() == '0';
      if (blocked ? !includeBlocks : !includeHandles) continue;
      recorded.add((coord: coord, value: blocked ? '0' : handle['value'].toString(), blocked: blocked));
    }
    if (recorded.isEmpty) return null;

    final anchor = findPatternAnchor(recorded.map((r) => r.coord));
    final entries = recorded
        .map((r) => AssemblyHandlePatternEntry(offset: r.coord - anchor, value: r.value, blocked: r.blocked))
        .toList();

    final id = _generatePatternId();
    assemblyHandlePatterns[id] = AssemblyHandlePattern(id: id, name: _nextDefaultPatternName(), entries: entries);
    saveUndoState();
    notifyListeners();
    return id;
  }

  /// Renames pattern [id] to [newName]. Returns false (and changes nothing) if the name is empty or already taken.
  @override
  bool renameAssemblyHandlePattern(String id, String newName) {
    final pattern = assemblyHandlePatterns[id];
    final trimmed = newName.trim();
    if (pattern == null || trimmed.isEmpty) return false;
    if (trimmed == pattern.name) return true;
    if (assemblyHandlePatterns.values.any((p) => p.name == trimmed)) return false;

    assemblyHandlePatterns[id] = pattern.copyWith(name: trimmed);
    saveUndoState();
    notifyListeners();
    return true;
  }

  /// Deletes pattern [id] from the design.
  @override
  void deleteAssemblyHandlePattern(String id) {
    if (assemblyHandlePatterns.remove(id) == null) return;
    saveUndoState();
    notifyListeners();
  }

  /// Stamps pattern [id] onto [layerKey]/[attachMode] with its anchor at grid coordinate [anchorCoord].
  ///
  /// Existing blocks/enforced values at target positions are cleared so the pattern fully overrides them.
  /// When [enforce] is true, every placed non-blocked value is also enforced. The pattern is rotated about its anchor
  /// by [rotationSteps] 90° steps (square grid only). A single undo snapshot is saved.
  @override
  void placeAssemblyHandlePattern(String id, String layerKey, String attachMode, Offset anchorCoord,
      {bool enforce = false, int rotationSteps = 0}) {
    final pattern = assemblyHandlePatterns[id];
    final occupiedPoints = occupiedGridPoints[layerKey];
    if (pattern == null || occupiedPoints == null) return;

    final side = getSlatSideFromLayer(layerMap, layerKey, attachMode);
    final category = attachMode == 'top' ? 'ASSEMBLY_HANDLE' : 'ASSEMBLY_ANTIHANDLE';

    final coords = pattern.coordinatesAt(anchorCoord, rotationSteps: rotationSteps, gridMode: gridMode);
    for (int i = 0; i < pattern.entries.length; i++) {
      final entry = pattern.entries[i];
      final coord = coords[i];
      final slatId = occupiedPoints[coord];
      if (slatId == null) continue; // defensive - the canvas only calls this when all positions are valid
      final slat = slats[slatId]!;
      final position = slat.slatCoordinateToPosition[coord]!;
      final key = (slat.phantomParent ?? slatId, position, side);

      // clear any previous overrides, otherwise smartSetHandle's enforcement pass would revert the new value.
      // removeLink (not just clearEnforcedValue) is needed as enforcing a lone handle puts it in a single-member
      // link group, which would otherwise survive and keep the handle drawn as linked. It also detaches the
      // position from any wider link group so the pattern value doesn't propagate to other handles.
      assemblyLinkManager.removeBlock(key);
      assemblyLinkManager.removeLink(key);

      if (entry.blocked) {
        applyHandleBlock(key, category: category, requestStateUpdate: false);
        continue;
      }

      smartSetHandle(slat, position, side, entry.value, category);
      final enforcedValue = int.tryParse(entry.value);
      if (enforce && enforcedValue != null && enforcedValue != 0) {
        setHandleEnforcedValue(key, enforcedValue, requestStateUpdate: false);
      }
    }

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }
}
