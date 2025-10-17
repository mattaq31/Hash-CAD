import 'package:flutter/services.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'dart:math';


import 'layer_manager.dart';
import '../app_management/shared_app_state.dart';

List<String> getOrderedKeys(Map<String, Map<String, dynamic>> layerMap) {
  return layerMap.keys.toList()
    ..sort((a, b) => layerMap[b]!['order'].compareTo(layerMap[a]!['order']));
}

Widget slatIcon(DesignState appState) {
  bool isSelected = appState.slatAdditionType == 'tube';
  return GestureDetector(
    onTap: () {
      appState.setSlatAdditionType('tube');
    },
    child: Container(
      width: 40, // Shrunk size
      height: 40,
      margin: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
        borderRadius: BorderRadius.circular(6),
        border: isSelected
            ? Border.all(color: Colors.black, width: 2)
            : null,
        boxShadow: isSelected
            ? [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.5),
            blurRadius: 6,
            spreadRadius: 1,
          )
        ]
            : [],
      ),
    ),
  );
}


Widget dBSlatIcon(DesignState appState) {
  bool isSelected = appState.slatAdditionType == 'DB-L-120';
  return GestureDetector(
    onTap: () {
      appState.setSlatAdditionType('DB-L-120');
    },
    child: Container(
      width: 40, // Shrunk size
      height: 40,
      margin: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
        borderRadius: BorderRadius.circular(6),
        border: isSelected
            ? Border.all(color: Colors.black, width: 2)
            : null,
        boxShadow: isSelected
            ? [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.5),
            blurRadius: 6,
            spreadRadius: 1,
          )
        ]
            : [],
      ),
    ),
  );
}

//  Widgets/painters for labeled pictographs in slat palette
typedef GlyphPainterBuilder = CustomPainter Function(Color color);

class SlatOption extends StatelessWidget {
  final String label;
  final bool isSelected;
  final Color color;
  final VoidCallback onTap;
  final GlyphPainterBuilder painterBuilder;

  const SlatOption({
    super.key,
    required this.label,
    required this.isSelected,
    required this.color,
    required this.painterBuilder,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? Colors.black : Colors.grey.shade300,
            width: isSelected ? 2 : 1,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.08),
                    blurRadius: 6,
                    spreadRadius: 1,
                    offset: const Offset(0, 1),
                  )
                ]
              : [],
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey.shade800,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
            ),
            SizedBox(
              width: 40,
              height: 40,
              child: CustomPaint(
                painter: painterBuilder(color),
              ),
            ),
            SizedBox(width: 10)
          ],
        ),
      ),
    );
  }
}

class SlatGlyphPainter extends CustomPainter {
  final Color color;
  SlatGlyphPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final double padding = 6;
    final double barHeight = 8;

    final rect = Rect.fromLTWH(
      - padding * 7,
      (size.height - barHeight) / 2,
      size.width + 6 * padding,
      barHeight,
    );

    canvas.drawRect(rect, paint);
  }

  @override
  bool shouldRepaint(covariant SlatGlyphPainter oldDelegate) => oldDelegate.color != color;
}

class DoubleBarrelGlyphPainter extends CustomPainter {
  final Color color;
  final String dBType;

  DoubleBarrelGlyphPainter(this.dBType, {required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final double padding = 6;
    final double barHeight = 8;
    final double spacing = 6;
    final totalHeight = barHeight * 2 + spacing;
    final top = (size.height - totalHeight) / 2;

    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = barHeight;

    // Compute the four points used by the path so we can derive direction for arrow
    late Offset p1, p2, p3, p4;
    Path path = Path();

    if (dBType == 'DB-L-60') {
      p3 = Offset(-padding * 9 + size.width + 6 * padding, top + barHeight * 2.5);
      p4 = Offset(-padding * 9, top + barHeight * 2.5);
      p1 = Offset(-padding * 9 + 2 * padding, top + barHeight / 2);
      p2 = Offset(-padding * 9 + size.width + 6 * padding + 2 * padding, top + barHeight / 2);
    }
    else if (dBType == 'DB-R-60') {
      p3 = Offset(-padding * 9 + size.width + 6 * padding, top + barHeight / 2);
      p4 = Offset(-padding * 9, top + barHeight / 2);
      p1 = Offset(-padding * 9 + 2 * padding, top + barHeight * 2.5);
      p2 = Offset(-padding * 9 + size.width + 6 * padding + 2 * padding, top + barHeight * 2.5);
    }
    else if (dBType == 'DB-L-120') {
      p3 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight * 2.5);
      p4 = Offset(-padding * 7, top + barHeight * 2.5);
      p1 = Offset(-padding * 7 - 2 * padding, top + barHeight / 2);
      p2 = Offset(-padding * 7 + size.width + 6 * padding - 2 * padding, top + barHeight / 2);
    }
    else if (dBType == 'DB-R-120') {
      p3 = Offset(-padding * 7 + size.width + 6 * padding,top + barHeight / 2);
      p4 = Offset(-padding * 7, top + barHeight / 2);
      p1 = Offset(-padding * 7 - 2 * padding, top + barHeight * 2.5);
      p2 = Offset(-padding * 7 + size.width + 6 * padding - 2 * padding, top + barHeight * 2.5);
    }
    else if (dBType == 'DB-L') {
      p3 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight * 2.5);
      p4 = Offset(-padding * 7, top + barHeight * 2.5);
      p1 = Offset(-padding * 7, top + barHeight / 2);
      p2 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight / 2);
    }
    else if (dBType == 'DB-R') {
      p3 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight / 2);
      p4 = Offset(-padding * 7, top + barHeight / 2);
      p1 = Offset(-padding * 7, top + barHeight * 2.5);
      p2 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight * 2.5);
    }
    else {
      // nothing to draw
      return;
    }

    // Draw the stroked path
    path.moveTo(p1.dx, p1.dy);
    path.lineTo(p2.dx, p2.dy);
    path.lineTo(p3.dx, p3.dy);
    path.lineTo(p4.dx, p4.dy);
    canvas.drawPath(path, paint);

    // Arrowhead (at p4) and tail (near p1), styled to match SlatPainter aids
    final Offset endDir = p4 - p3;
    final Offset startDir = p2 - p1;

    if (endDir.distance > 0.001 && startDir.distance > 0.001) {
      final Offset vEnd = endDir / endDir.distance;   // normalized
      final Offset vStart = startDir / startDir.distance;

      // Arrowhead — filled triangle pointing along vEnd
      final double arrowSize = barHeight * 1.8;          // modest size for sidebar glyph
      final double arrowAngle = pi / 4.5; // ~40° wings
      final Offset tip = p4 - Offset(5,0); // added offset for beauty
      final double theta = vEnd.direction;
      final Offset left  = tip - Offset.fromDirection(theta - arrowAngle, arrowSize);
      final Offset right = tip - Offset.fromDirection(theta + arrowAngle, arrowSize);

      final Path arrowPath = Path()
        ..moveTo(tip.dx, tip.dy)
        ..lineTo(left.dx, left.dy)
        ..lineTo(right.dx, right.dy)
        ..close();

      final Paint fillPaint = Paint()
        ..color = color
        ..style = PaintingStyle.fill;

      canvas.drawPath(arrowPath, fillPaint);

      // Tail — short transverse line near the start
      final double tailHalfLen = barHeight * 0.6; // length each side from center
      final double phi = vStart.direction;
      final Offset tailCenter = p1 - vStart * (barHeight * 0.4); // pull slightly "behind" start
      final Offset tailA = tailCenter + Offset.fromDirection(phi - pi / 2, tailHalfLen);
      final Offset tailB = tailCenter + Offset.fromDirection(phi + pi / 2, tailHalfLen);

      final Paint tailPaint = Paint()
        ..color = color
        ..strokeWidth = barHeight / 2
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      canvas.drawLine(tailA, tailB, tailPaint);
    }

  }

  @override
  bool shouldRepaint(covariant DoubleBarrelGlyphPainter oldDelegate) => oldDelegate.color != color;
}

class SlatDesignTools extends StatefulWidget {
  const SlatDesignTools({super.key});

  @override
  State<SlatDesignTools> createState() => _SlatDesignTools();
}

class _SlatDesignTools extends State<SlatDesignTools>
    with WidgetsBindingObserver {
  FocusNode slatAddFocusNode = FocusNode();
  TextEditingController slatAddTextController = TextEditingController();
  late final ScrollController _slatPaletteCtrl;
  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _slatPaletteCtrl = ScrollController();
    _scrollController = ScrollController();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      var appState = context.read<DesignState>(); // Use read instead of watch
      slatAddTextController.text = appState.slatAddCount.toString();
      slatAddFocusNode.addListener(() {
        if (!slatAddFocusNode.hasFocus) {
          _updateSlatAddCount(appState);
        }
      });
    });
  }

  void _updateSlatAddCount(DesignState appState) {
    int? newValue = int.tryParse(slatAddTextController.text);
    if (newValue != null && newValue >= 1 && newValue <= 32) {
      appState.updateSlatAddCount(newValue);
    } else if (newValue != null && newValue < 1) {
      appState.updateSlatAddCount(1);
    } else {
      appState.updateSlatAddCount(32);
    }
    slatAddTextController.text = appState.slatAddCount.toString();
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    final colorScheme = Theme.of(context).colorScheme;

    final List<Widget> slatTiles = [
      SlatOption(
        label: 'Standard Slat',
        isSelected: appState.slatAdditionType == 'tube',
        color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
        painterBuilder: (color) => SlatGlyphPainter(color: color),
        onTap: () => appState.setSlatAdditionType('tube'),
      ),
      if (appState.gridMode == '90') ...[
        SlatOption(
          label: 'DB-L',
          isSelected: appState.slatAdditionType == 'DB-L',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-L', color: color),
          onTap: () => appState.setSlatAdditionType('DB-L'),
        ),
        SlatOption(
          label: 'DB-R',
          isSelected: appState.slatAdditionType == 'DB-R',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-R', color: color),
          onTap: () => appState.setSlatAdditionType('DB-R'),
        ),
      ] else ...[
        SlatOption(
          label: 'DB-L-60',
          isSelected: appState.slatAdditionType == 'DB-L-60',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-L-60', color: color),
          onTap: () => appState.setSlatAdditionType('DB-L-60'),
        ),
        SlatOption(
          label: 'DB-L-120',
          isSelected: appState.slatAdditionType == 'DB-L-120',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-L-120', color: color),
          onTap: () => appState.setSlatAdditionType('DB-L-120'),
        ),
        SlatOption(
          label: 'DB-R-60',
          isSelected: appState.slatAdditionType == 'DB-R-60',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-R-60', color: color),
          onTap: () => appState.setSlatAdditionType('DB-R-60'),
        ),
        SlatOption(
          label: 'DB-R-120',
          isSelected: appState.slatAdditionType == 'DB-R-120',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-R-120', color: color),
          onTap: () => appState.setSlatAdditionType('DB-R-120'),
        ),
      ],
    ];

    return Column(children: [
      Text("Slat Design",
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 5),
      Text(
        "Setup", // Title above the segmented button
        style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      SizedBox(height: 10),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          FilledButton.icon(
            onPressed: () async {
              if (appState.gridMode != '90') {
                final result = await showDialog<bool>(
                    context: context,
                    builder: (BuildContext context) => AlertDialog(
                          title: const Text('Switching Grid Type'),
                          content: const Text(
                              'Warning: switching grid type will erase your current design!'),
                          actions: <Widget>[
                            TextButton(
                              onPressed: () => Navigator.pop(context, false),
                              // Cancel
                              child: const Text('Cancel'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.pop(context, true),
                              // Confirm
                              child: const Text('Go ahead'),
                            ),
                          ],
                        ));
                if (result == true) {
                  appState.setGridMode('90');
                  slatAddTextController.text = '1';
                }
              }
            },
            label: Text("90° Grid"),
            style: ElevatedButton.styleFrom(
              // backgroundColor: Colors.red, // Red background
              // foregroundColor: Colors.white, // White text
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8), // Rounded edges
              ),
            ),
          ),
          SizedBox(width: 10),
          FilledButton.icon(
            onPressed: () async {
              if (appState.gridMode != '60') {
                final result = await showDialog<bool>(
                    context: context,
                    builder: (BuildContext context) => AlertDialog(
                          title: const Text('Switching Grid Type'),
                          content: const Text(
                              'Warning: switching grid type will erase your current design!'),
                          actions: <Widget>[
                            TextButton(
                              onPressed: () => Navigator.pop(context, false),
                              // Cancel
                              child: const Text('Cancel'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.pop(context, true),
                              // Confirm
                              child: const Text('Go ahead'),
                            ),
                          ],
                        ));
                if (result == true) {
                  appState.setGridMode('60');
                  slatAddTextController.text = '1';
                }
              }
            },
            label: Text("60° Grid"),
            style: ElevatedButton.styleFrom(
              // backgroundColor: Colors.red, // Red background
              // foregroundColor: Colors.white, // White text
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8), // Rounded edges
              ),
            ),
          ),
        ],
      ),
      SizedBox(height: 10),
      FilledButton.icon(
        onPressed: () {
          appState.clearAll();
        },
        icon: Icon(Icons.cleaning_services, size: 18),
        label: Text("Clear All"),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.red,
          // Red background
          foregroundColor: Colors.white,
          // White text
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: TextStyle(fontSize: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8), // Rounded edges
          ),
        ),
      ),
      Divider(thickness: 1, color: Colors.grey.shade200),
      Text(
        "Slat Edit Mode", // Title above the segmented button
        style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      SizedBox(height: 5),
      SegmentedButton<String>(
        segments: <ButtonSegment<String>>[
          ButtonSegment<String>(
              value: "Add",
              label: Text('Add'),
              icon: Icon(Icons.add_circle_outline,
                  color: Theme.of(context).colorScheme.primary)),
          ButtonSegment<String>(
              value: "Delete",
              label: Text('Delete'),
              icon: Icon(Icons.delete_outline,
                  color: Theme.of(context).colorScheme.primary)),
          ButtonSegment<String>(
              value: 'Move',
              label: Text('Edit'),
              icon: Icon(Icons.pan_tool,
                  color: Theme.of(context).colorScheme.primary)),
        ],
        selected: <String>{actionState.slatMode},
        onSelectionChanged: (Set<String> newSelection) {
          setState(() {
            actionState.updateSlatMode(newSelection.first);
          });
        },
      ),
      SizedBox(height: 5),
      // Buttons
      Divider(thickness: 1, color: Colors.grey.shade200),
      Text(
        "Slat Palette", // Title above the segmented button
        style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      Container(
        width: (40 + 4) * 6 + 12,
        padding: const EdgeInsets.all(6),
        child: SizedBox(
          height: 180, // ~3 tiles visible
          child: Scrollbar(
            thumbVisibility: true,
            controller: _slatPaletteCtrl,
            child: ListView.separated(
              controller: _slatPaletteCtrl,
              itemCount: slatTiles.length,
              separatorBuilder: (_, __) => const SizedBox(height: 6),
              itemBuilder: (_, i) => slatTiles[i],
            ),
          ),
        ),
      ),
      Divider(thickness: 1, color: Colors.grey.shade200),
      Text(
        "Number of Slats to Draw", // Title above the segmented button
        style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      SizedBox(height: 10),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 180,
            child: TextField(
              controller: slatAddTextController,
              focusNode: slatAddFocusNode,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'Manual Input',
              ),
              textInputAction: TextInputAction.done,
              inputFormatters: <TextInputFormatter>[FilteringTextInputFormatter.digitsOnly],
              onSubmitted: (value) {
                _updateSlatAddCount(appState);
              },
            ),
          ),
          IconButton(
            icon: Icon(Icons.arrow_upward),
            onPressed: () {
              if (appState.slatAddCount < 32) {
                appState.updateSlatAddCount(appState.slatAddCount + 1);
                slatAddTextController.text = appState.slatAddCount.toString();
              }
            },
          ),
          IconButton(
            icon: Icon(Icons.arrow_downward),
            onPressed: () {
              if (appState.slatAddCount > 1) {
                appState.updateSlatAddCount(appState.slatAddCount - 1);
                slatAddTextController.text = appState.slatAddCount.toString();
              }
            },
          ),
        ],
      ),
      SizedBox(height: 10),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          ActionChip(
            label: Text('1'),
            onPressed: () {
              appState.updateSlatAddCount(1);
              slatAddTextController.text = appState.slatAddCount.toString();
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('8'),
            onPressed: () {
              appState.updateSlatAddCount(8);
              slatAddTextController.text = appState.slatAddCount.toString();
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('16'),
            onPressed: () {
              appState.updateSlatAddCount(16);
              slatAddTextController.text = appState.slatAddCount.toString();
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('32'),
            onPressed: () {
              appState.updateSlatAddCount(32);
              slatAddTextController.text = appState.slatAddCount.toString();
            },
          ),
        ],
      ),
      Divider(thickness: 1, color: Colors.grey.shade200),
      Text("Adjust Slat Colors",
          style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
      SizedBox(height: 10),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 110, // Fixed width to align colons
            child: Text("Set Colour:",
                textAlign: TextAlign.right,
                style: TextStyle(fontSize: 14, color: Colors.black87)),
          ),
          SizedBox(width: 5),
          IconButton(
            tooltip: 'Assign colour to selected slats',
            onPressed: () {
              appState.assignColorToSelectedSlats(appState.uniqueSlatColor);
            },
            icon: const Icon(Icons.format_paint, size: 20, color: Colors.white),
            style: IconButton.styleFrom(
              backgroundColor: colorScheme.primary,
              shape: RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.circular(8), // Adjust radius as needed
              ),
              padding: const EdgeInsets.all(8),
              minimumSize: const Size(36, 36),
              // Ensures square shape
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          SizedBox(width: 5),
          PopupMenuButton(
            constraints: BoxConstraints(
              minWidth: 200,
              // Set min width to prevent overflow
              maxWidth: 780, // Adjust as needed
            ),
            offset: Offset(0, 40),
            // Position below the button
            itemBuilder: (context) {
              return [
                PopupMenuItem(
                  child: ColorPicker(
                    hexInputBar: true,
                    pickerColor: appState.uniqueSlatColor,
                    onColorChanged: (color) {
                      appState.setUniqueSlatColor(color);
                    },
                    pickerAreaHeightPercent: 0.5,
                  ),
                ),
              ];
            },
            child: Container(
              width: 35, // Width of the rectangle
              height: 20, // Height of the rectangle
              decoration: BoxDecoration(
                color: appState.uniqueSlatColor,
                // Use the color from the list
                border: Border.all(color: Colors.black, width: 1),
                borderRadius:
                    BorderRadius.circular(4), // Optional rounded corners
              ),
            ),
          ),
        ],
      ),
      SizedBox(height: 10),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 110, // Fixed width to align colons
            child: Text("Reset Colours:",
                textAlign: TextAlign.right,
                style: TextStyle(fontSize: 14, color: Colors.black87)),
          ),
          SizedBox(width: 5),
          IconButton(
            tooltip: 'Reset current layer',
            onPressed: () {
              appState.clearSlatColorsFromLayer(appState.selectedLayerKey);
            },
            icon: const Icon(Icons.format_color_reset_outlined,
                size: 20, color: Colors.black87),
            style: IconButton.styleFrom(
              backgroundColor: Colors.grey[300],
              shape: RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.circular(8), // Adjust radius as needed
              ),
              padding: const EdgeInsets.all(8),
              minimumSize: const Size(36, 36),
              // Ensures square shape
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          SizedBox(width: 5),
          IconButton(
            tooltip: 'Reset all layers',
            onPressed: () {
              appState.clearAllSlatColors();
            },
            icon: const Icon(Icons.format_color_reset,
                size: 20, color: Colors.black87),
            style: IconButton.styleFrom(
              backgroundColor: Colors.grey[300],
              shape: RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.circular(8), // Adjust radius as needed
              ),
              padding: const EdgeInsets.all(8),
              minimumSize: const Size(36, 36),
              // Ensures square shape
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          )
        ],
      ),

      SizedBox(height: 10),
      Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          SizedBox(
            width: 110,
            child: Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Text(
                "Layer Colours:",
                textAlign: TextAlign.right,
                style: TextStyle(fontSize: 14, color: Colors.black87),
              ),
            ),
          ),
          SizedBox(width: 5),
          Expanded(
            child: Builder(
              builder: (context) {
                final colorSet = appState.uniqueSlatColorsByLayer[appState.selectedLayerKey] ?? [];

                if (colorSet.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: EdgeInsets.only(bottom: 15),
                      child: Text(
                        'No colors assigned yet',
                        style: TextStyle(fontSize: 14, color: Colors.black54),
                      ),
                    ),
                  );
                }

                return Scrollbar(
                  controller: _scrollController,
                  thumbVisibility: true,
                  trackVisibility: true,
                  thickness: 8,
                  radius: Radius.circular(4),
                  scrollbarOrientation: ScrollbarOrientation.bottom,
                  child: SingleChildScrollView(
                    controller: _scrollController,
                    scrollDirection: Axis.horizontal,
                    padding: EdgeInsets.only(bottom: 16),
                    child: Row(
                      children: colorSet.asMap().entries.map((entry) {
                        int index = entry.key;
                        Color oldColor = entry.value;
                        return Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 4.0),
                          child: Tooltip(
                            message: 'Click to edit slats in this layer with this color',
                            child: Stack(
                              clipBehavior: Clip.none,
                              children: [
                                PopupMenuButton(
                                  tooltip: '',
                                  constraints: const BoxConstraints(minWidth: 300, maxWidth: 780),
                                  offset: const Offset(0, 40),
                                  itemBuilder: (_) => [
                                    PopupMenuItem(
                                      enabled: false,
                                      padding: EdgeInsets.zero,
                                      child: SingleChildScrollView(
                                        child: ColorPicker(
                                          hexInputBar: true,
                                          pickerColor: oldColor,
                                          onColorChanged: (newColor) {
                                            appState.editSlatColorSearch(appState.selectedLayerKey, index, newColor);
                                          },
                                          pickerAreaHeightPercent: 0.5,
                                        ),
                                      ),
                                    ),
                                  ],
                                  child: Container(
                                    width: 35,
                                    height: 20,
                                    decoration: BoxDecoration(
                                      color: oldColor,
                                      border: Border.all(color: Colors.black, width: 1),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                  ),
                                ),
                                Positioned(
                                  top: -4,
                                  right: -6,
                                  child: SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: Material(
                                      color: Colors.white,
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: IconButton(
                                        padding: EdgeInsets.zero,
                                        iconSize: 14,
                                        icon: Icon(Icons.close, color: Colors.black54),
                                        onPressed: () {
                                          appState.removeSlatColorFromLayer(appState.selectedLayerKey, index);
                                        },
                                        tooltip: 'Reset color to layer color',
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),


      SizedBox(height: 5),
      Divider(thickness: 2, color: Colors.grey.shade300),
      LayerManagerWidget(
        appState: appState,
        actionState: actionState,
      ),
      SizedBox(height: 10),
      Divider(thickness: 2, color: Colors.grey.shade300),
    ]);
  }

  @override
  void dispose() {
    slatAddFocusNode.dispose();
    _slatPaletteCtrl.dispose();
    slatAddTextController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
