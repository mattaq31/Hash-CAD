import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import '../../crisscross_core/common_utilities.dart';
import '../../dialogs/alert_window.dart';
import 'grid_control_contract.dart';

/// Mixin containing keyboard event handlers for GridAndCanvas
mixin GridControlKeyboardEventsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  Map<ShortcutActivator, VoidCallback> getKeyboardBindings(DesignState appState, ActionState actionState, BuildContext context) {
    return {
      // Rotation shortcut
      SingleActivator(LogicalKeyboardKey.keyR): () {
        if (getActionMode(actionState) == 'Slat-Move' && dragActive) {
          setState(() {
            moveRotationSteps += 1;
            var (_, newHoverValid) = hoverCalculator(lastPointerPosition, appState, actionState, true);
            hoverValid = newHoverValid;
          });
        } else {
          appState.rotateLayerDirection(appState.selectedLayerKey);
        }
        if (getActionMode(actionState) == 'Slat-Add' && hoverPosition != null) {
          setHoverCoordinates(appState);
        }
      },
      // flip shortcut for 60deg layers
      SingleActivator(LogicalKeyboardKey.keyF): () {
        appState.flipMultiSlatGenerator();
        if (getActionMode(actionState) == 'Slat-Add' && hoverPosition != null) {
          setHoverCoordinates(appState);
        }
      },
      // flip shortcut (T key only works in move mode now)
      SingleActivator(LogicalKeyboardKey.keyT): () {
        if (getActionMode(actionState) == 'Slat-Move' && dragActive) {
          moveFlipRequested = !moveFlipRequested;
        }
      },
      // delete shortcut (when in move mode)
      SingleActivator(LogicalKeyboardKey.delete): () {
        appState.removeSlats(appState.selectedSlats);
        appState.removeSelectedCargo(actionState.cargoAttachMode);
        appState.deleteSelectedHandles(actionState.assemblyAttachMode);
      },
      SingleActivator(LogicalKeyboardKey.backspace): () {
        appState.removeSlats(appState.selectedSlats);
        appState.removeSelectedCargo(actionState.cargoAttachMode);
        appState.deleteSelectedHandles(actionState.assemblyAttachMode);
      },
      // Navigation shortcuts
      SingleActivator(LogicalKeyboardKey.arrowUp): () {
        appState.cycleActiveLayer(true);
        setHoverCoordinates(appState);
      },
      SingleActivator(LogicalKeyboardKey.arrowDown): () {
        appState.cycleActiveLayer(false);
        setHoverCoordinates(appState);
      },
      // Action shortcuts
      SingleActivator(LogicalKeyboardKey.keyA): () {
        appState.addLayer();
      },
      SingleActivator(LogicalKeyboardKey.digit1): () {
        if (actionState.panelMode == 0) {
          actionState.updateSlatMode('Add');
        }
        else if (actionState.panelMode == 1) {
          actionState.updateAssemblyMode('Add');
        }
        else if (actionState.panelMode == 2) {
          actionState.updateCargoMode('Add');
        }
      },
      SingleActivator(LogicalKeyboardKey.digit2): () {
        if (actionState.panelMode == 0) {
          actionState.updateSlatMode('Delete');
        }
        else if (actionState.panelMode == 1) {
          actionState.updateAssemblyMode('Delete');
        }
        else if (actionState.panelMode == 2) {
          actionState.updateCargoMode('Delete');
        }
      },
      SingleActivator(LogicalKeyboardKey.digit3): () {
        if (actionState.panelMode == 0) {
          actionState.updateSlatMode('Move');
        }
        else if (actionState.panelMode == 1) {
          actionState.updateAssemblyMode('Move');
        }
        else if (actionState.panelMode == 2) {
          actionState.updateCargoMode('Move');
        }
      },

      // Undo shortcuts (platform-specific)
      SingleActivator(LogicalKeyboardKey.keyZ, control: true, includeRepeats: false): () {
        appState.undo2DAction();
      },
      SingleActivator(LogicalKeyboardKey.keyZ, meta: true, includeRepeats: false): () {
        appState.undo2DAction();
      },

      // Redo shortcuts
      SingleActivator(LogicalKeyboardKey.keyZ, control: true, shift: true, includeRepeats: false): () {
        appState.undo2DAction(redo: true);
      },
      SingleActivator(LogicalKeyboardKey.keyZ, meta: true, shift: true, includeRepeats: false): () {
        appState.undo2DAction(redo: true);
      },
      SingleActivator(LogicalKeyboardKey.keyY, control: true, includeRepeats: false): () {
        appState.undo2DAction(redo: true);
      },

      // Edit assembly handle shortcut - opens dialog when handles are selected
      SingleActivator(LogicalKeyboardKey.keyE): () {
        if (getActionMode(actionState) == 'Assembly-Move' && appState.selectedAssemblyPositions.isNotEmpty) {
          // Get the first selected handle to populate the dialog
          var firstCoord = appState.selectedAssemblyPositions.first;
          var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[firstCoord];
          if (slatID == null) return;

          var slat = appState.slats[slatID]!;
          int position = slat.slatCoordinateToPosition[firstCoord]!;
          int integerSlatSide = getSlatSideFromLayer(appState.layerMap, slat.layer, actionState.assemblyAttachMode);
          var handleDict = getHandleDict(slat, integerSlatSide);

          if (!(handleDict[position]?['category']?.toString().contains('ASSEMBLY') ?? false)) return;

          String currentValue = handleDict[position]!['value'].toString();
          HandleKey handleKey = (slatID, position, integerSlatSide);

          // Show edit dialog and apply changes
          showAssemblyHandleEditDialog(context, appState, currentValue, handleKey).then((result) {
            if (result != null) {
              appState.hammingValueValid = false;
              List<Offset> positionsToUpdate = List.from(appState.selectedAssemblyPositions);

              for (int i = 0; i < positionsToUpdate.length; i++) {
                var coord = positionsToUpdate[i];
                var updateSlatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[coord];
                if (updateSlatID == null) continue;
                var updateSlat = appState.slats[updateSlatID]!;
                int updatePos = updateSlat.slatCoordinateToPosition[coord]!;
                var updateHandleDict = getHandleDict(updateSlat, integerSlatSide);

                if (!(updateHandleDict[updatePos]?['category']?.toString().contains('ASSEMBLY') ?? false)) continue;

                String category = updateHandleDict[updatePos]!['category'].toString();
                bool isLast = (i == positionsToUpdate.length - 1);

                if (result['enforceInPlace'] == true) {
                  int currentValue = int.parse(updateHandleDict[updatePos]!['value'].toString());
                  appState.setHandleEnforcedValue((updateSlatID, updatePos, integerSlatSide), currentValue, requestStateUpdate: isLast);
                } else {
                  if (result['enforce'] == true) {
                    appState.setHandleEnforcedValue((updateSlatID, updatePos, integerSlatSide), result['value'] as int, requestStateUpdate: false);
                  }
                  appState.smartSetHandle(updateSlat, updatePos, integerSlatSide, result['value'].toString(), category, requestStateUpdate: isLast);
                }

              }
            }
          });
        }
      },
    };
  }

  KeyEventResult handleKeyEvent(FocusNode node, KeyEvent event) {
    setState(() {
      // Handle the shift key state
      if (event is KeyDownEvent) {
        isShiftPressed = event.logicalKey.keyLabel.contains('Shift');
          isCtrlPressed = event.logicalKey.keyLabel.contains('Control');
        isMetaPressed = event.logicalKey.keyLabel.contains('Meta'); // macOS meta key
      } else if (event is KeyUpEvent) {
        if (event.logicalKey.keyLabel.contains('Shift')) {
          isShiftPressed = false;
        }
        if (event.logicalKey.keyLabel.contains('Control')) {
          isCtrlPressed = false;
        }
        if (event.logicalKey.keyLabel.contains('Meta')) {
          isMetaPressed = false; // macOS meta key
        }
      }
    });
    // Return false to allow the event to continue to be processed
    return KeyEventResult.ignored;
  }
}
