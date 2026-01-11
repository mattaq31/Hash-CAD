import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'dart:math';

import '../graphics/crosshatch_shader.dart';
import '../crisscross_core/seed.dart';
import 'slat_painter.dart';


void paintSeedFromArray(Canvas canvas, Map<int, Offset> coordinates, double gridSize,
    int rotationAngle, int transverseAngle, {Color color=Colors.red, double alpha=1.0,
      bool crosshatch=false, bool printHandles=false, int cols=16, int rows=5}){

  final paint = Paint()
    ..color = color.withValues(alpha:alpha)
    ..strokeWidth = 2
    ..style = PaintingStyle.stroke;

  final spotPaint = Paint()
    ..color = color.withValues(alpha:alpha)
    ..strokeWidth = 2
    ..style = PaintingStyle.fill;

  if (crosshatch){
    paint.shader = CrossHatchShader.shader;
    paint.color = Colors.red;
    spotPaint.shader = CrossHatchShader.shader;
    spotPaint.color = Colors.red;
  }
  final path = Path();

  double extendX = gridSize * cos(rotationAngle * (pi / 180));
  double extendY = gridSize * sin(rotationAngle * (pi / 180));
  double transExtendX = gridSize * cos(transverseAngle * (pi / 180));
  double transExtendY = gridSize * sin(transverseAngle * (pi / 180));
  double farTransExtendX = gridSize * rows * cos(transverseAngle * (pi / 180));
  double farTransExtendY = gridSize * rows * sin(transverseAngle * (pi / 180));

  double startX = coordinates[1]!.dx  - extendX;
  double startY = coordinates[1]!.dy - extendY;

  path.moveTo(startX, startY);

  // Horizontal snaking lines
  for (int i = 1; i < rows+1; i++) {
    if (i == rows) {
      if (i % 2 != 0) {
        path.lineTo(coordinates[i*cols]!.dx + extendX, coordinates[i*cols]!.dy + extendY);
        path.lineTo(coordinates[i*cols]!.dx + extendX/2 + transExtendX/2, coordinates[i*cols]!.dy + extendY/2 + transExtendY/2);

      } else {
        path.lineTo(coordinates[(i-1)*cols + 1]!.dx - extendX, coordinates[(i-1)*cols + 1]!.dy - extendY);
        path.lineTo(coordinates[(i-1)*cols + 1]!.dx - extendX/2 - transExtendX/2, coordinates[(i-1)*cols + 1]!.dy - extendY/2 - transExtendY/2);

      }
    } else {
      if (i % 2 != 0) {
        path.lineTo(coordinates[i*cols]!.dx + extendX, coordinates[i*cols]!.dy + extendY);
        path.lineTo(coordinates[(1+i)*cols]!.dx + extendX, coordinates[(1+i)*cols]!.dy + extendY);
      } else {
        path.lineTo(coordinates[(i-1)*cols + 1]!.dx - extendX, coordinates[(i-1)*cols + 1]!.dy - extendY);
        path.lineTo(coordinates[(i)*cols + 1]!.dx - extendX, coordinates[(i)*cols + 1]!.dy - extendY);
      }
    }
  }

  // Vertical snaking lines
  for (int j = 1; j < cols + 2; j++) {
    if (j == (cols + 1)) {
      if (j % 2 != 0) {
        path.relativeLineTo(-farTransExtendX, -farTransExtendY);
      } else {
        path.relativeLineTo(farTransExtendX, farTransExtendY);
      }
    } else {
      if (j % 2 != 0) {
        path.relativeLineTo(-farTransExtendX, -farTransExtendY);
        path.relativeLineTo(-extendX, -extendY);

      } else {
        path.relativeLineTo(farTransExtendX, farTransExtendY);
        path.relativeLineTo(-extendX, -extendY);
      }
    }
  }

  path.close();

  canvas.drawPath(path, paint);

  if(printHandles) {
    for (Offset coord in coordinates.values) {
        canvas.drawCircle(coord, gridSize/3, spotPaint);
      }
    }
}


class SeedPainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;
  final List<Seed> seeds;
  final List<bool> seedTransparency;

  final double handleJump;
  final int rows;
  final int cols;
  final Color color;
  final bool printHandles;
  final bool showLabels;

  SeedPainter({
    required this.scale,
    required this.canvasOffset,
    required this.seeds,
    required this.handleJump,
    required this.printHandles,
    required this.seedTransparency,
    this.rows = 5,
    this.cols = 16,
    this.color = Colors.red,
    this.showLabels = true,
  });

  @override
  void paint(Canvas canvas, Size size) {

    if(seeds.isEmpty){
      return;
    }

    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    // First pass: draw all seed pictographs
    for (var i = 0; i < seeds.length; i++) {
      Seed seed = seeds[i];
      double transparency = seedTransparency[i] ? 0.5 : 1.0;
      paintSeedFromArray(
          canvas, seed.coordinates, handleJump, seed.rotationAngle!,
          seed.transverseAngle!, color: color, cols:cols, rows:rows,
          printHandles: printHandles, alpha:transparency);
    }

    // Second pass: draw all seed ID labels on top
    if (showLabels) {
      for (var i = 0; i < seeds.length; i++) {
        Seed seed = seeds[i];
        _drawSeedLabel(canvas, seed, handleJump);
      }
    }

    canvas.restore();
  }

  void _drawSeedLabel(Canvas canvas, Seed seed, double gridSize) {
    // Position label at the first coordinate (corner of the seed)
    final cornerCoord = seed.coordinates[1]!;

    // Offset the label slightly outside the seed boundary (although this may vary with rotation, whatever it looks fine in most cases)
    final labelSize = gridSize * 1.2;
    final labelCenter = Offset(
      cornerCoord.dx - gridSize * 0.4,
      cornerCoord.dy - gridSize * 0.4,
    );

    final textPainter = TextPainter(
      text: TextSpan(
        text: seed.ID,
        style: TextStyle(
          color: isColorDark(color) ? Colors.white : Colors.black,
          fontFamily: 'Roboto',
          fontSize: gridSize * 0.9,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
      textAlign: TextAlign.center,
    );
    textPainter.layout();

    double baselineOffset;
    if (kIsWeb || defaultTargetPlatform == TargetPlatform.windows) {
      baselineOffset = textPainter.height;
    } else {
      baselineOffset = textPainter.computeDistanceToActualBaseline(TextBaseline.alphabetic);
    }

    final labelRect = Rect.fromCenter(
      center: labelCenter,
      width: labelSize,
      height: labelSize,
    );

    final textOffset = Offset(
      labelCenter.dx - textPainter.width / 2 + 0.1,
      labelCenter.dy - baselineOffset / 2 - 0.5,
    );

    // Draw colored background
    canvas.drawRRect(
      RRect.fromRectAndRadius(labelRect, Radius.circular(gridSize * 0.2)),
      Paint()
        ..color = color
        ..style = PaintingStyle.fill,
    );

    // Draw border
    canvas.drawRRect(
      RRect.fromRectAndRadius(labelRect, Radius.circular(gridSize * 0.2)),
      Paint()
        ..color = Colors.black
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.1,
    );

    textPainter.paint(canvas, textOffset);
  }

  @override
  bool shouldRepaint(covariant SeedPainter oldDelegate) {
    return
      oldDelegate.seeds != seeds ||
        oldDelegate.rows != rows ||
        oldDelegate.color != color ||
        oldDelegate.cols != cols ||
        oldDelegate.showLabels != showLabels;
  }
}