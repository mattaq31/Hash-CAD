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

void drawSlat(List<Offset> coords, Canvas canvas, DesignState appState, ActionState actionState, Paint slatPaint, bool phantomSlat){
  /// Paints a slat and takes care of adjustments such as drawing aids, tip extensions, etc.

  Offset slatExtendFront = calculateSlatExtend(coords[0], coords[1], appState.gridSize);
  Offset slatExtendBack = calculateSlatExtend(coords[coords.length - 2], coords.last, appState.gridSize);

  // Build path from the coordinate sequence
  final path = Path(); // TODO: what happens here when there are layer-bridging slats?

  // draws beginning of slat path here
  if (actionState.drawingAids){
    path.moveTo(coords[0].dx - slatExtendFront.dx * 0.5, coords[0].dy - slatExtendFront.dy * 0.5);
  }
  else{
    if (!actionState.extendSlatTips){
      path.moveTo(coords[0].dx, coords[0].dy);
    }
    else{
      path.moveTo(coords[0].dx - slatExtendFront.dx, coords[0].dy - slatExtendFront.dy);
    }
  }
  for (int i = 1; i < coords.length; i++) {
    path.lineTo(coords[i].dx, coords[i].dy);
  }
  if (!actionState.drawingAids && actionState.extendSlatTips){
    path.lineTo(coords.last.dx + slatExtendBack.dx, coords.last.dy + slatExtendBack.dy);
  }

  if (phantomSlat) {
    final color = slatPaint.color;
    final hsl = HSLColor.fromColor(color);
    final hatchColor = isColorDark(color)
        ? hsl.withLightness((hsl.lightness + 0.3).clamp(0.0, 1.0)).toColor()
        : hsl.withLightness((hsl.lightness - 0.3).clamp(0.0, 1.0)).toColor();

    // Use a fraction of gridSize to determine stripe density
    final double patternSize = appState.gridSize / 6;
    final double angle = calculateSlatAngle(coords.first, coords[1]);

    slatPaint.shader = LinearGradient(
      begin: Alignment.centerLeft,
      end: Alignment.centerRight,
      colors: [
        color,
        color,
        hatchColor,
        hatchColor,
      ],
      stops: const [0.0, 0.5, 0.5, 1.0],
      tileMode: TileMode.repeated,
      transform: GradientRotation(angle),
    ).createShader(Rect.fromLTWH(0, 0, patternSize, patternSize));
  }

  // draws final path here
  canvas.drawPath(path, slatPaint);

  if (actionState.drawingAids) {
    drawSlatDrawingAids(
        canvas,
        coords,
        slatExtendFront,
        slatExtendBack,
        appState.gridSize,
        slatPaint,
        slatPaint.color,
        1.0);
  }
}


void drawSlatDrawingAids(Canvas canvas, List coords, Offset slatExtendFront, Offset slatExtendBack, double gridSize, Paint rodPaint, Color color, double slatAlpha){

  // different directions calculated as this can change throughout a customized non-rod slat
  final arrowDirection = (coords.last - coords[coords.length - 2]).direction;
  final tailDirection = (coords[1] - coords.first).direction;

  // Arrowhead at the end
  final arrowSize = gridSize * 0.8;
  final arrowAngle = pi / 4.5;
  final arrowP1 = coords.last + slatExtendBack;
  final arrowLeft = arrowP1 - Offset.fromDirection(arrowDirection - arrowAngle, arrowSize);
  final arrowRight = arrowP1 - Offset.fromDirection(arrowDirection + arrowAngle, arrowSize);

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

  // Tail at the start
  final tailSize = gridSize * 0.4;
  final tailP1 = coords.first - slatExtendFront * 0.7;
  final tailLeft = tailP1 + Offset.fromDirection(tailDirection - pi / 2, tailSize);
  final tailRight = tailP1 + Offset.fromDirection(tailDirection + pi / 2, tailSize);
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

  // dash parameters
  const dashSize = 1.0;
  const gapSize = 1.0;
  final dashCount = 5;

  //  calculate and apply dotted lines at 1/4, 1/2, 3/4 of the slat length
  for (final fraction in [4, 2, 1.3333333]) {
    Offset? middle;
    List<Offset>? middlePair;
    Offset? centerPoint;
    double fracDirection;

    // if odd handle count, there should be a single middle point
    if (coords.length.isOdd){
      middle = coords[coords.length ~/ fraction];
      fracDirection = (coords[(coords.length ~/ fraction) + 1] - coords[(coords.length ~/ fraction) - 1]).direction;
      centerPoint = middle;
    }
    // if even handle count, need to find surrounding middle handle pair
    else{
      middlePair = [
        coords[(coords.length ~/ fraction) - 1],
        coords[coords.length ~/ fraction],
      ];
      fracDirection = (middlePair[1] - middlePair[0]).direction;
      centerPoint = (middlePair[0] + middlePair[1]) / 2;
    }

    final totalDashLength = dashSize * dashCount + gapSize * (dashCount - 1);
    final perpDirection = Offset.fromDirection(fracDirection + pi / 2, 1.0);
    final start = centerPoint! - perpDirection * (totalDashLength / 2);

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

    // first 64 are light, the other 64 are dark - this should be enough for now
    for (int i = 1; i <= 128; i++) {
      TextSpan textSpan = TextSpan(text: i < 65 ? '$i' : '${i-64}', style: i < 65 ? textStyle : textStyleLight);
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
  void drawBorder(Canvas canvas, List<Offset> coords, Color color, Offset slatExtend, bool slatTipExtended, String slatType) {
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
      Offset interSlatExtend = calculateSlatExtend(coords.first, coords[2], appState.gridSize * sqrt(3)/2);

      // since cos (90 - x) = sin(x) and vice versa
      // the negative sign is included due to the directionality of the grid (up = -ve, left = -ve, down = +ve, right = +ve)
      flippedSlatExtend = Offset(-interSlatExtend.dy, interSlatExtend.dx);
    }
    else {
      // since cos (90 - x) = sin(x) and vice versa
      // the negative sign is included due to the directionality of the grid (up = -ve, left = -ve, down = +ve, right = +ve)
      flippedSlatExtend = Offset(-slatExtend.dy, slatExtend.dx);
    }

    // the below contain the calculations for precisely framing slats according to their shape.  If tip extensions are enabled, these also need to be included to add some extra space
    // TODO: the below could probably be streamlined further but works well for now
    Map<String, dynamic> coordinateBuilder = {};
    coordinateBuilder['tube'] = {
      '1a': 0,
      '1b': 0,
      '2a': 31,
      '2b': 31,
      'slatExtend1a': slatTipExtended? 1.5: 0.5,
      'slatExtend1b': slatTipExtended? 1.5: 0.5,
      'slatExtend2a': slatTipExtended? 1.5: 0.5,
      'slatExtend2b': slatTipExtended? 1.5: 0.5,
      'yFlip': 1.0,
      'slatExtendX': 0.5,
      'slatExtendXMax': 1.5,
      'slatExtendY': 0.5,
      'slatExtendYMax': 1.5
    };

    coordinateBuilder['DB-L'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 1.3,
      'slatExtend2b': 1.3,
      'yFlip': 1.0
    };
    coordinateBuilder['DB-R'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 1.3,
      'slatExtend2b': 1.3,
      'yFlip': -1.0
    };
    coordinateBuilder['DB-L-60'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 1.6,
      'slatExtend2b': 0.7,
      'yFlip': 1.0
    };
    coordinateBuilder['DB-L-120'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 0.7,
      'slatExtend2b': 1.6,
      'yFlip': 1.0
    };

    coordinateBuilder['DB-R-120'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 0.7,
      'slatExtend2b': 1.6,
      'yFlip': -1.0
    };

    coordinateBuilder['DB-R-60'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 1.6,
      'slatExtend2b': 0.7,
      'yFlip': -1.0
    };

    var pData = coordinateBuilder[slatType];

    Offset slatP1A = coords[pData['1a']] - slatExtend * pData['slatExtend1a'] + flippedSlatExtend * pData['yFlip'];
    Offset slatP1B = coords[pData['1b']] - slatExtend * pData['slatExtend1b'] - flippedSlatExtend * pData['yFlip'];
    Offset slatP2A = coords[pData['2a']] + slatExtend * pData['slatExtend2a'] - flippedSlatExtend * pData['yFlip'];
    Offset slatP2B = coords[pData['2b']] + slatExtend * pData['slatExtend2b'] + flippedSlatExtend * pData['yFlip'];

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

    final sortedSlats = List<Slat>.from(slats)
      ..sort((a, b) => layerMap[a.layer]?['order'].compareTo(layerMap[b.layer]?['order']));

    String selectedLayerTopside = (layerMap[selectedLayer]?['top_helix'] == 'H5') ? 'H5' : 'H2';
    for (var slat in sortedSlats) {

      // logic on whether slat should be hidden (or otherwise)
      if (hiddenSlats.contains(slat.id)){
        continue;
      }

      // turns off phantoms if the user has chosen to not view them
      if(slat.phantomParent != null && !actionState.viewPhantoms){
        continue;
      }

      if (layerMap[slat.layer]?['hidden']) {
        continue;
      }
      if (actionState.isolateSlatLayerView && slat.layer != selectedLayer) {
        continue;
      }

      // main slat paint setup
      Color mainColor = slat.uniqueColor ?? layerMap[slat.layer]?['color'];
      Paint rodPaint = Paint()
        ..color = mainColor
        ..strokeWidth = appState.gridSize / 2
        ..style = PaintingStyle.stroke;
      if (slat.layer != selectedLayer) {
        rodPaint = Paint()
          ..color = mainColor.withValues(alpha: mainColor.a * 0.2)
          ..strokeWidth = appState.gridSize / 2
          ..style = PaintingStyle.stroke;
      }

      // gathers all the coordinates for the selected slat
      List unSortedCoords = slat.slatPositionToCoordinate.entries
          .toList()
        ..sort((a, b) => a.key.compareTo(b.key)); // sort by the integer key

      List<Offset> coords = unSortedCoords.map((e) => getRealCoord(e.value)).toList();

      // if slat out of the visible rectangle, can skip drawing to speed up rendering
      final slatBounds = Rect.fromPoints(
        coords.reduce((a, b) => Offset(
            a.dx < b.dx ? a.dx : b.dx, a.dy < b.dy ? a.dy : b.dy)),
        coords.reduce((a, b) => Offset(
            a.dx > b.dx ? a.dx : b.dx, a.dy > b.dy ? a.dy : b.dy)),
      ).inflate(appState.gridSize * 1.5);
      if (!slatBounds.overlaps(visibleRect)) continue;

      // draw the actual slat here
      drawSlat(coords, canvas, appState, actionState, rodPaint, slat.phantomParent != null);

      // slat extension angles and lengths (in case this is requested by the user)
      Offset slatExtendFront = calculateSlatExtend(coords[0], coords[1], appState.gridSize);

      // Draw slat position numbers if activated
      if (slat.layer == selectedLayer && actionState.slatNumbering) {
        bool isDark = isColorDark(mainColor);
        int i = 1;
        for (Offset coord in coords) {
          final labelPainter = labelPainters[!isDark ? i : i + 64]; // max 64 characters for now, can increase if necessary....
          if (labelPainter == null) continue;

          final textOffset = Offset(
            coord.dx - labelPainter.width / 2,
            coord.dy - labelPainter.height / 2,
          );

          labelPainter.paint(canvas, textOffset);
          i++;
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
                if(slat.phantomParent != null){
                  color = Colors.red;
                }
                else {
                  color = Colors.green;
                }

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

            void drawText(String text, Offset offset, Color textColor, double fontSize) {
              final textPainter = TextPainter(
                text: TextSpan(
                  text: text,
                  style: TextStyle(
                    color: textColor,
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

            drawText(topText, Offset(position.dx, position.dy - halfHeight / 2), isColorDark(topColor) ? Colors.white : Colors.black,  halfHeight * 0.8);
            drawText(bottomText, Offset(position.dx, position.dy + halfHeight / 2), isColorDark(bottomColor) ? Colors.white : Colors.black, halfHeight * 0.8);

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
            text: slat.id.replaceFirst('-I', '-') + (slat.slatType != 'tube' ? ' (${slat.slatType})' : ''),
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

        // find the center of all coords
        double sumX = 0, sumY = 0;
        for (final c in coords) {
          sumX += c.dx;
          sumY += c.dy;
        }

        Offset center = Offset(sumX / coords.length, sumY / coords.length);

        // assume angle can be found correctly from middle coords - might need to change if some weird slat types are used
        double angle = calculateSlatAngle(coords[coords.length ~/ 2], coords[(coords.length ~/ 2) + 1]);

        canvas.save();
        canvas.translate(center.dx, center.dy);

        // Flip upside-down labels
        if (angle > pi / 2 || angle < -pi / 2) {
          angle += pi;
        }
        canvas.rotate(angle);

        final baseRect = Rect.fromCenter(
          center: Offset.zero,
          width: slat.slatType == 'tube' ? appState.gridSize * 3 : appState.gridSize * 6,
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
        drawBorder(canvas, coords, mainColor, slatExtendFront, (actionState.drawingAids || actionState.extendSlatTips), slat.slatType);
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
