import 'package:flutter/material.dart';

/// Custom painter for a 'delete' display
class DeletePainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;
  final Offset? hoverPosition;
  final double gridSize;

  DeletePainter(this.scale, this.canvasOffset, this.hoverPosition, this.gridSize);

  @override
  void paint(Canvas canvas, Size size) {

    // usual transformations required to draw on the canvas
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    final Paint paint = Paint()
      ..color = Colors.red
      ..strokeWidth = gridSize / 7 // Adjust thickness
      ..strokeCap = StrokeCap.round;

    if (hoverPosition != null) {
      // Define the endpoints of the 'X'
      Offset topLeft = hoverPosition! - Offset(gridSize / 4, gridSize / 4);
      Offset bottomRight = hoverPosition! + Offset(gridSize / 4, gridSize / 4);
      Offset topRight = hoverPosition! + Offset(gridSize / 4, -gridSize / 4);
      Offset bottomLeft = hoverPosition! - Offset(gridSize / 4, -gridSize / 4);
      // Draw the two lines forming the 'X'
      canvas.drawLine(topLeft, bottomRight, paint);
      canvas.drawLine(topRight, bottomLeft, paint);
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}