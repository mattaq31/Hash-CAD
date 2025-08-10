import 'dart:math';
import 'dart:ui';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../crisscross_core/slats.dart';
import 'helper_functions.dart';
import '../app_management/shared_app_state.dart';
import '../crisscross_core/seed.dart';


bool isColorDark(Color color) {
  // Convert color brightness to 0-255 scale
  double brightness = (color.r * 0.299 + color.g * 0.587 + color.b * 0.114);
  return brightness < 0.5; // You can adjust this threshold if needed
}

drawSlatDrawingAids(Canvas canvas, Offset p1, Offset p2, Offset slatExtend, double gridSize, Paint rodPaint, Color color, double slatAlpha){

  final direction = (p2 - p1).direction;

    // Arrowhead at the end (p2)
    final arrowSize = gridSize * 0.8;
    final arrowAngle = pi / 4.5;
    final arrowP1 = p2 + slatExtend;
    final arrowLeft = arrowP1 - Offset.fromDirection(direction - arrowAngle, arrowSize);
    final arrowRight = arrowP1 - Offset.fromDirection(direction + arrowAngle, arrowSize);

    final arrowPath = Path()
      ..moveTo(arrowP1.dx, arrowP1.dy)
      ..lineTo(arrowLeft.dx, arrowLeft.dy)
      ..lineTo(arrowRight.dx, arrowRight.dy)
      ..close();  // closes the triangle

    final arrowPaint = Paint()
      ..color = rodPaint.color.withValues(alpha: color.a * slatAlpha)
      ..style = PaintingStyle.fill;

    final tailPaint = Paint()
      ..color = rodPaint.color.withValues(alpha: color.a * slatAlpha)
      ..strokeWidth = gridSize / 4
      ..style = PaintingStyle.fill;

    canvas.drawPath(arrowPath, arrowPaint);

    // Tail at the start (p1)
    final tailSize = gridSize * 0.4;
    final tailP1 = p1 - slatExtend * 0.7;
    final tailLeft = tailP1 + Offset.fromDirection(direction - pi / 2, tailSize);
    final tailRight = tailP1 + Offset.fromDirection(direction + pi / 2, tailSize);
    canvas.drawLine(tailLeft, tailRight, tailPaint);

    // Dotted lines at 1/4, 1/2, 3/4
    final dottedPaint = Paint()
      ..color = Colors.black.withValues(alpha: color.a * slatAlpha)
      ..strokeWidth = rodPaint.strokeWidth/4
      ..style = PaintingStyle.stroke;

    final dottedCenterPaint = Paint()
      ..color = Colors.black.withValues(alpha: color.a * slatAlpha)
      ..strokeWidth = rodPaint.strokeWidth/2
      ..style = PaintingStyle.stroke;

    for (final fraction in [0.25, 0.5, 0.75]) {
      final centerPoint = p1 + (p2-p1) * fraction;
      const dashSize = 1.0;
      const gapSize = 1.0;
      final dashCount = 5;
      final totalDashLength = dashSize * dashCount + gapSize * (dashCount - 1);
      final perpDirection = Offset.fromDirection(direction + pi / 2, 1.0);
      final start = centerPoint - perpDirection * (totalDashLength / 2);

      for (int i = 0; i < dashCount; i++) {
        final dStart = start + perpDirection * i.toDouble() * (dashSize + gapSize);
        final dEnd = dStart + perpDirection * dashSize;
        canvas.drawLine(dStart, dEnd, fraction == 0.5 ? dottedCenterPaint : dottedPaint);
      }
    }
}



/// Custom painter for the slats themselves
class SlatPainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;

  final Map<String, Map<String, dynamic>> layerMap;
  final List<Slat> slats;
  final String selectedLayer;
  final List<String> selectedSlats;
  final List<String> hiddenSlats;
  final ActionState actionState;
  final DesignState appState;
  late Map<int, TextPainter> labelPainters;


  SlatPainter(this.scale, this.canvasOffset, this.slats,
      this.layerMap, this.selectedLayer, this.selectedSlats, this.hiddenSlats,
      this.actionState, this.appState){

    labelPainters = <int, TextPainter>{};
    TextStyle textStyle = TextStyle(
      color: Colors.black,
      fontFamily: 'Roboto',
      fontWeight: FontWeight.bold,
      fontSize: appState.gridSize * 0.4, // small enough for grid point
    );

    TextStyle textStyleLight = TextStyle(
      color: Colors.white,
      fontFamily: 'Roboto',
      fontWeight: FontWeight.bold,
      fontSize: appState.gridSize * 0.4, // small enough for grid point
    );

    for (int i = 1; i <= 64; i++) {
      TextSpan textSpan = TextSpan(text: i < 33 ? '$i' : '${i-32}', style: i < 33 ? textStyle : textStyleLight);
      TextPainter textPainter = TextPainter(
        text: textSpan,
        textAlign: TextAlign.center,
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();
      labelPainters[i] = textPainter;
    }
  }


  Offset getRealCoord(Offset slatCoord){
    return appState.convertCoordinateSpacetoRealSpace(slatCoord);
  }

  /// draws a dotted border around a slat when selected
  void drawBorder(Canvas canvas, Slat slat, Color color, Offset slatExtend, bool slatTipExtended) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = appState.gridSize / 6
      ..strokeCap = StrokeCap.round;

    final spacing = appState.gridSize / 4;

    Offset flippedSlatExtend;

    if (appState.gridMode == '60'){
      // for the 60 degree system, the slats are extended out by 90 degrees from their positions (since they are rectangular).
      // Their angle doesn't exactly match the grid angle, and so the spacing between slats is not precisely gridSize/2.
      // If you calculate the geometry (assuming parallel lines), the actual distance between slats is instead gridSize * sqrt(3)/2 i.e. sin 60deg.
      Offset interSlatExtend = calculateSlatExtend(getRealCoord(slat.slatPositionToCoordinate[1]!), getRealCoord(slat.slatPositionToCoordinate[32]!), appState.gridSize * sqrt(3)/2);

      // since cos (90 - x) = sin(x) and vice versa
      // the negative sign is included due to the directionality of the grid (up = -ve, left = -ve, down = +ve, right = +ve)
      flippedSlatExtend = Offset(-interSlatExtend.dy, interSlatExtend.dx);
    }
    else {
      // since cos (90 - x) = sin(x) and vice versa
      // the negative sign is included due to the directionality of the grid (up = -ve, left = -ve, down = +ve, right = +ve)
      flippedSlatExtend = Offset(-slatExtend.dy, slatExtend.dx);
    }


    // calculations for these are basically 1.5 extensions away from slat edge, and then 1 extension away in the 90 degree direction to create the border for a slat
    // if tip extensions are off, then it's just 0.5 extensions away from the slat edge
    double tipExtension;
    if (slatTipExtended) {
      tipExtension = 1.5;
    } else {
      tipExtension = 0.5;
    }

    Offset slatP1A = getRealCoord(slat.slatPositionToCoordinate[1]!) - slatExtend * tipExtension + flippedSlatExtend;
    Offset slatP1B = getRealCoord(slat.slatPositionToCoordinate[1]!) - slatExtend * tipExtension - flippedSlatExtend;
    Offset slatP2A = getRealCoord(slat.slatPositionToCoordinate[32]!) + slatExtend * tipExtension - flippedSlatExtend;
    Offset slatP2B = getRealCoord(slat.slatPositionToCoordinate[32]!) + slatExtend * tipExtension + flippedSlatExtend;

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

    // current viewport bounds
    final visibleRect = Rect.fromLTWH(
      -canvasOffset.dx / scale,
      -canvasOffset.dy / scale,
      size.width / scale,
      size.height / scale,
    );

    final isWeb = kIsWeb;

    // TODO: slat draw length should be parametrized
    final sortedSlats = List<Slat>.from(slats)
      ..sort((a, b) => layerMap[a.layer]?['order'].compareTo(layerMap[b.layer]?['order']));

    String selectedLayerTopside = (layerMap[selectedLayer]?['top_helix'] == 'H5') ? 'H5' : 'H2';

    for (var slat in sortedSlats) {
      if (hiddenSlats.contains(slat.id)){
        continue;
      }
      if (layerMap[slat.layer]?['hidden']) {
        continue;
      }

      Color mainColor = slat.uniqueColor ?? layerMap[slat.layer]?['color'];

      if (actionState.isolateSlatLayerView && slat.layer != selectedLayer) {
        continue;
      }

      Paint rodPaint = Paint()
        ..color = mainColor
        ..strokeWidth = appState.gridSize / 2
        ..style = PaintingStyle.fill;
      if (slat.layer != selectedLayer) {
        rodPaint = Paint()
          ..color = mainColor.withValues(alpha: mainColor.a * 0.2)
          ..strokeWidth = appState.gridSize / 2
          ..style = PaintingStyle.fill;
      }

      var p1 = getRealCoord(slat.slatPositionToCoordinate[1]!);
      var p2 = getRealCoord(slat.slatPositionToCoordinate[32]!);

      Offset slatExtend = calculateSlatExtend(p1, p2, appState.gridSize);

      // if slat out of the visible rectangle, can skip drawing to speed up rendering
      final slatBounds = Rect.fromPoints(p1, p2).inflate(appState.gridSize * 1.5);
      if (!slatBounds.overlaps(visibleRect)) {
        continue; // skip drawing this slat
      }

      if (actionState.drawingAids){
        canvas.drawLine(p1 - slatExtend * 0.5, p2, rodPaint);
      }
      else {
        if (!actionState.extendSlatTips){
          canvas.drawLine(p1, p2, rodPaint);
        }
        else {
          canvas.drawLine(p1 - slatExtend, p2 + slatExtend, rodPaint);
        }
      }

      if (actionState.drawingAids){
        drawSlatDrawingAids(canvas, p1, p2, slatExtend, appState.gridSize, rodPaint, mainColor, slat.layer != selectedLayer ? 0.2 : 1.0);
      }

      // Draw slat position numbers if activated
      if (slat.layer == selectedLayer && actionState.slatNumbering) {
        bool isDark = isColorDark(mainColor);
        for (int i = 1; i <= 32; i++) {
          final slatCoord = getRealCoord(slat.slatPositionToCoordinate[i]!);
          final labelPainter = labelPainters[!isDark ? i : i + 32];
          if (labelPainter == null) continue;

          final textOffset = Offset(
            slatCoord.dx - labelPainter.width / 2,
            slatCoord.dy - labelPainter.height / 2,
          );

          labelPainter.paint(canvas, textOffset);
        }
      }

      if (slat.layer == selectedLayer && (actionState.displayAssemblyHandles || actionState.displayCargoHandles)) {
        for (int i = 0; i < slat.maxLength; i++) {
          final int handleIndex = i + 1;
          final h5 = slat.h5Handles[handleIndex];
          final h2 = slat.h2Handles[handleIndex];
          if (h5 == null && h2 == null) continue;

          Set<String> categoriesPresent = {
            if (h5 != null) h5["category"],
            if (h2 != null) h2["category"],
          };

          // the below controls the logic and formatting for placing handle markers on slats
          if ((actionState.displayAssemblyHandles && (categoriesPresent.contains('ASSEMBLY_HANDLE') || categoriesPresent.contains('ASSEMBLY_ANTIHANDLE'))) || (actionState.displayCargoHandles && (categoriesPresent.contains('CARGO') || categoriesPresent.contains('SEED')))) {
            String topText = '↑X';
            String bottomText = '↓X';
            Color topColor = Colors.grey;
            Color bottomColor = Colors.grey;
            String topCategory = '';
            String bottomCategory = '';
            bool topValid = true;
            bool bottomValid = true;

            void updateHandleData(Map<String, dynamic> handle, String side, int sideName) {
              final category = handle["category"];
              final descriptor = handle["value"];
              final isTop = side == "top";

              String shortText = descriptor;
              Color color = Colors.grey;

              if(actionState.plateValidation){
                if (isTop){
                  topValid = !slat.checkPlaceholder(handleIndex, sideName);
                }
                else{
                  bottomValid = !slat.checkPlaceholder(handleIndex, sideName);
                }
              }

              if (category == 'CARGO') {
                shortText = appState.cargoPalette[descriptor]?.shortName ?? descriptor;
                color = appState.cargoPalette[descriptor]?.color ?? Colors.grey;
              } else if (category.contains('ASSEMBLY')) {
                color = Colors.green;
              } else if (category == 'SEED') {
                color = appState.cargoPalette['SEED']!.color;
                shortText = '🌱${getIndexFromSeedText(descriptor)}';
              }

              if (isTop) {
                topText = category == 'SEED' ? shortText :'↑$shortText';
                topColor = color;
                topCategory = category;
              } else {
                bottomText = category == 'SEED' ? shortText :'↓$shortText';
                bottomColor = color;
                bottomCategory = category;
              }
            }

            if (h5 != null  && h5['category'] != 'FLAT') {
              final side = selectedLayerTopside == 'H5' ? 'top' : 'bottom';
              updateHandleData(h5, side, 5);
            }
            if (h2 != null && h2['category'] != 'FLAT') {
              final side = selectedLayerTopside == 'H2' ? 'top' : 'bottom';
              updateHandleData(h2, side, 2);
            }

            final position = getRealCoord(slat.slatPositionToCoordinate[handleIndex]!);
            final size = appState.gridSize * 0.85;
            final halfHeight = size / 2;

            // Check if the handle marker is within the visible rectangle
            final handleRect = Rect.fromCenter(center: position, width: size, height: size);
            if (!handleRect.overlaps(visibleRect)) {
              continue; // Skip drawing this handle marker if not visible
            }

            final rectTop = Rect.fromCenter(
              center: Offset(position.dx, position.dy - halfHeight / 2),
              width: size,
              height: halfHeight,
            );

            final rectBottom = Rect.fromCenter(
              center: Offset(position.dx, position.dy + halfHeight / 2),
              width: size,
              height: halfHeight,
            );

            void drawHandleMarker(Rect rect, Color color, String category, bool isTop) {
              final paint = Paint()..color = color..style = PaintingStyle.fill;
              if (category == 'UNUSED') { // not doing triangles for now
                final path = Path();
                final centerX = rect.center.dx;
                final topY = rect.top;
                final bottomY = rect.bottom;

                if (isTop) {
                  path.moveTo(centerX, topY); // Top center
                  path.lineTo(rect.left, bottomY); // Bottom left
                  path.lineTo(rect.right, bottomY); // Bottom right
                } else {
                  path.moveTo(centerX, bottomY); // Bottom center
                  path.lineTo(rect.left, topY); // Top left
                  path.lineTo(rect.right, topY); // Top right
                }
                path.close();
                canvas.drawPath(path, paint);
              } else {
                canvas.drawRect(rect, paint);
              }

              final isInvalid = (isTop && !topValid) || (!isTop && !bottomValid);

              // Draw dotted red border if invalid
              if (isInvalid) {
                final dotPaint = Paint()
                  ..color = Colors.red
                  ..style = PaintingStyle.stroke
                  ..strokeWidth = 1.0;

                const double dotLength = 0.5;
                const double gapLength = 0.5;

                void drawDottedLine(Offset start, Offset end) {
                  final totalLength = (end - start).distance;
                  final offset = end - start;
                  final direction = offset / offset.distance;

                  double drawn = 0;
                  while (drawn < totalLength) {
                    final currentStart = start + direction * drawn;
                    final currentEnd = start + direction * (drawn + dotLength).clamp(0, totalLength);

                    canvas.drawLine(currentStart, currentEnd, dotPaint);
                    drawn += dotLength + gapLength;
                  }
                }

                // Draw all 4 sides with dots
                drawDottedLine(rect.topLeft, rect.topRight);
                drawDottedLine(rect.topRight, rect.bottomRight);
                drawDottedLine(rect.bottomRight, rect.bottomLeft);
                drawDottedLine(rect.bottomLeft, rect.topLeft);
              }
            }

            drawHandleMarker(rectTop, topColor, topCategory, true);
            drawHandleMarker(rectBottom, bottomColor, bottomCategory, false);

            void drawText(String text, Offset offset, double fontSize) {
              final textPainter = TextPainter(
                text: TextSpan(
                  text: text,
                  style: TextStyle(
                    color: Colors.white,
                    fontFamily: 'Roboto',
                    fontSize: fontSize,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                textDirection: TextDirection.ltr,
                textAlign: TextAlign.center,
              );
              textPainter.layout();
              final baselineOffset = textPainter.height;
              final actualOffset = Offset(
                offset.dx - textPainter.width / 2 - 0.1,
                offset.dy - baselineOffset / 2 + 0.3,
              );
              textPainter.paint(canvas, actualOffset);
            }

            drawText(topText, Offset(position.dx, position.dy - halfHeight / 2), halfHeight * 0.8);
            drawText(bottomText, Offset(position.dx, position.dy + halfHeight / 2), halfHeight * 0.8);

            canvas.drawLine(
              Offset(rectTop.left, position.dy),
              Offset(rectTop.right, position.dy),
              Paint()..color = Colors.white..strokeWidth = 0.5,
            );
          }
        }
      }

      // displays slat IDs as an overlay on top of the slat
      if (actionState.displaySlatIDs && slat.layer == selectedLayer){
        final textPainter = TextPainter(
          text: TextSpan(
            text: slat.id.replaceFirst('-I', '-'),
            style: TextStyle(
              color: Colors.white,
              fontFamily: 'Roboto',
              fontSize: appState.gridSize * 0.6,
              fontWeight: FontWeight.bold,
            ),
          ),
          textDirection: TextDirection.ltr,
          textAlign: TextAlign.center
        );
        textPainter.layout();

        double baselineOffset;
        if (isWeb || defaultTargetPlatform == TargetPlatform.windows) {
          baselineOffset = textPainter.height + 0.5;
        } else {
          baselineOffset = textPainter.computeDistanceToActualBaseline(TextBaseline.alphabetic) ?? 0;
        }

        Offset centerExtend = calculateSlatExtend(p1, p2, 2 * (appState.gridSize * 32 / 2 - appState.gridSize / 2));
        Offset center = Offset(
          p1.dx + centerExtend.dx,
          p1.dy + centerExtend.dy,
        );

        canvas.save();
        canvas.translate(center.dx, center.dy);

        double angle = calculateSlatAngle(p1, p2);
        // Flip upside-down labels
        if (angle > pi / 2 || angle < -pi / 2) {
          angle += pi;
        }
        canvas.rotate(angle);

        final baseRect = Rect.fromCenter(
          center: Offset.zero,
          width: appState.gridSize * 2,
          height: appState.gridSize * 0.85,
        );

        final textOffset = Offset(
          - textPainter.width / 2 - 0.1,
          - baselineOffset / 2 - 0.9,
        );

        canvas.drawRect(
          baseRect,
          Paint()
            ..color = Colors.black
            ..style = PaintingStyle.fill,
        );
        textPainter.paint(canvas, textOffset);
        canvas.restore();
      }

      if (selectedSlats.contains(slat.id)) {
        drawBorder(canvas, slat, mainColor, slatExtend, (actionState.drawingAids || actionState.extendSlatTips));
      }
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant SlatPainter oldDelegate) {
    return oldDelegate.scale != scale ||
        oldDelegate.canvasOffset != canvasOffset ||
        oldDelegate.slats != slats ||  // Consider using `identical()` or custom equality
        oldDelegate.selectedLayer != selectedLayer ||
        !listEquals(oldDelegate.selectedSlats, selectedSlats) ||
        !listEquals(oldDelegate.hiddenSlats, hiddenSlats) ||
        oldDelegate.actionState != actionState ||
        oldDelegate.appState != appState;
  }
}
