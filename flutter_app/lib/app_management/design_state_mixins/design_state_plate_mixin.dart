import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/handle_plates.dart';
import '../main_design_io.dart';

/// Mixin containing plate import and handle assignment operations for DesignState
mixin DesignStatePlateMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;

  PlateLibrary get plateStack;

  void importPlates() async {
    await importPlatesFromFile(plateStack);

    // TODO: if plate already exists, show warning dialog
    // TODO: how to handle identical wells
    notifyListeners();
  }

  void removePlate(String plateName) {
    plateStack.removePlate(plateName);
    notifyListeners();
  }

  void removeAllPlates() {
    plateStack.clear();
    notifyListeners();
  }

  void plateAssignAllHandles() {
    void assignHandleIfPresent(Slat slat, int posn, int side, Map<int, Map<String, dynamic>> handles) {
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
      final category = handle['category'];
      final originalValue = handle['value'];
      late final String lookupValue;

      if (category == 'SEED') {
        // Format the SEED value for lookup
        lookupValue = originalValue.replaceFirst(RegExp(r'^[^-]+-'), '').replaceAll('-', '_');
      } else {
        lookupValue = originalValue;
      }

      if (plateStack.contains(category, posn, side, lookupValue)) {
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
