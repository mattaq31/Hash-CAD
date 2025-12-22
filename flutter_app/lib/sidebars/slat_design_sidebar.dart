import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import 'layer_manager.dart';
import '../app_management/shared_app_state.dart';
import 'slat_edit_selection_panel.dart';
import 'slat_add_selection_panel.dart';


List<String> getOrderedKeys(Map<String, Map<String, dynamic>> layerMap) {
  return layerMap.keys.toList()
    ..sort((a, b) => layerMap[b]!['order'].compareTo(layerMap[a]!['order']));
}

class SlatDesignTools extends StatefulWidget {
  const SlatDesignTools({super.key});

  @override
  State<SlatDesignTools> createState() => _SlatDesignTools();
}

class _SlatDesignTools extends State<SlatDesignTools> {

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    final colorScheme = Theme.of(context).colorScheme;

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

      if (actionState.slatMode == 'Add') SlatAddPanel(),
      if (actionState.slatMode == 'Move') SlatEditPanel(),

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

}
