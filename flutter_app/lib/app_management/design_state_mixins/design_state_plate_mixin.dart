import 'package:flutter/material.dart';

import '../../crisscross_core/handle_plates.dart';
import '../design_io/design_io.dart';
import 'design_state_contract.dart';

/// Mixin containing plate import and handle assignment operations for DesignState
mixin DesignStatePlateMixin on ChangeNotifier, DesignStateContract {

  @override
  void importPlates() async {
    await importPlatesFromFile(plateStack);
    syncCargoFromPlates(plateStack, cargoPalette);

    // TODO: if plate already exists, show warning dialog
    // TODO: how to handle identical wells
    notifyListeners();
  }

  @override
  void removePlate(String plateName) {
    plateStack.removePlate(plateName);
    notifyListeners();
  }

  @override
  void removeAllPlates() {
    plateStack.clear();
    notifyListeners();
  }

  @override
  void plateAssignAllHandles() {
    void assignHandleIfPresent(slat, int posn, int side, Map<int, Map<String, dynamic>> handles) {
      if (!handles.containsKey(posn)) {
        if (plateStack.contains('FLAT', posn, side, 'BLANK')) {
          final data = plateStack.getOligoData('FLAT', posn, side, 'BLANK');
          slat.setHandle(
            posn,
            side,
            data['sequence'],
            data['well'],
            data['plateName'],
            'BLANK',
            'FLAT',
            data['concentration'],
          );
        }
        return;
      }

      final handle = handles[posn]!;
      final category = handle['category'] as String?;
      final originalValue = handle['value'];

      // Blocked handles (value '0') on assembly positions need a flat staple sequence.
      // Use setHandle() so the handle is properly removed from placeholderList.
      if (originalValue == '0' && (category == 'ASSEMBLY_HANDLE' || category == 'ASSEMBLY_ANTIHANDLE')) {
        if (plateStack.contains('FLAT', posn, side, 'BLANK')) {
          final data = plateStack.getOligoData('FLAT', posn, side, 'BLANK');
          slat.setHandle(
            posn,
            side,
            data['sequence'],
            data['well'],
            data['plateName'],
            originalValue,
            category!,
            data['concentration'] as int,
          );
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

      if (plateStack.contains(category!, posn, side, lookupValue)) {
        final data = plateStack.getOligoData(category, posn, side, lookupValue);
        slat.setHandle(
          posn,
          side,
          data['sequence'],
          data['well'],
          data['plateName'],
          originalValue,
          category,
          data['concentration'],
        );
      }
    }

    for (var slat in slats.values) {
      for (int posn = 1; posn < slat.maxLength + 1; posn++) {
        assignHandleIfPresent(slat, posn, 2, slat.h2Handles);
        assignHandleIfPresent(slat, posn, 5, slat.h5Handles);
      }
    }
    notifyListeners();
  }
}
