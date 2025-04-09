import 'package:flutter/services.dart';
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:provider/provider.dart';
import 'shared_app_state.dart';
import '2d_painters/grid_painter.dart';
import '2d_painters/slat_hover_painter.dart';
import '2d_painters/slat_painter.dart';
import '2d_painters/helper_functions.dart';
import '2d_painters/delete_painter.dart';

/// Class that takes care of painting all 2D objects on the grid, including the grid itself, slats and slat hover effects.
class GridAndCanvas extends StatefulWidget {
  const GridAndCanvas({super.key});

  @override
  State<GridAndCanvas> createState() => _GridAndCanvasState();
}

class _GridAndCanvasState extends State<GridAndCanvas> {

  double initialScale = 1.0; // scale parameters
  double minScale = 0.5;
  double maxScale = 6.0;

  double scale = 0.8; // actual running scale value
  Offset offset = Offset(800,700); // actual running offset value

  // for the gesture detector (touchpad)
  Offset initialPanOffset = Offset.zero;
  Offset initialGestureFocalPoint = Offset.zero;

  Offset? hoverPosition; // Stores the snapped position of the hovering slat
  bool hoverValid = true;  // Flag to indicate if the hovering slat is in a valid position

  bool dragActive = false;  // currently in slat drag mode (panning turned off)
  Offset slatMoveAnchor = Offset.zero; // the anchor point of the slats being moved
  List<String> hiddenSlats = []; // slats that are hidden from view while being moved

  bool isShiftPressed = false; // keyboard bool check
  final FocusNode keyFocusNode = FocusNode(); // Persistent focus node for keyboard


  /// Function for converting a mouse zoom event into a 'scale' and 'offset' to be used when pinpointing the current position on the grid.
  /// 'zoomFactor' affects the scroll speed (higher is slower).
  (double, Offset) scrollZoomCalculator(PointerScrollEvent event, {double zoomFactor = 0.1}) {

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
  bool checkCoordinateOccupancy(DesignState appState, List<Offset> coordinates){

    final occupiedPositions = appState.occupiedGridPoints[appState.selectedLayerKey]?.keys;
    if (occupiedPositions == null) return false;

    final hiddenPositions = <Offset>{};
    for (var slat in hiddenSlats) {
      hiddenPositions.addAll(appState.slats[slat]?.slatPositionToCoordinate.values ?? {});
    }

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

    List<Offset> slatCoordinates = [];
    // TODO: there must be a faster way to get this to run properly...
    if (preSelectedSlats){
      Offset slatOffset =  appState.convertRealSpacetoCoordinateSpace(snapPosition - slatMoveAnchor);
      for (var slat in appState.selectedSlats){
        for (var coord in appState.slats[slat]!.slatPositionToCoordinate.values){
          slatCoordinates.add(coord + slatOffset);
        }
      }
    }
    // preselectedSlats means that the slats are already selected and are being moved
    else {
      Map<int, Map<int, Offset>> allSlatCoordinates = generateSlatPositions(snapPosition!, false, false, appState);
      slatCoordinates = allSlatCoordinates.values.expand((innerMap) => innerMap.values).toList();
    }

    snapHoverValid = !checkCoordinateOccupancy(appState, slatCoordinates);
    return (snapPosition, snapHoverValid);
  }

  /// logic for changing the slat cursor type based on the current action mode
  SystemMouseCursor getCursorForSlatMode(String slatMode) {
    switch (slatMode) {
      case "Add":
        return SystemMouseCursors.precise; // Example: crosshair for adding
      case "Delete":
        return SystemMouseCursors.precise; // Example: blocked cursor for removal
      case "Move":
        return SystemMouseCursors.grab; // Example: pointer for selecting
      default:
        return SystemMouseCursors.basic; // Default cursor
    }
  }

  Offset gridSnap(Offset inputPosition, DesignState designState){
    if (designState.gridMode == '90') {
      return Offset(
        (((inputPosition.dx - offset.dx) / scale) / designState.gridSize).round() *
            designState.gridSize,
        (((inputPosition.dy - offset.dy) / scale) / designState.gridSize).round() *
            designState.gridSize,
      );
    }
    else if (designState.gridMode == '60'){

      double inX = (inputPosition.dx - offset.dx) / scale;
      double inY = (inputPosition.dy - offset.dy) / scale;

      int row = (inY / designState.y60Jump).round(); // Round to nearest row index
      double snappedY = row * designState.y60Jump;

      double xOffset = (row.isOdd ? designState.x60Jump : 0);  // accounts for adding an offset where the checkerboard effect is applied

      int col = ((inX - xOffset) / (2 * designState.x60Jump)).round(); // Use rounding as usual
      double snappedX = xOffset + col * 2 * designState.x60Jump;

      return Offset(snappedX, snappedY);

    }
    else{
     throw Exception('Grid system not supported');
    }
  }

  Map<int, Map<int, Offset>> generateSlatPositions(Offset cursorPoint, bool endPointsOnly, bool realSpaceFormat, DesignState appState){

    // slats added to a persistent list here
    Map<int, Map<int, Offset>> incomingSlats = {};
    int direction = appState.layerMap[appState.selectedLayerKey]!["direction"];
    Offset cursorCoordinate, slatMultiJump, slatInnerJump;

    if (realSpaceFormat){
      cursorCoordinate = cursorPoint;
      if (appState.gridMode == '60'){
        slatMultiJump = multiplyOffsets(appState.multiSlatGenerators[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
        slatInnerJump = multiplyOffsets(appState.slatDirectionGenerators[(appState.gridMode, direction)]!, Offset(appState.x60Jump, appState.y60Jump));
      }
      else{
        slatMultiJump = appState.multiSlatGenerators[(appState.gridMode, direction)]! * appState.gridSize;
        slatInnerJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]! * appState.gridSize;
      }
    }
    else{
      cursorCoordinate = appState.convertRealSpacetoCoordinateSpace(cursorPoint);
      slatMultiJump = appState.multiSlatGenerators[(appState.gridMode, direction)]!;
      slatInnerJump = appState.slatDirectionGenerators[(appState.gridMode, direction)]!;
    }

    for (int j = 0; j < appState.slatAddCount; j++) {
      incomingSlats[j] = {};
      if (endPointsOnly){
        incomingSlats[j]?[1] = cursorCoordinate + (slatMultiJump * j.toDouble());
        incomingSlats[j]?[32] = cursorCoordinate + (slatMultiJump * j.toDouble()) + (slatInnerJump * 32);
      }
      else {
        for (int i = 0; i < 32; i++) {
          incomingSlats[j]?[i + 1] = cursorCoordinate + (slatMultiJump * j.toDouble()) + (slatInnerJump * i.toDouble());
        }
      }
    }
    return incomingSlats;
    // RETURN LISTS INSTEAD OF MAPS (SHOULD I DO THE SAME FOR SLAT GENERATION?)
  }


  @override
  Widget build(BuildContext context) {

    // watches the current slat and layer statuses
    var appState = context.watch<DesignState>();

    // watches the current action mode
    var actionState = context.watch<ActionState>();

    // main app activity defined here
    return Scaffold(
      body: Listener(
        // this handles mouse zoom events only
        onPointerSignal: (PointerSignalEvent event) {
          if (event is PointerScrollEvent) {
            setState(() {
              var (calcScale, calcOffset) = scrollZoomCalculator(event);
              scale = calcScale;
              offset = calcOffset;
            });
          }
        },
        // the following three event handlers are specifically setup to handle the slat move mode
        onPointerDown: (event){
          keyFocusNode.requestFocus(); // I don't know why keyboard focus keeps being lost, but this should help fix the problem

          // in move mode, a slat can be moved directly with a click and drag - this detects if a slat is under the pointer when clicked
          if(actionState.slatMode == "Move"){
            final Offset snappedPosition = gridSnap(event.position, appState);
            if (checkCoordinateOccupancy(appState, [appState.convertRealSpacetoCoordinateSpace(snappedPosition)])){
              dragActive = true;  // drag mode is signalled here - panning is now disabled
              slatMoveAnchor = snappedPosition; // the slats to be moved are anchored to the cursor
            }
          }
        },

        onPointerMove: (PointerMoveEvent event){
          // when drag mode is activated, the slat will again follow the cursor (similar to the mouse hover mode)
          if (actionState.slatMode == "Move" && dragActive) {
            setState(() {
              if(hiddenSlats.isEmpty) {
                for (var slat in appState.selectedSlats) {
                  hiddenSlats.add(slat);
                }
              }
              var (localHoverPosition, localHoverValid) = hoverCalculator(event.position, appState, actionState, true);
              hoverPosition = localHoverPosition;
              hoverValid = localHoverValid;
            });
          }
        },
        onPointerUp: (event){
          // drag is always cancelled when the pointer is let go
          if (actionState.slatMode == "Move") {
            setState(() {
              if (hoverValid && dragActive && hoverPosition != null) {
                var convCoordHoverPosition = appState.convertRealSpacetoCoordinateSpace(hoverPosition!);
                var convCoordAnchor = appState.convertRealSpacetoCoordinateSpace(slatMoveAnchor);
                for (var slat in appState.selectedSlats){
                  appState.updateSlatPosition(slat, appState.slats[slat]!.slatPositionToCoordinate.map((key, value) => MapEntry(key, value + convCoordHoverPosition! - convCoordAnchor)));
                }
              }
              dragActive = false;
              hiddenSlats = [];
              hoverPosition = null; // Hide the hovering slat when cursor leaves the grid area
              slatMoveAnchor = Offset.zero;
            });
          }
        },

        // this handles keyboard events (only)
        child: KeyboardListener(
          focusNode: keyFocusNode,
          autofocus: true,
          onKeyEvent: (KeyEvent event) {
            setState(() {
              if (event is KeyDownEvent){
                isShiftPressed = event.logicalKey.keyLabel.contains('Shift');
                if (event.logicalKey.keyLabel.contains('Alt')){
                  appState.rotateLayerDirection(appState.selectedLayerKey);
                }
              }
              else{
                isShiftPressed = false;
              }
              if (event is KeyUpEvent){
                isShiftPressed = false;
              }
            });
          },
          // this handles the hovering function in most modes i.e. having a single slat follow the mouse to indicate where its position will be if dropped
          child: MouseRegion(
            cursor: getCursorForSlatMode(actionState.slatMode),  // TODO: it looks better if the cursor changes when hovering over a slat, rather than always being the same in move mode
            onHover: (event) {
              keyFocusNode.requestFocus();
              if (actionState.slatMode == "Add" || actionState.slatMode == "Delete") {
                setState(() {
                  var (localHoverPosition, localHoverValid) = hoverCalculator(event.position, appState, actionState, false);
                  hoverPosition = localHoverPosition;
                  hoverValid = localHoverValid;
                });
              }
            },
            onExit: (event) {
              setState(() {
                hoverPosition = null; // Hide the hovering slat when cursor leaves the grid area
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
                if (dragActive) {
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
              // this is the actual point a new slat is being added to the system
              onTapDown: (details) {
                keyFocusNode.requestFocus();
                final Offset snappedPosition = gridSnap(details.localPosition, appState);
                if (actionState.slatMode == "Add"){
                  if (!hoverValid) { // cannot place slats if blocked by other slats
                    return;
                  }
                  // slats added to a persistent list here
                  Map<int, Map<int, Offset>> incomingSlats = {};

                  incomingSlats = generateSlatPositions(snappedPosition, false, false, appState);

                  // if not already taken, can proceed to add a new slat
                  appState.clearSelection();
                  appState.addSlats(appState.selectedLayerKey, incomingSlats);
                }
                else if (actionState.slatMode == "Delete"){
                  // slats removed from the persistent list here
                  var coordConvertedPosition = appState.convertRealSpacetoCoordinateSpace(snappedPosition);
                  if (checkCoordinateOccupancy(appState, [coordConvertedPosition])) {
                      appState.removeSlat(appState.occupiedGridPoints[appState.selectedLayerKey]![coordConvertedPosition]!);
                    }
                }
              },

              onTapUp: (TapUpDetails details) {
                keyFocusNode.requestFocus();
                final Offset snappedPosition = appState.convertRealSpacetoCoordinateSpace(gridSnap(details.localPosition, appState));

                if (actionState.slatMode == "Move") {
                  // TODO: on touchpad, the shift click seems to clear the selection instead of add on (probably due to multiple clicks?)

                  if (checkCoordinateOccupancy(appState, [snappedPosition])){
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
              },
              // the custom painter here constantly re-applies the grid and slats to the screen while moving around
              child: Stack(
                children: [
                  CustomPaint(
                    size: Size.infinite,
                    painter: GridPainter(scale, offset, appState.gridSize, appState.gridMode),
                    child: Container(),
                  ),
                  CustomPaint(
                    size: Size.infinite,
                    painter: SlatHoverPainter(
                        scale,
                        offset,
                        appState.layerMap[appState.selectedLayerKey]?['color'],
                        hoverValid,
                        (hoverPosition != null  && actionState.slatMode == "Add") ? generateSlatPositions(hoverPosition!, false, true, appState): {},
                        hoverPosition,
                        !dragActive,
                        appState.selectedSlats.map((e) => appState.slats[e]!).toList(),
                        slatMoveAnchor,
                        appState
                    ),
                    child: Container(),
                  ),
                  CustomPaint(
                    size: Size.infinite,
                    painter: SlatPainter(
                        scale,
                        offset,
                        appState.slats.values.toList(),
                        appState.layerMap,
                        appState.selectedLayerKey,
                        appState.selectedSlats,
                        hiddenSlats,
                        actionState.displayAssemblyHandles,
                        appState),
                    child: Container(),
                  ),
                  CustomPaint(
                    size: Size.infinite,
                    painter: DeletePainter(scale, offset, actionState.slatMode == "Delete" ? hoverPosition: null, appState.gridSize),
                    child: Container(),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}