import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';

/// Mixin containing helper calculation functions for GridAndCanvas
mixin GridControlHelpersMixin<T extends StatefulWidget> on State<T> {
  // Required state - to be provided by _GridAndCanvasState
  double get scale;
  Offset get offset;
  double get minScale;
  double get maxScale;
  Offset? get hoverPosition;
  List<String> get hiddenSlats;
  List<Offset> get hiddenCargo;
  Offset get slatMoveAnchor;

  // Methods from other mixins
  Map<int, Map<int, Offset>> generateSlatPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState);
  Map<int, Offset> generateCargoPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState);
  Map<int, Offset> generateSeedPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState);

  /// Function for converting a mouse zoom event into a 'scale' and 'offset' to be used when pinpointing the current position on the grid.
  /// 'zoomFactor' affects the scroll speed (higher is slower).
  (double, Offset) scrollZoomCalculator(PointerScrollEvent event, {double zoomFactor = 0.2}) {
    double newScale = scale;

    // only checks vertical scroll movement (in or out)
    // scale = global variable containing the current scale
    if (event.scrollDelta.dy > 0) {
      newScale = (scale * (1 - zoomFactor)).clamp(minScale, maxScale);
    } else if (event.scrollDelta.dy < 0) {
      newScale = (scale * (1 + zoomFactor)).clamp(minScale, maxScale);
    }

    // the localPosition can be used to focus the zoom in the direction of the pointer
    // think of it this way:
    // the 'localPosition' is the x/y coordinate of the pointer in terms of a 'world scale'
    // however, the actually offset of the current view will have changed throughout use
    // to find the new offset, first find the focus point of the current offset i.e. subtract the localPosition from the current offset
    // next, translate this focus point into the new scale system by multiplying by the new scale and dividing by the old one
    // finally, subtracting this focus point from the pointer coordinates in 'world scale' will result in the coordinates of the new
    // 'origin' or offset of the current view
    final Offset focus = (event.localPosition - offset);
    var calcOffset = event.localPosition - focus * (newScale / scale);

    return (newScale, calcOffset);
  }

  /// Function for checking if a slat can be placed at a given coordinate.
  bool checkCoordinateOccupancy(DesignState appState, ActionState actionState, List<Offset> coordinates) {
    Iterable<Offset>? occupiedPositions;
    Set<Offset> hiddenPositions = {};

    if (actionState.panelMode == 0) {
      // slat mode
      occupiedPositions = appState.occupiedGridPoints[appState.selectedLayerKey]?.keys;
      for (var slat in hiddenSlats) {
        hiddenPositions.addAll(appState.slats[slat]?.slatPositionToCoordinate.values ?? {});
      }
    } else {
      // cargo mode (or otherwise)
      String additionalOccupancy = '';
      if (appState.cargoAdditionType == 'SEED') {
        // if in seed mode, need to calculate collisions with slats too!
        int targetLayerOrder =
            appState.layerMap[appState.selectedLayerKey]!["order"] + (actionState.cargoAttachMode == 'top' ? 1 : -1);
        if (targetLayerOrder != -1 && targetLayerOrder < appState.layerMap.length) {
          additionalOccupancy =
              appState.layerMap.keys.firstWhere((key) => appState.layerMap[key]!['order'] == targetLayerOrder);
        }
      }
      if (additionalOccupancy != '') {
        occupiedPositions = {
          ...?appState.occupiedCargoPoints['${appState.selectedLayerKey}-${actionState.cargoAttachMode}']?.keys,
          ...?appState.occupiedGridPoints[additionalOccupancy]?.keys
        };
      } else {
        occupiedPositions =
            appState.occupiedCargoPoints['${appState.selectedLayerKey}-${actionState.cargoAttachMode}']?.keys;
      }
      hiddenPositions.addAll(hiddenCargo);
    }

    if (occupiedPositions == null) return false;

    for (var coord in coordinates) {
      if (occupiedPositions.contains(coord) && !hiddenPositions.contains(coord)) {
        return true;
      }
    }

    return false;
  }

  /// Function for converting a mouse hover event into a 'snapPosition' and 'hoverValid' flag to be used when pinpointing the current position on the grid.
  (Offset, bool) hoverCalculator(
      Offset eventPosition, DesignState appState, ActionState actionState, bool preSelectedPositions) {
    // the position is snapped to the nearest grid point
    // the function needs to make sure the global offset/scale
    // due to panning/zooming are taken into account
    Offset snapPosition = gridSnap(eventPosition, appState);
    // check to see if clicked position is taken by a slat already
    bool snapHoverValid = true;
    List<Offset> queryCoordinates = [];

    if (actionState.panelMode == 0) {
      // slat mode
      // TODO: there must be a faster way to get this to run properly...
      // preselectedSlats means that the slats are already selected and are being moved
      if (preSelectedPositions) {
        Offset slatOffset = appState.convertRealSpacetoCoordinateSpace(snapPosition - slatMoveAnchor);
        for (var slat in appState.selectedSlats) {
          for (var coord in appState.slats[slat]!.slatPositionToCoordinate.values) {
            queryCoordinates.add(coord + slatOffset);
          }
        }
      } else {
        Map<int, Map<int, Offset>> allSlatCoordinates = generateSlatPositions(snapPosition, false, appState);
        queryCoordinates = allSlatCoordinates.values.expand((innerMap) => innerMap.values).toList();
      }
    } else {
      // everything else
      Map<int, Offset> allCargoCoordinates;
      if (preSelectedPositions) {
        for (var coord in appState.selectedHandlePositions) {
          queryCoordinates.add(appState.convertRealSpacetoCoordinateSpace(snapPosition - slatMoveAnchor) + coord);
        }
      } else {
        if (appState.cargoAdditionType != 'SEED') {
          allCargoCoordinates = generateCargoPositions(snapPosition, false, appState);
        } else {
          allCargoCoordinates = generateSeedPositions(snapPosition, false, appState); // seed has a special occupancy grid
        }
        queryCoordinates = allCargoCoordinates.values.toList();
      }
    }

    snapHoverValid = !checkCoordinateOccupancy(appState, actionState, queryCoordinates);

    return (snapPosition, snapHoverValid);
  }

  Map<int, Offset> getCargoHoverPoints(DesignState appState, ActionState actionState) {
    if (hoverPosition != null && getActionMode(actionState) == 'Cargo-Add') {
      if (appState.cargoAdditionType != 'SEED') {
        return generateCargoPositions(hoverPosition!, true, appState);
      } else {
        return generateSeedPositions(hoverPosition!, true, appState);
      }
    } else if (hoverPosition != null && getActionMode(actionState) == 'Cargo-Move') {
      return appState.selectedHandlePositions.asMap();
    } else {
      return {};
    }
  }

  /// logic for changing the slat cursor type based on the current action mode
  SystemMouseCursor getCursorForSlatMode(String actionMode) {
    if (actionMode.contains("Add")) {
      return SystemMouseCursors.precise;
    } else if (actionMode.contains("Delete")) {
      return SystemMouseCursors.none;
    } else if (actionMode.contains("Move")) {
      return SystemMouseCursors.grab;
    } else {
      return SystemMouseCursors.basic;
    }
  }

  Offset gridSnap(Offset inputPosition, DesignState designState) {
    if (designState.gridMode == '90') {
      return Offset(
        (((inputPosition.dx - offset.dx) / scale) / designState.gridSize).round() * designState.gridSize,
        (((inputPosition.dy - offset.dy) / scale) / designState.gridSize).round() * designState.gridSize,
      );
    } else if (designState.gridMode == '60') {
      // in the 60deg system, checking the closest y and closest x coordinate independently will not work.  Will need to check two coordinates closest to the input position in one dimension through a euclidean distance check.
      double inX = (inputPosition.dx - offset.dx) / scale;
      double inY = (inputPosition.dy - offset.dy) / scale;

      // Collect candidate rows
      int baseRow = (inY / designState.y60Jump).floor();
      List<Offset> candidates = [];

      // apply same offset snapping logic as in the normal grid
      for (int row = baseRow; row <= baseRow + 1; row++) {
        double snappedY = row * designState.y60Jump;
        double xOffset = row.isOdd ? designState.x60Jump : 0;

        int col = ((inX - xOffset) / (2 * designState.x60Jump)).round();
        double snappedX = xOffset + col * 2 * designState.x60Jump;

        candidates.add(Offset(snappedX, snappedY));
      }

      // Choose nearest candidate by computing Euclidean distance to the input coordinate
      Offset best = candidates.first;
      double bestDist = (inX - best.dx) * (inX - best.dx) + (inY - best.dy) * (inY - best.dy);

      for (var cand in candidates.skip(1)) {
        double dist = (inX - cand.dx) * (inX - cand.dx) + (inY - cand.dy) * (inY - cand.dy);
        if (dist < bestDist) {
          best = cand;
          bestDist = dist;
        }
      }

      return best;
    } else {
      throw Exception('Grid system not supported');
    }
  }

  String getActionMode(ActionState actionState) {
    if (actionState.panelMode == 0) {
      if (actionState.slatMode == "Add") {
        return "Slat-Add";
      } else if (actionState.slatMode == "Delete") {
        return "Slat-Delete";
      } else if (actionState.slatMode == "Move") {
        return "Slat-Move";
      } else {
        return "Neutral";
      }
    } else if (actionState.panelMode == 2) {
      if (actionState.cargoMode == 'Add') {
        return "Cargo-Add";
      } else if (actionState.cargoMode == 'Delete') {
        return "Cargo-Delete";
      } else if (actionState.cargoMode == 'Move') {
        return "Cargo-Move";
      } else {
        return "Neutral";
      }
    } else {
      return "Neutral";
    }
  }

  String getStatusIndicatorText(ActionState actionState, DesignState appState) {
    String actionMode = getActionMode(actionState);
    if (actionMode == 'Slat-Move') {
      return 'Slats Selected: ${appState.selectedSlats.length}';
    } else if (actionMode == 'Cargo-Move') {
      return 'Handles Selected: ${appState.selectedHandlePositions.length}';
    } else {
      return "";
    }
  }
}
