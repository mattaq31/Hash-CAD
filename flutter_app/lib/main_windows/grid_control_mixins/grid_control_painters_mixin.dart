import 'package:flutter/material.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import '../../2d_painters/grid_painter.dart';
import '../../2d_painters/slat_painter.dart';
import '../../2d_painters/slat_hover_painter.dart';
import '../../2d_painters/handle_hover_painter.dart';
import '../../2d_painters/delete_painter.dart';
import '../../2d_painters/seed_painter.dart';
import '../../2d_painters/drag_box_painter.dart';
import 'grid_control_contract.dart';

/// Mixin containing the CustomPaint widget builders for GridAndCanvas
mixin GridControlPaintersMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  /// Builds the stack of CustomPaint widgets for the 2D canvas
  Widget buildPainterStack(DesignState appState, ActionState actionState) {
    return Stack(
      children: [
        CustomPaint(
          size: Size.infinite,
          painter: GridPainter(
            scale,
            offset,
            appState.gridSize,
            appState.gridMode,
            scale < 0.5 ? false : actionState.displayGrid,
            actionState.displayBorder,
            zoomBoundsFlashOpacity,
            actionState.isSideBarCollapsed ? 80.0 : 72.0 + 330.0,
          ),
          child: Container(),
        ),
        RepaintBoundary(
          child: CustomPaint(
            size: Size.infinite,
            painter: SlatPainter(
              scale,
              offset,
              appState.slats.values.toList(),
              appState.layerMap,
              appState.selectedLayerKey,
              appState.selectedSlats,
              hiddenSlats,
              hiddenCargo,
              hiddenAssembly,
              actionState,
              appState,
            ),
            child: Container(),
          ),
        ),
        CustomPaint(
          size: Size.infinite,
          painter: actionState.panelMode == 0
              ? SlatHoverPainter(
                  scale,
                  offset,
                  appState.layerMap[appState.selectedLayerKey]?['color'],
                  hoverValid,
                  hoverSlatMap,
                  hoverPosition,
                  !dragActive,
                  appState.selectedSlats.map((e) => appState.slats[e]!).toList(),
                  slatMoveAnchor,
                  moveFlipRequested,
                  moveRotationSteps,
                  appState.gridMode,
                  appState,
                  actionState,
                )
              : HandleHoverPainter(
                  scale,
                  offset,
                  hoverValid,
                  getHandleHoverPoints(appState, actionState),
                  hoverPosition,
                  slatMoveAnchor,
                  appState,
                  actionState,
                ),
          child: Container(),
        ),
        CustomPaint(
          size: Size.infinite,
          painter: DeletePainter(
            scale,
            offset,
            getActionMode(actionState).contains('Delete') ? hoverPosition : null,
            appState.gridSize,
          ),
          child: Container(),
        ),
        RepaintBoundary(
          child: CustomPaint(
            size: Size.infinite,
            painter: SeedPainter(
              scale: scale,
              canvasOffset: offset,
              seeds: actionState.displaySeeds
                  ? appState.seedRoster.entries
                      .where((entry) => entry.key.$1 == appState.selectedLayerKey)
                      .map((entry) => entry.value)
                      .toList()
                  : [],
              seedTransparency: appState.seedRoster.entries
                  .where((entry) => entry.key.$1 == appState.selectedLayerKey)
                  .map((entry) => entry.key.$2 == 'bottom')
                  .toList(),
              handleJump: appState.gridSize,
              printHandles: false,
              color: appState.cargoPalette['SEED']!.color,
            ),
            child: Container(),
          ),
        ),
        CustomPaint(
          painter: DragPainter(
            dragBoxStart,
            dragBoxEnd,
            dragBoxActive,
          ),
        ),
      ],
    );
  }
}
