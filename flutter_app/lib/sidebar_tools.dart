import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'shared_app_state.dart';
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

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<MyAppState>();
    return AnimatedPositioned(
      duration: Duration(milliseconds: 300),
      left: 0,
      top: 0,
      bottom: 0,
      width: 300,
      // Sidebar width
      child: Material(
        elevation: 8,
        child: Container(
          color: Colors.white,
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text("Sidebar Menu",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              SizedBox(height: 20),

              // Buttons
              Row(
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
              SizedBox(height: 10),
              ElevatedButton(onPressed: () {}, child: Text("Button 2")),

              // Radio Selections
              SizedBox(height: 20),
              Text("Layers:"),

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
            ],
          ),
        ),
      ),
    );
  }
}
