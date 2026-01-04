import 'package:flutter/material.dart';

class HoneycombPainter extends CustomPainter {
  final Color color;
  final double size;
  final Color? highlightColor;
  final bool highlightTop;
  final bool highlightBottom;

  HoneycombPainter({
    required this.color,
    this.size = 20,
    this.highlightColor,
    this.highlightTop = false,
    this.highlightBottom = false,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final Paint paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final Paint highlightPaint = Paint()
      ..color = highlightColor ?? color
      ..style = PaintingStyle.fill;

    final double dx = this.size * 0.86602540378;

    // offsets are required to center position of circles in the hexagon canvas
    final double offset = size.width/2;
    final double offsetY = size.height/2;

    // Define the centers of the six circles
    // Index 4 = bottom circle, Index 5 = top circle
    final List<Offset> centers = [
      Offset(offset - dx, offsetY + this.size/2),
      Offset(offset + dx, offsetY - this.size/2),
      Offset(offset - dx, offsetY - this.size/2),
      Offset(offset + dx, offsetY + this.size/2),
      Offset(offset, offsetY + this.size),  // index 4 = bottom
      Offset(offset, offsetY - this.size),  // index 5 = top
    ];

    for (int i = 0; i < centers.length; i++) {
      final bool isHighlighted = (i == 5 && highlightTop) || (i == 4 && highlightBottom);
      canvas.drawCircle(centers[i], this.size / 2, isHighlighted ? highlightPaint : paint);
    }

  }

  @override
  bool shouldRepaint(covariant HoneycombPainter oldDelegate) {
    return oldDelegate.color != color ||
        oldDelegate.highlightColor != highlightColor ||
        oldDelegate.highlightTop != highlightTop ||
        oldDelegate.highlightBottom != highlightBottom ||
        oldDelegate.size != size;
  }
}

// Usage in a widget
class HoneycombCustomPainterWidget extends StatelessWidget {
  final Color color;
  final double size;
  final Color? highlightColor;
  final bool highlightTop;
  final bool highlightBottom;

  const HoneycombCustomPainterWidget({
    super.key,
    required this.color,
    this.size = 15,
    this.highlightColor,
    this.highlightTop = false,
    this.highlightBottom = false,
  });

  @override
  Widget build(BuildContext context) {

    // calculations here are based on the following:
    // circles are placed at the vertices of a regular hexagon
    // size = distance from center of hexagon to center of any circle
    // distance between center of hexagon to LHS or RHS is sqrt(3)/2 * size
    // all other distances are worked out from the above
    final double dx = size * 0.86602540378;
    final double totalWidth = (2 * dx) + size;
    final double totalHeight = 3 * size;
    return CustomPaint(
      size: Size(totalWidth, totalHeight),
      painter: HoneycombPainter(
        color: color,
        size: size,
        highlightColor: highlightColor,
        highlightTop: highlightTop,
        highlightBottom: highlightBottom,
      ),
    );
  }
}