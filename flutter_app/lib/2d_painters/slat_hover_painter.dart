import 'package:flutter/material.dart';
import '../crosshatch_shader.dart';
import '../crisscross_core/slats.dart';
import 'helper_functions.dart';
import '../shared_app_state.dart';

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
  final DesignState appState;

  SlatHoverPainter(this.scale, this.canvasOffset, this.slatColor,
      this.hoverValid, this.futureSlatEndPoints, this.hoverPosition,
      this.ignorePreSelectedSlats, this.preSelectedSlats, this.moveAnchor,
      this.appState);

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

      // if there are no preset positions, attempt to draw based on layer angle
      if (ignorePreSelectedSlats) {
        for (var slatCoords in futureSlatEndPoints.values) {
          Offset slatExtend = calculateSlatExtend(slatCoords[1]!, slatCoords[32]!, appState.gridSize);
          canvas.drawLine(slatCoords[1]! - slatExtend, slatCoords[32]! + slatExtend, hoverRodPaint);
        }
      }
      // otherwise, draw hover points based on the anchor and provided coordinates
      else {
        Offset anchorTranslate = hoverPosition! - moveAnchor;
        for (var slat in preSelectedSlats) {
          var p1 = appState.convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[1]!);
          var p2 = appState.convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[32]!);

          Offset slatExtend = calculateSlatExtend(p1, p2, appState.gridSize);
          canvas.drawLine(p1 - slatExtend + anchorTranslate, p2 + slatExtend + anchorTranslate, hoverRodPaint);
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