import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';
import 'package:flutter/material.dart';
import  'layer_manager.dart';

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
              if (appState.slatAddCount < 32) {
                appState.updateSlatAddCount(appState.slatAddCount+1);
                slatAddTextController.text = appState.slatAddCount.toString();

              }
            },
          ),
          IconButton(
            icon: Icon(Icons.arrow_downward),
            onPressed: () {
              if (appState.slatAddCount > 1) {
                appState.updateSlatAddCount(appState.slatAddCount-1);
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
                TextSpan(text: "'T'", style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ": Transpose slat draw direction"),
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
