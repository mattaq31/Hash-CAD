import 'dart:math';

import 'package:flutter/material.dart';
import 'slat_painter.dart';
import '../graphics/crosshatch_shader.dart';
import '../crisscross_core/slats.dart';
import 'helper_functions.dart';
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
  final int moveRotationSteps;
  final bool moveTranspose;
  final DesignState appState;
  final ActionState actionState;

  late Map<int, TextPainter> labelPainters;

  SlatHoverPainter(this.scale, this.canvasOffset, this.slatColor,
      this.hoverValid, this.futureSlatEndPoints, this.hoverPosition,
      this.ignorePreSelectedSlats, this.preSelectedSlats, this.moveAnchor,
      this.moveRotationSteps, this.moveTranspose, this.appState, this.actionState)
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
        ..style = PaintingStyle.fill;

      if (!hoverValid) {  // invalid slat
        hoverRodPaint.shader = CrossHatchShader.shader;
        hoverRodPaint.color = Colors.red;
      }

      // if there are no slats being moved, draw fresh slats based on the futureSlatEndPoints
      if (ignorePreSelectedSlats) {
        int index = 1;
        for (var slatCoords in futureSlatEndPoints.values) {
          Offset slatExtend = calculateSlatExtend(slatCoords[1]!, slatCoords[32]!, appState.gridSize);

          if(actionState.drawingAids){
            canvas.drawLine(slatCoords[1]! - slatExtend * 0.5, slatCoords[32]!, hoverRodPaint);
            drawSlatDrawingAids(canvas, slatCoords[1]!, slatCoords[32]!, slatExtend, appState.gridSize, hoverRodPaint, hoverRodPaint.color, 1.0);
          }
          else {
            canvas.drawLine(
                slatCoords[1]! - slatExtend, slatCoords[32]! + slatExtend,
                hoverRodPaint);
          }
          // Draw numbers 1 and 32
          final label1 = labelPainters[index]!;
          final label32 = labelPainters[index]!;

          label1.paint(canvas, slatCoords[1]! - Offset(label1.width / 2, label1.height / 2));
          label32.paint(canvas, slatCoords[32]! - Offset(label32.width / 2, label32.height / 2));
          index += 1;
        }
      }
      // otherwise, draw hover points based on the anchor and provided coordinates
      else {
        Offset anchorTranslate = hoverPosition! - moveAnchor;
        for (var slat in preSelectedSlats) {
          var p1 = appState.convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[1]!);
          var p2 = appState.convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[32]!);

          if (moveRotationSteps != 0) {
            // rotate the slat by the specified number of steps
            // TODO: this system works but is janky - rotating multiple slats together can result in them clashing - either should accept this or think it through further...
            double slatAngle = calculateSlatAngle(p1, p2);
            double newAngle = slatAngle + (moveRotationSteps * (appState.gridMode == '60' ? pi/3 : pi / 2));
            double xExtend = cos(newAngle) * appState.gridSize * 32;
            double yExtend = sin(newAngle) * appState.gridSize * 32;
            p2 = Offset(
              p1.dx + xExtend,
              p1.dy + yExtend,
            );
          }

          if (moveTranspose){
            // reverse the slat's direction if transpose is active
            var p1Clone = Offset(p1.dx, p1.dy);
            p1 = p2;
            p2 = p1Clone;
          }

          Offset slatExtend = calculateSlatExtend(p1, p2, appState.gridSize);
          if(actionState.drawingAids){
            canvas.drawLine(p1 - (slatExtend * 0.5) + anchorTranslate,  p2 + anchorTranslate, hoverRodPaint);
            drawSlatDrawingAids(canvas, p1 + anchorTranslate, p2 + anchorTranslate, slatExtend, appState.gridSize, hoverRodPaint, hoverRodPaint.color, 1.0);
          }
          else {
            canvas.drawLine(p1 - slatExtend + anchorTranslate, p2 + slatExtend + anchorTranslate, hoverRodPaint);
          }
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