import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import '../../crisscross_core/handle_utilities.dart';
import 'grid_control_contract.dart';

/// Mixin containing helper calculation functions for GridAndCanvas
mixin GridControlHelpersMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  /// Function for converting a mouse zoom event into a 'scale' and 'offset' to be used when pinpointing the current position on the grid.
  /// 'zoomFactor' affects the scroll speed (higher is slower).
  @override
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

  /// Function for checking if a slat or cargo can be placed at a given coordinate.
  /// Handles three seed collision scenarios:
  /// 1. Adding a new seed (cargoAdditionType == 'SEED')
  /// 2. Moving existing seed handles (Cargo-Move with SEED category handles)
  /// 3. Moving slats that have seed handles (Slat-Move with SEED category handles)
  @override
  bool checkCoordinateOccupancy(DesignState appState, ActionState actionState, List<Offset> coordinates) {
    Iterable<Offset>? occupiedPositions;
    Set<Offset> hiddenPositions = {};

    // For seed layer collision: we need to check ONLY seed handle positions against adjacent layer
    // (not all slat positions, since slats on adjacent layers intentionally cross each other)
    Map<Offset, Set<Offset>> seedLayerChecks = {}; // newSeedCoord -> adjacentLayerOccupancy
    Set<Offset> hiddenSeedLayerPositions = {}; // Old seed positions being moved (to exclude)

    if (actionState.panelMode == 0) {
      // slat mode
      occupiedPositions = appState.occupiedGridPoints[appState.selectedLayerKey]?.keys;

      for (var slatId in hiddenSlats) {
        var slat = appState.slats[slatId];
        if (slat == null) continue;
        hiddenPositions.addAll(slat.slatPositionToCoordinate.values);

        // Check if this slat has SEED handles - need to check adjacent layer collisions
        for (var handleType in [5, 2]) {
          var handleDict = getHandleDict(slat, handleType);

          // Find seed handle positions and their target layer
          List<int> seedPositions = [];
          for (var entry in handleDict.entries) {
            if (entry.value['category'] == 'SEED') {
              seedPositions.add(entry.key);
              var oldCoord = slat.slatPositionToCoordinate[entry.key];
              if (oldCoord != null) hiddenSeedLayerPositions.add(oldCoord);
            }
          }

          if (seedPositions.isNotEmpty) {
            int topHelixSide = getSlatSideFromLayer(appState.layerMap, slat.layer, 'top');
            var occupancyID = topHelixSide == handleType ? 'top' : 'bottom';
            int targetLayerOrder = getAdjacentLayerOrder(appState.layerMap, slat.layer, occupancyID);

            if (appState.layerNumberValid(targetLayerOrder)) {
              String? targetLayer = appState.getLayerByOrder(targetLayerOrder);
              if (targetLayer != null) {
                Set<Offset> adjacentOccupancy = appState.occupiedGridPoints[targetLayer]?.keys.toSet() ?? {};

                // Store old seed positions mapped to adjacent layer occupancy
                // We'll match these to new positions during the collision check phase
                for (var seedPos in seedPositions) {
                  seedLayerChecks[slat.slatPositionToCoordinate[seedPos]!] = adjacentOccupancy;
                }
              }
            }
          }
        }
      }
    } else {
      String layerSideKey = generateLayerSideKey(appState.selectedLayerKey, actionState.cargoAttachMode);
      appState.occupiedCargoPoints.putIfAbsent(layerSideKey, () => {});
      // cargo mode
      occupiedPositions = appState.occupiedCargoPoints[layerSideKey]?.keys;
      hiddenPositions.addAll(hiddenCargo);

      Set<Offset>? seedLayerOccupancy;

      // Case 1: Adding a new seed - all coordinates are seed positions
      if (appState.cargoAdditionType == 'SEED' && getActionMode(actionState) == 'Cargo-Add') {
        int targetLayerOrder = getAdjacentLayerOrder(appState.layerMap, appState.selectedLayerKey, actionState.cargoAttachMode);
        if (appState.layerNumberValid(targetLayerOrder)) {
          String? targetLayer = appState.getLayerByOrder(targetLayerOrder);
          if (targetLayer != null) {
            seedLayerOccupancy = appState.occupiedGridPoints[targetLayer]?.keys.toSet();
          }
        }
        // For seed addition, ALL coordinates need to be checked against adjacent layer
        if (seedLayerOccupancy != null) {
          for (var coord in coordinates) {
            seedLayerChecks[coord] = seedLayerOccupancy;
          }
        }
      }

      // Case 2: Moving existing seed handles
      if (getActionMode(actionState) == 'Cargo-Move' && hiddenCargo.isNotEmpty) {
        Set<Offset>? adjacentOccupancy;

        for (var coord in hiddenCargo) {
          var slatId = appState.occupiedGridPoints[appState.selectedLayerKey]?[coord];
          if (slatId == null) continue;
          var slat = appState.slats[slatId];
          if (slat == null) continue;
          int? position = slat.slatCoordinateToPosition[coord];
          if (position == null) continue;
          int integerSlatSide = getSlatSideFromLayer(appState.layerMap, slat.layer, actionState.cargoAttachMode);
          var handleDict = getHandleDict(slat, integerSlatSide);
          if (handleDict[position]?['category'] == 'SEED') {
            hiddenSeedLayerPositions.add(coord);

            // Get adjacent layer occupancy (cache it since it's the same for all)
            if (adjacentOccupancy == null) {
              int targetLayerOrder = getAdjacentLayerOrder(appState.layerMap, appState.selectedLayerKey, actionState.cargoAttachMode);
              if (appState.layerNumberValid(targetLayerOrder)) {
                String? targetLayer = appState.getLayerByOrder(targetLayerOrder);
                if (targetLayer != null) {
                  adjacentOccupancy = appState.occupiedGridPoints[targetLayer]?.keys.toSet() ?? {};
                }
              }
            }

            if (adjacentOccupancy != null) {
              seedLayerChecks[coord] = adjacentOccupancy;
            }
          }
        }
      }
    }

    if (occupiedPositions == null && seedLayerChecks.isEmpty) return false;

    // Check 1: Regular same-layer collision
    for (var coord in coordinates) {
      if (occupiedPositions != null && occupiedPositions.contains(coord) && !hiddenPositions.contains(coord)) {
        return true;
      }
    }

    // Check 2: Seed-layer collision (only for coordinates that correspond to seed handles)
    if (seedLayerChecks.isNotEmpty) {
      // For slat move: we need to map old seed positions to new positions
      // For cargo move/add: coordinates ARE the new positions directly
      if (actionState.panelMode == 0 && hiddenSlats.isNotEmpty) {
        // Match old positions to new positions in coordinates list
        // coordinates contains new positions for ALL selected slats in order
        int coordIndex = 0;
        for (var slatId in hiddenSlats) {
          var slat = appState.slats[slatId];
          if (slat == null) continue;
          var slatOldCoords = slat.slatPositionToCoordinate;
          for (var entry in slatOldCoords.entries) {
            if (coordIndex < coordinates.length) {
              Offset oldCoord = entry.value;
              Offset newCoord = coordinates[coordIndex];

              // Check if this position had a seed handle
              if (seedLayerChecks.containsKey(oldCoord)) {
                var adjacentOccupancy = seedLayerChecks[oldCoord]!;
                // Check if NEW position collides with adjacent layer
                if (adjacentOccupancy.contains(newCoord) && !hiddenSeedLayerPositions.contains(newCoord)) {
                  return true;
                }
              }
              coordIndex++;
            }
          }
        }
      } else {
        // Cargo mode: coordinates are new positions, hiddenCargo are old positions
        // Calculate offset from first hidden cargo to first coordinate
        if (hiddenCargo.isNotEmpty && coordinates.isNotEmpty) {
          for (int i = 0; i < coordinates.length && i < hiddenCargo.length; i++) {
            Offset oldCoord = hiddenCargo[i];
            Offset newCoord = coordinates[i];

            if (seedLayerChecks.containsKey(oldCoord)) {
              var adjacentOccupancy = seedLayerChecks[oldCoord]!;
              if (adjacentOccupancy.contains(newCoord) && !hiddenSeedLayerPositions.contains(newCoord)) {
                return true;
              }
            }
          }
        } else if (getActionMode(actionState) == 'Cargo-Add') {
          // For seed addition, all coordinates need checking
          for (var coord in coordinates) {
            // seedLayerChecks has all coordinates mapped to same adjacentOccupancy
            if (seedLayerChecks.containsKey(coord)) {
              var adjacentOccupancy = seedLayerChecks[coord]!;
              if (adjacentOccupancy.contains(coord)) {
                return true;
              }
            }
          }
        }
      }
    }

    return false;
  }

  /// Function for converting a mouse hover event into a 'snapPosition' and 'hoverValid' flag to be used when pinpointing the current position on the grid.
  @override
  (Offset, bool) hoverCalculator(Offset eventPosition, DesignState appState, ActionState actionState, bool preSelectedPositions) {
    // the position is snapped to the nearest grid point
    // the function needs to make sure the global offset/scale
    // due to panning/zooming are taken into account
    Offset snapPosition = gridSnap(eventPosition, appState);
    // check to see if clicked position is taken by a slat already
    bool snapHoverValid = true;
    List<Offset> queryCoordinates = [];

    if (actionState.panelMode == 0) {
      // slat mode
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

    // For cargo move, also check that all destination coordinates have slats to bind to
    if (snapHoverValid && actionState.panelMode != 0 && preSelectedPositions) {
      var slatPositions = appState.occupiedGridPoints[appState.selectedLayerKey]?.keys;
      if (slatPositions != null) {
        for (var coord in queryCoordinates) {
          if (!slatPositions.contains(coord)) {
            snapHoverValid = false;
            break;
          }
        }
      } else {
        snapHoverValid = false;
      }
    }

    return (snapPosition, snapHoverValid);
  }

  @override
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
  @override
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

  @override
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

  @override
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

  @override
  List<String> getStatusIndicatorText(ActionState actionState, DesignState appState) {
    String actionMode = getActionMode(actionState);
    if (actionMode == 'Slat-Move') {
      return ['Slats Selected: ${appState.selectedSlats.length}'];
    } else if (actionMode == 'Cargo-Move') {
      return ['Handles Selected: ${appState.selectedHandlePositions.length}',
      'Cargo Site: ${actionState.cargoAttachMode.toUpperCase()}'];
    } else {
      return [];
    }
  }
}
