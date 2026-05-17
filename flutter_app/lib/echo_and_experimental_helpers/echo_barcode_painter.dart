import 'package:flutter/material.dart';
import 'echo_category_colors.dart';

/// Draws the slat pictogram in each well for the echo output export report.
/// Each handle is given a colored bar, which matches the handle's category.
class HandleBarcodePainter extends CustomPainter {
  final Map<int, Map<String, dynamic>> h2Handles;
  final Map<int, Map<String, dynamic>> h5Handles;
  final int maxLength;
  final Set<(int, int)> manualPositions;
  final int _paintFingerprint;

  HandleBarcodePainter({
    required this.h2Handles,
    required this.h5Handles,
    this.maxLength = 32,
    this.manualPositions = const {},
  }) : _paintFingerprint = Object.hash(
          maxLength,
          _fingerprintHandleMap(h2Handles),
          _fingerprintHandleMap(h5Handles),
          _fingerprintManualPositions(manualPositions),
        );

  /// Returns the effective display category for a handle in the barcode view.
  /// Priority: fluorophore > blocked-as-flat > normal category.
  static String? effectiveCategoryForHandle(Map<String, dynamic>? handle) {
    if (handle == null) return null;
    final category = handle['category'] as String?;
    if (handle['fluorophore'] != null && category != null && category.contains('ASSEMBLY')) {
      return 'FLUOROPHORE';
    }
    if (category != null && handle['value'] == '0' && (category == 'ASSEMBLY_HANDLE' || category == 'ASSEMBLY_ANTIHANDLE')) {
      return 'FLAT';
    }
    return category;
  }

  static int _fingerprintHandleMap(Map<int, Map<String, dynamic>> handles) {
    final sortedKeys = handles.keys.toList()..sort();
    return Object.hashAll(sortedKeys.map((position) {
      final handle = handles[position]!;
      return Object.hash(
        position,
        effectiveCategoryForHandle(handle),
        handle['value'],
        handle['category'],
        handle['fluorophore'],
      );
    }));
  }

  static int _fingerprintManualPositions(Set<(int, int)> positions) {
    final sortedPositions = positions.toList()
      ..sort((a, b) => a.$1 != b.$1 ? a.$1.compareTo(b.$1) : a.$2.compareTo(b.$2));
    return Object.hashAll(sortedPositions.map((position) => Object.hash(position.$1, position.$2)));
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
      final color = isManual ? categoryColor('MANUAL') : categoryColor(effectiveCategoryForHandle(handle));
      final rect = Rect.fromLTWH(i * rectWidth, 0, rectWidth, rowHeight);
      canvas.drawRect(rect, Paint()..color = color);
      canvas.drawRect(rect, linePaint);
    }

    // Bottom row: H2
    for (int i = 0; i < maxLength; i++) {
      final pos = i + 1;
      final handle = h2Handles[pos];
      final isManual = manualPositions.contains((2, pos));
      final color = isManual ? categoryColor('MANUAL') : categoryColor(effectiveCategoryForHandle(handle));
      final rect = Rect.fromLTWH(i * rectWidth, rowHeight, rectWidth, rowHeight);
      canvas.drawRect(rect, Paint()..color = color);
      canvas.drawRect(rect, linePaint);
    }
  }

  @override
  bool shouldRepaint(HandleBarcodePainter oldDelegate) => _paintFingerprint != oldDelegate._paintFingerprint;
}
