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
              ElevatedButton(onPressed: () {}, child: Text("Button 1")),
              SizedBox(height: 10),
              ElevatedButton(onPressed: () {}, child: Text("Button 2")),

              // Radio Selections
              SizedBox(height: 20),
              Text("Layers:"),

              Column(
                children: appState.layerList.asMap().entries.map((entry) {
                  int index = entry.key;
                  var option = entry.value;
                  return ListTile(
                    leading: Radio(
                      value: option["value"],
                      groupValue: null,
                      onChanged: (var value) {},
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
                                child: StatefulBuilder(
                                  builder: (context, setState) {
                                    // Local color state
                                    return ColorPicker(
                                      pickerColor: appState.slatColor,
                                      onColorChanged: (color) {
                                        setState(() {
                                          appState.updateColor(index, color);
                                        });
                                      },
                                      pickerAreaHeightPercent: 0.5,
                                    );
                                  }
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
