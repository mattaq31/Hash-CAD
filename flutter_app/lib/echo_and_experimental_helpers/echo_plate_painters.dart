import 'package:flutter/material.dart';
import 'echo_plate_constants.dart';

/// Builds a chamfered plate path: 3 chamfered corners (H1 bottom-left,
/// A12 top-right, H12 bottom-right) and 1 square corner (A1 top-left),
/// matching Eppendorf twin-tec 96-well plate geometry.
Path buildChamferedPlatePath(Size size) {
  final w = size.width;
  final h = size.height;
  const c = echoChamferSize;

  return Path()
    ..moveTo(0, 0)
    ..lineTo(w - c, 0)
    ..lineTo(w, c)
    ..lineTo(w, h - c)
    ..lineTo(w - c, h)
    ..lineTo(c, h)
    ..lineTo(0, h - c)
    ..close();
}

/// Paints a chamfered border stroke around the plate.
class PlateBorderPainter extends CustomPainter {
  final Color color;
  final double strokeWidth;

  PlateBorderPainter({required this.color, required this.strokeWidth});

  @override
  void paint(Canvas canvas, Size size) {
    final path = buildChamferedPlatePath(size);
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth;
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(PlateBorderPainter old) => color != old.color || strokeWidth != old.strokeWidth;
}

/// Clips content to the chamfered plate shape.
class PlateChamferClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) => buildChamferedPlatePath(size);

  @override
  bool shouldReclip(PlateChamferClipper oldClipper) => false;
}
