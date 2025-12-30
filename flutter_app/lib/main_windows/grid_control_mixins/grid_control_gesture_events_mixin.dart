import 'package:flutter/material.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import 'grid_control_contract.dart';

/// Mixin containing gesture event handlers for GridAndCanvas
mixin GridControlGestureEventsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  void handleScaleStart(ScaleStartDetails details) {
    initialScale = scale;
    initialPanOffset = offset;
    initialGestureFocalPoint = details.focalPoint;
  }

  void handleScaleUpdate(ScaleUpdateDetails details) {
    // turn off scaling completely while moving around with a slat in move mode
    if (dragActive || dragBoxActive) {
      return;
    }
    setState(() {
      // this scaling system is identical to the one used for the mouse wheel zoom (see function above)
      final newScale = (initialScale * details.scale).clamp(minScale, maxScale);
      if (newScale == initialScale) {
        offset = initialPanOffset + (details.focalPoint - initialGestureFocalPoint) / scale;
      } else {
        offset = details.focalPoint - (((details.focalPoint - offset) / scale) * newScale);
      }
      // TODO: not sure if the fact that pan and zoom cannot be handled simultaneously is a problem... should circle back here if so
      scale = newScale;
    });
  }

  void handleTapDown(TapDownDetails details, DesignState appState, ActionState actionState, BuildContext context) {
    final Offset snappedPosition = gridSnap(details.localPosition, appState);
    if (getActionMode(actionState) == 'Slat-Add') {
      if (!hoverValid) {
        // cannot place slats if blocked by other slats
        return;
      }
      // slats added to a persistent list here
      Map<int, Map<int, Offset>> incomingSlats = generateSlatPositions(snappedPosition, false, appState);
      appState.clearSelection();
      //  proceed to add new slats if valid
      appState.addSlats(appState.selectedLayerKey, incomingSlats);
    } else if (getActionMode(actionState) == 'Slat-Delete') {
      // slats removed from the persistent list here
      var coordConvertedPosition = appState.convertRealSpacetoCoordinateSpace(snappedPosition);
      if (checkCoordinateOccupancy(appState, actionState, [coordConvertedPosition])) {
        appState.removeSlat(appState.occupiedGridPoints[appState.selectedLayerKey]![coordConvertedPosition]!);
      }
    } else if (getActionMode(actionState) == 'Cargo-Add') {
      if (!hoverValid) {
        return;
      }

      Map<int, Offset> incomingCargo;

      if (appState.cargoAdditionType == 'SEED') {
        incomingCargo = generateSeedPositions(snappedPosition, false, appState);
      } else {
        incomingCargo = generateCargoPositions(snappedPosition, false, appState);
      }

      // proceed to add new cargo if valid
      appState.clearSelection();
      if (appState.cargoAdditionType != null) {
        if (appState.cargoAdditionType == 'SEED') {
          appState.attachSeed(appState.selectedLayerKey, actionState.cargoAttachMode, incomingCargo, context);
        } else {
          appState.attachCargo(
              appState.cargoPalette[appState.cargoAdditionType]!, appState.selectedLayerKey, actionState.cargoAttachMode, incomingCargo);
        }
      }
    } else if (getActionMode(actionState) == 'Cargo-Delete') {
      // cargo removed from the persistent list here
      var coordConvertedPosition = appState.convertRealSpacetoCoordinateSpace(snappedPosition);
      if (checkCoordinateOccupancy(appState, actionState, [coordConvertedPosition])) {
        appState.removeCargo(
            appState.occupiedGridPoints[appState.selectedLayerKey]![coordConvertedPosition]!,
            actionState.cargoAttachMode,
            coordConvertedPosition);
      }
    }
  }

  void handleTapUp(TapUpDetails details, DesignState appState, ActionState actionState) {
    final Offset snappedPosition = appState.convertRealSpacetoCoordinateSpace(gridSnap(details.localPosition, appState));

    if (getActionMode(actionState) == 'Slat-Move') {
      if (checkCoordinateOccupancy(appState, actionState, [snappedPosition])) {
        if (appState.selectedSlats.isNotEmpty && !isShiftPressed) {
          appState.clearSelection();
        }
        // this flips a selection if the slat was already clicked (and pressing shift)
        appState.selectSlat(appState.occupiedGridPoints[appState.selectedLayerKey]![snappedPosition]!);
      } else {
        appState.clearSelection();
      }
    } else if (getActionMode(actionState) == 'Cargo-Move') {
      if (checkCoordinateOccupancy(appState, actionState, [snappedPosition])) {
        if (appState.selectedHandlePositions.isNotEmpty && !isShiftPressed) {
          appState.clearSelection();
        }
        // this flips a selection if the cargo was already clicked (and pressing shift)
        appState.selectHandle(snappedPosition);
      } else {
        appState.clearSelection();
      }
    }
  }
}
