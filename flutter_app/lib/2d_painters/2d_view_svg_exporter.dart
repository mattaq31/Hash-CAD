import 'dart:math';
import 'package:flutter/material.dart';
import 'package:xml/xml.dart';

import '../crisscross_core/slats.dart';
import '../crisscross_core/seed.dart';
import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import 'slat_painter.dart';
import 'helper_functions.dart';

// Use conditional imports
import 'export_svg_web.dart' if (dart.library.io) 'export_svg_desktop.dart';

String _colorToHex(Color color) {
  return '#${color.toARGB32().toRadixString(16).padLeft(8, '0').substring(2)}';
}

/// Shows a dialog for selecting SVG export options.
/// Returns null if cancelled, otherwise returns a map of export options.
Future<Map<String, dynamic>?> showSvgExportDialog(
  BuildContext context,
  ActionState actionState,
) async {
  bool exportPositionNumbers = actionState.slatNumbering;
  bool exportCargoHandles = actionState.displayCargoHandles;
  bool exportAssemblyHandles = actionState.displayAssemblyHandles;
  bool exportSlatIDs = actionState.displaySlatIDs;
  String layerMode = 'fullStack'; // 'fullStack' or 'highlightCurrent'

  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (context, setDialogState) => AlertDialog(
        title: const Text('SVG Export Options'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Elements to include:',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              CheckboxListTile(
                title: const Text('Position Numbers'),
                subtitle: const Text('Handle position numbers (1, 2, 3...) on slats'),
                value: exportPositionNumbers,
                onChanged: (value) {
                  setDialogState(() => exportPositionNumbers = value ?? false);
                },
              ),
              CheckboxListTile(
                title: const Text('Cargo/Seed Handles'),
                subtitle: const Text('Cargo markers and seed handles'),
                value: exportCargoHandles,
                onChanged: (value) {
                  setDialogState(() => exportCargoHandles = value ?? false);
                },
              ),
              CheckboxListTile(
                title: const Text('Assembly Handles'),
                subtitle: const Text('Assembly handle markers'),
                value: exportAssemblyHandles,
                onChanged: (value) {
                  setDialogState(() => exportAssemblyHandles = value ?? false);
                },
              ),
              CheckboxListTile(
                title: const Text('Slat IDs'),
                subtitle: const Text('Slat ID labels centered on slats'),
                value: exportSlatIDs,
                onChanged: (value) {
                  setDialogState(() => exportSlatIDs = value ?? false);
                },
              ),
              const SizedBox(height: 16),
              const Text(
                'Layer rendering:',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              RadioListTile<String>(
                title: const Text('Full opacity stack'),
                subtitle: const Text('All layers shown at full opacity in order'),
                value: 'fullStack',
                groupValue: layerMode,
                onChanged: (value) {
                  setDialogState(() => layerMode = value!);
                },
              ),
              RadioListTile<String>(
                title: const Text('Highlight current layer'),
                subtitle: const Text('Current layer on top, others at reduced opacity'),
                value: 'highlightCurrent',
                groupValue: layerMode,
                onChanged: (value) {
                  setDialogState(() => layerMode = value!);
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, {
              'positionNumbers': exportPositionNumbers,
              'cargoHandles': exportCargoHandles,
              'assemblyHandles': exportAssemblyHandles,
              'slatIDs': exportSlatIDs,
              'layerMode': layerMode,
            }),
            child: const Text('Export'),
          ),
        ],
      ),
    ),
  );
}

/// Exports slats and optional visual elements to an SVG file.
Future<void> exportSlatsToSvg({
  required List<Slat> slats,
  required Map<String, Map<String, dynamic>> layerMap,
  required DesignState appState,
  required ActionState actionState,
  required Map<String, dynamic> exportOptions,
}) async {
  final gridSize = appState.gridSize;
  final selectedLayer = appState.selectedLayerKey;
  final selectedLayerTopside = (layerMap[selectedLayer]?['top_helix'] == 'H5') ? 'H5' : 'H2';
  final String layerMode = exportOptions['layerMode'] ?? 'fullStack';
  final bool highlightCurrentLayer = layerMode == 'highlightCurrent';

  double? minX, maxX, minY, maxY;

  // Group slat elements by layer - now storing XmlElement groups per slat
  final Map<String, List<XmlElement>> layerGroups = {};

  // Sort slats by layer order
  final sortedSlats = List<Slat>.from(slats)
    ..sort((a, b) {
      final orderA = layerMap[a.layer]?['order'] as num? ?? double.maxFinite;
      final orderB = layerMap[b.layer]?['order'] as num? ?? double.maxFinite;
      return orderA.compareTo(orderB);
    });

  for (final slat in sortedSlats) {
    // Skip hidden layers
    if (layerMap[slat.layer]?['hidden'] == true) continue;

    // Gather ordered coordinates like in slat_painter.dart
    final entries = slat.slatPositionToCoordinate.entries.toList()..sort((a, b) => a.key.compareTo(b.key));
    if (entries.isEmpty) continue;

    final coords = entries.map((e) => appState.convertCoordinateSpacetoRealSpace(e.value)).toList(growable: false);

    // Compute tip extensions just like drawSlat in painter
    final slatExtendFront = calculateSlatExtend(coords[0], coords[1], gridSize);
    final slatExtendBack = calculateSlatExtend(coords[coords.length - 2], coords.last, gridSize);

    // Build full list of points to encode into path 'd'
    final List<Offset> pathPoints = [];
    if (actionState.extendSlatTips) {
      pathPoints.add(Offset(coords.first.dx - slatExtendFront.dx, coords.first.dy - slatExtendFront.dy));
    } else {
      pathPoints.add(coords.first);
    }
    pathPoints.addAll(coords.skip(1));
    if (actionState.extendSlatTips) {
      pathPoints.add(Offset(coords.last.dx + slatExtendBack.dx, coords.last.dy + slatExtendBack.dy));
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

    // Use unique color if available
    final Color slatColor = slat.uniqueColor ?? layerMap[slat.layer]?['color'] ?? const Color(0xFF000000);

    // Build slat group with all elements
    final slatGroupBuilder = XmlBuilder();
    slatGroupBuilder.element('g', nest: () {
      slatGroupBuilder.attribute('id', slat.id);

      // 1. Add slat path
      slatGroupBuilder.element('path', nest: () {
        slatGroupBuilder.attribute('d', d.toString());
        slatGroupBuilder.attribute('fill', 'none');
        slatGroupBuilder.attribute('stroke', _colorToHex(slatColor));
        slatGroupBuilder.attribute('stroke-width', (gridSize / 2).toStringAsFixed(2));
        slatGroupBuilder.attribute('stroke-linejoin', 'round');
      });

      // 2. Add position numbers if enabled (only for selected layer)
      if (exportOptions['positionNumbers'] == true && slat.layer == selectedLayer) {
        _addPositionNumbers(slatGroupBuilder, coords, slatColor, gridSize);
      }

      // 3. Add handle markers if enabled (only for selected layer)
      if (slat.layer == selectedLayer) {
        _addHandleMarkers(
          slatGroupBuilder,
          slat,
          appState,
          gridSize,
          selectedLayerTopside,
          exportOptions['cargoHandles'] == true,
          exportOptions['assemblyHandles'] == true,
        );
      }

      // 4. Add slat ID if enabled (only for selected layer)
      if (exportOptions['slatIDs'] == true && slat.layer == selectedLayer) {
        _addSlatID(slatGroupBuilder, slat, coords, gridSize);
      }
    });

    final slatGroup = slatGroupBuilder.buildFragment().firstChild as XmlElement;
    layerGroups.putIfAbsent(slat.layer, () => []).add(slatGroup);
  }

  // Provide some padding around the drawing
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
    builder.attribute('viewBox', '${viewX.toStringAsFixed(2)} ${viewY.toStringAsFixed(2)} ${width.toStringAsFixed(2)} ${height.toStringAsFixed(2)}');

    // Order layers based on mode
    List<MapEntry<String, List<XmlElement>>> orderedLayers = layerGroups.entries.toList();

    if (highlightCurrentLayer) {
      // Sort so selected layer is last (on top)
      orderedLayers.sort((a, b) {
        if (a.key == selectedLayer) return 1; // selected layer goes last
        if (b.key == selectedLayer) return -1;
        final orderA = layerMap[a.key]?['order'] as num? ?? double.maxFinite;
        final orderB = layerMap[b.key]?['order'] as num? ?? double.maxFinite;
        return orderA.compareTo(orderB);
      });
    } else {
      // Normal order by layer order
      orderedLayers.sort((a, b) {
        final orderA = layerMap[a.key]?['order'] as num? ?? double.maxFinite;
        final orderB = layerMap[b.key]?['order'] as num? ?? double.maxFinite;
        return orderA.compareTo(orderB);
      });
    }

    // Add each layer group containing slat subgroups
    for (final entry in orderedLayers) {
      final isSelectedLayer = entry.key == selectedLayer;
      final opacity = (highlightCurrentLayer && !isSelectedLayer) ? 0.2 : 1.0;

      builder.element('g', nest: () {
        builder.attribute('id', entry.key);
        if (opacity < 1.0) {
          builder.attribute('opacity', opacity.toStringAsFixed(2));
        }
        for (final slatGroup in entry.value) {
          builder.xml(slatGroup.toXmlString());
        }
      });
    }
  });

  final document = builder.buildDocument();
  final svgString = document.toXmlString(pretty: true);
  await saveSvg(svgString, '${appState.designName}_2d_layer_graphics.svg');
}

/// Adds position numbers (1, 2, 3...) at each handle coordinate.
void _addPositionNumbers(XmlBuilder builder, List<Offset> coords, Color slatColor, double gridSize) {
  final bool isDark = isColorDark(slatColor);
  final Color textColor = isDark ? Colors.white : Colors.black;
  final double fontSize = gridSize * 0.4;

  for (int i = 0; i < coords.length; i++) {
    final coord = coords[i];
    builder.element('text', nest: () {
      builder.attribute('x', coord.dx.toStringAsFixed(2));
      builder.attribute('y', coord.dy.toStringAsFixed(2));
      builder.attribute('dominant-baseline', 'central');
      builder.attribute('dy', '0.1em');
      builder.attribute('fill', _colorToHex(textColor));
      builder.attribute('font-size', fontSize.toStringAsFixed(2));
      builder.attribute('font-weight', 'bold');
      builder.attribute('font-family', 'Roboto, Arial, sans-serif');
      builder.attribute('text-anchor', 'middle');
      builder.text('${i + 1}');
    });
  }
}

/// Adds handle markers (cargo, seed, assembly) for a slat.
void _addHandleMarkers(
  XmlBuilder builder,
  Slat slat,
  DesignState appState,
  double gridSize,
  String selectedLayerTopside,
  bool exportCargo,
  bool exportAssembly,
) {
  final size = gridSize * 0.85;
  final halfHeight = size / 2;

  for (int i = 0; i < slat.maxLength; i++) {
    final handleIndex = i + 1;
    final h5 = slat.h5Handles[handleIndex];
    final h2 = slat.h2Handles[handleIndex];

    // Check for blocks
    bool topBlocked = appState.assemblyLinkManager.handleBlocks.contains((slat.phantomParent ?? slat.id, handleIndex, selectedLayerTopside == 'H5' ? 5 : 2));
    bool bottomBlocked = appState.assemblyLinkManager.handleBlocks.contains((slat.phantomParent ?? slat.id, handleIndex, selectedLayerTopside == 'H5' ? 2 : 5));

    if (h5 == null && h2 == null && !topBlocked && !bottomBlocked) continue;

    // Determine categories present
    Set<String> categoriesPresent = {
      if (h5 != null) h5["category"],
      if (h2 != null) h2["category"],
    };

    bool hasCargo = categoriesPresent.contains('CARGO') || categoriesPresent.contains('SEED');
    bool hasAssembly = categoriesPresent.contains('ASSEMBLY_HANDLE') || categoriesPresent.contains('ASSEMBLY_ANTIHANDLE');
    bool hasBlocks = topBlocked || bottomBlocked;

    // Check if we should export this handle based on options
    if (!(exportCargo && hasCargo) && !(exportAssembly && (hasAssembly || hasBlocks))) continue;

    final standardizedPosition = slat.slatPositionToCoordinate[handleIndex]!;
    final position = appState.convertCoordinateSpacetoRealSpace(standardizedPosition);

    // Initialize handle data
    String topText = '';
    String bottomText = '';
    Color topColor = Colors.grey;
    Color bottomColor = Colors.grey;
    bool showTop = false;
    bool showBottom = false;
    bool topIsSeed = false;
    bool bottomIsSeed = false;

    void updateHandleData(Map<String, dynamic> handle, String side, int sideName) {
      final category = handle["category"];
      final descriptor = handle["value"];
      final isTop = side == "top";

      // Skip FLAT handles
      if (category == 'FLAT') return;

      String shortText = descriptor;
      Color color = Colors.grey;
      bool isSeed = false;

      if (category == 'CARGO') {
        if (!exportCargo) return;
        shortText = appState.cargoPalette[descriptor]?.shortName ?? descriptor;
        color = appState.cargoPalette[descriptor]?.color ?? Colors.grey;
      } else if (category.contains('ASSEMBLY')) {
        if (!exportAssembly) return;
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
        if (!exportCargo) return;
        color = appState.cargoPalette['SEED']?.color ?? Colors.orange;
        shortText = getIndexFromSeedText(descriptor).toString();
        isSeed = true;
      } else {
        return;
      }

      if (isTop) {
        topText = shortText;
        topColor = color;
        showTop = true;
        topIsSeed = isSeed;
      } else {
        bottomText = shortText;
        bottomColor = color;
        showBottom = true;
        bottomIsSeed = isSeed;
      }
    }

    if (h5 != null) {
      final side = selectedLayerTopside == 'H5' ? 'top' : 'bottom';
      updateHandleData(h5, side, 5);
    }
    if (h2 != null) {
      final side = selectedLayerTopside == 'H2' ? 'top' : 'bottom';
      updateHandleData(h2, side, 2);
    }

    // Handle blocks
    if (topBlocked && exportAssembly) {
      topText = 'X';
      topColor = appState.assemblyHandleBlockedColor;
      showTop = true;
    }
    if (bottomBlocked && exportAssembly) {
      bottomText = 'X';
      bottomColor = appState.assemblyHandleBlockedColor;
      showBottom = true;
    }

    if (!showTop && !showBottom) continue;

    // Create handle marker group
    builder.element('g', nest: () {
      builder.attribute('class', 'handle-marker');
      builder.attribute('data-position', handleIndex.toString());

      final double textFontSize = halfHeight * 0.7;

      // Top marker rect (always draw the top half rect if showing top)
      if (showTop) {
        final rectX = position.dx - size / 2;
        final rectY = position.dy - size / 2;
        builder.element('rect', nest: () {
          builder.attribute('x', rectX.toStringAsFixed(2));
          builder.attribute('y', rectY.toStringAsFixed(2));
          builder.attribute('width', size.toStringAsFixed(2));
          builder.attribute('height', halfHeight.toStringAsFixed(2));
          builder.attribute('fill', _colorToHex(topColor));
        });
        // Add text with arrow prefix
        final String displayText = topIsSeed ? topText : '↑$topText';
        builder.element('text', nest: () {
          builder.attribute('x', position.dx.toStringAsFixed(2));
          builder.attribute('y', (position.dy - halfHeight / 2).toStringAsFixed(2));
          builder.attribute('dominant-baseline', 'central');
          builder.attribute('dy', '0.1em');
          builder.attribute('fill', _colorToHex(isColorDark(topColor) ? Colors.white : Colors.black));
          builder.attribute('font-size', textFontSize.toStringAsFixed(2));
          builder.attribute('font-weight', 'bold');
          builder.attribute('font-family', 'Roboto, Arial, sans-serif');
          builder.attribute('text-anchor', 'middle');
          builder.text(displayText);
        });
      }

      // Bottom marker rect
      if (showBottom) {
        final rectX = position.dx - size / 2;
        final rectY = position.dy;
        builder.element('rect', nest: () {
          builder.attribute('x', rectX.toStringAsFixed(2));
          builder.attribute('y', rectY.toStringAsFixed(2));
          builder.attribute('width', size.toStringAsFixed(2));
          builder.attribute('height', halfHeight.toStringAsFixed(2));
          builder.attribute('fill', _colorToHex(bottomColor));
        });
        // Add text with arrow prefix
        final String displayText = bottomIsSeed ? bottomText : '↓$bottomText';
        builder.element('text', nest: () {
          builder.attribute('x', position.dx.toStringAsFixed(2));
          builder.attribute('y', (position.dy + halfHeight / 2).toStringAsFixed(2));
          builder.attribute('dominant-baseline', 'central');
          builder.attribute('dy', '0.1em');
          builder.attribute('fill', _colorToHex(isColorDark(bottomColor) ? Colors.white : Colors.black));
          builder.attribute('font-size', textFontSize.toStringAsFixed(2));
          builder.attribute('font-weight', 'bold');
          builder.attribute('font-family', 'Roboto, Arial, sans-serif');
          builder.attribute('text-anchor', 'middle');
          builder.text(displayText);
        });
      }

      // White dividing line at center (always show when any handle marker is present)
      builder.element('line', nest: () {
        builder.attribute('x1', (position.dx - size / 2).toStringAsFixed(2));
        builder.attribute('y1', position.dy.toStringAsFixed(2));
        builder.attribute('x2', (position.dx + size / 2).toStringAsFixed(2));
        builder.attribute('y2', position.dy.toStringAsFixed(2));
        builder.attribute('stroke', '#FFFFFF');
        builder.attribute('stroke-width', '0.5');
      });
    });
  }
}

/// Adds slat ID label at the center of the slat.
void _addSlatID(XmlBuilder builder, Slat slat, List<Offset> coords, double gridSize) {
  // Find center of all coords
  double sumX = 0, sumY = 0;
  for (final c in coords) {
    sumX += c.dx;
    sumY += c.dy;
  }
  final center = Offset(sumX / coords.length, sumY / coords.length);

  // Calculate rotation angle from middle coords
  double angle = calculateSlatAngle(coords[coords.length ~/ 2], coords[(coords.length ~/ 2) + 1]);
  double angleDegrees = angle * (180 / pi);

  // Flip upside-down labels
  if (angle > pi / 2 || angle < -pi / 2) {
    angleDegrees += 180;
  }

  // Slat ID text
  String slatIdText = slat.id.replaceFirst('-I', '-') + (slat.slatType != 'tube' ? ' (${slat.slatType})' : '');
  double rectWidth = slat.slatType == 'tube' ? gridSize * 3 : gridSize * 6;
  double rectHeight = gridSize * 0.85;
  double fontSize = gridSize * 0.6;

  // Build group with rotation transform
  builder.element('g', nest: () {
    builder.attribute('class', 'slat-id');
    builder.attribute('transform', 'translate(${center.dx.toStringAsFixed(2)}, ${center.dy.toStringAsFixed(2)}) rotate(${angleDegrees.toStringAsFixed(2)})');

    // Background rect centered at origin (after transform)
    builder.element('rect', nest: () {
      builder.attribute('x', (-rectWidth / 2).toStringAsFixed(2));
      builder.attribute('y', (-rectHeight / 2).toStringAsFixed(2));
      builder.attribute('width', rectWidth.toStringAsFixed(2));
      builder.attribute('height', rectHeight.toStringAsFixed(2));
      builder.attribute('fill', '#000000');
    });

    // Text centered at origin
    builder.element('text', nest: () {
      builder.attribute('x', '0');
      builder.attribute('y', '0');
      builder.attribute('dominant-baseline', 'central');
      builder.attribute('dy', '0.1em');
      builder.attribute('fill', '#FFFFFF');
      builder.attribute('font-size', fontSize.toStringAsFixed(2));
      builder.attribute('font-weight', 'bold');
      builder.attribute('font-family', 'Roboto, Arial, sans-serif');
      builder.attribute('text-anchor', 'middle');
      builder.text(slatIdText);
    });
  });
}
