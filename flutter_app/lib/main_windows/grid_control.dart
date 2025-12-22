import 'package:flutter/services.dart';
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'dart:math' as math;
import 'package:provider/provider.dart';

import '../app_management/shared_app_state.dart';
import '../2d_painters/grid_painter.dart';
import '../2d_painters/slat_hover_painter.dart';
import '../2d_painters/slat_painter.dart';
import '../2d_painters/helper_functions.dart';
import '../2d_painters/delete_painter.dart';
import '../2d_painters/cargo_hover_painter.dart';
import '../2d_painters/drag_box_painter.dart';
import '../2d_painters/seed_painter.dart';
import '../main_windows/floating_switches.dart';
import '../2d_painters/2d_view_svg_exporter.dart';


/// Class that takes care of painting all 2D objects on the grid, including the grid itself, slats and slat hover effects.
class GridAndCanvas extends StatefulWidget {

  const GridAndCanvas({super.key});

  @override
  State<GridAndCanvas> createState() => _GridAndCanvasState();
}

class _GridAndCanvasState extends State<GridAndCanvas> {

  double initialScale = 1.0; // scale parameters
  double minScale = 0.1;
  double maxScale = 6.0;

  bool moveFlipRequested = false;

  double scale = 0.8; // actual running scale value
  Offset offset = Offset(800,700); // actual running offset value

  // for the gesture detector (touchpad)
  Offset initialPanOffset = Offset.zero;
  Offset initialGestureFocalPoint = Offset.zero;

  Offset? hoverPosition; // Stores the snapped position of the hovering slat
  bool hoverValid = true;  // Flag to indicate if the hovering slat is in a valid position
  Map<int, Map<int, Offset>> hoverSlatMap = {}; // transient map of hovering slats

  bool dragActive = false;  // currently in slat drag mode (panning turned off)
  Offset slatMoveAnchor = Offset.zero; // the anchor point of the slats being moved
  List<String> hiddenSlats = []; // slats that are hidden from view while being moved
  List<Offset> hiddenCargo = []; // cargo that is hidden from view while being moved

  bool isShiftPressed = false; // keyboard bool check
  bool isCtrlPressed = false; // keyboard bool check
  bool isMetaPressed = false; // keyboard bool check (macOS)
  final FocusNode keyFocusNode = FocusNode(); // Persistent focus node for keyboard

  // controls for drag-select box
  bool dragBoxActive = false;
  Offset? dragBoxStart;
  Offset? dragBoxEnd;

  /// updates the coordinates for the hover slat preview
  void setHoverCoordinates(DesignState appState){
    if (hoverPosition == null) return;
    hoverSlatMap = generateSlatPositions(hoverPosition!, true, appState); // REAL space
    final paths = hoverSlatMap.values
        .map((inner) => inner.values.toList())
        .toList();
    appState.setHoverPreview(HoverPreview(
      kind: 'Slat-Add',
      isValid: hoverValid,
      slatPaths: paths,
    ));

  }

  /// Function for converting a mouse zoom event into a 'scale' and 'offset' to be used when pinpointing the current position on the grid.
  /// 'zoomFactor' affects the scroll speed (higher is slower).
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

  /// Function for checking if a slat can be placed at a given coordinate.
  bool checkCoordinateOccupancy(DesignState appState, ActionState actionState, List<Offset> coordinates){

    Iterable<Offset>? occupiedPositions;
    Set<Offset> hiddenPositions = {};

    if (actionState.panelMode == 0) {  // slat mode
      occupiedPositions = appState.occupiedGridPoints[appState.selectedLayerKey]?.keys;
      for (var slat in hiddenSlats) {
        hiddenPositions.addAll(appState.slats[slat]?.slatPositionToCoordinate.values ?? {});
      }
    }
    else{ // cargo mode (or otherwise)
      String additionalOccupancy = '';
      if(appState.cargoAdditionType == 'SEED'){
        // if in seed mode, need to calculate collisions with slats too!
        int targetLayerOrder = appState.layerMap[appState.selectedLayerKey]!["order"] + (actionState.cargoAttachMode == 'top' ? 1 : -1);
        if (targetLayerOrder != -1 && targetLayerOrder < appState.layerMap.length) {
          additionalOccupancy = appState.layerMap.keys.firstWhere((key) => appState.layerMap[key]!['order'] == targetLayerOrder);
        }
      }
      if (additionalOccupancy != '') {
        occupiedPositions = {
          ...?appState.occupiedCargoPoints['${appState.selectedLayerKey}-${actionState.cargoAttachMode}']?.keys,
          ...?appState.occupiedGridPoints[additionalOccupancy]?.keys
        };
      }
      else{
        occupiedPositions = appState.occupiedCargoPoints['${appState.selectedLayerKey}-${actionState.cargoAttachMode}']?.keys;
      }
      hiddenPositions.addAll(hiddenCargo);
    }

    if (occupiedPositions == null) return false;

    for (var coord in coordinates) {
      if (occupiedPositions.contains(coord) && !hiddenPositions.contains(coord)) {
        return true;
      }
    }

    return false;
  }

  /// Function for converting a mouse hover event into a 'snapPosition' and 'hoverValid' flag to be used when pinpointing the current position on the grid.
  (Offset, bool) hoverCalculator(Offset eventPosition, DesignState appState, ActionState actionState, bool preSelectedSlats){

    // the position is snapped to the nearest grid point
    // the function needs to make sure the global offset/scale
    // due to panning/zooming are taken into account
    Offset snapPosition = gridSnap(eventPosition, appState);
    // check to see if clicked position is taken by a slat already
    bool snapHoverValid = true;
    List<Offset> queryCoordinates = [];

    if (actionState.panelMode == 0) {  // slat mode
      // TODO: there must be a faster way to get this to run properly...
      // preselectedSlats means that the slats are already selected and are being moved
      if (preSelectedSlats) {
        Offset slatOffset = appState.convertRealSpacetoCoordinateSpace(snapPosition - slatMoveAnchor);
        for (var slat in appState.selectedSlats) {
          for (var coord in appState.slats[slat]!.slatPositionToCoordinate
              .values) {
            queryCoordinates.add(coord + slatOffset);
          }
        }
      }
      else {
        Map<int, Map<int, Offset>> allSlatCoordinates = generateSlatPositions(snapPosition, false, appState);
        queryCoordinates = allSlatCoordinates.values.expand((innerMap) => innerMap.values).toList();
      }
    }
    else{  // everything else
      Map<int, Offset> allCargoCoordinates;
      if (appState.cargoAdditionType != 'SEED') {
        allCargoCoordinates = generateCargoPositions(snapPosition, false, appState);
      }
      else{
        allCargoCoordinates = generateSeedPositions(snapPosition, false, appState); // seed has a special occupancy grid
      }
      queryCoordinates = allCargoCoordinates.values.toList();
    }

    snapHoverValid = !checkCoordinateOccupancy(appState, actionState, queryCoordinates);

    return (snapPosition, snapHoverValid);
  }

  /// logic for changing the slat cursor type based on the current action mode
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

  Offset gridSnap(Offset inputPosition, DesignState designState){
    if (designState.gridMode == '90') {
      return Offset(
        (((inputPosition.dx - offset.dx) / scale) / designState.gridSize).round() * designState.gridSize,
        (((inputPosition.dy - offset.dy) / scale) / designState.gridSize).round() * designState.gridSize,
      );
    }
    else if (designState.gridMode == '60'){
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
    }
    else{
     throw Exception('Grid system not supported');
    }
  }

  String getActionMode(ActionState actionState) {
    if (actionState.panelMode == 0){
      if (actionState.slatMode == "Add") {
        return "Slat-Add";
      } else if (actionState.slatMode == "Delete") {
        return "Slat-Delete";
      } else if (actionState.slatMode == "Move") {
        return "Slat-Move";
      } else {
        return "Neutral";
      }
    }
    else if (actionState.panelMode == 2){
      if (actionState.cargoMode == 'Add'){
        return "Cargo-Add";
      }
      else if (actionState.cargoMode == 'Delete'){
        return "Cargo-Delete";
      }
      else if (actionState.cargoMode == 'Move'){
        return "Cargo-Move";
      }
      else{
        return "Neutral";
      }
    }
    else {
      return "Neutral";
    }
  }

  Map<int, Map<int, Offset>> generateSlatPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState){

    // slats added to a persistent list here
    Map<int, Map<int, Offset>> incomingSlats = {};

    int direction;
    if (appState.slatAdditionType == 'tube'){
      direction = appState.layerMap[appState.selectedLayerKey]!["direction"];
    }
    else{
      direction = appState.layerMap[appState.selectedLayerKey]!["DBDirection"];
    }

    Offset cursorCoordinate, slatMultiJump, slatInnerJump;
    double transposeDirection = appState.slatAddDirection == 'down' ? 1 : -1;

    var multiGenerator = appState.slatAdditionType == 'tube' ? appState.multiSlatGenerators : appState.multiSlatGeneratorsDB;
    var directionGenerator = appState.slatAdditionType == 'tube' ? appState.slatDirectionGenerators : appState.slatDirectionGeneratorsDB;

    if (realSpaceFormat){
      cursorCoordinate = cursorPoint;
      if (appState.gridMode == '60'){
        slatMultiJump = multiplyOffsets(multiGenerator[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
        slatInnerJump = multiplyOffsets(directionGenerator[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
      }
      else{
        slatMultiJump = multiGenerator[(appState.gridMode, direction)]! * appState.gridSize;
        slatInnerJump = directionGenerator[(appState.gridMode, direction)]! * appState.gridSize;
      }
    }
    else{
      cursorCoordinate = appState.convertRealSpacetoCoordinateSpace(cursorPoint);
      slatMultiJump = multiGenerator[(appState.gridMode, direction)]!;
      slatInnerJump = directionGenerator[(appState.gridMode, direction)]!;
    }

    int shearOffset = 0;
    double dbSign = 1;
    if (appState.slatAdditionType == 'tube') {
      slatMultiJump = slatMultiJump * transposeDirection;
      slatInnerJump = slatInnerJump * transposeDirection;
    }
    else {
      if (appState.slatAdditionType == 'DB-R-60' || appState.slatAdditionType == 'DB-R-120' || appState.slatAdditionType == 'DB-R'){
        dbSign = -1;
      }

      // for DB slats in 60degree mode, slats can have a different 'shear' value too, which we refer to as '60' and '120' types (referring to the inner angle of the first kink)
      if (appState.slatAdditionType == 'DB-L-120'){
      shearOffset = 1;
      }
      else if (appState.slatAdditionType == 'DB-R-60'){
        shearOffset = -1;
      }
    }

    for (int j = 0; j < appState.slatAddCount; j++) {
      incomingSlats[j] = {};
      for (int i = 0; i < 32; i++) {
        if (appState.slatAdditionType == 'tube') {
          incomingSlats[j]?[i + 1] = cursorCoordinate + (slatMultiJump * j.toDouble()) + (slatInnerJump * i.toDouble());
        }
        else{
          // double barrel slat generation
          if (i < 16){
            incomingSlats[j]?[i + 1] = cursorCoordinate + (slatMultiJump * j.toDouble() * 2 * dbSign) + (slatInnerJump * i.toDouble());
          }
          else{
            incomingSlats[j]?[i + 1] = cursorCoordinate + (slatMultiJump * (1 + (j.toDouble() * 2)) * dbSign) + (slatInnerJump * (31 + shearOffset - i).toDouble());
          }
        }
      }
    }
    return incomingSlats;
  }

  Map<int, Offset> generateCargoPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState){

    // cargo added to a persistent list here
    Map<int, Offset> incomingCargo = {};
    int direction = appState.layerMap[appState.selectedLayerKey]!["direction"];
    double transposeDirection = appState.slatAddDirection == 'down' ? 1 : -1;
    Offset cursorCoordinate, multiJump;
    if (realSpaceFormat){
      cursorCoordinate = cursorPoint;
      if (appState.gridMode == '60'){
        multiJump = multiplyOffsets(appState.slatDirectionGenerators[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
      }
      else{
        multiJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]! * appState.gridSize;
      }
    }
    else{
      cursorCoordinate = appState.convertRealSpacetoCoordinateSpace(cursorPoint);
      multiJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]!;
    }

    multiJump = multiJump * transposeDirection;

    for (int j = 0; j < appState.cargoAddCount; j++) {
      incomingCargo[j] = cursorCoordinate + (multiJump * j.toDouble());
    }
    return incomingCargo;
  }

  Map<int, Offset> generateSeedPositions(Offset cursorPoint, bool realSpaceFormat, DesignState appState){

    // seed handles added to a persistent list here
    Map<int, Offset> incomingHandles = {};
    int direction = appState.layerMap[appState.selectedLayerKey]!["direction"];
    double transposeDirection = appState.slatAddDirection == 'down' ? 1 : -1;

    Offset cursorCoordinate, heightMultiJump, widthMultiJump;
    if (realSpaceFormat){
      cursorCoordinate = cursorPoint;
      if (appState.gridMode == '60'){
        heightMultiJump = multiplyOffsets(appState.slatDirectionGenerators[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
        widthMultiJump = multiplyOffsets(appState.multiSlatGenerators[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
      }
      else{
        heightMultiJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]! * appState.gridSize;
        widthMultiJump = appState.multiSlatGenerators[(appState.gridMode, direction)]! * appState.gridSize;
      }
    }
    else{
      cursorCoordinate = appState.convertRealSpacetoCoordinateSpace(cursorPoint);
      heightMultiJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]!;
      widthMultiJump = appState.multiSlatGenerators[(appState.gridMode, direction)]!;
    }
    if (appState.gridMode == '90') { // TODO: investigate whether having a full flip is of interest in 60 degree mode too...
      heightMultiJump = heightMultiJump * transposeDirection;
    }

    widthMultiJump = widthMultiJump * transposeDirection;
    
    for (int i = 0; i < appState.seedOccupancyDimensions['width']!; i++) {
      for (int j = 0; j < appState.seedOccupancyDimensions['height']!; j++) {
        incomingHandles[1 + (i*appState.seedOccupancyDimensions['height']!+j)] = cursorCoordinate + (widthMultiJump * i.toDouble()) + (heightMultiJump * j.toDouble());
      }
    }
    return incomingHandles;
  }

  /// Centers the 2D view on all slats, accounting for all UI elements
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
    canvasHeight -= 80.0;  // Top padding (floating title)
    canvasHeight -= 100.0; // Bottom padding (toggle panel)

    // Ensure minimum canvas size
    Size canvasSize = Size(
        canvasWidth.clamp(100, double.infinity),
        canvasHeight.clamp(100, double.infinity)
    );

    // Collect all slat coordinates
    List<Offset> allSlatCoordinates = [];
    for (String layerKey in appState.occupiedGridPoints.keys) {
      allSlatCoordinates.addAll(appState.occupiedGridPoints[layerKey]!.keys);
    }

    if (allSlatCoordinates.isEmpty) return;

    // Convert to real space and calculate bounding box
    List<Offset> realSpaceCoordinates = allSlatCoordinates
        .map((coord) => appState.convertCoordinateSpacetoRealSpace(coord))
        .toList();

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
    double boundingWidth = (maxX - minX) * 1.1;  // 10% padding
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


  @override
  Widget build(BuildContext context) {


    // watches the current slat and layer statuses
    var appState = context.watch<DesignState>();

    // watches the current action mode
    var actionState = context.watch<ActionState>();

    // main app activity defined here
    return Stack(
      children: [
        Scaffold(
        body: Listener(
          // this handles mouse zoom events only
          onPointerSignal: (PointerSignalEvent event) {
            if (event is PointerScrollEvent && !dragBoxActive) {
              setState(() {
                var (calcScale, calcOffset) = scrollZoomCalculator(event);
                scale = calcScale;
                offset = calcOffset;
              });
            }
          },

          // the following three event handlers are specifically setup to handle the slat move mode
          onPointerDown: (event){
            if (actionState.slatMode == "Move") {
              // Start drag-box selection
              if (isCtrlPressed || isMetaPressed) { // ctrl or meta key pressed
                setState(() {
                  dragBoxActive = true;
                  dragBoxStart = event.position;
                  dragBoxEnd = event.position;
                });
              } else { // starts slat drag mode (first need to detect if a slat is under the pointer first)
                final Offset snappedPosition = gridSnap(event.position, appState);
                if (checkCoordinateOccupancy(appState, actionState, [appState.convertRealSpacetoCoordinateSpace(snappedPosition)])) {
                  dragActive = true; // drag mode is signalled here - panning is now disabled
                  slatMoveAnchor = snappedPosition; // the slats to be moved are anchored to the cursor
                }
              }
            }
          },
          onPointerMove: (PointerMoveEvent event){
            if (dragBoxActive) {
              // Update drag-box
              setState(() {
                dragBoxEnd = event.position;
              });
            } else if (getActionMode(actionState) == 'Slat-Move' && dragActive) {
              // when drag mode is activated, the slat will again follow the cursor (similar to the mouse hover mode)
              setState(() {
                if (hiddenSlats.isEmpty) {
                  for (var slat in appState.selectedSlats) {
                    hiddenSlats.add(slat);
                  }
                }
                var (localHoverPosition, localHoverValid) =
                hoverCalculator(event.position, appState, actionState, true);
                hoverPosition = localHoverPosition;
                hoverValid = localHoverValid;
              });
            }
          },
          onPointerUp: (event){
            // drag is always cancelled when the pointer is let go
            if (dragBoxActive) {
              // Finish drag-box selection
              final rect = Rect.fromPoints((dragBoxStart! - offset) / scale, (dragBoxEnd! - offset) / scale);

              final selected = <String>{};
              for (var entry in appState.slats.entries) {
                if (entry.value.layer != appState.selectedLayerKey) continue; // only select slats from the active layer
                final slat = entry.value;
                final coords = slat.slatPositionToCoordinate.values.map((coord) => appState.convertCoordinateSpacetoRealSpace(coord));
                // If any part of slat falls inside the rect → select it
                if (coords.any((pt) => rect.contains(pt))) {
                  selected.add(entry.key);
                }
              }
              // add all selected slats
              for (var ID in selected) {
                  appState.selectSlat(ID, addOnly: true);
              }

              setState(() {
                dragBoxActive = false;
                dragBoxStart = null;
                dragBoxEnd = null;
              });

            } else if (getActionMode(actionState) == 'Slat-Move') {
              setState(() {
                if (hoverValid && dragActive && hoverPosition != null) {
                  var convCoordHoverPosition = appState.convertRealSpacetoCoordinateSpace(hoverPosition!);
                  var convCoordAnchor = appState.convertRealSpacetoCoordinateSpace(slatMoveAnchor);
                  for (var slat in appState.selectedSlats){
                    appState.updateSlatPosition(slat, appState.slats[slat]!.slatPositionToCoordinate.map((key, value) => MapEntry(key, value + convCoordHoverPosition - convCoordAnchor)));
                    if (moveFlipRequested) {
                      if (appState.slats[slat]!.slatType == 'tube') { // double barrel flips are currently blocked
                        appState.slats[slat]!.reverseDirection();
                      }
                    }
                  }
                }
                dragActive = false;
                hiddenSlats = [];
                hoverPosition = null; // Hide the hovering slat when cursor leaves the grid area
                slatMoveAnchor = Offset.zero;
                moveFlipRequested = false; // reset the flip request
              });
            }
          },

          // this handles keyboard events (only)
          child: CallbackShortcuts(
            bindings: {
              // Rotation shortcut
              SingleActivator(LogicalKeyboardKey.keyR): () {
                if (getActionMode(actionState) == 'Slat-Move' && dragActive) {
                    // moveRotationStepsRequested += 1;
                  // TODO: reinstate this system when confirmed
                }
                else {
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
                }
                else {
                  appState.flipSlatAddDirection();
                }
                if (getActionMode(actionState) == 'Slat-Add' && hoverPosition != null) {
                  setHoverCoordinates(appState);
                }
              },
              // delete shortcut (when in move mode)
              SingleActivator(LogicalKeyboardKey.delete): () {
                for (var slat in appState.selectedSlats) {
                  appState.removeSlat(slat);
                }
              },
              SingleActivator(LogicalKeyboardKey.backspace): () {
                for (var slat in appState.selectedSlats) {
                  appState.removeSlat(slat);
                }
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
                else if (actionState.panelMode == 2) {
                  actionState.updateCargoMode('Add');
                }
              },
              SingleActivator(LogicalKeyboardKey.digit2): () {
                  if (actionState.panelMode == 0) {
                    actionState.updateSlatMode('Delete');
                  }
                  else if (actionState.panelMode == 2) {
                    actionState.updateCargoMode('Delete');
                  }
              },
              SingleActivator(LogicalKeyboardKey.digit3): () {
                  if (actionState.panelMode == 0) {
                    actionState.updateSlatMode('Move');
                  }
                  else if (actionState.panelMode == 2) {
                    actionState.updateCargoMode('Move');
                  }
              },

              // Undo shortcuts (platform-specific)
              SingleActivator(
                  LogicalKeyboardKey.keyZ,
                  control: true
              ): () {
                  appState.undo2DAction();
              },
              SingleActivator(
                  LogicalKeyboardKey.keyZ,
                  meta: true
              ): () {
                  appState.undo2DAction();
              },

              // Redo shortcuts
              SingleActivator(
                LogicalKeyboardKey.keyZ,
                control: true,
                shift: true,
              ): () {
                appState.undo2DAction(redo: true);
              },
              SingleActivator(
                LogicalKeyboardKey.keyZ,
                meta: true,
                shift: true,
              ): () {
                appState.undo2DAction(redo: true);
              },
              SingleActivator(
                LogicalKeyboardKey.keyY,
                control: true,
              ): () {
                appState.undo2DAction(redo: true);
              },
            },
            child: Focus(
              autofocus: true,
              focusNode: keyFocusNode,
              onKeyEvent: (FocusNode node, KeyEvent event) {
                setState(() {
                  // Handle the shift key state
                  if (event is KeyDownEvent) {
                    isShiftPressed = event.logicalKey.keyLabel.contains('Shift');
                    isCtrlPressed = event.logicalKey.keyLabel.contains('Control');
                    isMetaPressed = event.logicalKey.keyLabel.contains('Meta'); // macOS meta key
                  } else if (event is KeyUpEvent) {
                    if (event.logicalKey.keyLabel.contains('Shift')) {
                      isShiftPressed  = false;
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
              },
              // this handles the hovering function in add or delete mode i.e. having a single slat or 'X' follow the mouse to indicate where its position will be if clicked
              child: MouseRegion(
              cursor: getCursorForSlatMode(getActionMode(actionState)),  // TODO: it looks better if the cursor changes when hovering over a slat, rather than always being the same in move mode
                onHover: (event) {
                  keyFocusNode.requestFocus();  // returns focus back to keyboard shortcuts

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
                },
                onExit: (event) {
                  setState(() {
                    hoverPosition = null; // Hide the hovering slat when cursor leaves the grid area
                    hoverSlatMap = {};
                    context.read<DesignState>().setHoverPreview(null);
                  });
                },
                // this handles A) scaling applied via a multi-touch operation and B) the actual placement of a slat on the grid
                child: GestureDetector(
                  onScaleStart: (details) {
                    initialScale = scale;
                    initialPanOffset = offset;
                    initialGestureFocalPoint = details.focalPoint;
                  },
                  onScaleUpdate: (details) {
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
                  },
                  // this is the actual point a new slat or cargo module is being added to the system
                  onTapDown: (details) {
                    final Offset snappedPosition = gridSnap(details.localPosition, appState);
                    if (getActionMode(actionState) == 'Slat-Add'){
                      if (!hoverValid) { // cannot place slats if blocked by other slats
                        return;
                      }
                      // slats added to a persistent list here
                      Map<int, Map<int, Offset>> incomingSlats = {};
                      incomingSlats = generateSlatPositions(snappedPosition, false, appState);
                      // if not already taken, can proceed to add a new slat
                      appState.clearSelection();
                      appState.addSlats(appState.selectedLayerKey, incomingSlats);
                    }
                    else if (getActionMode(actionState) == 'Slat-Delete'){
                      // slats removed from the persistent list here
                      var coordConvertedPosition = appState.convertRealSpacetoCoordinateSpace(snappedPosition);
                      if (checkCoordinateOccupancy(appState, actionState, [coordConvertedPosition])) {
                          appState.removeSlat(appState.occupiedGridPoints[appState.selectedLayerKey]![coordConvertedPosition]!);
                        }
                    }
                    else if (getActionMode(actionState) == 'Cargo-Add'){
                      if (!hoverValid) {
                        return;
                      }

                      Map<int, Offset> incomingCargo;

                      if (appState.cargoAdditionType == 'SEED'){
                        incomingCargo = generateSeedPositions(snappedPosition, false, appState);
                      }
                      else {
                        incomingCargo = generateCargoPositions(snappedPosition, false, appState);
                      }
                      // if not already taken, can proceed to add a new slat
                      appState.clearSelection();
                      if (appState.cargoAdditionType != null) {
                        if (appState.cargoAdditionType == 'SEED'){
                          appState.attachSeed(appState.selectedLayerKey, actionState.cargoAttachMode, incomingCargo, context);
                        }
                        else {
                          appState.attachCargo(appState.cargoPalette[appState
                              .cargoAdditionType]!, appState.selectedLayerKey,
                              actionState.cargoAttachMode, incomingCargo);
                        }
                      }
                    }
                    else if (getActionMode(actionState) == 'Cargo-Delete'){
                      // cargo removed from the persistent list here
                      var coordConvertedPosition = appState.convertRealSpacetoCoordinateSpace(snappedPosition);
                      if (checkCoordinateOccupancy(appState, actionState, [coordConvertedPosition])) {
                        appState.removeCargo(appState.occupiedCargoPoints['${appState.selectedLayerKey}-${actionState.cargoAttachMode}']![coordConvertedPosition]!, actionState.cargoAttachMode, coordConvertedPosition);
                      }
                    }
                  },

                  onTapUp: (TapUpDetails details) {
                    final Offset snappedPosition = appState.convertRealSpacetoCoordinateSpace(gridSnap(details.localPosition, appState));

                    if (getActionMode(actionState) == 'Slat-Move') {
                      if (checkCoordinateOccupancy(appState, actionState, [snappedPosition])){
                        if (appState.selectedSlats.isNotEmpty && !isShiftPressed) {
                          appState.clearSelection();
                        }
                        // this flips a selection if the slat was already clicked (and pressing shift)
                        appState.selectSlat(appState.occupiedGridPoints[appState.selectedLayerKey]![snappedPosition]!);
                      }
                      else {
                        appState.clearSelection();
                      }
                    }
                    // TODO: ADD CARGO MOVE MODE!!

                  },
                  // the custom painters here constantly re-apply objects to the screen while moving around
                  child: Stack(
                    children: [
                      CustomPaint(
                        size: Size.infinite,
                        painter: GridPainter(scale, offset, appState.gridSize, appState.gridMode, scale < 0.5 ? false : actionState.displayGrid, actionState.displayBorder),
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
                              actionState,
                              appState),
                          child: Container(),
                        ),
                      ),
                      CustomPaint(
                        size: Size.infinite,
                        painter: actionState.panelMode == 0 ? SlatHoverPainter(
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
                            actionState
                        ): CargoHoverPainter(
                            scale,
                            offset,
                            appState.cargoAdditionType != null ? appState.cargoPalette[appState.cargoAdditionType]! : null,
                            hoverValid,
                            (hoverPosition != null && getActionMode(actionState) == 'Cargo-Add') ? appState.cargoAdditionType == 'SEED' ? generateSeedPositions(hoverPosition!, true, appState) : generateCargoPositions(hoverPosition!, true, appState) : {},
                            hoverPosition,
                            [],
                            slatMoveAnchor,
                            appState
                        ),
                        child: Container(),
                      ),
                      CustomPaint(
                        size: Size.infinite,
                        painter: DeletePainter(scale, offset, getActionMode(actionState).contains('Delete') ? hoverPosition: null, appState.gridSize),
                        child: Container(),
                      ),
                      RepaintBoundary(
                        child: CustomPaint(
                          size: Size.infinite,
                          painter: SeedPainter(
                              scale: scale,
                              canvasOffset: offset,
                              seeds: actionState.displaySeeds ? appState.seedRoster.entries
                                  .where((entry) => entry.key.$1 == appState.selectedLayerKey)
                                  .map((entry) => entry.value)
                                  .toList() : [],
                              seedTransparency:  appState.seedRoster.entries
                                  .where((entry) => entry.key.$1 == appState.selectedLayerKey)
                                  .map((entry) => entry.key.$2 == 'bottom')
                                  .toList(),
                              handleJump: appState.gridSize,
                              printHandles: false,
                              color: appState.cargoPalette['SEED']!.color),
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
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
        // Top-left floating button that moves with sidebar
        AnimatedPositioned(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
          top: 20,
          left: actionState.isSideBarCollapsed ? 72 + 15 : 72 + 330 + 10,
          child: Tooltip(
            message: 'Export Slat Design to SVG Image',
            waitDuration: Duration(milliseconds: 500), // Optional: delay before showing
            child: FloatingActionButton.small(
              foregroundColor: Theme.of(context).colorScheme.onPrimary,
              backgroundColor: Theme.of(context).colorScheme.primary,
              child: Icon(Icons.camera), // Placeholder icon
              onPressed: () {
                exportSlatsToSvg(
                  slats: appState.slats.values.toList(),
                  layerMap: appState.layerMap,
                  appState: appState,
                  actionState: actionState
                );
              },
            ),
          ),
        ),
        TogglePanel(actionState: actionState, onCenterPressed: centerOnSlats)
    ]);
  }
}