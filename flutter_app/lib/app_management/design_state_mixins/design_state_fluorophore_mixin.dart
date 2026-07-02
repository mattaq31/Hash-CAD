// Mixin for fluorophore library management and handle fluorophore assignment.

import 'package:flutter/material.dart';

import '../../crisscross_core/fluorophore.dart';
import '../../crisscross_core/slats.dart';
import '../../crisscross_core/slat_standardized_mapping.dart';
import '../../crisscross_core/common_utilities.dart' hide getLayerByOrder;
import 'design_state_contract.dart';

/// Mixin containing fluorophore library CRUD and per-handle fluorophore assignment for DesignState.
mixin DesignStateFluorophoreMixin on ChangeNotifier, DesignStateContract {

  // === Library CRUD ===

  /// Adds a new fluorophore to the per-design palette.
  @override
  void addFluorophore(Fluorophore fluorophore) {
    fluorophorePalette[fluorophore.name] = fluorophore;
    saveUndoState();
    notifyListeners();
  }

  /// Renames a fluorophore in the palette and cascades the change to all tagged handles.
  @override
  void renameFluorophore(String oldName, String newName) {
    if (!fluorophorePalette.containsKey(oldName) || oldName == newName) return;
    if (fluorophorePalette.containsKey(newName)) return;

    final entry = fluorophorePalette.remove(oldName)!;
    fluorophorePalette[newName] = entry.copyWith(name: newName);

    // Cascade rename to all tagged handles
    for (var slat in slats.values) {
      for (var side in [2, 5]) {
        final handleDict = getHandleDict(slat, side);
        for (var entry in handleDict.entries.toList()) {
          if (entry.value['fluorophore'] == oldName) {
            _invalidatePlateAssignmentIfNeeded(slat, entry.key, side);
            getHandleDict(slat, side)[entry.key]?['fluorophore'] = newName;
          }
        }
      }
    }

    plateCompatibilityWarning = null;
    saveUndoState();
    notifyListeners();
  }

  /// Deletes a fluorophore from the palette and clears it from all tagged handles.
  @override
  void deleteFluorophore(String name) {
    if (!fluorophorePalette.containsKey(name)) return;
    fluorophorePalette.remove(name);

    // Clear fluorophore from all handles using it
    for (var slat in slats.values) {
      for (var side in [2, 5]) {
        final handleDict = getHandleDict(slat, side);
        for (var entry in handleDict.entries.toList()) {
          if (entry.value['fluorophore'] == name) {
            _invalidatePlateAssignmentIfNeeded(slat, entry.key, side);
            getHandleDict(slat, side)[entry.key]?.remove('fluorophore');
          }
        }
      }
    }

    plateCompatibilityWarning = null;
    saveUndoState();
    notifyListeners();
  }

  /// Updates the visual marker shape of a fluorophore in the palette.
  @override
  void updateFluorophoreShape(String name, FluorophoreShape shape) {
    if (!fluorophorePalette.containsKey(name)) return;
    fluorophorePalette[name] = fluorophorePalette[name]!.copyWith(shape: shape);
    saveUndoState();
    notifyListeners();
  }

  // === Per-handle assignment ===

  /// Assigns a fluorophore tag to the handle at [key], propagating to phantom copies.
  @override
  void assignFluorophoreToHandle(HandleKey key, String fluorophoreName) {
    if (!fluorophorePalette.containsKey(fluorophoreName)) return;

    final (slatId, position, side) = key;
    final slat = slats[slatId];
    if (slat == null) return;

    // Resolve base slat ID for phantom-aware storage
    final baseId = slat.phantomParent ?? slatId;
    final baseSlat = slats[baseId];
    if (baseSlat == null) return;

    final handleDict = getHandleDict(baseSlat, side);
    final handle = handleDict[position];
    if (handle == null) return;

    // Only assign to non-blocked assembly handles
    final category = handle['category'] as String?;
    if (category == null || !category.contains('ASSEMBLY')) return;
    if (handle['value'] == '0') return;

    _invalidatePlateAssignmentFamily(baseId, position, side);
    final updatedHandle = getHandleDict(baseSlat, side)[position];
    if (updatedHandle == null) return;
    updatedHandle['fluorophore'] = fluorophoreName;

    // Mirror to all phantom copies
    _mirrorFluorophoreToPhantoms(baseId, position, side, fluorophoreName);

    plateCompatibilityWarning = null;
    saveUndoState();
    notifyListeners();
  }

  /// Removes any fluorophore tag from the handle at [key], propagating to phantom copies.
  @override
  void clearFluorophoreFromHandle(HandleKey key) {
    final (slatId, position, side) = key;
    final slat = slats[slatId];
    if (slat == null) return;

    final baseId = slat.phantomParent ?? slatId;
    final baseSlat = slats[baseId];
    if (baseSlat == null) return;

    final handleDict = getHandleDict(baseSlat, side);
    final handle = handleDict[position];
    if (handle == null) return;

    _invalidatePlateAssignmentFamily(baseId, position, side);
    getHandleDict(baseSlat, side)[position]?.remove('fluorophore');

    // Mirror clear to phantoms
    _mirrorFluorophoreToPhantoms(baseId, position, side, null);

    plateCompatibilityWarning = null;
    saveUndoState();
    notifyListeners();
  }

  /// Assigns a fluorophore to multiple handles at once across matching slats.
  @override
  void massAssignFluorophore(Map<String, Set<(int, int)>> perSlatPositions, String fluorophoreName) {
    if (!fluorophorePalette.containsKey(fluorophoreName)) return;

    for (var entry in perSlatPositions.entries) {
      final slatId = entry.key;
      final slat = slats[slatId];
      if (slat == null) continue;

      for (var (side, position) in entry.value) {
        final baseId = slat.phantomParent ?? slatId;
        final baseSlat = slats[baseId];
        if (baseSlat == null) continue;

        final handleDict = getHandleDict(baseSlat, side);
        final handle = handleDict[position];
        if (handle == null) continue;

        final category = handle['category'] as String?;
        if (category == null || !category.contains('ASSEMBLY')) continue;
        if (handle['value'] == '0') continue;

        _invalidatePlateAssignmentFamily(baseId, position, side);
        final updatedHandle = getHandleDict(baseSlat, side)[position];
        if (updatedHandle == null) continue;
        updatedHandle['fluorophore'] = fluorophoreName;
        _mirrorFluorophoreToPhantoms(baseId, position, side, fluorophoreName);
      }
    }

    plateCompatibilityWarning = null;
    saveUndoState();
    notifyListeners();
  }

  /// Clears fluorophore tags from multiple handles at once across matching slats.
  @override
  void massClearFluorophore(Map<String, Set<(int, int)>> perSlatPositions) {
    for (var entry in perSlatPositions.entries) {
      final slatId = entry.key;
      final slat = slats[slatId];
      if (slat == null) continue;

      for (var (side, position) in entry.value) {
        final baseId = slat.phantomParent ?? slatId;
        final baseSlat = slats[baseId];
        if (baseSlat == null) continue;

        final handleDict = getHandleDict(baseSlat, side);
        final handle = handleDict[position];
        if (handle == null) continue;

        _invalidatePlateAssignmentFamily(baseId, position, side);
        getHandleDict(baseSlat, side)[position]?.remove('fluorophore');
        _mirrorFluorophoreToPhantoms(baseId, position, side, null);
      }
    }

    plateCompatibilityWarning = null;
    saveUndoState();
    notifyListeners();
  }

  /// Removes all fluorophore tags from every handle in the design.
  @override
  void clearAllFluorophoreAssignments() {
    for (var slat in slats.values) {
      for (var side in [2, 5]) {
        final handleDict = getHandleDict(slat, side);
        for (var entry in handleDict.entries.toList()) {
          if (entry.value['fluorophore'] != null) {
            _invalidatePlateAssignmentIfNeeded(slat, entry.key, side);
            getHandleDict(slat, side)[entry.key]?.remove('fluorophore');
          }
        }
      }
    }
    plateCompatibilityWarning = null;
    saveUndoState();
    notifyListeners();
  }

  // === Query ===

  /// Returns the compatibility token for plate lookup: fluorophore name if tagged, else standard compatibility.
  @override
  String? getEffectiveCompatibility(String slatType, int position, int side, String slatId) {
    final slat = slats[slatId];
    if (slat == null) return getRequiredStapleCompatibility(slatType, position, side);

    final baseId = slat.phantomParent ?? slatId;
    final baseSlat = slats[baseId];
    if (baseSlat == null) return getRequiredStapleCompatibility(slatType, position, side);

    final handleDict = getHandleDict(baseSlat, side);
    final fluorophore = handleDict[position]?['fluorophore'] as String?;
    if (fluorophore != null) return fluorophore;

    return getRequiredStapleCompatibility(slatType, position, side);
  }

  // === Internal helpers ===

  /// Mirrors a fluorophore assignment (or removal) to all phantom copies of a base slat.
  void _mirrorFluorophoreToPhantoms(String baseId, int position, int side, String? fluorophoreName) {
    for (var slat in slats.values) {
      if (slat.phantomParent == baseId) {
        final handleDict = getHandleDict(slat, side);
        final handle = handleDict[position];
        if (handle != null) {
          if (fluorophoreName != null) {
            handle['fluorophore'] = fluorophoreName;
          } else {
            handle.remove('fluorophore');
          }
        }
      }
    }
  }

  /// Converts an assigned handle back to a placeholder if its compatibility source has changed.
  void _invalidatePlateAssignmentIfNeeded(Slat slat, int position, int side) {
    final handle = getHandleDict(slat, side)[position];
    if (handle == null || handle['placeholder'] == true) return;

    final value = handle['value']?.toString() ?? '';
    final category = handle['category'] as String? ?? '';
    slat.setPlaceholderHandle(position, side, value, category);
  }

  /// Invalidates any assigned plate staples on a base handle and all of its phantom copies.
  void _invalidatePlateAssignmentFamily(String baseId, int position, int side) {
    final affectedSlatIds = [baseId, ...phantomMap[baseId]?.values ?? const <String>[]];
    for (var affectedSlatId in affectedSlatIds) {
      final affectedSlat = slats[affectedSlatId];
      if (affectedSlat == null) continue;
      _invalidatePlateAssignmentIfNeeded(affectedSlat, position, side);
    }
  }
}
