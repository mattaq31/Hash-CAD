import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'shared_app_state.dart';
import 'rating_indicator.dart';
import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';

class SideBarTools extends StatefulWidget {
  const SideBarTools({super.key});

  @override
  State<SideBarTools> createState() => _SideBarToolsState();
}

class _SideBarToolsState extends State<SideBarTools> {
  int selectedValue = 1;
  TextEditingController controller = TextEditingController(text: '1');
  bool isCollapsed = false;
  bool collapseAnimation = false;
  String slatModelSelection = 'Add';

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();

    return AnimatedPositioned(
      duration: Duration(milliseconds: 500),
      bottom: 0,
      top: 0,
      onEnd: () {
        setState(() {
          collapseAnimation = !collapseAnimation;
        });
      },
      width: isCollapsed ? 70 : 330, // Change width based on collapse state
      // Sidebar width
      child: Material(
        elevation: 8,
        child: Container(
          width: isCollapsed ? 70 : 330,
          color: Colors.white,
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Hamburger icon to toggle sidebar
              Align(
                alignment: Alignment.centerLeft,
                child: IconButton(
                  icon: Icon(isCollapsed ? Icons.menu : Icons.close),
                  onPressed: () {
                    setState(() {
                      isCollapsed = !isCollapsed;
                    });
                  },
                ),
              ),

              Visibility(
                visible: !isCollapsed && !collapseAnimation,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Divider(thickness: 2, color: Colors.grey.shade300),
                    Text("Slat Design",
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                    SizedBox(height: 10),
                    Text(
                      "Slat Edit Mode", // Title above the segmented button
                      style:
                          TextStyle(fontSize: 16, color: Colors.grey.shade600),
                    ),
                    SizedBox(height: 5),
                    SegmentedButton<String>(
                      segments: const <ButtonSegment<String>>[
                        ButtonSegment<String>(value: "Add", label: Text('Add'), icon: Icon(Icons.add_circle_outline)),
                        ButtonSegment<String>(value: "Delete", label: Text('Delete'), icon: Icon(Icons.delete_outline)),
                        ButtonSegment<String>(value: 'Move', label: Text('Move'), icon: Icon(Icons.pan_tool)),
                      ],
                      selected: <String>{slatModelSelection},
                      onSelectionChanged: (Set<String> newSelection) {
                        setState(() {
                          slatModelSelection = newSelection.first;
                          actionState.updateSlatMode(slatModelSelection);
                        });
                      },
                    ),
                    SizedBox(height: 20),
                    // Buttons
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SizedBox(
                          width: 180,
                          child: TextField(
                            controller: controller,
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(
                              border: OutlineInputBorder(),
                              labelText: 'Number of Slats to Draw',
                            ),
                            textInputAction: TextInputAction.done,
                            inputFormatters: <TextInputFormatter>[ FilteringTextInputFormatter.digitsOnly],
                            onSubmitted: (value) {
                              int? newValue = int.tryParse(value);
                              if (newValue != null && newValue >= 1 && newValue <= 32) {
                                selectedValue = newValue;
                                controller.text = selectedValue.toString();
                              }
                              else if (newValue != null && newValue < 1) {
                                selectedValue = 1;
                                controller.text = '1';
                              }
                              else {
                                selectedValue = 32;
                                controller.text = '32';
                              }
                              appState.updateSlatAddCount(selectedValue);
                            },
                          ),
                        ),
                        IconButton(
                          icon: Icon(Icons.arrow_upward),
                          onPressed: () {
                            if (selectedValue < 32) {
                              selectedValue++;
                              controller.text = selectedValue.toString();
                              appState.updateSlatAddCount(selectedValue);
                            }
                          },
                        ),
                        IconButton(
                          icon: Icon(Icons.arrow_downward),
                          onPressed: () {
                              if (selectedValue > 1) {
                                selectedValue--;
                                controller.text = selectedValue.toString();
                                appState.updateSlatAddCount(selectedValue);
                              }
                          },
                        ),
                      ],
                    ),
                    // Radio Selections
                    SizedBox(height: 10),
                    Text("Layer Manager",
                          style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),

                    ReorderableListView(
                      shrinkWrap: true,
                      buildDefaultDragHandles: false,
                      onReorder: (int oldIndex, int newIndex) {
                        if (newIndex > oldIndex) {
                          newIndex--; // Adjust index when moving down
                        }
                        setState(() {
                          final item = appState.layerList.removeAt(oldIndex);
                          appState.layerList.insert(newIndex, item);
                        });
                      },
                      children: appState.layerList.asMap().entries.map((entry) {
                          int index = entry.key;
                          var option = entry.value;
                          return ListTile(
                            key: ValueKey(option["value"]),
                            leading: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  ReorderableDragStartListener(
                                    index: index,
                                    child: Icon(Icons.drag_handle, color: Colors.black),
                                  ),
                                  SizedBox(width: 8),
                                  Radio(
                                    value: option["value"],
                                    groupValue: appState.layerList[appState.selectedLayerIndex]['value'],
                                    onChanged: (var value) {
                                      appState.updateSelectedLayer(index); // Update state on selection
                                    },
                                  ),
                                ],
                              ),
                            title: Text(option["label"]),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                // Popup color picker
                                PopupMenuButton(
                                  constraints: BoxConstraints(
                                    minWidth: 200, // Set min width to prevent overflow
                                    maxWidth: 780, // Adjust as needed
                                  ),
                                  offset: Offset(0, 40), // Position below the button

                                  itemBuilder: (context) {
                                    return [
                                      PopupMenuItem(
                                        child: ColorPicker(
                                          pickerColor: appState.layerList[index]["color"],
                                          onColorChanged: (color) {
                                            setState(() {
                                              appState.updateColor(index, color);
                                            });
                                          },
                                          pickerAreaHeightPercent: 0.5,
                                        ),
                                      ),
                                    ];
                                  },
                                  child: GestureDetector(
                                    onTap: null, // Pop-up opens on button press
                                    child: Container(
                                      width: 24,
                                      height: 24,
                                      decoration: BoxDecoration(
                                        color: option["color"],
                                        shape: BoxShape.circle,
                                        border:
                                            Border.all(color: Colors.black, width: 1),
                                      ),
                                    ),
                                  ),
                                ),
                                SizedBox(width: 8),
                                IconButton(
                                  icon: Icon(Icons.close, color: Colors.red),
                                  onPressed: () {},
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                    ),
                    Divider(thickness: 2, color: Colors.grey.shade300),
                    SizedBox(height: 10),
                    Text("Assembly Handles",
                        style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                    SizedBox(height: 10),
                    Text(
                      "Handle Generation", // Title above the segmented button
                      style:
                      TextStyle(fontSize: 16, color: Colors.grey.shade600),
                    ),
                    SizedBox(height: 5),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        ElevatedButton.icon(
                          onPressed: () {},
                          icon: Icon(Icons.shuffle, size: 18),
                          label: Text("Randomize"),
                          style: ElevatedButton.styleFrom(
                            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            textStyle: TextStyle(fontSize: 16),
                          ),
                        ),
                        SizedBox(width: 10),
                        ElevatedButton.icon(
                          onPressed: () {},
                          icon: Icon(Icons.auto_awesome, size: 18),
                          label: Text("Evolve"),
                          style: ElevatedButton.styleFrom(
                            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            textStyle: TextStyle(fontSize: 16),
                          ),
                        ),
                      ],
                    ),
                    CheckboxListTile(
                      title: const Text('Reset current handles'),
                      value: true,
                      onChanged: (bool? value) {
                        setState(() {

                        });
                      },
                    ),
                    FilledButton.icon(
                      onPressed: () {},
                      icon: Icon(Icons.delete_sweep, size: 18),
                      label: Text("Delete all handles"),
                      style: ElevatedButton.styleFrom(
                        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        textStyle: TextStyle(fontSize: 16),
                      ),
                    ),
                    SizedBox(height: 20),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text("Design Hamming Score",
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                            SizedBox(width: 20),
                            RatingIndicator(rating: 90.0),
                          ],
                        ),
                        SizedBox(height: 10),
                        ElevatedButton.icon(
                          onPressed: () {},
                          label: Text("Recalculate Score"),
                          style: ElevatedButton.styleFrom(
                            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            textStyle: TextStyle(fontSize: 16),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              )],
          ),
        ),
      ),
    );
  }
}
