
import 'package:flutter/material.dart';
import 'slat_painter.dart';
import '../graphics/crosshatch_shader.dart';
import '../crisscross_core/slats.dart';
import '../app_management/shared_app_state.dart';

/// Custom painter for the slat hover display
class SlatHoverPainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;
  final Color slatColor;
  final bool hoverValid;

  final Map<int, Map<int, Offset>> futureSlatEndPoints;

  final Offset? hoverPosition;
  final bool ignorePreSelectedSlats;
  final List<Slat> preSelectedSlats;
  final Offset moveAnchor;
  final bool moveTranspose;
  final DesignState appState;
  final ActionState actionState;

  late Map<int, TextPainter> labelPainters;

  SlatHoverPainter(this.scale, this.canvasOffset, this.slatColor,
      this.hoverValid, this.futureSlatEndPoints, this.hoverPosition,
      this.ignorePreSelectedSlats, this.preSelectedSlats, this.moveAnchor,
      this.moveTranspose, this.appState, this.actionState)
  {
    labelPainters = <int, TextPainter>{};
    TextStyle textStyle = TextStyle(
      color: Colors.black,
      fontFamily: 'Roboto',
      fontWeight: FontWeight.bold,
      fontSize: appState.gridSize * 0.4, // small enough for grid point
    );

    for (int i = 1; i <= 32; i++) {
      TextSpan textSpan = TextSpan(text: '$i', style: textStyle);
      TextPainter textPainter = TextPainter(
        text: textSpan,
        textAlign: TextAlign.center,
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();
      labelPainters[i] = textPainter;
    }
  }

  @override
  void paint(Canvas canvas, Size size) {

    // usual transformations required to draw on the canvas
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    if (hoverPosition != null) {
      final Paint hoverRodPaint = Paint()
        ..color = slatColor.withValues(alpha: 0.5) // Semi-transparent slat
        ..strokeWidth = appState.gridSize / 2
        ..style = PaintingStyle.stroke;

      if (!hoverValid) {  // invalid slat
        hoverRodPaint.shader = CrossHatchShader.shader;
        hoverRodPaint.color = Colors.red;
      }

      // if there are no slats being moved, draw fresh slats based on the futureSlatEndPoints
      if (ignorePreSelectedSlats) {
        int index = 1;
        for (var slatCoords in futureSlatEndPoints.values) {

          drawSlat(slatCoords.values.toList(), canvas, appState, actionState, hoverRodPaint, false);

          // Draw numbers at the beginning and end of the new slat
          final labelBegin = labelPainters[index]!;
          final labelFin = labelPainters[index]!;

          labelBegin.paint(canvas, slatCoords[1]! - Offset(labelBegin.width / 2, labelBegin.height / 2));
          if (appState.slatAdditionType == 'tube') {
            labelFin.paint(canvas, slatCoords[slatCoords.length]! -
                Offset(labelFin.width / 2, labelFin.height / 2));
          }
          index += 1;
        }
      }
      // otherwise, draw hover points based on the anchor and provided coordinates
      else {
        Offset anchorTranslate = hoverPosition! - moveAnchor;
        for (var slat in preSelectedSlats) {

          // gathers all the coordinates for the selected slat
          List unSortedCoords = slat.slatPositionToCoordinate.entries
              .toList()
            ..sort((a, b) => a.key.compareTo(b.key)); // sort by the integer key

          List<Offset> coords = unSortedCoords.map((e) => appState.convertCoordinateSpacetoRealSpace(e.value)).toList();
          if (moveTranspose && slat.slatType == 'tube'){
            // reverse the coordinates
            coords = coords.reversed.toList();
          }

          // apply the anchor translation to the coordinates before drawing
          coords = coords.map((e) => e + anchorTranslate).toList();

          drawSlat(coords, canvas, appState, actionState, hoverRodPaint, slat.phantomID != null);
        }
      }
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant SlatHoverPainter oldDelegate) {
    return hoverPosition != oldDelegate.hoverPosition ||
        hoverValid != oldDelegate.hoverValid;
  }
}