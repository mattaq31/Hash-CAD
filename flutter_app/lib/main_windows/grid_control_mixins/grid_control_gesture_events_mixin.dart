import 'dart:math';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import '../../app_management/server_state.dart';
import '../../crisscross_core/common_utilities.dart';
import '../alert_window.dart';
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

  Future<void> handleTapDown(TapDownDetails details, DesignState appState, ActionState actionState, BuildContext context) async {
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
        // Check if this handle belongs to an active seed
        var seedKey = appState.isHandlePartOfActiveSeed(
          appState.selectedLayerKey,
          actionState.cargoAttachMode,
          coordConvertedPosition,
        );

        if (seedKey != null) {
          // Show dialog for seed handle deletion
          final result = await showSeedHandleDeletionDialog(context, appState.seedRoster[seedKey]!.ID);

          if (result == 'group') {
            // Delete entire seed (existing behavior)
            appState.removeSeed(appState.selectedLayerKey, actionState.cargoAttachMode, coordConvertedPosition);
          } else if (result == 'single') {
            // Dissolve seed and delete just this handle
            appState.dissolveSeed(seedKey, skipStateUpdate: true);
            appState.removeSingleSeedHandle(
              appState.occupiedGridPoints[appState.selectedLayerKey]![coordConvertedPosition]!,
              actionState.cargoAttachMode,
              coordConvertedPosition,
            );
          }
          // null (cancel) does nothing
        } else {
          // Check if this is an isolated seed handle (SEED category but not in roster)
          String slatID = appState.occupiedGridPoints[appState.selectedLayerKey]![coordConvertedPosition]!;
          var slat = appState.slats[slatID]!;
          int position = slat.slatCoordinateToPosition[coordConvertedPosition]!;
          int integerSlatSide = int.parse(
              appState.layerMap[appState.selectedLayerKey]?['${actionState.cargoAttachMode}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
          var handleDict = integerSlatSide == 5 ? slat.h5Handles : slat.h2Handles;

          if (handleDict[position]?['category'] == 'SEED') {
            // Isolated seed handle - use removeSingleSeedHandle
            appState.removeSingleSeedHandle(
              slatID,
              actionState.cargoAttachMode,
              coordConvertedPosition,
            );
          } else {
            // Regular cargo - use removeCargo
            appState.removeCargo(
              slatID,
              actionState.cargoAttachMode,
              coordConvertedPosition,
            );
          }
        }
      }
    } else if (getActionMode(actionState) == 'Assembly-Add') {
      if (!hoverValid) return;
      var coordConvertedPosition = appState.convertRealSpacetoCoordinateSpace(snappedPosition);

      // Validate: must have slat at position
      if (!appState.occupiedGridPoints[appState.selectedLayerKey]!.containsKey(coordConvertedPosition)) return;

      // Validate: no cargo at position
      String layerSideKey = '${appState.selectedLayerKey}-${actionState.assemblyAttachMode}';
      if (appState.occupiedCargoPoints[layerSideKey]?.containsKey(coordConvertedPosition) ?? false) return;

      var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]![coordConvertedPosition]!;
      var slat = appState.slats[slatID]!;
      int position = slat.slatCoordinateToPosition[coordConvertedPosition]!;
      int integerSlatSide = getSlatSideFromLayer(appState.layerMap, slat.layer, actionState.assemblyAttachMode);

      // Determine handle value - random mode generates fresh value each click
      String handleValue;
      if (actionState.assemblyRandomMode) {
        var serverState = context.read<ServerState>();
        int maxLibrarySize = int.tryParse(serverState.evoParams['unique_handle_sequences'] ?? '64') ?? 64;
        handleValue = (Random().nextInt(maxLibrarySize) + 1).toString();
      } else {
        handleValue = actionState.assemblyHandleValue;
      }

      String category = actionState.assemblyAttachMode == 'top' ? 'ASSEMBLY_HANDLE' : 'ASSEMBLY_ANTIHANDLE';

      appState.clearAssemblySelection();
      appState.smartSetHandle(slat, position, integerSlatSide, handleValue, category, requestStateUpdate: true);

      // If enforce mode is on, set the enforced value for this handle
      if (actionState.assemblyEnforceMode) {
        HandleKey key = (slatID, position, integerSlatSide);
        if (slat.phantomParent != null){
          // if phantom, need to get the original slat ID
          key = (slat.phantomParent!, position, integerSlatSide);
        }
        appState.setHandleEnforcedValue(key, int.parse(handleValue));
      }

      appState.hammingValueValid = false;

    } else if (getActionMode(actionState) == 'Assembly-Delete') {
      var coordConvertedPosition = appState.convertRealSpacetoCoordinateSpace(snappedPosition);
      var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[coordConvertedPosition];
      if (slatID == null) return;

      var slat = appState.slats[slatID]!;
      int position = slat.slatCoordinateToPosition[coordConvertedPosition]!;
      int integerSlatSide = getSlatSideFromLayer(appState.layerMap, slat.layer, actionState.assemblyAttachMode);
      var handleDict = getHandleDict(slat, integerSlatSide);

      if (handleDict[position]?['category']?.toString().contains('ASSEMBLY') ?? false) {
        appState.smartDeleteHandle(slat, position, integerSlatSide, cascadeDelete: false, requestStateUpdate: true);
        appState.hammingValueValid = false;
      }
    }
  }

  Future<void> handleTapUp(TapUpDetails details, DesignState appState, ActionState actionState, BuildContext context) async {
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
        // Check if this handle belongs to an active seed
        var seedKey = appState.isHandlePartOfActiveSeed(
          appState.selectedLayerKey,
          actionState.cargoAttachMode,
          snappedPosition,
        );

        if (seedKey != null) {
          // Show dialog for seed handle selection
          final result = await showSeedHandleSelectionDialog(context, appState.seedRoster[seedKey]!.ID);

          if (result == 'group') {
            // Select all handles in the seed group
            if (!isShiftPressed) appState.clearSelection();
            for (var coord in appState.getAllSeedHandleCoordinates(seedKey)) {
              appState.selectHandle(coord, addOnly: true);
            }
          } else if (result == 'single') {
            // Select just this handle
            if (appState.selectedHandlePositions.isNotEmpty && !isShiftPressed) {
              appState.clearSelection();
            }
            appState.selectHandle(snappedPosition);
          }
          // null (cancel) does nothing
        } else {
          // Regular cargo or isolated seed handle - select normally without popup
          if (appState.selectedHandlePositions.isNotEmpty && !isShiftPressed) {
            appState.clearSelection();
          }
          appState.selectHandle(snappedPosition);
        }
      } else {
        appState.clearSelection();
      }
    } else if (getActionMode(actionState) == 'Assembly-Move') {
      // Check if there's an assembly handle at this position
      var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[snappedPosition];
      if (slatID != null) {
        var slat = appState.slats[slatID]!;
        int position = slat.slatCoordinateToPosition[snappedPosition]!;
        int integerSlatSide = getSlatSideFromLayer(appState.layerMap, slat.layer, actionState.assemblyAttachMode);
        var handleDict = getHandleDict(slat, integerSlatSide);

        // Check if position has an assembly handle OR is a blocked handle (so it can be unblocked)
        HandleKey handleKey = (slatID, position, integerSlatSide);
        bool isAssemblyHandle = handleDict[position]?['category']?.toString().contains('ASSEMBLY') ?? false;
        bool isBlockedHandle = appState.assemblyLinkManager.handleBlocks.contains(handleKey);

        if (isAssemblyHandle || isBlockedHandle) {
          if (appState.selectedAssemblyPositions.isNotEmpty && !isShiftPressed) {
            appState.clearAssemblySelection();
          }
          appState.selectAssemblyHandle(snappedPosition);
        } else {
          appState.clearAssemblySelection();
        }
      } else {
        appState.clearAssemblySelection();
      }
    }
  }

  /// Handle right-click (secondary tap) to select handle and all linked handles
  Future<void> handleSecondaryTapUp(TapUpDetails details, DesignState appState, ActionState actionState) async {
    if (getActionMode(actionState) != 'Assembly-Move') return;

    final Offset snappedPosition = appState.convertRealSpacetoCoordinateSpace(gridSnap(details.localPosition, appState));

    // Check if there's an assembly handle at this position
    var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[snappedPosition];
    if (slatID == null) return;

    var slat = appState.slats[slatID]!;
    int position = slat.slatCoordinateToPosition[snappedPosition]!;
    int integerSlatSide = getSlatSideFromLayer(appState.layerMap, slat.layer, actionState.assemblyAttachMode);
    var handleDict = getHandleDict(slat, integerSlatSide);

    if (!(handleDict[position]?['category']?.toString().contains('ASSEMBLY') ?? false)) return;

    // Get all linked handles
    HandleKey clickedKey = (slatID, position, integerSlatSide);
    List<HandleKey> linkedHandles = appState.assemblyLinkManager.getLinkedHandles(clickedKey);

    // Clear previous selection and select all linked handles
    appState.clearAssemblySelection();

    for (var key in linkedHandles) {
      var linkedSlat = appState.slats[key.$1];
      // cannot select handles on other layers or sides (at least for now)
      if(linkedSlat!.layer != appState.selectedLayerKey || key.$3 != integerSlatSide) continue;

      Offset? coord = linkedSlat.slatPositionToCoordinate[key.$2];
      if (coord != null) {
        appState.selectAssemblyHandle(coord, addOnly: true);
      }
    }
  }
}
