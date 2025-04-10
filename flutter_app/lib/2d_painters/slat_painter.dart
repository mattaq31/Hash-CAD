import 'package:flutter/material.dart';
import '../crisscross_core/slats.dart';
import 'helper_functions.dart';
import 'package:flutter/foundation.dart';
import 'dart:ui';
import '../app_management/shared_app_state.dart';


/// Custom painter for the slats themselves
class SlatPainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;

  final Map<String, Map<String, dynamic>> layerMap;
  final List<Slat> slats;
  final String selectedLayer;
  final List<String> selectedSlats;
  final List<String> hiddenSlats;
  final bool drawAssemblyHandles;
  final DesignState appState;

  SlatPainter(this.scale, this.canvasOffset, this.slats,
      this.layerMap, this.selectedLayer, this.selectedSlats, this.hiddenSlats,
      this.drawAssemblyHandles, this.appState);


  Offset getRealCoord(Offset slatCoord){
    return appState.convertCoordinateSpacetoRealSpace(slatCoord);
  }

  /// draws a dotted border around a slat when selected
  void drawBorder(Canvas canvas, Slat slat, Color color, Offset slatExtend) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = appState.gridSize / 6
      ..strokeCap = StrokeCap.round;

    final spacing = appState.gridSize / 4;

    // since cos (90 - x) = sin(x) and vice versa
    // the negative sign is included due to the directionality of the grid (up = -ve, left = -ve, down = +ve, right = +ve)
    Offset flippedSlatExtend = Offset(-slatExtend.dy, slatExtend.dx);

    // calculations for these are basically 1.5 extensions away from slat edge, and then 1 extension away in the 90 degree direction to create the border for a slat
    Offset slatP1A = getRealCoord(slat.slatPositionToCoordinate[1]!) - slatExtend * 1.5 + flippedSlatExtend;
    Offset slatP1B = getRealCoord(slat.slatPositionToCoordinate[1]!) - slatExtend * 1.5 - flippedSlatExtend;
    Offset slatP2A = getRealCoord(slat.slatPositionToCoordinate[32]!) + slatExtend * 1.5 - flippedSlatExtend;
    Offset slatP2B = getRealCoord(slat.slatPositionToCoordinate[32]!) + slatExtend * 1.5 + flippedSlatExtend;

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
        ..strokeWidth = appState.gridSize / 2
        ..style = PaintingStyle.fill;
      if (slat.layer != selectedLayer) { // TODO: alpha values can start to overlap when there are loads of layers....
        rodPaint = Paint()
          ..color = layerMap[slat.layer]?['color'].withValues(alpha: 0.2)
          ..strokeWidth = appState.gridSize / 2
          ..style = PaintingStyle.fill;
      }

      var p1 = getRealCoord(slat.slatPositionToCoordinate[1]!);
      var p2 = getRealCoord(slat.slatPositionToCoordinate[32]!);

      Offset slatExtend = calculateSlatExtend(p1, p2, appState.gridSize);

      canvas.drawLine(p1 - slatExtend, p2 + slatExtend, rodPaint);

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

            final position = getRealCoord(slat.slatPositionToCoordinate[i + 1]!);
            final size = appState.gridSize * 0.85; // Adjust size as needed
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
              topBaselineOffset = topTextPainter.computeDistanceToActualBaseline(TextBaseline.alphabetic) ?? 0;
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
