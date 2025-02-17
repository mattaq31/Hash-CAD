import 'dart:ui';

import 'package:flutter/services.dart';

import 'crisscross_core/slats.dart';
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:provider/provider.dart';
import 'crosshatch_shader.dart';
import 'shared_app_state.dart';

class GridAndCanvas extends StatefulWidget {
  const GridAndCanvas({super.key});

  @override
  State<GridAndCanvas> createState() => _GridAndCanvasState();
}

class _GridAndCanvasState extends State<GridAndCanvas> {
  final double gridSize = 10.0; // Grid cell size
  double initialScale = 1.0;
  Offset initialPanOffset = Offset.zero;
  Offset initialGestureFocalPoint = Offset.zero;
  double scale = 1.0;
  double minScale = 0.5;
  double maxScale = 3.0;
  Offset offset = Offset.zero;
  Offset? hoverPosition; // Stores the snapped position of the hovering slat
  bool hoverValid = true;
  bool dragActive = false;
  bool isShiftPressed = false;
  Offset slatMoveAnchor = Offset.zero;
  final FocusNode keyFocusNode = FocusNode(); // Persistent focus node
  List<String> hiddenSlats = [];

  /// Function for converting a mouse zoom event into a 'scale' and 'offset' to be used when pinpointing the current position on the grid.
  /// 'zoomFactor' affects the scroll speed (higher is slower).
  (double, Offset) scrollZoomCalculator(PointerScrollEvent event,
      {double zoomFactor = 0.1}) {
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
    else {
      for (int j = 0; j < appState.slatAddCount; j++) {
        for (int i = 0; i < 32; i++) {
          if (appState.layerList[appState.selectedLayerIndex]["direction"] ==
              'horizontal') {
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

  bool checkCoordinateOccupancy(DesignState appState, List<Offset> coordinates){

    // TODO: this is now usable, but I'm sure this can still be optimized
    Set<Offset> occupiedPositions = appState.occupiedGridPoints[appState.selectedLayerIndex]?.keys.toSet() ?? {};
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


  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();

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
        // the following three event handlers are specifically setup to handle the move mode
        onPointerDown: (event){
          // in move mode, a slat can be moved directly with a click and drag - this detects if a slat is under the pointer when clicked
          if(actionState.slatMode == "Move"){
            final Offset snappedPosition = Offset(
              (((event.position.dx - offset.dx) / scale) / gridSize).round() *
                  gridSize,
              (((event.position.dy - offset.dy) / scale) / gridSize).round() *
                  gridSize,
            );
            if (appState.occupiedGridPoints.containsKey(appState.selectedLayerIndex) && appState.occupiedGridPoints[appState.selectedLayerIndex]!.keys.contains(snappedPosition)) {
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
              if (hoverValid && dragActive){
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
              }
              else{
                isShiftPressed = false;
              }
            });
          },
          // this handles the hovering function in most modes i.e. having a single slat follow the mouse to indicate where its position will be if dropped
          child: MouseRegion(
            cursor: _getCursorForSlatMode(actionState.slatMode),  // TODO: it looks better if the cursor changes when hovering over a slat, rather than always being the same in move mode
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
              // this is the actual point a slat is added to the system
              onTapDown: (details) {

                // snap the coordinate to the grid, while taking into account the global offset and scale
                final Offset snappedPosition = Offset(
                  (((details.localPosition.dx - offset.dx) / scale) / gridSize).round() *
                      gridSize,
                  (((details.localPosition.dy - offset.dy) / scale) / gridSize).round() *
                      gridSize,
                );

                if (actionState.slatMode == "Add"){

                  if (!hoverValid) { // cannot place slats if blocked by other slats
                    return;
                  }

                  // slats added to a persistent list here
                  Map<int, Map<int, Offset>> incomingSlats = {};
                  // Map<int, Offset> slatCoordinates = {};
                  for (int j = 0; j < appState.slatAddCount; j++) {
                    incomingSlats.putIfAbsent(j, () => {});
                    for (int i = 0; i < 32; i++) {
                      if (appState.layerList[appState.selectedLayerIndex]
                      ["direction"] ==
                          'horizontal') {
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
                  appState.addSlats(snappedPosition, appState.selectedLayerIndex, incomingSlats);
                }
                else if (actionState.slatMode == "Delete"){
                  // slats removed from the persistent list here
                  if (appState.occupiedGridPoints.containsKey(appState.selectedLayerIndex) && appState.occupiedGridPoints[appState.selectedLayerIndex]!.keys.contains(snappedPosition)) {
                    appState.removeSlat(appState.occupiedGridPoints[appState.selectedLayerIndex]![snappedPosition]!);
                  }
                }
                else if (actionState.slatMode == "Move") {
                  // TODO: if this could also be made faster, perhaps using a set, that would be great
                  if (appState.occupiedGridPoints.containsKey(appState.selectedLayerIndex) && appState.occupiedGridPoints[appState.selectedLayerIndex]!.keys.contains(snappedPosition)) {
                    if (appState.selectedSlats.isNotEmpty && !isShiftPressed){
                      appState.clearSelection();
                    }
                    appState.selectSlat(appState.occupiedGridPoints[appState.selectedLayerIndex]![snappedPosition]!);
                  }
                  else{
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
                        appState.layerList[appState.selectedLayerIndex]['color'],
                        hoverPosition,
                        appState.layerList[appState.selectedLayerIndex]['direction'],
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
                        appState.layerList,
                        appState.selectedLayerIndex,
                        appState.selectedSlats,
                        hiddenSlats),
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

SystemMouseCursor _getCursorForSlatMode(String slatMode) {
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
      ..color = Colors.grey[300]!
      ..style = PaintingStyle.fill;

    // Calculate the bounds of the visible area in the grid's coordinate space
    final double left = -canvasOffset.dx / scale;
    final double top = -canvasOffset.dy / scale;
    final double right = left + size.width / scale;
    final double bottom = top + size.height / scale;

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
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant GridPainter oldDelegate) {
    return false;
  }
}

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
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);
    // Draw the hovering slat
    if (hoverPosition != null) {
      final Paint hoverRodPaint = Paint()
        ..color = slatColor.withValues(alpha: 0.5) // Semi-transparent slat
        ..strokeWidth = gridSize / 2
        ..style = PaintingStyle.fill;

      if (!hoverValid) {
        hoverRodPaint.shader = CrossHatchShader.shader;
        hoverRodPaint.color = Colors.red;
      }

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
      } else {
        Offset anchorTranslate = hoverPosition! - moveAnchor;
        // I should draw a line for each selected Slat, starting from the first coordinate in each slat
        // a new paint style is not needed!
        for (var slat in preSelectedSlats) {
          if (direction == 'vertical') {
            canvas.drawLine(
              Offset(
                  slat.slatPositionToCoordinate[1]!.dx + anchorTranslate.dx,
                  slat.slatPositionToCoordinate[1]!.dy +anchorTranslate.dy - gridSize / 2),
              Offset(
                  slat.slatPositionToCoordinate[1]!.dx + anchorTranslate.dx,
                  slat.slatPositionToCoordinate[1]!.dy + anchorTranslate.dy + gridSize * 31 + gridSize / 2),
              hoverRodPaint,
            );
          } else {
            canvas.drawLine(
              Offset(
                  slat.slatPositionToCoordinate[1]!.dx + anchorTranslate.dx - gridSize / 2,
                  slat.slatPositionToCoordinate[1]!.dy + anchorTranslate.dy),
              Offset(
                  slat.slatPositionToCoordinate[1]!.dx + anchorTranslate.dx + gridSize * 31 + gridSize / 2,
                  slat.slatPositionToCoordinate[1]!.dy + anchorTranslate.dy),
              hoverRodPaint,
            );
          }
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

class SlatPainter extends CustomPainter {
  final double gridSize;
  final double scale;
  final Offset canvasOffset;

  final List<Map<String, dynamic>> layerList;
  final List<Slat> slats;
  final int selectedLayer;
  final List<String> selectedSlats;
  final List<String> hiddenSlats;

  SlatPainter(this.scale, this.canvasOffset, this.gridSize, this.slats,
      this.layerList, this.selectedLayer, this.selectedSlats, this.hiddenSlats);

  void drawBorder(Canvas canvas, Slat slat, Color color) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = gridSize / 6
      ..strokeCap = StrokeCap.round;

    final spacing = gridSize / 4;

    if (layerList[slat.layer]['direction'] == 'vertical') {
      final startY = slat.slatPositionToCoordinate[1]!.dy - gridSize / 2;
      final endY = slat.slatPositionToCoordinate[32]!.dy + gridSize / 2;
      final x = slat.slatPositionToCoordinate[1]!.dx;

      // Draw dots along vertical sides
      for (double y = startY; y <= endY; y += spacing) {
        canvas.drawPoints(
            PointMode.points,
            [
              Offset(x - gridSize / 2, y), // Left side
              Offset(x + gridSize / 2, y), // Right side
            ],
            paint);
      }

      // Draw dots along horizontal ends
      for (double dx = -gridSize / 4; dx <= gridSize / 4; dx += spacing) {
        canvas.drawPoints(
            PointMode.points,
            [
              Offset(x + dx, startY - gridSize / 4), // Top end
              Offset(x + dx, endY + gridSize / 4), // Bottom end
            ],
            paint);
      }
    } else {
      final startX = slat.slatPositionToCoordinate[1]!.dx - gridSize / 2;
      final endX = slat.slatPositionToCoordinate[32]!.dx + gridSize / 2;
      final y = slat.slatPositionToCoordinate[1]!.dy;

      // Draw dots along horizontal sides
      for (double x = startX; x <= endX; x += spacing) {
        canvas.drawPoints(
            PointMode.points,
            [
              Offset(x, y - gridSize / 2), // Top side
              Offset(x, y + gridSize / 2), // Bottom side
            ],
            paint);
      }

      // Draw dots along vertical ends
      for (double dy = -gridSize / 4; dy <= gridSize / 4; dy += spacing) {
        canvas.drawPoints(
            PointMode.points,
            [
              Offset(startX - gridSize / 4, y + dy), // Left end
              Offset(endX + gridSize / 4, y + dy), // Right end
            ],
            paint);
      }
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    // TODO: slat draw length should be parametrized

    final sortedSlats = List<Slat>.from(slats)
      ..sort((a, b) =>
          layerList[a.layer]['order'].compareTo(layerList[b.layer]['order']));

    for (var slat in sortedSlats) {
      if(hiddenSlats.contains(slat.id)){
        continue;
      }
      Paint rodPaint = Paint()
        ..color = layerList[slat.layer]['color']
        ..strokeWidth = gridSize / 2
        ..style = PaintingStyle.fill;
      if (slat.layer != selectedLayer) {
        rodPaint = Paint()
          ..color = layerList[slat.layer]['color'].withValues(alpha: 0.5)
          ..strokeWidth = gridSize / 2
          ..style = PaintingStyle.fill;
      }

      if (layerList[slat.layer]['direction'] == 'vertical') {
        canvas.drawLine(
            Offset(slat.slatPositionToCoordinate[1]!.dx,
                slat.slatPositionToCoordinate[1]!.dy - gridSize / 2),
            Offset(slat.slatPositionToCoordinate[32]!.dx,
                slat.slatPositionToCoordinate[32]!.dy + gridSize / 2),
            rodPaint);
      } else {
        canvas.drawLine(
            Offset(slat.slatPositionToCoordinate[1]!.dx - gridSize / 2,
                slat.slatPositionToCoordinate[1]!.dy),
            Offset(slat.slatPositionToCoordinate[32]!.dx + gridSize / 2,
                slat.slatPositionToCoordinate[32]!.dy),
            rodPaint);
      }
      if (selectedSlats.contains(slat.id)) {
        drawBorder(canvas, slat, layerList[slat.layer]['color']);
      }
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true; // Always repaint since the slat list might change TODO: can this be smarter?
  }
}
