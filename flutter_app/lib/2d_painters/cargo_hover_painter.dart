import 'package:flutter/material.dart';
import '../graphics/crosshatch_shader.dart';
import '../app_management/shared_app_state.dart';
import  '../crisscross_core/cargo.dart';
import './seed_painter.dart';
import '../crisscross_core/seed.dart';

/// Custom painter for the cargo hover display
class CargoHoverPainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;
  final Cargo? cargo;
  final bool hoverValid;
  final Map<int, Offset> cargoArrayPoints;

  final Offset? hoverPosition;
  final List<Offset> preSelectedPositions;
  final Offset moveAnchor;
  final DesignState appState;

  CargoHoverPainter(this.scale, this.canvasOffset, this.cargo,
      this.hoverValid, this.cargoArrayPoints, this.hoverPosition,
      this.preSelectedPositions, this.moveAnchor, this.appState);

  @override
  void paint(Canvas canvas, Size size) {

    if (cargo == null) {
      return;
    }

    // usual transformations required to draw on the canvas
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    if (hoverPosition != null && cargoArrayPoints.isNotEmpty) {
      if (appState.cargoAdditionType == 'SEED'){ // special seed drawing supersedes normal cargo drawing
        Seed seed = Seed(coordinates: cargoArrayPoints);

        paintSeedFromArray(canvas, cargoArrayPoints, appState.gridSize,
            seed.rotationAngle!, seed.transverseAngle!,
            alpha: 0.5,
            color: appState.cargoPalette['SEED']!.color,
            printHandles: true,
            crosshatch: !hoverValid);
      }
      else {
        final Paint hoverRodPaint = Paint()
          ..color = cargo!.color.withValues(alpha: 0.5) // Semi-transparent slat
          ..strokeWidth = appState.gridSize / 2
          ..style = PaintingStyle.fill;

        if (!hoverValid) { // invalid slat
          hoverRodPaint.shader = CrossHatchShader.shader;
          hoverRodPaint.color = Colors.red;
        }

        // if there are no preset positions, attempt to draw based on layer angle
        if (preSelectedPositions.isEmpty) {
          for (var coord in cargoArrayPoints.values) {
            final rect = Rect.fromCenter(
              center: coord,
              width: appState.gridSize * 0.85,
              height: appState.gridSize * 0.85,
            );

            // Fill rectangle
            canvas.drawRect(rect, hoverRodPaint);

            // Outline with thin black border
            final borderPaint = Paint()
              ..style = PaintingStyle.stroke
              ..strokeWidth = 0.1
              ..color = Colors.black;

            canvas.drawRect(rect, borderPaint);
          }
        }
        // otherwise, draw hover points based on the anchor and provided coordinates
        else {
          // Offset anchorTranslate = hoverPosition! - moveAnchor;
          for (var coord in preSelectedPositions) {
            // convert the below to a rect with the correct syntax
            final rect = Rect.fromCenter(
              center: coord,
              width: appState.gridSize * 0.85,
              height: appState.gridSize * 0.85,
            );

            // Fill rectangle
            canvas.drawRect(rect, hoverRodPaint);

            // Outline with thin black border
            final borderPaint = Paint()
              ..style = PaintingStyle.stroke
              ..strokeWidth = 0.1
              ..color = Colors.black;

            canvas.drawRect(rect, borderPaint);
          }
        }
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