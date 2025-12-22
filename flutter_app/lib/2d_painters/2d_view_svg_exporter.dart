import 'dart:ui';
import 'package:xml/xml.dart';
import '../crisscross_core/slats.dart';
import '../app_management/shared_app_state.dart';
import 'helper_functions.dart';

// Use conditional imports
import 'export_svg_web.dart' if (dart.library.io) 'export_svg_desktop.dart';

String _colorToHex(Color color) {
  return '#${color.value.toRadixString(16).padLeft(8, '0').substring(2)}';
}

Future<void> exportSlatsToSvg({
  required List<Slat> slats,
  required Map<String, Map<String, dynamic>> layerMap,
  required DesignState appState,
  required ActionState actionState,
}) async {
  final gridSize = appState.gridSize;

  double? minX, maxX, minY, maxY;

  // Group <path> elements by layer
  final Map<String, List<XmlElement>> layerGroups = {};

  for (final slat in slats) {
    // Skip hidden layers
    if (layerMap[slat.layer]?['hidden'] == true) continue;

    // Gather ordered coordinates like in slat_painter.dart
    final entries = slat.slatPositionToCoordinate.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key));
    if (entries.isEmpty) continue;

    final coords = entries
        .map((e) => appState.convertCoordinateSpacetoRealSpace(e.value))
        .toList(growable: false);

    // Compute tip extensions just like drawSlat in painter
    final slatExtendFront = calculateSlatExtend(coords[0], coords[1], gridSize);
    final slatExtendBack = calculateSlatExtend(
        coords[coords.length - 2], coords.last, gridSize);

    // Build full list of points to encode into path 'd'
    final List<Offset> pathPoints = [];
    if (actionState.extendSlatTips) {
      pathPoints.add(Offset(
          coords.first.dx - slatExtendFront.dx, coords.first.dy - slatExtendFront.dy));
    } else {
      pathPoints.add(coords.first);
    }
    pathPoints.addAll(coords.skip(1));
    if (actionState.extendSlatTips) {
      pathPoints.add(Offset(
          coords.last.dx + slatExtendBack.dx, coords.last.dy + slatExtendBack.dy));
    }

    // Track bounds (for viewBox) across all path points
    for (final p in pathPoints) {
      minX = (minX == null) ? p.dx : (p.dx < minX ? p.dx : minX);
      maxX = (maxX == null) ? p.dx : (p.dx > maxX ? p.dx : maxX);
      minY = (minY == null) ? p.dy : (p.dy < minY ? p.dy : minY);
      maxY = (maxY == null) ? p.dy : (p.dy > maxY ? p.dy : maxY);
    }

    // Compose SVG path 'd' command: M x0 y0 L x1 y1 ...
    final StringBuffer d = StringBuffer();
    d.write('M ${pathPoints.first.dx.toStringAsFixed(2)} ${pathPoints.first.dy.toStringAsFixed(2)}');
    for (int i = 1; i < pathPoints.length; i++) {
      final p = pathPoints[i];
      d.write(' L ${p.dx.toStringAsFixed(2)} ${p.dy.toStringAsFixed(2)}');
    }

    final Color color = layerMap[slat.layer]?['color'] ?? const Color(0xFF000000);
    final pathEl = XmlElement(XmlName('path'), [
      XmlAttribute(XmlName('id'), slat.id),
      XmlAttribute(XmlName('d'), d.toString()),
      XmlAttribute(XmlName('fill'), 'none'),
      XmlAttribute(XmlName('stroke'), _colorToHex(color)),
      XmlAttribute(XmlName('stroke-width'), (gridSize / 2).toStringAsFixed(2)),
      XmlAttribute(XmlName('stroke-linejoin'), 'round'),
    ]);

    layerGroups.putIfAbsent(slat.layer, () => []).add(pathEl);
  }

  // Provide some padding around the drawing like before
  final width = ((maxX ?? 100) - (minX ?? 0)) + gridSize * 4;
  final height = ((maxY ?? 100) - (minY ?? 0)) + gridSize * 4;
  final viewX = (minX ?? 0) - gridSize * 2;
  final viewY = (minY ?? 0) - gridSize * 2;

  final builder = XmlBuilder();
  builder.processing('xml', 'version="1.0" encoding="UTF-8"');
  builder.element('svg', nest: () {
    builder.attribute('xmlns', 'http://www.w3.org/2000/svg');
    builder.attribute('width', width.toStringAsFixed(2));
    builder.attribute('height', height.toStringAsFixed(2));
    builder.attribute('viewBox',
        '${viewX.toStringAsFixed(2)} ${viewY.toStringAsFixed(2)} ${width.toStringAsFixed(2)} ${height.toStringAsFixed(2)}');

    // Add each layer group
    for (final entry in layerGroups.entries) {
      final layerName = entry.key;
      final paths = entry.value;
      builder.element('g', nest: () {
        builder.attribute('id', layerName);
        for (final path in paths) {
          builder.xml(path.toXmlString());
        }
      });
    }
  });

  final document = builder.buildDocument();
  final svgString = document.toXmlString(pretty: true);
  await saveSvg(svgString, '${appState.designName}_2d_layer_graphics.svg');
}
