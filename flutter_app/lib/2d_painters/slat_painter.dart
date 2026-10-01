import 'dart:math';
import 'dart:ui';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../crisscross_core/fluorophore.dart';
import '../crisscross_core/slats.dart';
import '../echo_and_experimental_helpers/echo_plate_constants.dart' show slatDisplayName;
import 'helper_functions.dart';
import 'text_painter_cache.dart';
import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';

import '../crisscross_core/seed.dart';

const double kHandleTextMinScale = 2.14;

/// Shared paint for the white divider line between the top/bottom halves of a handle marker.
final Paint _handleDividerPaint = Paint()..color = Colors.white..strokeWidth = 0.5;

/// Shared paint for the dotted red border around handles that failed plate validation.
final Paint _invalidHandlePaint = Paint()..color = Colors.red..style = PaintingStyle.stroke..strokeWidth = 1.0;

/// Shared paint for the dark outline around selected handles.
final Paint _selectedHandlePaint = Paint()
  ..color = Colors.black
  ..style = PaintingStyle.stroke
  ..strokeWidth = 3.0
  ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 0.3);

/// Paint for the translucent layer that dims unselected slats in the selected layer while a selection exists.
final Paint _dimLayerPaint = Paint()..color = Colors.black.withValues(alpha: 0.5);

/// Shared fill paint for the black background behind slat ID labels.
final Paint _slatIdBackgroundPaint = Paint()..color = Colors.black..style = PaintingStyle.fill;

/// Kinds of text label drawn by [SlatPainter] on top of its cached geometry.
enum _SlatLabelKind { handle, number, slatId }

/// A text label recorded while building the slat scene.  Labels are drawn every frame (culled to the viewport and
/// subject to level-of-detail rules) rather than baked into the cached geometry pictures.
class _SlatLabel {
  final _SlatLabelKind kind;
  final String text;
  final Color color;
  final double fontSize;
  /// Centre point of the label in world (canvas) coordinates.
  final Offset position;
  /// True if the owning slat is dimmed (unselected slat in the selected layer while a selection exists).
  final bool dimmed;
  /// Slat ID labels only: rotation (radians) and size of the black background box.
  final double angle;
  final Size backgroundSize;

  const _SlatLabel(this.kind, this.text, this.color, this.fontSize, this.position, this.dimmed,
      {this.angle = 0, this.backgroundSize = Size.zero});
}

/// Geometry for the whole slat layer recorded in world coordinates, plus the labels to overlay on it.
///
/// Rebuilding this is as expensive as one old-style full frame, but it only happens when the design, display settings,
/// selection or hidden items change.  Pan/zoom frames just replay the pictures under a new transform, so their cost no
/// longer grows with the number of slats/handles in view.
class _SlatScene {
  /// Slats in layers at or below the selected layer (the selected layer carries all handles and labels).
  final Picture below;
  /// Slats in layers above the selected layer - drawn after the labels so they still tint them, as before.
  final Picture above;
  final List<_SlatLabel> labels;

  _SlatScene(this.below, this.above, this.labels);
}

/// Inputs that determine the slat scene's contents - when unchanged, the cached scene is reused.
class _SlatSceneKey {
  final DesignState appState;
  final ActionState actionState;
  final int designVersion;
  final int actionVersion;
  final int groupVersion;
  final String selectedLayer;
  final List<String> selectedSlats;
  final List<String> hiddenSlats;
  final List<Offset> hiddenCargo;
  final List<Offset> hiddenAssembly;

  _SlatSceneKey(this.appState, this.actionState, this.designVersion, this.actionVersion, this.groupVersion,
      this.selectedLayer, this.selectedSlats, this.hiddenSlats, this.hiddenCargo, this.hiddenAssembly);

  bool matches(_SlatSceneKey other) =>
      identical(appState, other.appState) &&
      identical(actionState, other.actionState) &&
      designVersion == other.designVersion &&
      actionVersion == other.actionVersion &&
      groupVersion == other.groupVersion &&
      selectedLayer == other.selectedLayer &&
      listEquals(selectedSlats, other.selectedSlats) &&
      listEquals(hiddenSlats, other.hiddenSlats) &&
      listEquals(hiddenCargo, other.hiddenCargo) &&
      listEquals(hiddenAssembly, other.hiddenAssembly);
}

// There is a single 2D canvas, so one cached scene suffices.  Old pictures are left to the garbage collector rather
// than disposed, since a frame already submitted to the raster thread may still reference them.
_SlatSceneKey? _cachedSceneKey;
_SlatScene? _cachedScene;

bool isColorDark(Color color) {
  // Convert color brightness to 0-255 scale
  double brightness = (color.r * 0.299 + color.g * 0.587 + color.b * 0.114);
  return brightness < 0.5; // You can adjust this threshold if needed
}

/// Paints a slat and takes care of adjustments such as drawing aids, tip extensions, etc.
void drawSlat(List<Offset> coords, Canvas canvas, DesignState appState, ActionState actionState, Paint slatPaint, bool phantomSlat){
  Offset slatExtendFront = calculateSlatExtend(coords[0], coords[1], appState.gridSize);
  Offset slatExtendBack = calculateSlatExtend(coords[coords.length - 2], coords.last, appState.gridSize);

  // Build path from the coordinate sequence
  final path = Path(); // TODO: what happens here when there are layer-bridging slats?

  // draws beginning of slat path here
  if (actionState.drawingAids){
    path.moveTo(coords[0].dx - slatExtendFront.dx * 0.5, coords[0].dy - slatExtendFront.dy * 0.5);
  }
  else{
    if (!actionState.extendSlatTips){
      path.moveTo(coords[0].dx, coords[0].dy);
    }
    else{
      path.moveTo(coords[0].dx - slatExtendFront.dx, coords[0].dy - slatExtendFront.dy);
    }
  }
  for (int i = 1; i < coords.length; i++) {
    path.lineTo(coords[i].dx, coords[i].dy);
  }
  if (!actionState.drawingAids && actionState.extendSlatTips){
    path.lineTo(coords.last.dx + slatExtendBack.dx, coords.last.dy + slatExtendBack.dy);
  }

  if (phantomSlat) {
    final color = slatPaint.color;
    final hsl = HSLColor.fromColor(color);
    final hatchColor = isColorDark(color)
        ? hsl.withLightness((hsl.lightness + 0.3).clamp(0.0, 1.0)).toColor()
        : hsl.withLightness((hsl.lightness - 0.3).clamp(0.0, 1.0)).toColor();

    // Use a fraction of gridSize to determine stripe density
    final double patternSize = appState.gridSize / 6;
    final double angle = calculateSlatAngle(coords.first, coords[1]);

    slatPaint.shader = LinearGradient(
      begin: Alignment.centerLeft,
      end: Alignment.centerRight,
      colors: [
        color,
        color,
        hatchColor,
        hatchColor,
      ],
      stops: const [0.0, 0.5, 0.5, 1.0],
      tileMode: TileMode.repeated,
      transform: GradientRotation(angle),
    ).createShader(Rect.fromLTWH(0, 0, patternSize, patternSize));
  }

  // draws final path here
  canvas.drawPath(path, slatPaint);

  if (actionState.drawingAids) {
    drawSlatDrawingAids(
        canvas,
        coords,
        slatExtendFront,
        slatExtendBack,
        appState.gridSize,
        slatPaint,
        slatPaint.color,
        1.0);
  }
}


void drawSlatDrawingAids(Canvas canvas, List coords, Offset slatExtendFront, Offset slatExtendBack, double gridSize, Paint rodPaint, Color color, double slatAlpha){

  // different directions calculated as this can change throughout a customized non-rod slat
  final arrowDirection = (coords.last - coords[coords.length - 2]).direction;
  final tailDirection = (coords[1] - coords.first).direction;

  // Arrowhead at the end
  final arrowSize = gridSize * 0.8;
  final arrowAngle = pi / 4.5;
  final arrowP1 = coords.last + slatExtendBack;
  final arrowLeft = arrowP1 - Offset.fromDirection(arrowDirection - arrowAngle, arrowSize);
  final arrowRight = arrowP1 - Offset.fromDirection(arrowDirection + arrowAngle, arrowSize);

  final arrowPath = Path()
    ..moveTo(arrowP1.dx, arrowP1.dy)
    ..lineTo(arrowLeft.dx, arrowLeft.dy)
    ..lineTo(arrowRight.dx, arrowRight.dy)
    ..close();  // closes the triangle

  final arrowPaint = Paint()
    ..color = rodPaint.color.withValues(alpha: color.a * slatAlpha)
    ..style = PaintingStyle.fill;

  final tailPaint = Paint()
    ..color = rodPaint.color.withValues(alpha: color.a * slatAlpha)
    ..strokeWidth = gridSize / 4
    ..style = PaintingStyle.fill;

  canvas.drawPath(arrowPath, arrowPaint);

  // Tail at the start
  final tailSize = gridSize * 0.4;
  final tailP1 = coords.first - slatExtendFront * 0.7;
  final tailLeft = tailP1 + Offset.fromDirection(tailDirection - pi / 2, tailSize);
  final tailRight = tailP1 + Offset.fromDirection(tailDirection + pi / 2, tailSize);
  canvas.drawLine(tailLeft, tailRight, tailPaint);

  // Dotted lines at 1/4, 1/2, 3/4
  final dottedPaint = Paint()
    ..color = Colors.black.withValues(alpha: color.a * slatAlpha)
    ..strokeWidth = rodPaint.strokeWidth/4
    ..style = PaintingStyle.stroke;

  final dottedCenterPaint = Paint()
    ..color = Colors.black.withValues(alpha: color.a * slatAlpha)
    ..strokeWidth = rodPaint.strokeWidth/2
    ..style = PaintingStyle.stroke;

  // dash parameters
  const dashSize = 1.0;
  const gapSize = 1.0;
  final dashCount = 5;

  //  calculate and apply dotted lines at 1/4, 1/2, 3/4 of the slat length
  for (final fraction in [4, 2, 1.3333333]) {
    Offset? middle;
    List<Offset>? middlePair;
    Offset? centerPoint;
    double fracDirection;

    // if odd handle count, there should be a single middle point
    if (coords.length.isOdd){
      middle = coords[coords.length ~/ fraction];
      fracDirection = (coords[(coords.length ~/ fraction) + 1] - coords[(coords.length ~/ fraction) - 1]).direction;
      centerPoint = middle;
    }
    // if even handle count, need to find surrounding middle handle pair
    else{
      middlePair = [
        coords[(coords.length ~/ fraction) - 1],
        coords[coords.length ~/ fraction],
      ];
      fracDirection = (middlePair[1] - middlePair[0]).direction;
      centerPoint = (middlePair[0] + middlePair[1]) / 2;
    }

    final totalDashLength = dashSize * dashCount + gapSize * (dashCount - 1);
    final perpDirection = Offset.fromDirection(fracDirection + pi / 2, 1.0);
    final start = centerPoint! - perpDirection * (totalDashLength / 2);

    for (int i = 0; i < dashCount; i++) {
      final dStart = start + perpDirection * i.toDouble() * (dashSize + gapSize);
      final dEnd = dStart + perpDirection * dashSize;
      canvas.drawLine(dStart, dEnd, fraction == 0.5 ? dottedCenterPaint : dottedPaint);
    }
  }
}

/// Custom painter for the slats themselves
class SlatPainter extends CustomPainter {
  final double scale;
  final Offset canvasOffset;

  final Map<String, Map<String, dynamic>> layerMap;
  final List<Slat> slats;
  final String selectedLayer;
  final List<String> selectedSlats;
  final List<String> hiddenSlats;
  final List<Offset> hiddenCargo;
  final List<Offset> hiddenAssembly;
  final ActionState actionState;
  final DesignState appState;
  final int groupVersion;

  /// Bumped on every DesignState/ActionState notification - lets [shouldRepaint] skip repaints when neither changed
  /// (e.g. pure hover moves), since both states are mutated in place and can't be compared by identity.
  final int designVersion;
  final int actionVersion;

  SlatPainter(this.scale, this.canvasOffset, this.slats,
      this.layerMap, this.selectedLayer, this.selectedSlats, this.hiddenSlats,
      this.hiddenCargo, this.hiddenAssembly, this.actionState, this.appState, this.groupVersion,
      {this.designVersion = 0, this.actionVersion = 0});


  Offset getRealCoord(Offset slatCoord){
    return appState.convertCoordinateSpacetoRealSpace(slatCoord);
  }

  /// draws a dotted border around a slat when selected
  void drawBorder(Canvas canvas, List<Offset> coords, Color color, Offset slatExtend, bool slatTipExtended, String slatType) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = appState.gridSize / 6
      ..strokeCap = StrokeCap.round;

    final spacing = appState.gridSize / 4;

    Offset flippedSlatExtend;

    if (appState.gridMode == '60'){
      // for the 60 degree system, the slats are extended out by 90 degrees from their positions (since they are rectangular).
      // Their angle doesn't exactly match the grid angle, and so the spacing between slats is not precisely gridSize/2.
      // If you calculate the geometry (assuming parallel lines), the actual distance between slats is instead gridSize * sqrt(3)/2 i.e. sin 60deg.
      Offset interSlatExtend = calculateSlatExtend(coords.first, coords[2], appState.gridSize * sqrt(3)/2);

      // since cos (90 - x) = sin(x) and vice versa
      // the negative sign is included due to the directionality of the grid (up = -ve, left = -ve, down = +ve, right = +ve)
      flippedSlatExtend = Offset(-interSlatExtend.dy, interSlatExtend.dx);
    }
    else {
      // since cos (90 - x) = sin(x) and vice versa
      // the negative sign is included due to the directionality of the grid (up = -ve, left = -ve, down = +ve, right = +ve)
      flippedSlatExtend = Offset(-slatExtend.dy, slatExtend.dx);
    }

    // the below contain the calculations for precisely framing slats according to their shape.  If tip extensions are enabled, these also need to be included to add some extra space
    // TODO: the below could probably be streamlined further but works well for now
    Map<String, dynamic> coordinateBuilder = {};
    coordinateBuilder['tube'] = {
      '1a': 0,
      '1b': 0,
      '2a': 31,
      '2b': 31,
      'slatExtend1a': slatTipExtended? 1.5: 0.5,
      'slatExtend1b': slatTipExtended? 1.5: 0.5,
      'slatExtend2a': slatTipExtended? 1.5: 0.5,
      'slatExtend2b': slatTipExtended? 1.5: 0.5,
      'yFlip': 1.0,
      'slatExtendX': 0.5,
      'slatExtendXMax': 1.5,
      'slatExtendY': 0.5,
      'slatExtendYMax': 1.5
    };

    coordinateBuilder['DB-L'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 1.3,
      'slatExtend2b': 1.3,
      'yFlip': 1.0
    };
    coordinateBuilder['DB-R'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 1.3,
      'slatExtend2b': 1.3,
      'yFlip': -1.0
    };
    coordinateBuilder['DB-L-60'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 1.6,
      'slatExtend2b': 0.7,
      'yFlip': 1.0
    };
    coordinateBuilder['DB-L-120'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 0.7,
      'slatExtend2b': 1.6,
      'yFlip': 1.0
    };

    coordinateBuilder['DB-R-120'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 0.7,
      'slatExtend2b': 1.6,
      'yFlip': -1.0
    };

    coordinateBuilder['DB-R-60'] = {
      '1a': 31,
      '1b': 0,
      '2a': 15,
      '2b': 16,
      'slatExtend1a': slatTipExtended? 1.6: 0.6,
      'slatExtend1b': slatTipExtended? 1.6: 0.6,
      'slatExtend2a': 1.6,
      'slatExtend2b': 0.7,
      'yFlip': -1.0
    };

    var pData = coordinateBuilder[slatType];

    Offset slatP1A = coords[pData['1a']] - slatExtend * pData['slatExtend1a'] + flippedSlatExtend * pData['yFlip'];
    Offset slatP1B = coords[pData['1b']] - slatExtend * pData['slatExtend1b'] - flippedSlatExtend * pData['yFlip'];
    Offset slatP2A = coords[pData['2a']] + slatExtend * pData['slatExtend2a'] - flippedSlatExtend * pData['yFlip'];
    Offset slatP2B = coords[pData['2b']] + slatExtend * pData['slatExtend2b'] + flippedSlatExtend * pData['yFlip'];

    // Function to generate spaced points between two given points
    List<Offset> generateDots(Offset start, Offset end) {
      double distance = (end - start).distance;
      int dotCount = (distance / spacing).floor();
      List<Offset> dots = [];

      for (int i = 1; i <= dotCount; i++) {
        double t = i / (dotCount + 1); // Interpolation factor
        Offset dot = Offset(
          start.dx + (end.dx - start.dx) * t,
          start.dy + (end.dy - start.dy) * t,
        );
        dots.add(dot);
      }
      return dots;
    }

    // Generate dots for all four edges
    List<Offset> dots = [
      ...generateDots(slatP1A, slatP1B),
      ...generateDots(slatP1A, slatP2B),
      ...generateDots(slatP1B, slatP2A),
      ...generateDots(slatP2A, slatP2B),
    ];

    // Draw all dots at once
    canvas.drawPoints(PointMode.points, dots, paint);
  }

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(canvasOffset.dx, canvasOffset.dy);
    canvas.scale(scale);

    // current viewport bounds
    final visibleRect = Rect.fromLTWH(
      -canvasOffset.dx / scale,
      -canvasOffset.dy / scale,
      size.width / scale,
      size.height / scale,
    );

    final key = _SlatSceneKey(appState, actionState, designVersion, actionVersion, groupVersion, selectedLayer,
        selectedSlats, hiddenSlats, hiddenCargo, hiddenAssembly);
    if (_cachedScene == null || !_cachedSceneKey!.matches(key)) {
      _cachedScene = _buildScene();
      _cachedSceneKey = key;
    }
    final scene = _cachedScene!;

    canvas.drawPicture(scene.below);
    _drawLabels(canvas, scene.labels, visibleRect);
    canvas.drawPicture(scene.above);

    canvas.restore();
  }

  /// Draws the visible text labels on top of the cached geometry, skipping text that would be too small to read.
  void _drawLabels(Canvas canvas, List<_SlatLabel> labels, Rect visibleRect) {
    const double minReadableTextPx = 4.0;
    final bool drawHandleText = scale >= kHandleTextMinScale;
    final bool drawNumberText = appState.gridSize * 0.4 * scale >= minReadableTextPx;
    final bool drawSlatIdText = appState.gridSize * 0.6 * scale >= minReadableTextPx;
    if (!drawHandleText && !drawNumberText && !drawSlatIdText) return;

    // labels never extend further than a long slat ID box (6 grid units wide) from their centre
    final cullRect = visibleRect.inflate(appState.gridSize * 3.5);
    final isWeb = kIsWeb;
    bool dimLayerOpen = false;

    for (final label in labels) {
      switch (label.kind) {
        case _SlatLabelKind.handle:
          if (!drawHandleText) continue;
        case _SlatLabelKind.number:
          if (!drawNumberText) continue;
        case _SlatLabelKind.slatId:
          if (!drawSlatIdText) continue;
      }
      if (!cullRect.contains(label.position)) continue;

      // dimmed slats' labels are dimmed as a block, matching how their geometry was recorded
      if (label.dimmed && !dimLayerOpen) {
        canvas.saveLayer(visibleRect, _dimLayerPaint);
        dimLayerOpen = true;
      } else if (!label.dimmed && dimLayerOpen) {
        canvas.restore();
        dimLayerOpen = false;
      }

      final textPainter = TextPainterCache.get(label.text, label.color, label.fontSize);
      switch (label.kind) {
        case _SlatLabelKind.handle:
          textPainter.paint(canvas, Offset(label.position.dx - textPainter.width / 2 - 0.1,
              label.position.dy - textPainter.height / 2 + 0.2));
        case _SlatLabelKind.number:
          textPainter.paint(canvas, label.position - Offset(textPainter.width / 2, textPainter.height / 2));
        case _SlatLabelKind.slatId:
          double baselineOffset;
          if (isWeb || defaultTargetPlatform == TargetPlatform.windows) {
            baselineOffset = textPainter.height + 0.5;
          } else {
            baselineOffset = textPainter.computeDistanceToActualBaseline(TextBaseline.alphabetic);
          }
          canvas.save();
          canvas.translate(label.position.dx, label.position.dy);
          canvas.rotate(label.angle);
          canvas.drawRect(
              Rect.fromCenter(center: Offset.zero, width: label.backgroundSize.width, height: label.backgroundSize.height),
              _slatIdBackgroundPaint);
          textPainter.paint(canvas, Offset(-textPainter.width / 2 - 0.1, -baselineOffset / 2 - 0.9));
          canvas.restore();
      }
    }
    if (dimLayerOpen) canvas.restore();
  }

  /// Records every slat (no viewport culling) into world-space pictures and collects the text labels to overlay.
  _SlatScene _buildScene() {
    final recorderBelow = PictureRecorder();
    final recorderAbove = PictureRecorder();
    final canvasBelow = Canvas(recorderBelow);
    final canvasAbove = Canvas(recorderAbove);
    final List<_SlatLabel> labels = [];

    // Sets for the per-handle lookups below (the incoming lists would make each check O(n))
    final Set<String> hiddenSlatSet = hiddenSlats.toSet();
    final Set<Offset> hiddenCargoSet = hiddenCargo.toSet();
    final Set<Offset> hiddenAssemblySet = hiddenAssembly.toSet();
    final Set<Offset> selectedHandleSet = appState.selectedHandlePositions.toSet();
    final Set<Offset> selectedAssemblySet = appState.selectedAssemblyPositions.toSet();

    // a single fill paint is recoloured for every handle marker rather than allocating one per marker
    final Paint markerPaint = Paint()..style = PaintingStyle.fill;

    final sortedSlats = List<Slat>.from(slats)
      ..sort((a, b) => layerMap[a.layer]?['order'].compareTo(layerMap[b.layer]?['order']));

    // When slats are selected, the rest of the selected layer is dimmed to make the selection stand out.  The dimmed
    // slats are drawn as one contiguous block inside a single translucent layer (so their handles/labels dim with them),
    // which means the selected layer is drawn as: unselected slats first, then the selected ones on top.
    final Set<String> selectedSet = selectedSlats.toSet();
    final int selectedOrder = layerMap[selectedLayer]?['order'] ?? 0;
    final List<Slat> drawOrder = [
      ...sortedSlats.where((sl) => layerMap[sl.layer]?['order'] < selectedOrder),
      ...sortedSlats.where((sl) => sl.layer == selectedLayer && !selectedSet.contains(sl.id)),
      ...sortedSlats.where((sl) => sl.layer == selectedLayer && selectedSet.contains(sl.id)),
      ...sortedSlats.where((sl) => layerMap[sl.layer]?['order'] > selectedOrder),
    ];
    final bool dimUnselected = selectedSet.isNotEmpty;
    bool dimLayerOpen = false;

    String selectedLayerTopside = (layerMap[selectedLayer]?['top_helix'] == 'H5') ? 'H5' : 'H2';
    for (var slat in drawOrder) {

      // open/close the dimming layer at the boundaries of the dimmed block (before any early 'continue')
      final bool dimThisSlat = dimUnselected && slat.layer == selectedLayer && !selectedSet.contains(slat.id);
      if (dimThisSlat && !dimLayerOpen) {
        canvasBelow.saveLayer(null, _dimLayerPaint);
        dimLayerOpen = true;
      } else if (!dimThisSlat && dimLayerOpen) {
        canvasBelow.restore();
        dimLayerOpen = false;
      }

      // slats above the selected layer go into the second picture so they're drawn over the label overlay
      final Canvas canvas = (layerMap[slat.layer]?['order'] ?? 0) > selectedOrder ? canvasAbove : canvasBelow;

      // logic on whether slat should be hidden (or otherwise)
      if (hiddenSlatSet.contains(slat.id)){
        continue;
      }

      // turns off phantoms if the user has chosen to not view them
      if(slat.phantomParent != null && !actionState.viewPhantoms){
        continue;
      }

      if (layerMap[slat.layer]?['hidden']) {
        continue;
      }
      if (actionState.isolateSlatLayerView && slat.layer != selectedLayer) {
        continue;
      }

      // main slat paint setup
      Color mainColor;
      switch (actionState.slatColorMode) {
        case SlatColorMode.natural:
          mainColor = slat.uniqueColor ?? layerMap[slat.layer]?['color'];
        case SlatColorMode.layer:
          mainColor = layerMap[slat.layer]?['color'];
        case SlatColorMode.group:
          mainColor = appState.resolveGroupColor(slat.id) ?? layerMap[slat.layer]?['color'];
      }
      Paint rodPaint = Paint()
        ..color = mainColor
        ..strokeWidth = appState.gridSize / 2
        ..style = PaintingStyle.stroke;
      if (slat.layer != selectedLayer) {
        rodPaint = Paint()
          ..color = mainColor.withValues(alpha: mainColor.a * 0.2)
          ..strokeWidth = appState.gridSize / 2
          ..style = PaintingStyle.stroke;
      }

      // gathers all the coordinates for the selected slat
      List sortedCoords = slat.slatPositionToCoordinate.entries.toList()..sort((a, b) => a.key.compareTo(b.key)); // sort by the integer key

      List<Offset> coords = sortedCoords.map((e) => getRealCoord(e.value)).toList();

      // draw the actual slat here
      drawSlat(coords, canvas, appState, actionState, rodPaint, slat.phantomParent != null);

      // slat extension angles and lengths (in case this is requested by the user)
      Offset slatExtendFront = calculateSlatExtend(coords[0], coords[1], appState.gridSize);

      // Draw slat position numbers if activated
      if (slat.layer == selectedLayer && actionState.slatNumbering) {
        final Color numberColor = isColorDark(mainColor) ? Colors.white : Colors.black;
        int i = 1;
        for (Offset coord in coords) {
          labels.add(_SlatLabel(_SlatLabelKind.number, '$i', numberColor, appState.gridSize * 0.4, coord, dimThisSlat));
          i++;
        }
      }

      if (slat.layer == selectedLayer && (actionState.displayAssemblyHandles || actionState.displayCargoHandles)) {
        for (int i = 0; i < slat.maxLength; i++) {
          final int handleIndex = i + 1;
          final h5 = slat.h5Handles[handleIndex];
          final h2 = slat.h2Handles[handleIndex];

          if (h5 == null && h2 == null) continue;

          Set<String> categoriesPresent = {
            if (h5 != null) h5["category"],
            if (h2 != null) h2["category"],
          };

          // the below controls the logic and formatting for placing handle markers on slats
          if ((actionState.displayAssemblyHandles && (categoriesPresent.contains('ASSEMBLY_HANDLE') || categoriesPresent.contains('ASSEMBLY_ANTIHANDLE'))) || (actionState.displayCargoHandles && (categoriesPresent.contains('CARGO') || categoriesPresent.contains('SEED')))) {
            String topText = '↑X';
            String bottomText = '↓X';
            Color topColor = Colors.grey;
            Color bottomColor = Colors.grey;
            String topCategory = '';
            String bottomCategory = '';
            bool topValid = true;
            bool bottomValid = true;

            void updateHandleData(Map<String, dynamic> handle, String side, int sideName) {
              final category = handle["category"];
              final descriptor = handle["value"];
              final isTop = side == "top";

              // Check if blocked (value is '0')
              bool isBlocked = descriptor == '0' || descriptor == 0;

              if (isBlocked) {
                if (isTop) {
                  topText = '↑X';
                  topColor = appState.assemblyHandleBlockedColor;
                  topCategory = category;
                } else {
                  bottomText = '↓X';
                  bottomColor = appState.assemblyHandleBlockedColor;
                  bottomCategory = category;
                }
                return; // Early return for blocked handles
              }

              String shortText = descriptor.toString();
              Color color = Colors.grey;

              if (actionState.plateValidation) {
                if (isTop) {
                  topValid = !slat.checkPlaceholder(handleIndex, sideName);
                }
                else {
                  bottomValid = !slat.checkPlaceholder(handleIndex, sideName);
                }
              }

              if (category == 'CARGO') {
                shortText = appState.cargoPalette[descriptor]?.shortName ?? descriptor;
                color = appState.cargoPalette[descriptor]?.color ?? Colors.grey;
              } else if (category.contains('ASSEMBLY')) {
                if (appState.assemblyLinkManager.handleLinkToGroup.containsKey((slat.id, handleIndex, sideName))) {
                  color = appState.assemblyHandleLinkedColor;
                } else if (slat.phantomParent != null) {
                  color = category == 'ASSEMBLY_ANTIHANDLE' ? appState.assemblyHandlePhantomAntiColor : appState.assemblyHandlePhantomColor;
                } else if (category == 'ASSEMBLY_ANTIHANDLE') {
                  color = appState.assemblyHandleAntiHandleColor;
                } else {
                  color = appState.assemblyHandleHandleColor;
                }
              } else if (category == 'SEED') {
                color = appState.cargoPalette['SEED']!.color;
                shortText = '🌱${getIndexFromSeedText(descriptor)}';
              }

              if (isTop) {
                topText = category == 'SEED' ? shortText : '↑$shortText';
                topColor = color;
                topCategory = category;
              } else {
                bottomText = category == 'SEED' ? shortText : '↓$shortText';
                bottomColor = color;
                bottomCategory = category;
              }
            }

            if (h5 != null && h5['category'] != 'FLAT') {
              final side = selectedLayerTopside == 'H5' ? 'top' : 'bottom';
              updateHandleData(h5, side, 5);
            }
            if (h2 != null && h2['category'] != 'FLAT') {
              final side = selectedLayerTopside == 'H2' ? 'top' : 'bottom';
              updateHandleData(h2, side, 2);
            }

            final standardizedPosition = slat.slatPositionToCoordinate[handleIndex]!;
            final position = getRealCoord(standardizedPosition);

            final size = appState.gridSize * 0.85;
            final halfHeight = size / 2;

            final rectTop = Rect.fromCenter(
              center: Offset(position.dx, position.dy - halfHeight / 2),
              width: size,
              height: halfHeight,
            );

            final rectBottom = Rect.fromCenter(
              center: Offset(position.dx, position.dy + halfHeight / 2),
              width: size,
              height: halfHeight,
            );

            void drawHandleMarker(Rect rect, Color color, String category, bool isTop, bool isSelected) {
              final paint = markerPaint..color = color;

              if (isSelected) {
                final glowRect = rect.inflate(appState.gridSize/30); // push glow outside box
                canvas.drawRRect(
                  RRect.fromRectAndRadius(glowRect, const Radius.circular(2)),
                  _selectedHandlePaint,
                );
              }

              if (category == 'UNUSED') { // not doing triangles for now
                final path = Path();
                final centerX = rect.center.dx;
                final topY = rect.top;
                final bottomY = rect.bottom;

                if (isTop) {
                  path.moveTo(centerX, topY); // Top center
                  path.lineTo(rect.left, bottomY); // Bottom left
                  path.lineTo(rect.right, bottomY); // Bottom right
                } else {
                  path.moveTo(centerX, bottomY); // Bottom center
                  path.lineTo(rect.left, topY); // Top left
                  path.lineTo(rect.right, topY); // Top right
                }
                path.close();
                canvas.drawPath(path, paint);
              } else {
                canvas.drawRect(rect, paint);
              }

              final isInvalid = (isTop && !topValid) || (!isTop && !bottomValid);

              // Draw dotted red border if invalid
              if (isInvalid) {
                const double dotLength = 0.5;
                const double gapLength = 0.5;

                // all dashes are collected as start/end pairs and drawn in one drawPoints call
                final List<Offset> dashPoints = [];
                void addDottedLine(Offset start, Offset end) {
                  final totalLength = (end - start).distance;
                  final offset = end - start;
                  final direction = offset / offset.distance;

                  double drawn = 0;
                  while (drawn < totalLength) {
                    dashPoints.add(start + direction * drawn);
                    dashPoints.add(start + direction * (drawn + dotLength).clamp(0, totalLength));
                    drawn += dotLength + gapLength;
                  }
                }

                addDottedLine(rect.topLeft, rect.topRight);
                addDottedLine(rect.topRight, rect.bottomRight);
                addDottedLine(rect.bottomRight, rect.bottomLeft);
                addDottedLine(rect.bottomLeft, rect.topLeft);
                canvas.drawPoints(PointMode.lines, dashPoints, _invalidHandlePaint);
              }
            }


            bool topHandleHidden = (hiddenCargoSet.contains(standardizedPosition) && actionState.cargoAttachMode == 'top') || (hiddenAssemblySet.contains(standardizedPosition) && actionState.assemblyAttachMode == 'top') || topCategory == '';
            bool bottomHandleHidden = (hiddenCargoSet.contains(standardizedPosition) && actionState.cargoAttachMode == 'bottom') || (hiddenAssemblySet.contains(standardizedPosition) && actionState.assemblyAttachMode == 'bottom') || bottomCategory == '';
            // top/bottom-only assembly handle view (selected in the assembly handles sidebar) - cargo is unaffected
            if (actionState.assemblyHandleViewSide == 'top' && bottomCategory.contains('ASSEMBLY')) bottomHandleHidden = true;
            if (actionState.assemblyHandleViewSide == 'bottom' && topCategory.contains('ASSEMBLY')) topHandleHidden = true;
            // Blocked handles now have ASSEMBLY category with value '0', so they pass the category.contains('ASSEMBLY') check
            bool topHandleSelected = (selectedHandleSet.contains(standardizedPosition) && actionState.cargoAttachMode == 'top') || (selectedAssemblySet.contains(standardizedPosition) && actionState.assemblyAttachMode == 'top' && topCategory.contains('ASSEMBLY'));
            bool bottomHandleSelected = (selectedHandleSet.contains(standardizedPosition) && actionState.cargoAttachMode == 'bottom') || (selectedAssemblySet.contains(standardizedPosition) && actionState.assemblyAttachMode == 'bottom' && bottomCategory.contains('ASSEMBLY'));

            // Check for enforced values (enforced value of 0 means blocked, so skip those)
            String slatKeyId = slat.phantomParent ?? slat.id;
            int topSide = selectedLayerTopside == 'H5' ? 5 : 2;
            int bottomSide = selectedLayerTopside == 'H5' ? 2 : 5;
            var topEnforcedValue = appState.assemblyLinkManager.getEnforceValue((slatKeyId, handleIndex, topSide));
            var bottomEnforcedValue = appState.assemblyLinkManager.getEnforceValue((slatKeyId, handleIndex, bottomSide));
            bool topEnforced = topEnforcedValue != null && topEnforcedValue > 0;
            bool bottomEnforced = bottomEnforcedValue != null && bottomEnforcedValue > 0;

            if (topHandleHidden && bottomHandleHidden) {
              continue; // Skip drawing if both handles are hidden
            }

            void drawText(String text, Offset offset, Color textColor, double fontSize) {
              labels.add(_SlatLabel(_SlatLabelKind.handle, text, textColor, fontSize, offset, dimThisSlat));
            }

            // Helper to draw enforced value indicator (dot at top-left corner)
            void drawEnforcedIndicator(Rect rect, Color fontColor) {
              final dotRadius = rect.width * 0.05;
              final paint = markerPaint..color = fontColor;
              canvas.drawCircle(
                Offset(rect.left + dotRadius * 1.5, rect.top + dotRadius + 0.5),
                dotRadius,
                paint,
              );
            }

            // Helper to draw fluorophore shape marker (bottom-left corner)
            void drawFluorophoreMarker(Rect rect, FluorophoreShape shape, Color fontColor) {
              final size = rect.width * 0.05;
              final center = Offset(rect.left + size * 1.5, rect.bottom - size * 2.5);
              final paint = markerPaint..color = fontColor;

              switch (shape) {
                case FluorophoreShape.square:
                  canvas.drawRect(Rect.fromCenter(center: center, width: size * 2, height: size * 2), paint);
                  break;
                case FluorophoreShape.dot:
                  canvas.drawCircle(center, size, paint);
                  break;
                case FluorophoreShape.diamond:
                  final dSize = size * 1.3;
                  final path = Path()
                    ..moveTo(center.dx, center.dy - dSize)
                    ..lineTo(center.dx + dSize, center.dy)
                    ..lineTo(center.dx, center.dy + dSize)
                    ..lineTo(center.dx - dSize, center.dy)
                    ..close();
                  canvas.drawPath(path, paint);
                  break;
                case FluorophoreShape.star:
                  final outerRadius = size * 1.4;
                  final innerRadius = outerRadius * 0.45;
                  final path = Path();
                  for (int j = 0; j < 8; j++) {
                    final radius = j.isEven ? outerRadius : innerRadius;
                    final angle = (j * pi / 4) - pi / 2;
                    final x = center.dx + radius * cos(angle);
                    final y = center.dy + radius * sin(angle);
                    if (j == 0) {
                      path.moveTo(x, y);
                    } else {
                      path.lineTo(x, y);
                    }
                  }
                  path.close();
                  canvas.drawPath(path, paint);
                  break;
              }
            }

            // Check for fluorophore markers
            final topHandle = topSide == 5 ? h5 : h2;
            final bottomHandle = bottomSide == 5 ? h5 : h2;
            final topFluorophore = topHandle?['fluorophore'] as String?;
            final bottomFluorophore = bottomHandle?['fluorophore'] as String?;
            final topMarker = topFluorophore == null ? null : appState.fluorophorePalette[topFluorophore];
            final bottomMarker = bottomFluorophore == null ? null : appState.fluorophorePalette[bottomFluorophore];

            if (!topHandleHidden) {
              drawHandleMarker(rectTop, topColor, topCategory, true, topHandleSelected);
              final topFontColor = isColorDark(topColor) ? Colors.white : Colors.black;
              if (topEnforced) drawEnforcedIndicator(rectTop, topFontColor);
              if (topMarker != null) {
                drawFluorophoreMarker(rectTop, topMarker.shape, topFontColor);
              }
              drawText(topText, Offset(position.dx, position.dy - halfHeight / 2),
                  topFontColor, halfHeight * 0.8);
            }
            if (!bottomHandleHidden) {
              drawHandleMarker(rectBottom, bottomColor, bottomCategory, false, bottomHandleSelected);
              final bottomFontColor = isColorDark(bottomColor) ? Colors.white : Colors.black;
              if (bottomEnforced) drawEnforcedIndicator(rectBottom, bottomFontColor);
              if (bottomMarker != null) {
                drawFluorophoreMarker(rectBottom, bottomMarker.shape, bottomFontColor);
              }
              drawText(bottomText, Offset(position.dx, position.dy + halfHeight / 2),
                  bottomFontColor, halfHeight * 0.8);
            }

            canvas.drawLine(
              Offset(rectTop.left, position.dy),
              Offset(rectTop.right, position.dy),
              _handleDividerPaint,
            );
          }
        }
      }

      // displays slat IDs as an overlay on top of the slat
      if (actionState.displaySlatIDs && slat.layer == selectedLayer){

        // find the center of all coords
        double sumX = 0, sumY = 0;
        for (final c in coords) {
          sumX += c.dx;
          sumY += c.dy;
        }

        Offset center = Offset(sumX / coords.length, sumY / coords.length);

        // assume angle can be found correctly from middle coords - might need to change if some weird slat types are used
        double angle = calculateSlatAngle(coords[coords.length ~/ 2], coords[(coords.length ~/ 2) + 1]);

        // Flip upside-down labels
        if (angle > pi / 2 || angle < -pi / 2) {
          angle += pi;
        }

        // the ID box and text are both drawn in the label overlay so the box sits above the handle text, as before
        labels.add(_SlatLabel(
          _SlatLabelKind.slatId,
          slatDisplayName(slat, layerMap, slats: appState.slats) + (slat.slatType != 'tube' ? ' (${slat.slatType})' : ''),
          Colors.white,
          appState.gridSize * 0.6,
          center,
          dimThisSlat,
          angle: angle,
          backgroundSize: Size(slat.slatType == 'tube' ? appState.gridSize * 3 : appState.gridSize * 6, appState.gridSize * 0.85),
        ));
      }

      if (selectedSlats.contains(slat.id)) {
        drawBorder(canvas, coords, mainColor, slatExtendFront, (actionState.drawingAids || actionState.extendSlatTips), slat.slatType);
      }
    }
    if (dimLayerOpen) canvasBelow.restore(); // the dimmed block ran to the end of the draw order

    return _SlatScene(recorderBelow.endRecording(), recorderAbove.endRecording(), labels);
  }

  @override
  bool shouldRepaint(covariant SlatPainter oldDelegate) {
    // Slats, selections and display settings live inside the mutable DesignState/ActionState objects, so changes to
    // them are detected via the version counters rather than by comparing the (in-place mutated) collections.
    return oldDelegate.scale != scale ||
        oldDelegate.canvasOffset != canvasOffset ||
        oldDelegate.designVersion != designVersion ||
        oldDelegate.actionVersion != actionVersion ||
        oldDelegate.selectedLayer != selectedLayer ||
        !listEquals(oldDelegate.selectedSlats, selectedSlats) ||
        !listEquals(oldDelegate.hiddenSlats, hiddenSlats) ||
        !listEquals(oldDelegate.hiddenCargo, hiddenCargo) ||
        !listEquals(oldDelegate.hiddenAssembly, hiddenAssembly) ||
        oldDelegate.actionState != actionState ||
        oldDelegate.groupVersion != groupVersion ||
        oldDelegate.appState != appState;
  }
}
