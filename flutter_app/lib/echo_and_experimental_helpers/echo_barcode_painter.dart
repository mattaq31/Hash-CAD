import 'package:flutter/material.dart';
import 'echo_category_colors.dart';

/// Draws the slat pictogram in each well for the echo output export report.
/// Each handle is given a colored bar, which matches the handle's category.
class HandleBarcodePainter extends CustomPainter {
  final Map<int, Map<String, dynamic>> h2Handles;
  final Map<int, Map<String, dynamic>> h5Handles;
  final int maxLength;
  final Set<(int, int)> manualPositions;

  HandleBarcodePainter({
    required this.h2Handles,
    required this.h5Handles,
    this.maxLength = 32,
    this.manualPositions = const {},
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

    // Top row: H5
    for (int i = 0; i < maxLength; i++) {
      final pos = i + 1;
      final handle = h5Handles[pos];
      final isManual = manualPositions.contains((5, pos));
      final color = isManual ? categoryColor('MANUAL') : categoryColor(_effectiveCategory(handle));
      final rect = Rect.fromLTWH(i * rectWidth, 0, rectWidth, rowHeight);
      canvas.drawRect(rect, Paint()..color = color);
      canvas.drawRect(rect, linePaint);
    }

    // Bottom row: H2
    for (int i = 0; i < maxLength; i++) {
      final pos = i + 1;
      final handle = h2Handles[pos];
      final isManual = manualPositions.contains((2, pos));
      final color = isManual ? categoryColor('MANUAL') : categoryColor(_effectiveCategory(handle));
      final rect = Rect.fromLTWH(i * rectWidth, rowHeight, rectWidth, rowHeight);
      canvas.drawRect(rect, Paint()..color = color);
      canvas.drawRect(rect, linePaint);
    }
  }

  @override
  bool shouldRepaint(HandleBarcodePainter oldDelegate) {
    return h2Handles.length != oldDelegate.h2Handles.length ||
        h5Handles.length != oldDelegate.h5Handles.length ||
        maxLength != oldDelegate.maxLength ||
        manualPositions.length != oldDelegate.manualPositions.length ||
        !manualPositions.containsAll(oldDelegate.manualPositions);
  }
}
