import 'dart:collection';

import 'package:flutter/services.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';
import 'package:flutter/material.dart';
import 'layer_manager.dart';

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
  bool isSelected = appState.slatAdditionType == 'double-barrel-A';
  return GestureDetector(
    onTap: () {
      appState.setSlatAdditionType('double-barrel-A');
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

    Path path;

    if (dBType == 'double-barrel-B') {
      path = Path()
        ..moveTo(-padding * 9 + size.width + 6 * padding + 2 * padding, top + barHeight / 2)
        ..lineTo(-padding * 9 + 2 * padding, top + barHeight / 2)
        ..lineTo(-padding * 9, top + barHeight * 2.5)
        ..lineTo(-padding * 9 + size.width + 6 * padding, top + barHeight * 2.5);
    }
    else if (dBType == 'double-barrel'){
      path = Path()
        ..moveTo(-padding * 7 + size.width + 6 * padding, top + barHeight / 2)
        ..lineTo(-padding * 7, top + barHeight / 2)
        ..lineTo(-padding * 7, top + barHeight * 2.5)
        ..lineTo(-padding * 7 + size.width + 6 * padding, top + barHeight * 2.5);
    }
    else {
      path = Path()
        ..moveTo(-padding * 7 + size.width + 6 * padding - 2 * padding, top + barHeight / 2)
        ..lineTo(-padding * 7 - 2 * padding, top + barHeight / 2)
        ..lineTo(-padding * 7, top + barHeight * 2.5)
        ..lineTo(-padding * 7 + size.width + 6 * padding, top + barHeight * 2.5);
    }

    canvas.drawPath(path, paint);
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

  @override
  void initState() {
    super.initState();
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
    final ScrollController _scrollController = ScrollController();

    return Column(children: [
      Text("Slat Design",
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 5),
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
      Divider(thickness: 1, color: Colors.grey.shade200),
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
      // Buttons
      Divider(thickness: 1, color: Colors.grey.shade200),
      Text(
        "Slat Palette", // Title above the segmented button
        style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      Container(
        // decoration: BoxDecoration(
        //   border: Border.all(color: Colors.grey.shade400, width: 1),
        //   borderRadius: BorderRadius.circular(8),
        // ),
        width: (40 + 4) * 6 + 12,
        padding: const EdgeInsets.all(6),
        child: Column(
          children: [
            SlatOption(
              label: 'CC6HB',
              isSelected: appState.slatAdditionType == 'tube',
              color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
              painterBuilder: (color) => SlatGlyphPainter(color: color),
              onTap: () => appState.setSlatAdditionType('tube'),
            ),
            if (appState.gridMode == '90') ...[
              SizedBox(height: 6),
              SlatOption(
                label: 'Double-Barrel',
                isSelected: appState.slatAdditionType == 'double-barrel',
                color: appState.layerMap[appState.selectedLayerKey]?['color'] ??
                    Colors.grey,
                painterBuilder: (color) =>
                    DoubleBarrelGlyphPainter('double-barrel', color: color),
                onTap: () => appState.setSlatAdditionType('double-barrel'),
              ),
            ],
            if (appState.gridMode == '60') ...[
              SizedBox(height: 6),
              SlatOption(
                label: 'Double-Barrel-A',
                isSelected: appState.slatAdditionType == 'double-barrel-A',
                color: appState.layerMap[appState.selectedLayerKey]?['color'] ??
                    Colors.grey,
                painterBuilder: (color) =>
                    DoubleBarrelGlyphPainter('double-barrel-A', color: color),
                onTap: () => appState.setSlatAdditionType('double-barrel-A'),
              ),
              SizedBox(height: 6),
              SlatOption(
                label: 'Double-Barrel-B',
                isSelected: appState.slatAdditionType == 'double-barrel-B',
                color: appState.layerMap[appState.selectedLayerKey]?['color'] ??
                    Colors.grey,
                painterBuilder: (color) =>
                    DoubleBarrelGlyphPainter('double-barrel-B', color: color),
                onTap: () => appState.setSlatAdditionType('double-barrel-B'),
              ),
            ]
          ],
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
              inputFormatters: <TextInputFormatter>[
                FilteringTextInputFormatter.digitsOnly
              ],
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
      Text("Keyboard Shortcuts",
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 10),
      Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'R'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Rotate slat draw direction"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'F'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Flip multi-slat draw direction"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'T'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Transpose slat draw direction"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'Up/Down arrow keys'",
                    style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Change layer"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'A'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Add new layer"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'1'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Switch to 'Add' mode"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'2'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Switch to 'Delete' mode"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'3'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Switch to 'Edit' mode"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'CMD/Ctrl-Z'",
                    style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Undo last action"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                    text: "'CMD-Shift-Z/Ctrl-Y'",
                    style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Redo last action"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
        ],
      ),
      Divider(thickness: 2, color: Colors.grey.shade300),
    ]);
  }

  @override
  void dispose() {
    slatAddFocusNode.dispose();
    super.dispose();
  }
}
