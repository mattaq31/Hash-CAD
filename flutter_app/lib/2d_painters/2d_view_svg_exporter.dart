import 'dart:io';
import 'dart:ui';
import 'dart:convert';
import 'dart:js_interop';
import 'package:xml/xml.dart';
import 'package:flutter/foundation.dart';
import 'package:web/web.dart' as web;
import 'package:file_picker/file_picker.dart';
import '../crisscross_core/slats.dart';
import '../app_management/shared_app_state.dart';
import 'helper_functions.dart';

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

  final Map<String, List<XmlElement>> layerGroups = {};

  for (final slat in slats) {
    if (layerMap[slat.layer]?['hidden'] == true) continue;

    Offset p1 = appState.convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[1]!);
    Offset p2 = appState.convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[32]!);

    Offset slatExtend = calculateSlatExtend(p1, p2, appState.gridSize);

    if (actionState.extendSlatTips){
      p1 = Offset(p1.dx - slatExtend.dx, p1.dy - slatExtend.dy);
      p2 = Offset(p2.dx + slatExtend.dx, p2.dy + slatExtend.dy);
    }

    final color = layerMap[slat.layer]?['color'] ?? const Color(0xFF000000);

    minX = [minX ?? p1.dx, p2.dx].reduce((a, b) => a < b ? a : b);
    maxX = [maxX ?? p1.dx, p2.dx].reduce((a, b) => a > b ? a : b);
    minY = [minY ?? p1.dy, p2.dy].reduce((a, b) => a < b ? a : b);
    maxY = [maxY ?? p1.dy, p2.dy].reduce((a, b) => a > b ? a : b);

    final line = XmlElement(XmlName('line'), [
      XmlAttribute(XmlName('id'), slat.id),
      XmlAttribute(XmlName('x1'), p1.dx.toStringAsFixed(2)),
      XmlAttribute(XmlName('y1'), p1.dy.toStringAsFixed(2)),
      XmlAttribute(XmlName('x2'), p2.dx.toStringAsFixed(2)),
      XmlAttribute(XmlName('y2'), p2.dy.toStringAsFixed(2)),
      XmlAttribute(XmlName('stroke'), _colorToHex(color)),
      XmlAttribute(XmlName('stroke-width'), (gridSize / 2).toStringAsFixed(2)),
    ]);

    layerGroups.putIfAbsent(slat.layer, () => []).add(line);
  }

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
    builder.attribute(
        'viewBox',
        '${viewX.toStringAsFixed(2)} ${viewY.toStringAsFixed(2)} '
            '${width.toStringAsFixed(2)} ${height.toStringAsFixed(2)}');

    // Add each layer group
    for (final entry in layerGroups.entries) {
      final layerName = entry.key;
      final lines = entry.value;

      builder.element('g', nest: () {
        builder.attribute('id', layerName);
        for (final line in lines) {
          builder.xml(line.toXmlString());
        }
      });
    }
  });

  final document = builder.buildDocument();
  final svgString = document.toXmlString(pretty: true);

  // file export logic
  if (kIsWeb){
    final bytes = utf8.encode(svgString);
    final blob = web.Blob([bytes.toJS].toJS);
    final url = web.URL.createObjectURL(blob);

    final anchor = web.HTMLAnchorElement()
      ..href = url
      ..download = '${appState.designName}_2d_layer_graphics.svg';
    anchor.click();

    web.URL.revokeObjectURL(url);
  }  else {
    String? filePath = await FilePicker.platform.saveFile(
      dialogTitle: 'Save As',
      fileName: '${appState.designName}_2d_layer_graphics.svg',
      type: FileType.custom,
      allowedExtensions: ['svg'],
    );

    // if filepath is null, return
    if (filePath == null) {
      return;
    }

    final file = File(filePath);
    await file.writeAsString(svgString);
  }

}

