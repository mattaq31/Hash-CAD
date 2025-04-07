import 'package:flutter/material.dart';
import 'dart:math';


/// Custom painter for the grid lines
class GridPainter extends CustomPainter {
  final double gridSize;
  final double scale;
  final Offset canvasOffset;
  final String gridSystem;

  GridPainter(this.scale, this.canvasOffset, this.gridSize, this.gridSystem);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    final Paint majorDotPaint = Paint()
      ..color = Colors.grey[700]!
      ..style = PaintingStyle.fill;

    final Paint minorDotPaint = Paint()
      ..color = Colors.grey[400]!
      ..style = PaintingStyle.fill;

    // Calculate the bounds of the visible area in the grid's coordinate space
    final double left = -canvasOffset.dx / scale;
    final double top = -canvasOffset.dy / scale;
    final double right = left + size.width / scale;
    final double bottom = top + size.height / scale;

    // draws permanent 'grid' area to guide user to a central area
    final Paint rectPaint = Paint()
      ..color = Colors.grey[400]!
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;

    canvas.drawRect(Rect.fromLTWH(-500, -500, 1000, 1000), rectPaint);

    // Draw dots TODO: does this need to be redrawn every time?

    if (gridSystem == '90') {
      for (double x = (left ~/ gridSize) * gridSize; x < right; x += gridSize) {
        for (double y = (top ~/ gridSize) * gridSize;
        y < bottom;
        y += gridSize) {
          if (x % (gridSize * 4) == 0 && y % (gridSize * 4) == 0) {
            // Major dots at grid intersections
            canvas.drawCircle(Offset(x, y), gridSize / 8, majorDotPaint);
          } else {
            // Minor dots between major grid points
            canvas.drawCircle(Offset(x, y), gridSize / 16, minorDotPaint);
          }
        }
      }
    }
    else if (gridSystem == '60'){

      // irregular hexagonal grid, matching slat system
      double yJump = gridSize / 2;
      double xJump = sqrt(gridSize * gridSize - yJump * yJump);

      int row = (top ~/ yJump); // Stable row index
      double originY = row * yJump; // Stable Y start

      for (double y = originY; y < bottom; y += yJump, row++) {

        // Compute stable X alignment from global origin
        int col = (left ~/ (2 * xJump));
        double startX = col * (2 * xJump);

        // Adjust startX based on row parity
        if (!(row % 2 == 0)) {
          startX += xJump;
        }

        for (double x = startX; x < right; x += 2 * xJump) {
          canvas.drawCircle(Offset(x, y), gridSize / 16, majorDotPaint);
        }
      }
    }
    else{
      throw Exception('Grid system not supported');
    }

    final Paint crosshairPaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 2.0;
    double crosshairSize = 10.0; // Length of crosshair lines
    canvas.drawLine(Offset(-crosshairSize, 0), Offset(crosshairSize, 0), crosshairPaint);
    canvas.drawLine(Offset(0, -crosshairSize), Offset(0, crosshairSize), crosshairPaint);

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant GridPainter oldDelegate) {
    return false;
  }
}