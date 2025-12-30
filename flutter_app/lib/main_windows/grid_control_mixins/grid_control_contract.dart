import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../app_management/shared_app_state.dart';
import '../../app_management/action_state.dart';

/// Contract defining all shared members between grid control mixins.
/// This enables IDE navigation (Find Usages) to work across mixins by
/// providing a single source of truth for all shared method signatures.
mixin GridControlContract<T extends StatefulWidget> on State<T> {
  // === State properties (provided by _GridAndCanvasState) ===
  double get scale;
  set scale(double value);
  Offset get offset;
  set offset(Offset value);
  double get minScale;
  double get maxScale;
  double get initialScale;
  set initialScale(double value);
  Offset get initialPanOffset;
  set initialPanOffset(Offset value);
  Offset get initialGestureFocalPoint;
  set initialGestureFocalPoint(Offset value);
  Offset? get hoverPosition;
  set hoverPosition(Offset? value);
  bool get hoverValid;
  set hoverValid(bool value);
  Map<int, Map<int, Offset>> get hoverSlatMap;
  set hoverSlatMap(Map<int, Map<int, Offset>> value);
  List<String> get hiddenSlats;
  set hiddenSlats(List<String> value);
  List<Offset> get hiddenCargo;
  set hiddenCargo(List<Offset> value);
  Offset get slatMoveAnchor;
  set slatMoveAnchor(Offset value);
  bool get dragActive;
  set dragActive(bool value);
  bool get moveFlipRequested;
  set moveFlipRequested(bool value);
  bool get isShiftPressed;
  set isShiftPressed(bool value);
  bool get isCtrlPressed;
  set isCtrlPressed(bool value);
  bool get isMetaPressed;
  set isMetaPressed(bool value);
  FocusNode get keyFocusNode;
  bool get dragBoxActive;
  set dragBoxActive(bool value);
  Offset? get dragBoxStart;
  set dragBoxStart(Offset? value);
  Offset? get dragBoxEnd;
  set dragBoxEnd(Offset? value);

  // === Methods from GridControlHelpersMixin ===
  (double, Offset) scrollZoomCalculator(PointerScrollEvent event, {double zoomFactor = 0.2});
  bool checkCoordinateOccupancy(DesignState appState, ActionState actionState, List<Offset> coordinates);
  (Offset, bool) hoverCalculator(Offset eventPosition, DesignState appState, ActionState actionState, bool preSelectedPositions);
  Map<int, Offset> getCargoHoverPoints(DesignState appState, ActionState actionState);
  SystemMouseCursor getCursorForSlatMode(String actionMode);
  Offset gridSnap(Offset inputPosition, DesignState designState);
  String getActionMode(ActionState actionState);
  List<String> getStatusIndicatorText(ActionState actionState, DesignState appState);

  // === Methods from GridControlPositionGeneratorsMixin ===
  Map<int, Map<int, Offset>> generateSlatPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState);
  Map<int, Offset> generateCargoPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState);
  Map<int, Offset> generateSeedPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState);
  void centerOnSlats();

  // === Methods from _GridAndCanvasState ===
  void setHoverCoordinates(DesignState appState);
}
