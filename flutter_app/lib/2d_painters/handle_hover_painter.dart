import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../graphics/crosshatch_shader.dart';
import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import './seed_painter.dart';
import '../crisscross_core/seed.dart';
import '../crisscross_core/slats.dart';
import '../crisscross_core/assembly_handle_pattern.dart';
import 'slat_painter.dart';


/// Custom painter for the cargo hover display
class HandleHoverPainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;
  // final Cargo? cargo;
  final bool hoverValid;
  final Map<int, Offset> cargoArrayPoints;
  final Offset? hoverPosition;
  final Offset moveAnchor;
  final DesignState appState;
  final ActionState actionState;
  /// 90° rotation steps of the pattern being placed - orients the north guide and triggers repaints on rotation.
  final int patternRotationSteps;

  HandleHoverPainter(this.scale, this.canvasOffset,
      this.hoverValid, this.cargoArrayPoints, this.hoverPosition,
      this.moveAnchor, this.appState, this.actionState, {this.patternRotationSteps = 0});

  @override
  void paint(Canvas canvas, Size size) {

    // usual transformations required to draw on the canvas
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    void drawText(String text, Offset offset, Color textColor, double fontSize) {
      final textPainter = TextPainter(
        text: TextSpan(
          text: text,
          style: TextStyle(
            color: textColor,
            fontFamily: 'Roboto',
            fontSize: fontSize,
            fontWeight: FontWeight.bold,
          ),
        ),
        textDirection: TextDirection.ltr,
        textAlign: TextAlign.center,
      );
      textPainter.layout();
      final baselineOffset = textPainter.height;
      final actualOffset = Offset(
        offset.dx - textPainter.width / 2 - 0.1,
        offset.dy - baselineOffset / 2 + 0.3,
      );
      textPainter.paint(canvas, actualOffset);
    }

    /// Draws a thin line with an upward arrow and a 'TOP' label marking the pattern's recorded north edge.
    ///
    /// The geometry is derived from the rotated entry offsets and a rotated north vector, using the same
    /// [rotateCoordinateSpace] transform as the handles themselves, so the guide always tracks the pattern.
    void drawPatternNorthGuide(List<AssemblyHandlePatternEntry> entries, Offset anchor) {
      final gridSize = appState.gridSize;
      final steps = appState.gridMode == '90' ? patternRotationSteps : 0;

      // entry offsets and the pattern's 'north' direction, both rotated and converted to real space
      final rotatedOffsets = entries
          .map((e) => appState.convertCoordinateSpacetoRealSpace(
              rotateCoordinateSpace(e.offset, Offset.zero, steps, appState.gridMode)))
          .toList();
      final northOffset = appState.convertCoordinateSpacetoRealSpace(
          rotateCoordinateSpace(const Offset(0, -1), Offset.zero, steps, appState.gridMode));
      final north = northOffset / northOffset.distance; // unit vector pointing to the pattern's recorded top
      final along = Offset(-north.dy, north.dx); // unit vector along the guide line

      // projections of every handle onto the two guide axes
      final northSpans = rotatedOffsets.map((o) => o.dx * north.dx + o.dy * north.dy);
      final alongSpans = rotatedOffsets.map((o) => o.dx * along.dx + o.dy * along.dy);
      // handle rectangles reach ~0.425 grid units from their coordinate in any direction, so clear that plus a gap
      final northDistance = northSpans.reduce(math.max) + gridSize * 0.65;
      final lineStart = north * northDistance + along * (alongSpans.reduce(math.min) - gridSize / 2);
      final lineEnd = north * northDistance + along * (alongSpans.reduce(math.max) + gridSize / 2);

      final arrowBase = (lineStart + lineEnd) / 2;
      final arrowTip = arrowBase + north * (gridSize * 0.35);
      final headSize = gridSize * 0.12;

      final guidePaint = Paint()
        ..color = Colors.black54
        ..strokeWidth = gridSize * 0.06
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      canvas.save();
      canvas.translate(anchor.dx, anchor.dy);
      canvas.drawLine(lineStart, lineEnd, guidePaint);
      canvas.drawLine(arrowBase, arrowTip, guidePaint);
      canvas.drawPath(
        Path()
          ..moveTo(arrowTip.dx - north.dx * headSize + along.dx * headSize,
              arrowTip.dy - north.dy * headSize + along.dy * headSize)
          ..lineTo(arrowTip.dx, arrowTip.dy)
          ..lineTo(arrowTip.dx - north.dx * headSize - along.dx * headSize,
              arrowTip.dy - north.dy * headSize - along.dy * headSize),
        guidePaint,
      );
      // label sits beside the arrow tip and stays upright at every rotation
      drawText('TOP', arrowTip + along * (gridSize * 0.55), Colors.black54, gridSize * 0.35);
      canvas.restore();
    }

    if (hoverPosition != null && cargoArrayPoints.isNotEmpty) {
      // Check if we're in assembly mode (panelMode == 2)
      bool isAssemblyMode = actionState.panelMode == 2;

      if (!isAssemblyMode && appState.cargoAdditionType == 'SEED') {
        // special seed drawing supersedes normal cargo drawing
        Seed seed = Seed(ID: 'dummy', coordinates: cargoArrayPoints);

        paintSeedFromArray(canvas, cargoArrayPoints, appState.gridSize,
            seed.rotationAngle!, seed.transverseAngle!,
            alpha: 0.5,
            color: appState.cargoPalette['SEED']!.color,
            printHandles: true,
            crosshatch: !hoverValid);

      } else if (isAssemblyMode) {
        // Assembly handle hover drawing
        String attachMode = actionState.assemblyAttachMode;

        // When placing a pattern, point keys are entry indices so each ghost can show its own value
        final patternEntries = actionState.assemblyPatternMode
            ? appState.assemblyHandlePatterns[actionState.selectedAssemblyPatternId]?.entries
            : null;

        for (var point in cargoArrayPoints.entries) {
          var coord = point.value;
          double squareSide = appState.gridSize * 0.85;
          Offset centerCoord;
          Color paintColor;
          final patternEntry = (patternEntries != null && point.key < patternEntries.length)
              ? patternEntries[point.key]
              : null;

          if (moveAnchor != Offset.zero) {
            // Moving mode - offset from anchor
            centerCoord = appState.convertCoordinateSpacetoRealSpace(coord) + hoverPosition! - moveAnchor;
            // Get color from existing handle at this position
            paintColor = attachMode == 'top' ? Colors.blue : Colors.orange;
          } else {
            // Add mode - direct position
            centerCoord = coord;
            paintColor = (patternEntry?.blocked ?? false)
                ? appState.assemblyHandleBlockedColor
                : (attachMode == 'top' ? Colors.blue : Colors.orange);
          }

          final Paint hoverRodPaint = Paint()
            ..color = paintColor.withValues(alpha: 0.5)
            ..strokeWidth = appState.gridSize / 2
            ..style = PaintingStyle.fill;

          if (!hoverValid) {
            hoverRodPaint.shader = CrossHatchShader.shader;
            hoverRodPaint.color = Colors.red;
          }

          centerCoord = attachMode == 'top'
              ? centerCoord - Offset(0, squareSide / 4)
              : centerCoord + Offset(0, squareSide / 4);

          final rect = Rect.fromCenter(
            center: centerCoord,
            width: squareSide,
            height: squareSide / 2,
          );

          // Fill rectangle
          canvas.drawRect(rect, hoverRodPaint);

          // Draw handle value text for Add mode
          // blocked pattern entries are shown by colour only, matching how the slat painter draws blocks
          String displayText = moveAnchor != Offset.zero
              ? (attachMode == 'top' ? '↑' : '↓')
              : patternEntry != null
                  ? (patternEntry.blocked ? '' : patternEntry.value)
                  : actionState.assemblyHandleValue;
          drawText(displayText, centerCoord, Colors.white, squareSide * 0.4);

          // Outline with thin black border
          final borderPaint = Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = 0.1
            ..color = Colors.black;

          canvas.drawRect(rect, borderPaint);
        }
        if (patternEntries != null && patternEntries.isNotEmpty && moveAnchor == Offset.zero) {
          drawPatternNorthGuide(patternEntries, hoverPosition!);
        }
      } else {
        // Cargo handle hover drawing
        for (var coord in cargoArrayPoints.values) {
          double squareSide = appState.gridSize * 0.85;
          Offset centerCoord;
          Color paintColor;

          if (moveAnchor != Offset.zero) {
            centerCoord = appState.convertCoordinateSpacetoRealSpace(coord) + hoverPosition! - moveAnchor;
            paintColor = appState.getCargoFromCoordinate(coord, appState.selectedLayerKey, actionState.cargoAttachMode).color;
          } else {
            centerCoord = coord;
            paintColor = appState.cargoPalette[appState.cargoAdditionType]?.color ?? Colors.grey;
          }

          final Paint hoverRodPaint = Paint()
            ..color = paintColor.withValues(alpha: 0.5)
            ..strokeWidth = appState.gridSize / 2
            ..style = PaintingStyle.fill;

          if (!hoverValid) {
            hoverRodPaint.shader = CrossHatchShader.shader;
            hoverRodPaint.color = Colors.red;
          }

          centerCoord = actionState.cargoAttachMode == 'top'
              ? centerCoord - Offset(0, squareSide / 4)
              : centerCoord + Offset(0, squareSide / 4);

          final rect = Rect.fromCenter(
            center: centerCoord,
            width: squareSide,
            height: squareSide / 2,
          );

          // Fill rectangle
          canvas.drawRect(rect, hoverRodPaint);

          drawText(actionState.cargoAttachMode == 'top' ? '↑' : '↓', centerCoord,
              isColorDark(paintColor) ? Colors.white : Colors.black, squareSide * 0.4);

          // Outline with thin black border
          final borderPaint = Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = 0.1
            ..color = Colors.black;

          canvas.drawRect(rect, borderPaint);
        }
      }
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant HandleHoverPainter oldDelegate) {
    return hoverPosition != oldDelegate.hoverPosition ||
        hoverValid != oldDelegate.hoverValid ||
        patternRotationSteps != oldDelegate.patternRotationSteps;
  }
}