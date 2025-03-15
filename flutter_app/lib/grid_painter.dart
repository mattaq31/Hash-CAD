import 'dart:math';
import 'dart:ui';

import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';

import 'crisscross_core/slats.dart';
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:provider/provider.dart';
import 'crosshatch_shader.dart';
import 'shared_app_state.dart';

/// Class that takes care of painting all 2D objects on the grid, including the grid itself, slats and slat hover effects.
class GridAndCanvas extends StatefulWidget {
  const GridAndCanvas({super.key});

  @override
  State<GridAndCanvas> createState() => _GridAndCanvasState();
}

class _GridAndCanvasState extends State<GridAndCanvas> {

  final double gridSize = 10.0; // Grid cell size (do not change)

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

    // TODO: this is now usable, but I'm sure this can still be optimized
    Set<Offset> occupiedPositions = appState.occupiedGridPoints[appState.selectedLayerKey]?.keys.toSet() ?? {};
    Set<Offset> hiddenPositions = {};

    // hidden slats are not considered for conflicts
    for (var slat in hiddenSlats){
      hiddenPositions.addAll(appState.slats[slat]!.slatPositionToCoordinate.values);
    }

    // Check for conflicts in occupied positions
    for (var coord in coordinates) {
      if (occupiedPositions.contains(coord) && !hiddenPositions.contains(coord)) {
        return true;
      }
    }
    return false;
  }

  /// Function for converting a mouse hover event into a 'snapPosition' and 'hoverValid' flag to be used when pinpointing the current position on the grid.
  (Offset, bool) hoverCalculator(Offset eventPosition, DesignState appState, bool preSelectedSlats){
    // the position is snapped to the nearest grid point
    // the function needs to make sure the global offset/scale
    // due to panning/zooming are taken into account
    Offset snapPosition = Offset(
      (((eventPosition.dx - offset.dx) / scale) / gridSize).round() * gridSize,
      (((eventPosition.dy - offset.dy) / scale) / gridSize).round() * gridSize,
    );

    // check to see if clicked position is taken by a slat already
    bool snapHoverValid = true;

    List<Offset> slatCoordinates = [];
    // TODO: there must be a faster way to get this to run properly...
    if (preSelectedSlats){
      Offset slatOffset =  snapPosition - slatMoveAnchor;
      for (var slat in appState.selectedSlats){
        for (var coord in appState.slats[slat]!.slatPositionToCoordinate.values){
          slatCoordinates.add(coord + slatOffset);
        }
      }
    }
    // preselectedSlats means that the slats are already selected and are being moved
    else {
      for (int j = 0; j < appState.slatAddCount; j++) {
        for (int i = 0; i < 32; i++) {
          // TODO: this eventually needs to be overriden when new angle types are introduced
          if (appState.layerMap[appState.selectedLayerKey]?["direction"] == 'horizontal') {
            slatCoordinates.add(Offset(snapPosition!.dx + i * gridSize,
                snapPosition!.dy + j * gridSize));
          } else {
            slatCoordinates.add(Offset(snapPosition!.dx + j * gridSize,
                snapPosition!.dy + i * gridSize));
          }
        }
      }
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
            final Offset snappedPosition = Offset(
              (((event.position.dx - offset.dx) / scale) / gridSize).round() * gridSize,
              (((event.position.dy - offset.dy) / scale) / gridSize).round() * gridSize);
            if (appState.occupiedGridPoints.containsKey(appState.selectedLayerKey) && appState.occupiedGridPoints[appState.selectedLayerKey]!.keys.contains(snappedPosition)) {
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
              var (localHoverPosition, localHoverValid) = hoverCalculator(event.position, appState, true);
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
                for (var slat in appState.selectedSlats){
                  appState.updateSlatPosition(slat, appState.slats[slat]!.slatPositionToCoordinate.map((key, value) => MapEntry(key, value + hoverPosition! - slatMoveAnchor)));
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
                  appState.rotateLayerDirection();
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
              if (actionState.slatMode == "Add") {
                setState(() {
                  var (localHoverPosition, localHoverValid) = hoverCalculator(event.position, appState, false);
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
                  final newScale =
                  (initialScale * details.scale).clamp(minScale, maxScale);
                  if (newScale == initialScale) {
                    offset = initialPanOffset +
                        (details.focalPoint - initialGestureFocalPoint) / scale;
                  } else {
                    offset = details.focalPoint -
                        (((details.focalPoint - offset) / scale) * newScale);
                  }
                  // TODO: not sure if the fact that pan and zoom cannot be handled simultaneously is a problem... should circle back here if so
                  scale = newScale;
                });
              },
              // this is the actual point a new slat is being added to the system
              onTapDown: (details) {
                keyFocusNode.requestFocus();
                // snap the coordinate to the grid, while taking into account the global offset and scale
                final Offset snappedPosition = Offset(
                  (((details.localPosition.dx - offset.dx) / scale) / gridSize).round() * gridSize,
                  (((details.localPosition.dy - offset.dy) / scale) / gridSize).round() * gridSize,
                );

                if (actionState.slatMode == "Add"){
                  if (!hoverValid) { // cannot place slats if blocked by other slats
                    return;
                  }
                  // slats added to a persistent list here
                  Map<int, Map<int, Offset>> incomingSlats = {};

                  for (int j = 0; j < appState.slatAddCount; j++) {
                    incomingSlats.putIfAbsent(j, () => {});
                    for (int i = 0; i < 32; i++) {
                      if (appState.layerMap[appState.selectedLayerKey]?["direction"] == 'horizontal') {
                        incomingSlats[j]?[i + 1] = Offset(
                            snappedPosition.dx + i * gridSize,
                            snappedPosition.dy + j * gridSize);
                      } else {
                        incomingSlats[j]?[i + 1] = Offset(
                            snappedPosition.dx + j * gridSize,
                            snappedPosition.dy + i * gridSize);
                      }
                    }
                  }
                  // if not already taken, can proceed to add a new slat
                  appState.clearSelection();
                  appState.addSlats(snappedPosition, appState.selectedLayerKey, incomingSlats);
                }
                else if (actionState.slatMode == "Delete"){
                  // slats removed from the persistent list here
                  if (appState.occupiedGridPoints.containsKey(appState.selectedLayerKey) && appState.occupiedGridPoints[appState.selectedLayerKey]!.keys.contains(snappedPosition)) {
                    appState.removeSlat(appState.occupiedGridPoints[appState.selectedLayerKey]![snappedPosition]!);
                  }
                }
              },

              onTapUp: (TapUpDetails details) {
                keyFocusNode.requestFocus();
                final Offset snappedPosition = Offset(
                  (((details.localPosition.dx - offset.dx) / scale) / gridSize).round() * gridSize,
                  (((details.localPosition.dy - offset.dy) / scale) / gridSize).round() * gridSize,
                );
                if (actionState.slatMode == "Move") {
                  // TODO: if this could also be made faster, perhaps using a set, that would be great
                  // TODO: on touchpad, the shift click seems to clear the selection instead of add on (probably due to multiple clicks?)
                  if (appState.occupiedGridPoints
                          .containsKey(appState.selectedLayerKey) &&
                      appState
                          .occupiedGridPoints[appState.selectedLayerKey]!.keys
                          .contains(snappedPosition)) {
                    if (appState.selectedSlats.isNotEmpty && !isShiftPressed) {
                      appState.clearSelection();
                    }
                    // this flips a selection if the slat was already clicked (and pressing shift)
                    appState.selectSlat(appState.occupiedGridPoints[
                        appState.selectedLayerKey]![snappedPosition]!);
                  } else {
                    appState.clearSelection();
                  }
                }
              },
              // the custom painter here constantly re-applies the grid and slats to the screen while moving around
              child: Stack(
                children: [
                  CustomPaint(
                    size: Size.infinite,
                    painter: GridPainter(scale, offset, gridSize),
                    child: Container(),
                  ),
                  CustomPaint(
                    size: Size.infinite,
                    painter: SlatHoverPainter(
                        scale,
                        offset,
                        gridSize,
                        appState.layerMap[appState.selectedLayerKey]?['color'],
                        hoverPosition,
                        appState.layerMap[appState.selectedLayerKey]?['direction'],
                        hoverValid,
                        appState.slatAddCount,
                        appState.selectedSlats.map((e) => appState.slats[e]!).toList(),
                        slatMoveAnchor,
                        !dragActive
                    ),
                    child: Container(),
                  ),
                  CustomPaint(
                    size: Size.infinite,
                    painter: SlatPainter(
                        scale,
                        offset,
                        gridSize,
                        appState.slats.values.toList(),
                        appState.layerMap,
                        appState.selectedLayerKey,
                        appState.selectedSlats,
                        hiddenSlats,
                        actionState.displayAssemblyHandles),
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

/// Custom painter for the grid lines
class GridPainter extends CustomPainter {
  final double gridSize;
  final double scale;
  final Offset canvasOffset;

  GridPainter(this.scale, this.canvasOffset, this.gridSize);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    final Paint majorDotPaint = Paint()
      ..color = Colors.grey[700]!
      ..style = PaintingStyle.fill;

    final Paint minorDotPaint = Paint()
      ..color = Colors.grey[400]!
      ..style = PaintingStyle.fill;

    // Calculate the bounds of the visible area in the grid's coordinate space
    final double left = -canvasOffset.dx / scale;
    final double top = -canvasOffset.dy / scale;
    final double right = left + size.width / scale;
    final double bottom = top + size.height / scale;

    // draws permanent 'grid' area to guide user to a central area
    final Paint rectPaint = Paint()
      ..color = Colors.grey[400]!
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;

    canvas.drawRect(Rect.fromLTWH(-500, -500, 1000, 1000), rectPaint);

    // Draw dots TODO: does this need to be redrawn every time?
    for (double x = (left ~/ gridSize) * gridSize; x < right; x += gridSize) {
      for (double y = (top ~/ gridSize) * gridSize; y < bottom; y += gridSize) {
        if (x % (gridSize * 4) == 0 && y % (gridSize * 4) == 0) {
          // Major dots at grid intersections
          canvas.drawCircle(Offset(x, y), gridSize / 8, majorDotPaint);
        } else {
          // Minor dots between major grid points
          canvas.drawCircle(Offset(x, y), gridSize / 16, minorDotPaint);
        }
      }
    }

    final Paint crosshairPaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 2.0;
    double crosshairSize = 10.0; // Length of crosshair lines
    canvas.drawLine(Offset(-crosshairSize, 0), Offset(crosshairSize, 0), crosshairPaint);
    canvas.drawLine(Offset(0, -crosshairSize), Offset(0, crosshairSize), crosshairPaint);

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant GridPainter oldDelegate) {
    return false;
  }
}

/// Function to calculate the angle of a slat based on its two end points
double calculateSlatAngle(Offset p1, Offset p2) {
  double dx = p2.dx - p1.dx;
  double dy = p2.dy - p1.dy;
  double angle = atan2(dy, dx); // Angle in radians
  return angle;
}

/// Function to calculate the tiny extension outside of the grid on either side of a slat, based on the slat's angle and the grid size.
Offset calculateSlatExtend(Offset p1, Offset p2, double gridSize){
  double slatAngle = calculateSlatAngle(p1, p2);
  double extX = (gridSize/2) * cos(slatAngle);
  double extY = (gridSize/2) * sin(slatAngle);
  return Offset(extX, extY);
}

/// Custom painter for the slat hover display
class SlatHoverPainter extends CustomPainter {
  final double gridSize;
  final double scale;
  final Offset canvasOffset;
  final Color slatColor;
  final Offset? hoverPosition;
  final String direction;
  final bool hoverValid;
  final int slatAddCount;
  final List<Slat> preSelectedSlats;
  final Offset moveAnchor;
  final bool ignorePreSelectedSlats;

  SlatHoverPainter(this.scale, this.canvasOffset, this.gridSize, this.slatColor,
      this.hoverPosition, this.direction, this.hoverValid, this.slatAddCount,
      this.preSelectedSlats, this.moveAnchor, this.ignorePreSelectedSlats);

  @override
  void paint(Canvas canvas, Size size) {

    // usual transformations required to draw on the canvas
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    if (hoverPosition != null) {
      final Paint hoverRodPaint = Paint()
        ..color = slatColor.withValues(alpha: 0.5) // Semi-transparent slat
        ..strokeWidth = gridSize / 2
        ..style = PaintingStyle.fill;

      if (!hoverValid) {  // invalid slat
        hoverRodPaint.shader = CrossHatchShader.shader;
        hoverRodPaint.color = Colors.red;
      }

      // if there are no preset positions, attempt to draw based on layer angle TODO: this needs to be updated with more options
      if (ignorePreSelectedSlats) {
        if (direction == 'vertical') {
          for (int i = 0; i < slatAddCount; i++) {
            canvas.drawLine(
              Offset(hoverPosition!.dx + i * gridSize,
                  hoverPosition!.dy - gridSize / 2),
              Offset(hoverPosition!.dx + i * gridSize,
                  hoverPosition!.dy + gridSize * 31 + gridSize / 2),
              hoverRodPaint,
            );
          }
        } else {
          for (int i = 0; i < slatAddCount; i++) {
            canvas.drawLine(
              Offset(hoverPosition!.dx - gridSize / 2,
                  hoverPosition!.dy + i * gridSize),
              Offset(hoverPosition!.dx + gridSize * 31 + gridSize / 2,
                  hoverPosition!.dy + i * gridSize),
              hoverRodPaint,
            );
          }
        }
      }
      // otherwise, draw hover points based on the anchor and provided coordinates
      else {
        Offset anchorTranslate = hoverPosition! - moveAnchor;
        for (var slat in preSelectedSlats) {
          Offset slatExtend = calculateSlatExtend(slat.slatPositionToCoordinate[1]!, slat.slatPositionToCoordinate[32]!, gridSize);
          canvas.drawLine(slat.slatPositionToCoordinate[1]! - slatExtend + anchorTranslate, slat.slatPositionToCoordinate[32]! + slatExtend + anchorTranslate, hoverRodPaint);
        }
      }
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant SlatHoverPainter oldDelegate) {
    return hoverPosition != oldDelegate.hoverPosition ||
        slatAddCount != oldDelegate.slatAddCount ||
        hoverValid != oldDelegate.hoverValid;
  }
}

/// Custom painter for the slats themselves
class SlatPainter extends CustomPainter {
  final double gridSize;
  final double scale;
  final Offset canvasOffset;

  final Map<String, Map<String, dynamic>> layerMap;
  final List<Slat> slats;
  final String selectedLayer;
  final List<String> selectedSlats;
  final List<String> hiddenSlats;
  final bool drawAssemblyHandles;

  SlatPainter(this.scale, this.canvasOffset, this.gridSize, this.slats,
      this.layerMap, this.selectedLayer, this.selectedSlats, this.hiddenSlats, this.drawAssemblyHandles);

  /// draws a dotted border around a slat when selected
  void drawBorder(Canvas canvas, Slat slat, Color color, Offset slatExtend) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = gridSize / 6
      ..strokeCap = StrokeCap.round;

    final spacing = gridSize / 4;

    // since cos (90 - x) = sin(x) and vice versa
    Offset flippedSlatExtend = Offset(slatExtend.dy, slatExtend.dx);

    // calculations for these are basically 1.5 extensions away from slat edge, and then 1 extension away in the 90 degree direction to create the border for a slat
    Offset slatP1A = slat.slatPositionToCoordinate[1]! - slatExtend * 1.5 + flippedSlatExtend;
    Offset slatP1B = slat.slatPositionToCoordinate[1]! - slatExtend * 1.5 - flippedSlatExtend;
    Offset slatP2A = slat.slatPositionToCoordinate[32]! + slatExtend * 1.5 - flippedSlatExtend;
    Offset slatP2B = slat.slatPositionToCoordinate[32]! + slatExtend * 1.5 + flippedSlatExtend;

    // Function to generate spaced points between two given points
    List<Offset> generateDots(Offset start, Offset end) {
      double distance = (end - start).distance;
      int dotCount = (distance / spacing).floor();
      List<Offset> dots = [];

      for (int i = 1; i <= dotCount; i++) {
        double t = i / (dotCount + 1); // Interpolation factor
        Offset dot = Offset(
          start.dx + (end.dx - start.dx) * t,
          start.dy + (end.dy - start.dy) * t,
        );
        dots.add(dot);
      }
      return dots;
    }

    // Generate dots for all four edges
    List<Offset> dots = [
      ...generateDots(slatP1A, slatP1B),
      ...generateDots(slatP1A, slatP2B),
      ...generateDots(slatP1B, slatP2A),
      ...generateDots(slatP2A, slatP2B),
    ];

    // Draw all dots at once
    canvas.drawPoints(PointMode.points, dots, paint);
  }

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    final isWeb = kIsWeb;

    // TODO: slat draw length should be parametrized
    final sortedSlats = List<Slat>.from(slats)
      ..sort((a, b) => layerMap[a.layer]?['order'].compareTo(layerMap[b.layer]?['order']));

    for (var slat in sortedSlats) {
      if(hiddenSlats.contains(slat.id)){
        continue;
      }
      Paint rodPaint = Paint()
        ..color = layerMap[slat.layer]?['color']
        ..strokeWidth = gridSize / 2
        ..style = PaintingStyle.fill;
      if (slat.layer != selectedLayer) { // TODO: alpha values can start to overlap when there are loads of layers....
        rodPaint = Paint()
          ..color = layerMap[slat.layer]?['color'].withValues(alpha: 0.2)
          ..strokeWidth = gridSize / 2
          ..style = PaintingStyle.fill;
      }

      Offset slatExtend = calculateSlatExtend(slat.slatPositionToCoordinate[1]!, slat.slatPositionToCoordinate[32]!, gridSize);

      canvas.drawLine(slat.slatPositionToCoordinate[1]! - slatExtend, slat.slatPositionToCoordinate[32]! + slatExtend, rodPaint);

      // TODO: H2/H5 position needs to be re-determined when directionality is flipped...
      if (slat.layer == selectedLayer && drawAssemblyHandles) {
        for (int i = 0; i < slat.maxLength; i++) {
          if (slat.h5Handles.containsKey(i + 1) || slat.h2Handles.containsKey(i + 1)) {
            String topText = '↑X';
            String bottomText = '↓X';
            Color topColor = Colors.red;
            Color bottomColor = Colors.red;
            if (slat.h5Handles.containsKey(i + 1)) {
              topText = '↑${slat.h5Handles[i + 1]!["descriptor"]}';
              topColor = Colors.green;
            }
            if (slat.h2Handles.containsKey(i + 1)) {
              bottomText = '↓${slat.h2Handles[i + 1]!["descriptor"]}';
              bottomColor = Colors.green;
            }

            final position = slat.slatPositionToCoordinate[i + 1]!;
            final size = gridSize * 0.85; // Adjust size as needed
            final halfHeight = size / 2;

            final rect_top = Rect.fromCenter(
              center: Offset(position.dx, position.dy - halfHeight/2),
              width: size,
              height: halfHeight,
            );

            final rect_bottom = Rect.fromCenter(
              center: Offset(position.dx, position.dy + halfHeight/2),
              width: size,
              height: halfHeight,
            );

            canvas.drawRect(
              rect_top,
              Paint()
                ..color = topColor
                ..style = PaintingStyle.fill,
            );

            canvas.drawRect(
              rect_bottom,
              Paint()
                ..color = bottomColor
                ..style = PaintingStyle.fill,
            );

            // Draw the top "2"
            final topTextPainter = TextPainter(
              text: TextSpan(
                text: topText,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: halfHeight * 0.8,
                  // Adjust font size to fit half the rectangle
                  fontWeight: FontWeight.bold,
                ),
              ),
              textDirection: TextDirection.ltr,
              textAlign: TextAlign.center,
            );
            topTextPainter.layout();

            double topBaselineOffset;

            if (isWeb){
              topBaselineOffset = topTextPainter.height;
            }
            else{
              topBaselineOffset = topTextPainter.computeDistanceToActualBaseline(TextBaseline.alphabetic) ??0;
            }

            final topOffset = Offset(
              position.dx - topTextPainter.width / 2 - 0.1,
              position.dy - halfHeight + (halfHeight - topBaselineOffset) / 2,
            );
            topTextPainter.paint(canvas, topOffset);

            final bottomTextPainter = TextPainter(
              text: TextSpan(
                text: bottomText,
                style: TextStyle(
                  color: Colors.white,
                  fontFamily: 'Roboto',
                  fontSize: halfHeight * 0.8,
                  fontWeight: FontWeight.bold,
                ),
              ),
              textDirection: TextDirection.ltr,
              textAlign: TextAlign.center,
            );
            bottomTextPainter.layout();

            double bottomBaselineOffset;
            if (isWeb) {
              bottomBaselineOffset = bottomTextPainter.height;
            } else {
              bottomBaselineOffset =
                  bottomTextPainter.computeDistanceToActualBaseline(
                          TextBaseline.alphabetic) ?? 0;
            }

            final bottomOffset = Offset(
              position.dx - bottomTextPainter.width / 2 - 0.1,
              position.dy +
                  halfHeight -
                  (halfHeight + bottomBaselineOffset) / 2,
            );
            bottomTextPainter.paint(canvas, bottomOffset);

            // Draw dividing line
            canvas.drawLine(
              Offset(rect_top.left, position.dy),
              Offset(rect_top.right, position.dy),
              Paint()
                ..color = Colors.white
                ..strokeWidth = 0.5,
            );
          }
        }
      }

      if (selectedSlats.contains(slat.id)) {
        drawBorder(canvas, slat, layerMap[slat.layer]?['color'], slatExtend);
      }
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true; // Always repaint since the slat list might change TODO: can this be smarter?
  }
}
