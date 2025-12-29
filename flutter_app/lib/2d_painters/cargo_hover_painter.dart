import 'package:flutter/material.dart';

import '../graphics/crosshatch_shader.dart';
import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import  '../crisscross_core/cargo.dart';
import './seed_painter.dart';
import '../crisscross_core/seed.dart';
import 'slat_painter.dart';


/// Custom painter for the cargo hover display
class CargoHoverPainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;
  // final Cargo? cargo;
  final bool hoverValid;
  final Map<int, Offset> cargoArrayPoints;
  final Offset? hoverPosition;
  final Offset moveAnchor;
  final DesignState appState;
  final ActionState actionState;

  CargoHoverPainter(this.scale, this.canvasOffset,
      this.hoverValid, this.cargoArrayPoints, this.hoverPosition,
      this.moveAnchor, this.appState, this.actionState);

  @override
  void paint(Canvas canvas, Size size) {

    // usual transformations required to draw on the canvas
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

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

    if (hoverPosition != null && cargoArrayPoints.isNotEmpty) {
    // TODO: this needs special fixing
      if (appState.cargoAdditionType == 'SEED'){ // special seed drawing supersedes normal cargo drawing
        Seed seed = Seed(ID: 'dummy', coordinates: cargoArrayPoints);

        paintSeedFromArray(canvas, cargoArrayPoints, appState.gridSize,
            seed.rotationAngle!, seed.transverseAngle!,
            alpha: 0.5,
            color: appState.cargoPalette['SEED']!.color,
            printHandles: true,
            crosshatch: !hoverValid);
      }
      else {

        // if there are no preset positions, attempt to draw based on layer angle
        for (var coord in cargoArrayPoints.values) {
          double squareSide = appState.gridSize * 0.85;
          Offset centerCoord;
          Color paintColor;

          if (moveAnchor != Offset.zero) {
            centerCoord = appState.convertCoordinateSpacetoRealSpace(coord) + hoverPosition! - moveAnchor;
            paintColor = appState.getCargoFromCoordinate(coord, appState.selectedLayerKey, actionState.cargoAttachMode).color;
          }
          else{
            centerCoord = coord;
            paintColor = appState.cargoPalette[appState.cargoAdditionType]?.color ?? Colors.grey;
          }

          final Paint hoverRodPaint = Paint()
            ..color = paintColor.withValues(alpha: 0.5) // Semi-transparent input
            ..strokeWidth = appState.gridSize / 2
            ..style = PaintingStyle.fill;

          if (!hoverValid) { // invalid location
            hoverRodPaint.shader = CrossHatchShader.shader;
            hoverRodPaint.color = Colors.red;
          }

          centerCoord = actionState.cargoAttachMode == 'top' ? centerCoord - Offset(0, squareSide/4) : centerCoord + Offset(0, squareSide/4);

          final rect = Rect.fromCenter(
            center: centerCoord,
            width: squareSide,
            height: squareSide/2,
          );

          // Fill rectangle
          canvas.drawRect(rect, hoverRodPaint);

          drawText(actionState.cargoAttachMode == 'top' ? '↑' : '↓', centerCoord, isColorDark(paintColor) ? Colors.white : Colors.black,  squareSide * 0.4);

          // Outline with thin black border
          final borderPaint = Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = 0.1
            ..color = Colors.black;

          canvas.drawRect(rect, borderPaint);
        }
        // otherwise, draw hover points based on the anchor and provided coordinates - TODO: preSelectedPositions should be removed, integrate anchor in the above

        // else {
        //   // Offset anchorTranslate = hoverPosition! - moveAnchor;
        //   for (var coord in preSelectedPositions) {
        //     // convert the below to a rect with the correct syntax
        //     final rect = Rect.fromCenter(
        //       center: coord,
        //       width: appState.gridSize * 0.85,
        //       height: appState.gridSize * 0.85,
        //     );
        //
        //     // Fill rectangle
        //     canvas.drawRect(rect, hoverRodPaint);
        //
        //     // Outline with thin black border
        //     final borderPaint = Paint()
        //       ..style = PaintingStyle.stroke
        //       ..strokeWidth = 0.1
        //       ..color = Colors.black;
        //
        //     canvas.drawRect(rect, borderPaint);
        //   }
        // }
      }
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CargoHoverPainter oldDelegate) {
    return hoverPosition != oldDelegate.hoverPosition ||
        hoverValid != oldDelegate.hoverValid;
  }
}