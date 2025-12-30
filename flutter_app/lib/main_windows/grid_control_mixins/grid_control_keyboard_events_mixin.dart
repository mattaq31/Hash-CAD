import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';

/// Mixin containing keyboard event handlers for GridAndCanvas
mixin GridControlKeyboardEventsMixin<T extends StatefulWidget> on State<T> {
  // Required state - to be provided by _GridAndCanvasState
  Offset? get hoverPosition;
  bool get dragActive;
  bool get moveFlipRequested;
  set moveFlipRequested(bool value);
  bool get isShiftPressed;
  set isShiftPressed(bool value);
  bool get isCtrlPressed;
  set isCtrlPressed(bool value);
  bool get isMetaPressed;
  set isMetaPressed(bool value);

  // Methods from other mixins
  String getActionMode(ActionState actionState);
  void setHoverCoordinates(DesignState appState);

  Map<ShortcutActivator, VoidCallback> getKeyboardBindings(DesignState appState, ActionState actionState) {
    return {
      // Rotation shortcut
      SingleActivator(LogicalKeyboardKey.keyR): () {
        if (getActionMode(actionState) == 'Slat-Move' && dragActive) {
          // moveRotationStepsRequested += 1;
          // TODO: reinstate this system when confirmed
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
      // flip shortcut for 60deg layers
      SingleActivator(LogicalKeyboardKey.keyT): () {
        if (getActionMode(actionState) == 'Slat-Move' && dragActive) {
          moveFlipRequested = !moveFlipRequested;
        } else {
          appState.flipSlatAddDirection();
        }
        if (getActionMode(actionState) == 'Slat-Add' && hoverPosition != null) {
          setHoverCoordinates(appState);
        }
      },
      // delete shortcut (when in move mode)
      SingleActivator(LogicalKeyboardKey.delete): () {
        appState.removeSlats(appState.selectedSlats);
      },
      SingleActivator(LogicalKeyboardKey.backspace): () {
        appState.removeSlats(appState.selectedSlats);
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
        } else if (actionState.panelMode == 2) {
          actionState.updateCargoMode('Add');
        }
      },
      SingleActivator(LogicalKeyboardKey.digit2): () {
        if (actionState.panelMode == 0) {
          actionState.updateSlatMode('Delete');
        } else if (actionState.panelMode == 2) {
          actionState.updateCargoMode('Delete');
        }
      },
      SingleActivator(LogicalKeyboardKey.digit3): () {
        if (actionState.panelMode == 0) {
          actionState.updateSlatMode('Move');
        } else if (actionState.panelMode == 2) {
          actionState.updateCargoMode('Move');
        }
      },

      // Undo shortcuts (platform-specific)
      SingleActivator(LogicalKeyboardKey.keyZ, control: true): () {
        appState.undo2DAction();
      },
      SingleActivator(LogicalKeyboardKey.keyZ, meta: true): () {
        appState.undo2DAction();
      },

      // Redo shortcuts
      SingleActivator(LogicalKeyboardKey.keyZ, control: true, shift: true): () {
        appState.undo2DAction(redo: true);
      },
      SingleActivator(LogicalKeyboardKey.keyZ, meta: true, shift: true): () {
        appState.undo2DAction(redo: true);
      },
      SingleActivator(LogicalKeyboardKey.keyY, control: true): () {
        appState.undo2DAction(redo: true);
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
