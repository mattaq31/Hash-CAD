import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';

/// Mixin containing mouse/pointer event handlers for GridAndCanvas
mixin GridControlMouseEventsMixin<T extends StatefulWidget> on State<T> {
  // Required state - to be provided by _GridAndCanvasState
  double get scale;
  set scale(double value);
  Offset get offset;
  set offset(Offset value);
  Offset? get hoverPosition;
  set hoverPosition(Offset? value);
  bool get hoverValid;
  set hoverValid(bool value);
  bool get dragActive;
  set dragActive(bool value);
  Offset get slatMoveAnchor;
  set slatMoveAnchor(Offset value);
  List<String> get hiddenSlats;
  set hiddenSlats(List<String> value);
  List<Offset> get hiddenCargo;
  set hiddenCargo(List<Offset> value);
  bool get moveFlipRequested;
  set moveFlipRequested(bool value);
  bool get isCtrlPressed;
  bool get isMetaPressed;
  bool get dragBoxActive;
  set dragBoxActive(bool value);
  Offset? get dragBoxStart;
  set dragBoxStart(Offset? value);
  Offset? get dragBoxEnd;
  set dragBoxEnd(Offset? value);

  // Methods from other mixins
  String getActionMode(ActionState actionState);
  (double, Offset) scrollZoomCalculator(PointerScrollEvent event, {double zoomFactor});
  Offset gridSnap(Offset inputPosition, DesignState designState);
  bool checkCoordinateOccupancy(DesignState appState, ActionState actionState, List<Offset> coordinates);
  (Offset, bool) hoverCalculator(Offset eventPosition, DesignState appState, ActionState actionState, bool preSelectedPositions);

  void handlePointerSignal(PointerSignalEvent event) {
    if (event is PointerScrollEvent && !dragBoxActive) {
      setState(() {
        var (calcScale, calcOffset) = scrollZoomCalculator(event);
        scale = calcScale;
        offset = calcOffset;
      });
    }
  }

  void handlePointerDown(PointerDownEvent event, DesignState appState, ActionState actionState) {
    if (getActionMode(actionState).contains('Move')) {
      // Start drag-box selection
      if (isCtrlPressed || isMetaPressed) {
        // ctrl or meta key pressed
        setState(() {
          dragBoxActive = true;
          dragBoxStart = event.position;
          dragBoxEnd = event.position;
        });
      } else {
        // starts drag mode (first need to detect if a slat or handle is under the pointer first)
        final Offset snappedPosition = gridSnap(event.position, appState);
        if (getActionMode(actionState) == 'Slat-Move') {
          // TODO: write a 'quick' check format for the checkCoordinateOccupancy function - also need to check all coordinates of a seed too if moving that
          if (checkCoordinateOccupancy(appState, actionState, [appState.convertRealSpacetoCoordinateSpace(snappedPosition)])) {
            dragActive = true; // drag mode is signalled here - panning is now disabled
            slatMoveAnchor = snappedPosition; // the slats to be moved are anchored to the cursor
          }
        } else {
          if (appState.occupiedCargoPoints['${appState.selectedLayerKey}-${actionState.cargoAttachMode}']!.keys
              .contains(appState.convertRealSpacetoCoordinateSpace(snappedPosition))) {
            dragActive = true;
            slatMoveAnchor = snappedPosition;
          }
        }
      }
    }
  }

  void handlePointerMove(PointerMoveEvent event, DesignState appState, ActionState actionState) {
    if (dragBoxActive) {
      // Update drag-box
      setState(() {
        dragBoxEnd = event.position;
      });
    } else if (getActionMode(actionState) == 'Slat-Move' && dragActive) {
      // when drag mode is activated, the slat will again follow the cursor (similar to the mouse hover mode)
      setState(() {
        if (hiddenSlats.isEmpty) {
          for (var slat in appState.selectedSlats) {
            hiddenSlats.add(slat);
          }
        }
        var (localHoverPosition, localHoverValid) = hoverCalculator(event.position, appState, actionState, true);
        hoverPosition = localHoverPosition;
        hoverValid = localHoverValid;
      });
    } else if (getActionMode(actionState) == 'Cargo-Move' && dragActive) {
      // when drag mode is activated, the cargo will again follow the cursor (similar to the mouse hover mode)
      setState(() {
        if (hiddenCargo.isEmpty) {
          for (var coordinate in appState.selectedHandlePositions) {
            hiddenCargo.add(coordinate);
          }
        }
        var (localHoverPosition, localHoverValid) = hoverCalculator(event.position, appState, actionState, true);
        hoverPosition = localHoverPosition;
        hoverValid = localHoverValid;
      });
    }
  }

  void handlePointerUp(PointerUpEvent event, DesignState appState, ActionState actionState) {
    // drag is always cancelled when the pointer is let go
    if (dragBoxActive) {
      // Finish drag-box selection
      final rect = Rect.fromPoints((dragBoxStart! - offset) / scale, (dragBoxEnd! - offset) / scale);

      if (getActionMode(actionState) == 'Slat-Move') {
        final selected = <String>{};
        for (var entry in appState.slats.entries) {
          if (entry.value.layer != appState.selectedLayerKey) {
            continue; // only select slats from the active layer
          }
          final slat = entry.value;
          final coords = slat.slatPositionToCoordinate.values.map((coord) => appState.convertCoordinateSpacetoRealSpace(coord));
          // If any part of slat falls inside the rect → select it
          if (coords.any((pt) => rect.contains(pt))) {
            selected.add(entry.key);
          }
        }
        // add all selected slats
        for (var ID in selected) {
          appState.selectSlat(ID, addOnly: true);
        }
      } else {
        for (var entry in appState.occupiedCargoPoints['${appState.selectedLayerKey}-${actionState.cargoAttachMode}']!.keys) {
          final coord = appState.convertCoordinateSpacetoRealSpace(entry);
          if (rect.contains(coord)) {
            appState.selectHandle(entry, addOnly: true);
          }
        }
      }

      setState(() {
        dragBoxActive = false;
        dragBoxStart = null;
        dragBoxEnd = null;
      });
    } else if (getActionMode(actionState) == 'Slat-Move') {
      setState(() {
        if (hoverValid && dragActive && hoverPosition != null) {
          // finalizes slat move and applies flips if requested
          var convCoordHoverPosition = appState.convertRealSpacetoCoordinateSpace(hoverPosition!);
          var convCoordAnchor = appState.convertRealSpacetoCoordinateSpace(slatMoveAnchor);
          List<Map<int, Offset>> transformedCoordinates = [];
          for (var slat in appState.selectedSlats) {
            transformedCoordinates.add(appState.slats[slat]!.slatPositionToCoordinate
                .map((key, value) => MapEntry(key, value + convCoordHoverPosition - convCoordAnchor)));
          }
          appState.updateMultiSlatPosition(appState.selectedSlats, transformedCoordinates, requestFlip: moveFlipRequested);
        }
        dragActive = false;
        hiddenSlats = [];
        hoverPosition = null; // Hide the hovering slat when cursor leaves the grid area
        slatMoveAnchor = Offset.zero;
        moveFlipRequested = false; // reset the flip request
      });
    } else if (getActionMode(actionState) == 'Cargo-Move') {
      setState(() {
        if (hoverValid && dragActive && hoverPosition != null) {
          // finalizes slat move and applies flips if requested
          var convCoordHoverPosition = appState.convertRealSpacetoCoordinateSpace(hoverPosition!);
          var convCoordAnchor = appState.convertRealSpacetoCoordinateSpace(slatMoveAnchor);
          Map<Offset, Offset> coordinateTransferMap = {};
          for (int i = 0; i < appState.selectedHandlePositions.length; i++) {
            coordinateTransferMap[appState.selectedHandlePositions[i]] =
                appState.selectedHandlePositions[i] + convCoordHoverPosition - convCoordAnchor;
          }
          appState.moveCargo(coordinateTransferMap, appState.selectedLayerKey, actionState.cargoAttachMode);
        }
        dragActive = false;
        hiddenCargo = [];
        hoverPosition = null; // Hide the hovering slat when cursor leaves the grid area
        slatMoveAnchor = Offset.zero;
      });
    }
  }
}
