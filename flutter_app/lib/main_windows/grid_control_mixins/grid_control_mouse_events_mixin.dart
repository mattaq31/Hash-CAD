import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import '../alert_window.dart';
import 'grid_control_contract.dart';

/// Mixin containing mouse/pointer event handlers for GridAndCanvas
mixin GridControlMouseEventsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
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

  Future<void> handlePointerUp(PointerUpEvent event, DesignState appState, ActionState actionState, BuildContext context) async {
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
        // Collect all handles in the drag box
        List<Offset> handlesInRect = [];
        appState.occupiedCargoPoints.putIfAbsent('${appState.selectedLayerKey}-${actionState.cargoAttachMode}', () => {});
        for (var entry in appState.occupiedCargoPoints['${appState.selectedLayerKey}-${actionState.cargoAttachMode}']!.keys) {
          final coord = appState.convertCoordinateSpacetoRealSpace(entry);
          if (rect.contains(coord)) {
            handlesInRect.add(entry);
          }
        }

        // Group handles by active seed membership
        Map<(String, String, Offset), List<Offset>> seedHandles = {}; // seedKey -> handles in rect
        List<Offset> nonSeedHandles = [];

        for (var handleCoord in handlesInRect) {
          var seedKey = appState.isHandlePartOfActiveSeed(
            appState.selectedLayerKey,
            actionState.cargoAttachMode,
            handleCoord,
          );
          if (seedKey != null) {
            seedHandles.putIfAbsent(seedKey, () => []);
            seedHandles[seedKey]!.add(handleCoord);
          } else {
            nonSeedHandles.add(handleCoord);
          }
        }

        // Select all non-seed handles (regular cargo + isolated seed handles)
        for (var coord in nonSeedHandles) {
          appState.selectHandle(coord, addOnly: true);
        }

        // For each active seed with handles in the rect, show dialog
        for (var seedEntry in seedHandles.entries) {
          var seedKey = seedEntry.key;
          var handlesInRectForSeed = seedEntry.value;
          String seedID = appState.seedRoster[seedKey]!.ID;

          final result = await showSeedHandleSelectionDialog(context, seedID);

          if (result == 'group') {
            // Select all handles of this seed
            for (var coord in appState.getAllSeedHandleCoordinates(seedKey)) {
              appState.selectHandle(coord, addOnly: true);
            }
          } else if (result == 'single') {
            // Select only the handles that were in the rect
            for (var coord in handlesInRectForSeed) {
              appState.selectHandle(coord, addOnly: true);
            }
          }
          // null (cancel) does nothing for this seed
        }
      }

      setState(() {
        dragBoxActive = false;
        dragBoxStart = null;
        dragBoxEnd = null;
        // Sync modifier key states with actual keyboard state (focus may have shifted to dialog)
        final keysPressed = HardwareKeyboard.instance.logicalKeysPressed;
        isCtrlPressed = keysPressed.any((key) => key == LogicalKeyboardKey.controlLeft || key == LogicalKeyboardKey.controlRight);
        isMetaPressed = keysPressed.any((key) => key == LogicalKeyboardKey.metaLeft || key == LogicalKeyboardKey.metaRight);
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
            coordinateTransferMap[appState.selectedHandlePositions[i]] = appState.selectedHandlePositions[i] + convCoordHoverPosition - convCoordAnchor;
          }
          appState.moveCargo(coordinateTransferMap, appState.selectedLayerKey, actionState.cargoAttachMode);
          appState.clearSelection();
          for (var newCoord in coordinateTransferMap.values) {
            appState.selectHandle(newCoord, addOnly: true);
          }
        }
        dragActive = false;
        hiddenCargo = [];
        hoverPosition = null; // Hide the hovering slat when cursor leaves the grid area
        slatMoveAnchor = Offset.zero;
      });
    }
  }
}
