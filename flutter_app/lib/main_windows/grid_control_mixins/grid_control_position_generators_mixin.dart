import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:math' as math;

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import '../../2d_painters/helper_functions.dart';
import 'grid_control_contract.dart';

/// Mixin containing position generation functions for GridAndCanvas
mixin GridControlPositionGeneratorsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  @override
  Map<int, Map<int, Offset>> generateSlatPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState) {
    // slats added to a persistent list here
    Map<int, Map<int, Offset>> incomingSlats = {};

    int direction = appState.layerMap[appState.selectedLayerKey]!["direction"];

    Offset cursorCoordinate, slatMultiJump, slatInnerJump;

    var multiGenerator = appState.multiSlatGenerators;
    var directionGenerator = appState.slatDirectionGenerators;

    if (realSpaceFormat) {
      cursorCoordinate = cursorPoint;
      if (appState.gridMode == '60') {
        slatMultiJump = multiplyOffsets(multiGenerator[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
        slatInnerJump = multiplyOffsets(directionGenerator[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
      } else {
        slatMultiJump = multiGenerator[(appState.gridMode, direction)]! * appState.gridSize;
        slatInnerJump = directionGenerator[(appState.gridMode, direction)]! * appState.gridSize;
      }
    } else {
      cursorCoordinate = appState.convertRealSpacetoCoordinateSpace(cursorPoint);

      slatMultiJump = multiGenerator[(appState.gridMode, direction)]!;
      slatInnerJump = directionGenerator[(appState.gridMode, direction)]!;
    }

    int shearOffset = 0;
    double dbSign = 1;
    if (appState.slatAdditionType != 'tube') {
      if (appState.slatAdditionType == 'DB-R-60' || appState.slatAdditionType == 'DB-R-120' || appState.slatAdditionType == 'DB-R') {
        dbSign = -1;
      }

      // for DB slats in 60degree mode, slats can have a different 'shear' value too, which we refer to as '60' and '120' types (referring to the inner angle of the first kink)
      if (appState.slatAdditionType == 'DB-L-120') {
        shearOffset = 1;
      } else if (appState.slatAdditionType == 'DB-R-60') {
        shearOffset = -1;
      }
    }

    for (int j = 0; j < appState.slatAddCount; j++) {
      incomingSlats[j] = {};
      for (int i = 0; i < 32; i++) {
        if (appState.slatAdditionType == 'tube') {
          incomingSlats[j]?[i + 1] = cursorCoordinate + (slatMultiJump * j.toDouble()) + (slatInnerJump * i.toDouble());
        } else {
          // double barrel slat generation
          if (i < 16) {
            incomingSlats[j]?[i + 1] = cursorCoordinate + (slatMultiJump * j.toDouble() * 2 * dbSign) + (slatInnerJump * i.toDouble());
          } else {
            incomingSlats[j]?[i + 1] = cursorCoordinate + (slatMultiJump * (1 + (j.toDouble() * 2)) * dbSign) + (slatInnerJump * (31 + shearOffset - i).toDouble());
          }
        }
      }
    }
    return incomingSlats;
  }

  @override
  Map<int, Offset> generateCargoPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState) {
    // cargo added to a persistent list here
    Map<int, Offset> incomingCargo = {};
    int direction = appState.layerMap[appState.selectedLayerKey]!["direction"];
    Offset cursorCoordinate, multiJump;
    if (realSpaceFormat) {
      cursorCoordinate = cursorPoint;
      if (appState.gridMode == '60') {
        multiJump = multiplyOffsets(appState.slatDirectionGenerators[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
      } else {
        multiJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]! * appState.gridSize;
      }
    } else {
      cursorCoordinate = appState.convertRealSpacetoCoordinateSpace(cursorPoint);
      multiJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]!;
    }

    for (int j = 0; j < appState.cargoAddCount; j++) {
      incomingCargo[j] = cursorCoordinate + (multiJump * j.toDouble());
    }
    return incomingCargo;
  }

  @override
  Map<int, Offset> generateSeedPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState) {
    // seed handles added to a persistent list here
    Map<int, Offset> incomingHandles = {};
    int direction = appState.layerMap[appState.selectedLayerKey]!["direction"];

    Offset cursorCoordinate, heightMultiJump, widthMultiJump;
    if (realSpaceFormat) {
      cursorCoordinate = cursorPoint;
      if (appState.gridMode == '60') {
        heightMultiJump = multiplyOffsets(appState.slatDirectionGenerators[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
        widthMultiJump = multiplyOffsets(appState.multiSlatGenerators[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
      } else {
        heightMultiJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]! * appState.gridSize;
        widthMultiJump = appState.multiSlatGenerators[(appState.gridMode, direction)]! * appState.gridSize;
      }
    } else {
      cursorCoordinate = appState.convertRealSpacetoCoordinateSpace(cursorPoint);
      heightMultiJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]!;
      widthMultiJump = appState.multiSlatGenerators[(appState.gridMode, direction)]!;
    }

    for (int i = 0; i < appState.seedOccupancyDimensions['width']!; i++) {
      for (int j = 0; j < appState.seedOccupancyDimensions['height']!; j++) {
        incomingHandles[1 + (i * appState.seedOccupancyDimensions['height']! + j)] =
            cursorCoordinate + (widthMultiJump * i.toDouble()) + (heightMultiJump * j.toDouble());
      }
    }
    return incomingHandles;
  }

  /// Centers the 2D view on all slats, accounting for all UI elements
  @override
  void centerOnSlats() {
    var appState = context.read<DesignState>();
    var actionState = context.read<ActionState>();

    // Get screen size
    Size screenSize = MediaQuery.of(context).size;

    // Calculate actual canvas dimensions
    double canvasWidth = screenSize.width;
    double canvasHeight = screenSize.height;

    // Account for 3D viewer split
    if (actionState.threeJSViewerActive) {
      canvasWidth *= actionState.splitScreenDividerWidth; // 2D view gets this fraction
      canvasWidth -= 10.0; // Subtract divider width
    }

    // Subtract navigation rail width (always present)
    canvasWidth -= 72.0;

    // Subtract sidebar width when expanded
    if (!actionState.isSideBarCollapsed) {
      canvasWidth -= 330.0;
    }

    // Account for top and bottom UI elements
    canvasHeight -= 80.0; // Top padding (floating title)
    canvasHeight -= 100.0; // Bottom padding (toggle panel)

    // Ensure minimum canvas size
    Size canvasSize = Size(canvasWidth.clamp(100, double.infinity), canvasHeight.clamp(100, double.infinity));

    // Collect all slat coordinates
    List<Offset> allSlatCoordinates = [];
    for (String layerKey in appState.occupiedGridPoints.keys) {
      allSlatCoordinates.addAll(appState.occupiedGridPoints[layerKey]!.keys);
    }

    if (allSlatCoordinates.isEmpty) return;

    // Convert to real space and calculate bounding box
    List<Offset> realSpaceCoordinates =
        allSlatCoordinates.map((coord) => appState.convertCoordinateSpacetoRealSpace(coord)).toList();

    double minX = realSpaceCoordinates.first.dx;
    double maxX = realSpaceCoordinates.first.dx;
    double minY = realSpaceCoordinates.first.dy;
    double maxY = realSpaceCoordinates.first.dy;

    for (Offset coord in realSpaceCoordinates) {
      minX = math.min(minX, coord.dx);
      maxX = math.max(maxX, coord.dx);
      minY = math.min(minY, coord.dy);
      maxY = math.max(maxY, coord.dy);
    }

    // Calculate center and dimensions with padding
    Offset slatCenter = Offset((minX + maxX) / 2, (minY + maxY) / 2);
    double boundingWidth = (maxX - minX) * 1.1; // 10% padding
    double boundingHeight = (maxY - minY) * 1.1;

    // Calculate scale to fit
    double scaleX = canvasSize.width / boundingWidth;
    double scaleY = canvasSize.height / boundingHeight;
    double newScale = math.min(scaleX, scaleY).clamp(minScale, maxScale);

    // Calculate canvas center accounting for UI offsets
    double canvasCenterX = canvasSize.width / 2;
    double canvasCenterY = canvasSize.height / 2;

    // Add navigation rail offset
    canvasCenterX += 72.0;

    // Add sidebar offset when expanded
    if (!actionState.isSideBarCollapsed) {
      canvasCenterX += 330.0;
    }

    // Add top padding offset
    canvasCenterY += 80.0;

    Offset canvasCenter = Offset(canvasCenterX, canvasCenterY);
    Offset newOffset = canvasCenter - (slatCenter * newScale);

    // Apply the new scale and offset
    setState(() {
      scale = newScale;
      offset = newOffset;
    });
  }
}
