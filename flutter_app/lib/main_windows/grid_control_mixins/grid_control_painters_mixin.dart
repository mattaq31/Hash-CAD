import 'package:flutter/material.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';
import '../../2d_painters/grid_painter.dart';
import '../../2d_painters/slat_painter.dart';
import '../../2d_painters/slat_hover_painter.dart';
import '../../2d_painters/cargo_hover_painter.dart';
import '../../2d_painters/delete_painter.dart';
import '../../2d_painters/seed_painter.dart';
import '../../2d_painters/drag_box_painter.dart';

/// Mixin containing the CustomPaint widget builders for GridAndCanvas
mixin GridControlPaintersMixin<T extends StatefulWidget> on State<T> {
  // Required state - to be provided by _GridAndCanvasState
  double get scale;
  Offset get offset;
  bool get hoverValid;
  Map<int, Map<int, Offset>> get hoverSlatMap;
  Offset? get hoverPosition;
  bool get dragActive;
  List<String> get hiddenSlats;
  List<Offset> get hiddenCargo;
  Offset get slatMoveAnchor;
  bool get moveFlipRequested;
  bool get dragBoxActive;
  Offset? get dragBoxStart;
  Offset? get dragBoxEnd;

  // Methods from other mixins
  String getActionMode(ActionState actionState);
  Map<int, Offset> getCargoHoverPoints(DesignState appState, ActionState actionState);

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
                  appState,
                  actionState,
                )
              : CargoHoverPainter(
                  scale,
                  offset,
                  hoverValid,
                  getCargoHoverPoints(appState, actionState),
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
