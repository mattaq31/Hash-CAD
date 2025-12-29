import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';

import '../app_management/shared_app_state.dart';
import '../graphics/honeycomb_pictogram.dart';
import '../app_management/action_state.dart';

class LayerManagerWidget extends StatelessWidget {
  final DesignState appState;
  final ActionState actionState;

  const LayerManagerWidget({
    super.key,
    required this.appState,
    required this.actionState,
  });

  List<String> getOrderedKeys(Map<String, Map<String, dynamic>> layerMap) {
    final entries = layerMap.entries.toList();
    entries.sort((a, b) => (b.value['order'] as int).compareTo(a.value['order'] as int));
    return entries.map((e) => e.key).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text("Layer Manager",
            style: TextStyle(
                fontSize: 22, fontWeight: FontWeight.bold)),
        CheckboxListTile(
          title: const Text('Isolate Current Layer', textAlign: TextAlign.center),
          value: actionState.isolateSlatLayerView,
          onChanged: (bool? value) {
              actionState.setIsolateSlatLayerView(value ?? false);
          },
        ),
        Container(
          constraints: BoxConstraints(
            maxHeight: min(
              // Height for 5 items, approximating a row having a height of 85
                5 * 85.0,
                // If fewer than 5 items, shrink to fit content
                getOrderedKeys(appState.layerMap).length * 85.0
            ),
          ),
          child: ReorderableListView(
            shrinkWrap: false,
            buildDefaultDragHandles: false,
            onReorder: (int oldIndex, int newIndex) {
              if (newIndex > oldIndex) {
                newIndex--; // Adjust index when moving down
              }
                // Extract and sort keys based on their current 'order' values
                final sortedKeys = getOrderedKeys(appState.layerMap);

                // Remove and reinsert the moved key
                final movedKey = sortedKeys.removeAt(oldIndex);
                sortedKeys.insert(newIndex, movedKey);

                // Pass the reordered keys to reOrderLayers
                appState.reOrderLayers(sortedKeys.reversed.toList(), context);
            },
            children: getOrderedKeys(appState.layerMap).map((key) {
              var entry = appState.layerMap[key]!;
              int index = appState.layerMap.length - (entry['order'] as int) - 1; // done to counteract the reversed order system of the layer sorter
              bool isSelected = key == appState.selectedLayerKey;

              return Material(
                key: ValueKey(key),
                child: Stack(
                    children: [
                      ListTile(
                        tileColor: isSelected
                            ? Colors.blue.shade100.withValues(alpha: 0.2) // Darker blue when selected
                            : Colors.white, // White when not selected
                        selected: isSelected,
                        selectedTileColor: Colors.blue.shade200.withValues(alpha: 0.2), // Add this
                        selectedColor: Colors.black, // Add this to keep text black when selected
                        contentPadding: EdgeInsets.symmetric(horizontal: 6.0, vertical: 0),
                        onTap: () {
                            appState.updateActiveLayer(key);
                        },
                        leading: ReorderableDragStartListener(
                          index: index,
                          child: Icon(Icons.drag_handle,
                              color: Colors.black),
                        ),
                        title: Row(
                          children: [
                            Expanded(child: Text("L${entry['order']+1}")),
                            Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(entry['top_helix'], style: TextStyle(fontSize: 12),),
                                SizedBox(height: 30),
                                Text(entry['bottom_helix'], style: TextStyle(fontSize: 12),),
                              ],
                            ),
                            SizedBox(width: 10),
                            Container(width: 30,
                                alignment: Alignment.center,
                                child: HoneycombCustomPainterWidget(color: entry["color"])),
                          ],
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            // Popup color picker
                            SizedBox(width: 8),
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
                                      pickerColor: entry["color"],
                                      onColorChanged: (color) {
                                          appState.updateLayerColor(key, color);
                                      },
                                      pickerAreaHeightPercent: 0.5,
                                    ),
                                  ),
                                ];
                              },
                              child: Container(
                                width: 30, // Width of the rectangle
                                height: 20, // Height of the rectangle
                                decoration: BoxDecoration(
                                  color: entry["color"],
                                  // Use the color from the list
                                  border: Border.all(
                                      color: Colors.black, width: 1),
                                  borderRadius: BorderRadius.circular(4), // Optional rounded corners
                                ),
                              ),
                            ),
                            SizedBox(width: 8),
                            IconButton(
                              icon: Icon(Icons.autorenew, color: Colors.blue),
                              onPressed: () {
                                  appState.flipLayer(key, context);
                              },
                              constraints: BoxConstraints(minWidth: 35, minHeight: 35), // Adjust width/height
                              padding: EdgeInsets.zero, // Remove default padding
                            ),
                            IconButton(
                              icon: Icon(appState.layerMap[key]!['hidden'] ? Icons.visibility_off : Icons.visibility, color: appState.layerMap[key]!['hidden'] ? Colors.grey: Colors.green),
                              onPressed: () {
                                  appState.flipLayerVisibility(key);
                              },
                              constraints: BoxConstraints(minWidth: 35, minHeight: 35), // Adjust width/height
                              padding: EdgeInsets.zero, // Remove default padding
                            ),
                            IconButton(
                              icon: Icon(Icons.close, color: appState.layerMap.length == 1 ? Colors.grey : Colors.red),
                              onPressed: appState.layerMap.length == 1 ? null : () {
                                  appState.deleteLayer(key);
                              },
                              constraints: BoxConstraints(minWidth: 35, minHeight: 35), // Adjust width/height
                              padding: EdgeInsets.zero,
                            ),
                          ],
                        ),
                      ),
                      Positioned(
                        bottom: 4,
                        right: 20,
                        child: Text(
                          "Layer ID: $key Slat Count: ${appState.layerMap[key]!['slat_count']}",
                          style: TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                      ),
                    ]
                ),
              );
            }).toList(),
          ),
        ),
        Text(
          "Total Slat Count: ${appState.layerMap.values.map((layer) => layer['slat_count']).reduce((a, b) => a + b)}",
        ),
        SizedBox(height: 10),
        FilledButton.icon(
          onPressed: () {
              appState.addLayer();
          },
          label: Text("Add Layer"),
          icon: Icon(Icons.add),
          style: ElevatedButton.styleFrom(
            padding: EdgeInsets.symmetric(
                horizontal: 16, vertical: 12),
            textStyle: TextStyle(fontSize: 16),
          ),
        ),
      ],
    );
  }
}