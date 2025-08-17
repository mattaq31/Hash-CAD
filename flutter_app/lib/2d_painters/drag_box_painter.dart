import 'package:flutter/material.dart';


class DragPainter extends CustomPainter {
  final Offset? start;
  final Offset? current;
  final bool isDragging;

  DragPainter(this.start, this.current, this.isDragging);

  @override
  void paint(Canvas canvas, Size size) {
    if (isDragging && start != null && current != null) {
      final rect = Rect.fromPoints(start!, current!);
      final paint = Paint()
        ..color = Colors.blue.withValues(alpha: 0.2)
        ..style = PaintingStyle.fill;
      final border = Paint()
        ..color = Colors.blue
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;

      canvas.drawRect(rect, paint);
      canvas.drawRect(rect, border);
    }
  }

  @override
  bool shouldRepaint(DragPainter old) =>
      old.start != start || old.current != current || old.isDragging != isDragging;
}