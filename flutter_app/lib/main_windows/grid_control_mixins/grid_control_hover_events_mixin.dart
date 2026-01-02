import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:provider/provider.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import 'grid_control_contract.dart';

/// Mixin containing hover event handlers for GridAndCanvas
mixin GridControlHoverEventsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
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
          // TODO: cargo/seed previews are still not used in the 3D system

          appState.setHoverPreview(HoverPreview(kind: 'Cargo-Add', isValid: hoverValid,cargoOrSeedPoints: pts));
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
