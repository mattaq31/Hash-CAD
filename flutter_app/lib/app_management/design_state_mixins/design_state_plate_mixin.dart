import 'package:flutter/material.dart';

import '../../crisscross_core/handle_plates.dart';
import '../../crisscross_core/slat_standardized_mapping.dart';
import '../../crisscross_core/slats.dart';
import '../design_io/design_io.dart';
import 'design_state_contract.dart';

/// Mixin containing plate import and handle assignment operations for DesignState
mixin DesignStatePlateMixin on ChangeNotifier, DesignStateContract {

  @override
  void importPlates() async {
    await importPlatesFromFile(plateStack);
    syncCargoFromPlates(plateStack, cargoPalette);
    plateCompatibilityWarning = null;

    // TODO: if plate already exists, show warning dialog
    // TODO: how to handle identical wells
    notifyListeners();
  }

  @override
  void removePlate(String plateName) {
    plateStack.removePlate(plateName);
    _revertHandlesFromPlate(plateName);
    plateCompatibilityWarning = null;
    notifyListeners();
  }

  /// Reverts all handles sourced from [plateName] back to placeholders.
  void _revertHandlesFromPlate(String plateName) {
    for (var slat in slats.values) {
      for (var entry in slat.h2Handles.entries.toList()) {
        if (entry.value['plate'] == plateName && entry.value['placeholder'] != true) {
          final value = entry.value['value'] as String? ?? '';
          final category = entry.value['category'] as String? ?? '';
          slat.setPlaceholderHandle(entry.key, 2, value, category);
        }
      }
      for (var entry in slat.h5Handles.entries.toList()) {
        if (entry.value['plate'] == plateName && entry.value['placeholder'] != true) {
          final value = entry.value['value'] as String? ?? '';
          final category = entry.value['category'] as String? ?? '';
          slat.setPlaceholderHandle(entry.key, 5, value, category);
        }
      }
    }
  }

  @override
  void removeAllPlates() {
    final plateNames = plateStack.listPlateNames();
    plateStack.clear();
    for (var plateName in plateNames) {
      _revertHandlesFromPlate(plateName);
    }
    plateCompatibilityWarning = null;
    notifyListeners();
  }

  @override
  void plateAssignAllHandles() {
    int compatibilityMismatchCount = 0;

    /// Records a compatibility mismatch when variants exist for a position but none match the required compatibility.
    void recordCompatibilityMismatch(String category, int posn, int side, String lookupValue, String? requiredCompatibility) {
      final availableCompatibilities = plateStack.availableCompatibilities(category, posn, side, lookupValue);
      if (availableCompatibilities.isEmpty) return;

      final normalizedRequired = normalizePlateCompatibility(requiredCompatibility);
      if (!availableCompatibilities.contains(normalizedRequired)) {
        compatibilityMismatchCount++;
      }
    }

    void assignHandleIfPresent(Slat slat, int posn, int side, Map<int, Map<String, dynamic>> handles) {
      final requiredCompatibility = getEffectiveCompatibility(slat.slatType, posn, side, slat.id);

      if (!handles.containsKey(posn)) {
        if (plateStack.contains('FLAT', posn, side, 'BLANK', compatibility: requiredCompatibility)) {
          final data = plateStack.getOligoData('FLAT', posn, side, 'BLANK', compatibility: requiredCompatibility);
          slat.setHandle(posn, side, data['sequence'], data['well'], data['plateName'], 'BLANK', 'FLAT', data['concentration']);
        } else {
          recordCompatibilityMismatch('FLAT', posn, side, 'BLANK', requiredCompatibility);
        }
        return;
      }

      final handle = handles[posn]!;
      final category = handle['category'] as String?;
      final originalValue = handle['value']?.toString() ?? '';
      if (category == null) return;

      // Blocked handles (value '0') on assembly positions need a flat staple sequence.
      // Use setHandle() so the handle is properly removed from placeholderList.
      if (originalValue == '0' && (category == 'ASSEMBLY_HANDLE' || category == 'ASSEMBLY_ANTIHANDLE')) {
        if (plateStack.contains('FLAT', posn, side, 'BLANK', compatibility: requiredCompatibility)) {
          final data = plateStack.getOligoData('FLAT', posn, side, 'BLANK', compatibility: requiredCompatibility);
          slat.setHandle(posn, side, data['sequence'], data['well'], data['plateName'], originalValue, category, data['concentration'] as int);
        } else {
          recordCompatibilityMismatch('FLAT', posn, side, 'BLANK', requiredCompatibility);
        }
        return;
      }

      late final String lookupValue;

      if (category == 'SEED') {
        // Format the SEED value for lookup
        lookupValue = originalValue.replaceFirst(RegExp(r'^[^-]+-'), '').replaceAll('-', '_');
      } else {
        lookupValue = originalValue;
      }

      if (plateStack.contains(category, posn, side, lookupValue, compatibility: requiredCompatibility)) {
        final data = plateStack.getOligoData(category, posn, side, lookupValue, compatibility: requiredCompatibility);
        slat.setHandle(posn, side, data['sequence'], data['well'], data['plateName'], originalValue, category, data['concentration']);
      } else {
        recordCompatibilityMismatch(category, posn, side, lookupValue, requiredCompatibility);
      }
    }

    for (var slat in slats.values) {
      for (int posn = 1; posn < slat.maxLength + 1; posn++) {
        assignHandleIfPresent(slat, posn, 2, slat.h2Handles);
        assignHandleIfPresent(slat, posn, 5, slat.h5Handles);
      }
    }

    plateCompatibilityWarning = compatibilityMismatchCount > 0
        ? '$compatibilityMismatchCount staple(s) could not be assigned because only incompatible compatibility variants were available.'
        : null;
    notifyListeners();
  }
}
