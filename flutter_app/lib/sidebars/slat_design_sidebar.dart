import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';
import 'package:flutter/material.dart';
import '../graphics/honeycomb_pictogram.dart';
import 'dart:math';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';

List<String> getOrderedKeys(Map<String, Map<String, dynamic>> layerMap) {
  return layerMap.keys.toList()
    ..sort((a, b) => layerMap[b]!['order'].compareTo(layerMap[a]!['order']));
}

class SlatDesignTools extends StatefulWidget {
  const SlatDesignTools({super.key});

  @override
  State<SlatDesignTools> createState() => _SlatDesignTools();
}

class _SlatDesignTools extends State<SlatDesignTools> with WidgetsBindingObserver {

  FocusNode slatAddFocusNode = FocusNode();

  TextEditingController slatAddTextController = TextEditingController(text: '1');
  int slatAddCount = 1;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      var appState = context.read<DesignState>(); // Use read instead of watch
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
      slatAddCount = newValue;
    } else if (newValue != null && newValue < 1) {
      slatAddCount = 1;
    } else {
      slatAddCount = 32;
    }
    slatAddTextController.text = slatAddCount.toString();
    appState.updateSlatAddCount(slatAddCount);
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();

    return Column(children: [
      Text("Slat Design",
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 5),
      Text(
        "Slat Edit Mode", // Title above the segmented button
        style:
        TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      SizedBox(height: 5),
      SegmentedButton<String>(
        segments: <ButtonSegment<String>>[
          ButtonSegment<String>(
              value: "Add",
              label: Text('Add'),
              icon: Icon(Icons.add_circle_outline, color: Theme.of(context).colorScheme.primary)),
          ButtonSegment<String>(
              value: "Delete",
              label: Text('Delete'),
              icon: Icon(Icons.delete_outline, color: Theme.of(context).colorScheme.primary)),
          ButtonSegment<String>(
              value: 'Move',
              label: Text('Move'),
              icon: Icon(Icons.pan_tool, color: Theme.of(context).colorScheme.primary)),
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
        style:
        TextStyle(fontSize: 16, color: Colors.grey.shade600),
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
                    builder: (BuildContext context) =>
                        AlertDialog(
                          title:
                          const Text('Switching Grid Type'),
                          content: const Text(
                              'Warning: switching grid type will erase your current design!'),
                          actions: <Widget>[
                            TextButton(
                              onPressed: () => Navigator.pop(context, false), // Cancel
                              child: const Text('Cancel'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.pop(context, true), // Confirm
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
                    builder: (BuildContext context) =>
                        AlertDialog(
                          title:
                          const Text('Switching Grid Type'),
                          content: const Text(
                              'Warning: switching grid type will erase your current design!'),
                          actions: <Widget>[
                            TextButton(
                              onPressed: () => Navigator.pop(context, false), // Cancel
                              child: const Text('Cancel'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.pop(context, true), // Confirm
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
      SizedBox(height: 5),
      FilledButton.icon(
        onPressed: () {
          appState.clearAll();
        },
        icon: Icon(Icons.cleaning_services, size: 18),
        label: Text("Clear All"),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.red, // Red background
          foregroundColor: Colors.white, // White text
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: TextStyle(fontSize: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8), // Rounded edges
          ),
        ),
      ),
      CheckboxListTile(
        title: const Text('Display Assembly Handles'),
        value: actionState.displayAssemblyHandles,
        onChanged: (bool? value) {
          setState(() {
            actionState.setAssemblyHandleDisplay(value ?? false);
          });
        },
      ),
      // SizedBox(height: 10),
      CheckboxListTile(
        title: const Text('Display Slat IDs'),
        value: actionState.displaySlatIDs,
        onChanged: (bool? value) {
          setState(() {
            actionState.setSlatIDDisplay(value ?? false);
          });
        },
      ),
      CheckboxListTile(
        title: const Text('Isolate Current Layer'),
        value: actionState.isolateSlatLayerView,
        onChanged: (bool? value) {
          setState(() {
            actionState.setIsolateSlatLayerView(value ?? false);
          });
        },
      ),
      // Buttons
      Divider(thickness: 1, color: Colors.grey.shade200),
      Text(
        "Number of Slats to Draw", // Title above the segmented button
        style:
        TextStyle(fontSize: 16, color: Colors.grey.shade600),
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
              if (slatAddCount < 32) {
                slatAddCount++;
                slatAddTextController.text = slatAddCount.toString();
                appState.updateSlatAddCount(slatAddCount);
              }
            },
          ),
          IconButton(
            icon: Icon(Icons.arrow_downward),
            onPressed: () {
              if (slatAddCount > 1) {
                slatAddCount--;
                slatAddTextController.text = slatAddCount.toString();
                appState.updateSlatAddCount(slatAddCount);
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
              slatAddCount = 1;
              slatAddTextController.text = slatAddCount.toString();
              appState.updateSlatAddCount(slatAddCount);
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('8'),
            onPressed: () {
              slatAddCount = 8;
              slatAddTextController.text = slatAddCount.toString();
              appState.updateSlatAddCount(slatAddCount);
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('16'),
            onPressed: () {
              slatAddCount = 16;
              slatAddTextController.text = slatAddCount.toString();
              appState.updateSlatAddCount(slatAddCount);
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('32'),
            onPressed: () {
              slatAddCount = 32;
              slatAddTextController.text = slatAddCount.toString();
              appState.updateSlatAddCount(slatAddCount);
            },
          ),
        ],
      ),
      Divider(thickness: 2, color: Colors.grey.shade300),
      Text("Layer Manager",
          style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.bold)),
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
            setState(() {
              // Extract and sort keys based on their current 'order' values
              final sortedKeys = getOrderedKeys(appState.layerMap);

              // Remove and reinsert the moved key
              final movedKey = sortedKeys.removeAt(oldIndex);
              sortedKeys.insert(newIndex, movedKey);

              // Pass the reordered keys to reOrderLayers
              appState.reOrderLayers(sortedKeys.reversed.toList());

            });
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
                    contentPadding: EdgeInsets.symmetric(horizontal: 8.0, vertical: 0),
                      onTap: () {
                      setState(() {
                        appState.updateActiveLayer(key);
                      });
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
                                  pickerColor: entry["color"],
                                  onColorChanged: (color) {
                                    setState(() {
                                      appState.updateLayerColor(key, color);
                                    });
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
                            setState(() {
                              appState.flipLayer(key);
                            });
                          },
                          constraints: BoxConstraints(minWidth: 35, minHeight: 35), // Adjust width/height
                          padding: EdgeInsets.zero, // Remove default padding
                        ),
                        IconButton(
                          icon: Icon(appState.layerMap[key]!['hidden'] ? Icons.visibility_off : Icons.visibility, color: appState.layerMap[key]!['hidden'] ? Colors.grey: Colors.green),
                          onPressed: () {
                            setState(() {
                                appState.flipLayerVisibility(key);
                            });
                          },
                          constraints: BoxConstraints(minWidth: 35, minHeight: 35), // Adjust width/height
                          padding: EdgeInsets.zero, // Remove default padding
                        ),
                        IconButton(
                          icon: Icon(Icons.close, color: appState.layerMap.length == 1 ? Colors.grey : Colors.red),
                          onPressed: appState.layerMap.length == 1 ? null : () {
                            setState(() {
                              appState.deleteLayer(key);
                            });
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
          setState(() {
            appState.addLayer();
          });
        },
        label: Text("Add Layer"),
        icon: Icon(Icons.add),
        style: ElevatedButton.styleFrom(
          padding: EdgeInsets.symmetric(
              horizontal: 16, vertical: 12),
          textStyle: TextStyle(fontSize: 16),
        ),
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
                TextSpan(text: "'R'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Rotate slat draw direction"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(text: "'F'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Flip multi-slat draw direction"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(text: "'Up/Down arrow keys'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Change layer"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(text: "'A'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Add new layer"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(text: "'1'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Switch to 'Add' mode"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(text: "'2'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Switch to 'Delete' mode"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(text: "'3'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Switch to 'Move' mode"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(text: "'CMD/Ctrl-Z'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Undo last action"),
              ],
            ),
            style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
          ),
          Text('(Only slat actions can be be reversed)', style: TextStyle(fontSize: 14, color: Colors.grey.shade600)),
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
