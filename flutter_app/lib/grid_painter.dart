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
  // List<String> selectedSlats = [];

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
        // this handles the hovering function i.e. having a single slat follow the mouse to indicate where its position will be if dropped
        child: MouseRegion(
          cursor: _getCursorForSlatMode(actionState.slatMode),
          onHover: (event) {
            if (actionState.slatMode == "Add") {
              setState(() {
                // the position is snapped to the nearest grid point
                // the function needs to make sure the global offset/scale
                // due to panning/zooming are taken into account
                hoverPosition = Offset(
                  (((event.position.dx - offset.dx) / scale) / gridSize)
                      .round() *
                      gridSize,
                  (((event.position.dy - offset.dy) / scale) / gridSize)
                      .round() *
                      gridSize,
                );

                // check to see if clicked position is taken by a slat already
                hoverValid = true;

                // TODO: there must be a faster way to get this to run properly...
                List<Offset> slatCoordinates = [];
                for (int j = 0; j < appState.slatAddCount; j++) {
                  for (int i = 0; i < 32; i++) {
                    if (appState.layerList[appState.selectedLayerIndex]
                    ["direction"] ==
                        'horizontal') {
                      slatCoordinates.add(Offset(hoverPosition!.dx + i *
                          gridSize,
                          hoverPosition!.dy + j * gridSize));
                    } else {
                      slatCoordinates.add(Offset(hoverPosition!.dx + j *
                          gridSize,
                          hoverPosition!.dy + i * gridSize));
                    }
                  }
                }
                // TODO: this is now usable, but I'm sure this can still be optimized
                Set<Offset> occupiedPositions = appState
                    .occupiedGridPoints[appState.selectedLayerIndex]?.keys
                    .toSet() ?? {};
                // Check for conflicts in occupied positions
                for (var coord in slatCoordinates) {
                  if (occupiedPositions.contains(coord)) {
                    hoverValid = false;
                    return;
                  }
                }
              });
            }
          },
          onExit: (event) {
            setState(() {
              hoverPosition =
                  null; // Hide the hovering slat when cursor leaves the grid area
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
            onTapUp: (details) {

              // Get tap position on the grid
              final RenderBox box = context.findRenderObject() as RenderBox;
              final Offset localPosition =
                  box.globalToLocal(details.globalPosition);

              // snap the coordinate to the grid, while taking into account the global offset and scale
              final Offset snappedPosition = Offset(
                (((localPosition.dx - offset.dx) / scale) / gridSize).round() *
                    gridSize,
                (((localPosition.dy - offset.dy) / scale) / gridSize).round() *
                    gridSize,
              );

              if (actionState.slatMode == "Add"){
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
                    // TODO: if this could also be made faster, perhaps using a set, that would be great
                    if (appState.occupiedGridPoints.containsKey(appState.selectedLayerIndex) && appState.occupiedGridPoints[appState.selectedLayerIndex]!.keys.contains(incomingSlats[j]?[i + 1])) {
                      return;
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
                      appState.layerList[appState.selectedLayerIndex]
                      ['color'],
                      hoverPosition,
                      appState.layerList[appState.selectedLayerIndex]
                      ['direction'],
                      hoverValid,
                      appState.slatAddCount),
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
                      appState.selectedSlats),
                  child: Container(),
                ),
              ],
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

  SlatHoverPainter(this.scale, this.canvasOffset, this.gridSize, this.slatColor,
      this.hoverPosition, this.direction, this.hoverValid, this.slatAddCount);

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

  SlatPainter(this.scale, this.canvasOffset, this.gridSize, this.slats,
      this.layerList, this.selectedLayer, this.selectedSlats);

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
