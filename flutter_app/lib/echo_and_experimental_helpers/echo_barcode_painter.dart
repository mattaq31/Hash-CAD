import 'package:flutter/material.dart';
import 'echo_category_colors.dart';

/// Draws the slat pictogram in each well for the echo output export report.
/// Each handle is given a colored bar, which matches the handle's category.
class HandleBarcodePainter extends CustomPainter {
  final Map<int, Map<String, dynamic>> h2Handles;
  final Map<int, Map<String, dynamic>> h5Handles;
  final int maxLength;

  HandleBarcodePainter({
    required this.h2Handles,
    required this.h5Handles,
    this.maxLength = 32,
  });

  /// Blocked handles (value '0') should display as FLAT staples.
  static String? _effectiveCategory(Map<String, dynamic>? handle) {
    if (handle == null) return null;
    final category = handle['category'] as String?;
    if (category != null && handle['value'] == '0' && (category == 'ASSEMBLY_HANDLE' || category == 'ASSEMBLY_ANTIHANDLE')) {
      return 'FLAT';
    }
    return category;
  }

  @override
  void paint(Canvas canvas, Size size) {
    final rectWidth = size.width / maxLength;
    final rowHeight = size.height / 2;
    final linePaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.5;

    // Top row: H2
    for (int i = 0; i < maxLength; i++) {
      final handle = h2Handles[i + 1];
      final color = categoryColor(_effectiveCategory(handle));
      final rect = Rect.fromLTWH(i * rectWidth, 0, rectWidth, rowHeight);
      canvas.drawRect(rect, Paint()..color = color);
      canvas.drawRect(rect, linePaint);
    }

    // Bottom row: H5
    for (int i = 0; i < maxLength; i++) {
      final handle = h5Handles[i + 1];
      final color = categoryColor(_effectiveCategory(handle));
      final rect = Rect.fromLTWH(i * rectWidth, rowHeight, rectWidth, rowHeight);
      canvas.drawRect(rect, Paint()..color = color);
      canvas.drawRect(rect, linePaint);
    }
  }

  @override
  bool shouldRepaint(HandleBarcodePainter oldDelegate) {
    return h2Handles.length != oldDelegate.h2Handles.length ||
        h5Handles.length != oldDelegate.h5Handles.length ||
        maxLength != oldDelegate.maxLength;
  }
}
