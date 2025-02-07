import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:provider/provider.dart';
import 'shared_app_state.dart';

class GridAndCanvas extends StatefulWidget {
  const GridAndCanvas({super.key});

  @override
  State<GridAndCanvas> createState() => _GridAndCanvasState();
}

class _GridAndCanvasState extends State<GridAndCanvas> {
  final double gridSize = 10.0; // Grid cell size
  // final List<Offset> slats = []; // List to hold the positions of slats
  final List<Map<String, dynamic>> slats =
      []; // List to hold the positions of slats

  double initialScale = 1.0;
  Offset initialPanOffset = Offset.zero;
  Offset initialGestureFocalPoint = Offset.zero;
  double scale = 1.0;
  double minScale = 0.5;
  double maxScale = 3.0;
  Offset offset = Offset.zero;
  Offset? hoverPosition; // Stores the snapped position of the hovering slat

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
    var calcOffset = event.localPosition - focus * (newScale/scale);

    return (newScale, calcOffset);
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<MyAppState>();

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
          onHover: (event) {
            setState(() {
              // these lines obtain the local position of the mouse pointer
              final RenderBox box = context.findRenderObject() as RenderBox;
              final Offset localPosition = box.globalToLocal(event.position);

              // the position is snapped to the nearest grid point
              // the function needs to make sure the global offset/scale
              // due to panning/zooming are taken into account
              hoverPosition = Offset(
                (((localPosition.dx - offset.dx) / scale) / gridSize).round() *
                    gridSize,
                (((localPosition.dy - offset.dy) / scale) / gridSize).round() *
                    gridSize,
              );
            });
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
                final newScale = (initialScale * details.scale).clamp(minScale, maxScale);
                if (newScale == initialScale){
                  offset = initialPanOffset + (details.focalPoint - initialGestureFocalPoint)/scale;
                }
                else
                  {
                    offset = details.focalPoint - (((details.focalPoint - offset)/scale) * newScale);
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

              // slats added to a persistent list here
              setState(() {
                slats.add({
                  "Position": snappedPosition,
                  "Layer": appState.selectedLayerIndex
                });
              });
            },
            // TODO: make the state management system more concise with less code duplication
            // the custom painter here constantly re-applies the grid and slats to the screen while moving around
            child: Consumer<MyAppState>(
              builder: (context, appState, child) {
                List<Offset> slatPositions =
                    slats.map((slat) => slat["Position"] as Offset).toList();
                List<int> layerIndices =
                    slats.map((slat) => slat["Layer"] as int).toList();
                List<Color> layerColors = layerIndices
                    .map((index) => appState.layerList[index]['color'] as Color)
                    .toList();
                List<String> layerDirections = layerIndices
                    .map((index) =>
                        appState.layerList[index]['direction'] as String)
                    .toList();

                return Stack(
                  children: [
                    CustomPaint(
                      size: Size.infinite,
                      painter: GridPainter(scale, offset, gridSize),
                      child: Container(),
                    ),
                    CustomPaint(
                      size: Size.infinite,
                      painter: SlatPainter(scale, offset, gridSize,
                          slatPositions, layerColors, layerDirections),
                      child: Container(),
                    ),
                    CustomPaint(
                      size: Size.infinite,
                      painter: SlatHoverPainter(
                          scale,
                          offset,
                          gridSize,
                          appState.layerList[appState.selectedLayerIndex] ['color'],
                          hoverPosition,
                          appState.layerList[appState.selectedLayerIndex]['direction']),
                      child: Container(),
                    )
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
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
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true; // Always repaint since the slat list might change
  }
}

class SlatHoverPainter extends CustomPainter {
  final double gridSize;
  final double scale;
  final Offset canvasOffset;
  final Color slatColor;
  final Offset? hoverPosition;
  final String direction;

  SlatHoverPainter(this.scale, this.canvasOffset, this.gridSize, this.slatColor,
      this.hoverPosition, this.direction);

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

      if (direction == 'vertical') {
        canvas.drawLine(
          Offset(hoverPosition!.dx, hoverPosition!.dy - gridSize / 2),
          Offset(hoverPosition!.dx,
              hoverPosition!.dy + gridSize * 32 + gridSize / 2),
          hoverRodPaint,
        );
      } else {
        canvas.drawLine(
          Offset(hoverPosition!.dx - gridSize / 2, hoverPosition!.dy),
          Offset(hoverPosition!.dx + gridSize * 32 + gridSize / 2,
              hoverPosition!.dy),
          hoverRodPaint,
        );
      }
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true; // Always repaint since the slat list might change TODO: can this be smarter?
  }
}

class SlatPainter extends CustomPainter {
  final double gridSize;
  final double scale;
  final Offset canvasOffset;
  final List<Offset> slats;
  final List<Color> slatColors;
  final List<String> directions;

  SlatPainter(this.scale, this.canvasOffset, this.gridSize, this.slats,
      this.slatColors, this.directions);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    // TODO: slat length should be parametrized
    List.generate(slats.length, (i) {
      Paint rodPaint = Paint()
        ..color = slatColors[i]
        ..strokeWidth = gridSize / 2
        ..style = PaintingStyle.fill;

      if (directions[i] == 'vertical') {
        canvas.drawLine(
            Offset(slats[i].dx, slats[i].dy - gridSize / 2),
            Offset(slats[i].dx, slats[i].dy + gridSize * 32 + gridSize / 2),
            rodPaint);
      } else {
        canvas.drawLine(
            Offset(slats[i].dx - gridSize / 2, slats[i].dy),
            Offset(slats[i].dx + gridSize * 32 + gridSize / 2, slats[i].dy),
            rodPaint);
      }
    });

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true; // Always repaint since the slat list might change TODO: can this be smarter?
  }
}
