import 'dart:ui' as ui;
import 'package:flutter/material.dart';

class CrossHatchShader {
  static ui.Shader? _shader;

  static Future<void> initialize(double size) async {
    if (_shader != null) return; // Only create once

    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder);

    final paint = Paint()
      ..color = Colors.red.withValues(alpha: 0.5)
      ..strokeWidth = 1
      ..style = PaintingStyle.stroke;

    final step = size / 5; // Adjust for density of cross-hatching

    // Draw diagonal lines (bottom-left to top-right)
    for (double i = -size; i < size * 2; i += step) {
      canvas.drawLine(Offset(i, 0), Offset(i + size, size), paint);
    }

    // Draw diagonal lines (top-left to bottom-right)
    for (double i = -size; i < size * 2; i += step) {
      canvas.drawLine(Offset(i + size, 0), Offset(i, size), paint);
    }

    final picture = recorder.endRecording();
    final image = await picture.toImage(size.toInt(), size.toInt());
    _shader = ui.ImageShader(image, TileMode.repeated, TileMode.repeated, Matrix4.identity().storage);
  }

  static ui.Shader? get shader => _shader;
}