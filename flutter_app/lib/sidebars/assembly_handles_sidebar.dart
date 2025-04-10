import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';
import 'package:flutter/material.dart';
import '../graphics/rating_indicator.dart';

class AssemblyHandleDesignTools extends StatefulWidget {
  const AssemblyHandleDesignTools({super.key});

  @override
  State<AssemblyHandleDesignTools> createState() => _AssemblyHandleDesignTools();
}

class _AssemblyHandleDesignTools extends State<AssemblyHandleDesignTools> with WidgetsBindingObserver {
  bool preventSelfComplementarySlats = true;
  TextEditingController handleAddTextController = TextEditingController(text: '32');
  int uniqueHandleCount = 32;

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    var serverState = context.watch<ServerState>();

    return Column(children: [
      Text("Assembly Handles",
          style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.bold)),
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
            onPressed: () {
              appState.generateRandomAssemblyHandles(uniqueHandleCount, preventSelfComplementarySlats);
              actionState.setAssemblyHandleDisplay(true);
            },
            icon: Icon(Icons.shuffle, size: 18),
            label: Text("Randomize"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(
                  horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
          SizedBox(width: 10),
          ElevatedButton.icon(
            onPressed: () {
              if (!kIsWeb) {
                actionState.activateEvolveMode();
              } else {
                showDialog<String>(
                    context: context,
                    builder: (BuildContext context) =>
                        AlertDialog(
                          title:
                          const Text('Assembly Handle Evolution'),
                          content: const Text('To run assembly handle evolution, please download the desktop version of the app! (LINK TBC)'),
                          actions: <Widget>[
                            TextButton(
                              onPressed: () =>
                                  Navigator.pop(context, 'OK'),
                              child: const Text('OK'),
                            ),
                          ],
                        ));
              }
            },
            icon: Icon(Icons.auto_awesome, size: 18),
            label: Text("Evolve"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(
                  horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
      SizedBox(height: 15),
      Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          Text("Handle library size", style: TextStyle(fontSize: 16)),
          SizedBox(width: 10),
          Padding(
            padding: const EdgeInsets.only(right: 25.0),
            child: Align(
              alignment: Alignment.centerRight,
              child: SizedBox(
                width: 60,
                child: TextField(
                  controller: handleAddTextController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(),
                  ),
                  textInputAction: TextInputAction.done,
                  inputFormatters: <TextInputFormatter>[
                    FilteringTextInputFormatter.digitsOnly
                  ],
                  onSubmitted: (value) {
                    int? newValue = int.tryParse(value);
                    if (newValue != null &&
                        newValue >= 1 &&
                        newValue <= 997) {
                      uniqueHandleCount = newValue;
                      handleAddTextController.text = uniqueHandleCount.toString();
                    } else if (newValue != null && newValue < 1) {
                      uniqueHandleCount = 1;
                      handleAddTextController.text = '1';
                    } else {
                      uniqueHandleCount = 997;
                      handleAddTextController.text = '997';
                    }
                    serverState.updateEvoParam('number_unique_handles', uniqueHandleCount.toString());
                  },
                ),
              ),
            ),
          ),
        ],
      ),
      CheckboxListTile(
        contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 0), // Reduces spacing
        title: const Text('Reset current handles', textAlign: TextAlign.center),
        value: true,
        onChanged: (bool? value) {
          setState(() {});
        },
      ),
      CheckboxListTile(
        contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 0), // Reduces spacing
        title: const Text('Prevent self-complementary slats', textAlign: TextAlign.center),
        value: preventSelfComplementarySlats,
        onChanged: (bool? value) {
          setState(() {
            preventSelfComplementarySlats = value ?? false;
            serverState.updateEvoParam("split_sequence_handles", preventSelfComplementarySlats.toString());
          });
        },
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
      FilledButton.icon(
        onPressed: () {
          appState.cleanAllHandles();
        },
        icon: Icon(Icons.delete_sweep, size: 18),
        label: Text("Delete all handles"),
        style: ElevatedButton.styleFrom(
          padding:
          EdgeInsets.symmetric(horizontal: 16, vertical: 12),
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
                  style: TextStyle(
                      fontSize: 16, fontWeight: FontWeight.bold)),
              SizedBox(width: 20),
              HammingIndicator(value: 0.0),
            ],
          ),
          SizedBox(height: 10),
          ElevatedButton.icon(
            onPressed: () {},
            label: Text("Recalculate Score"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(
                  horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
      SizedBox(height: 10),
      Divider(thickness: 2, color: Colors.grey.shade300),
    ]);
  }
}
