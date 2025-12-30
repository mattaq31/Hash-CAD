import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:provider/provider.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';

/// Mixin containing hover event handlers for GridAndCanvas
mixin GridControlHoverEventsMixin<T extends StatefulWidget> on State<T> {
  // Required state - to be provided by _GridAndCanvasState
  Offset? get hoverPosition;
  set hoverPosition(Offset? value);
  bool get hoverValid;
  set hoverValid(bool value);
  Map<int, Map<int, Offset>> get hoverSlatMap;
  set hoverSlatMap(Map<int, Map<int, Offset>> value);
  FocusNode get keyFocusNode;

  // Methods from other mixins
  String getActionMode(ActionState actionState);
  (Offset, bool) hoverCalculator(Offset eventPosition, DesignState appState, ActionState actionState, bool preSelectedPositions);
  void setHoverCoordinates(DesignState appState);
  Map<int, Offset> generateSeedPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState);
  Map<int, Offset> generateCargoPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState);

  void handleHover(PointerHoverEvent event, DesignState appState, ActionState actionState) {
    keyFocusNode.requestFocus(); // returns focus back to keyboard shortcuts

    if (getActionMode(actionState).contains('Add') || getActionMode(actionState).contains('Delete')) {
      setState(() {
        var (localHoverPosition, localHoverValid) = hoverCalculator(event.position, appState, actionState, false);
        hoverPosition = localHoverPosition;
        hoverValid = localHoverValid;

        // Publish preview to shared state, which can also be used in the 3D painter
        if (getActionMode(actionState) == 'Slat-Add' && hoverPosition != null) {
          setHoverCoordinates(appState);
        } else if (getActionMode(actionState) == 'Cargo-Add' && hoverPosition != null) {
          final pts = (appState.cargoAdditionType == 'SEED')
              ? generateSeedPositions(hoverPosition!, true, appState).values.toList()
              : generateCargoPositions(hoverPosition!, true, appState).values.toList();
          appState.setHoverPreview(HoverPreview(
            kind: 'Cargo-Add',
            isValid: hoverValid,
            cargoOrSeedPoints: pts,
          ));
        }
      });
    }
  }

  void handleHoverExit(PointerExitEvent event) {
    setState(() {
      hoverPosition = null; // Hide the hovering slat when cursor leaves the grid area
      hoverSlatMap = {};
      context.read<DesignState>().setHoverPreview(null);
    });
  }
}
