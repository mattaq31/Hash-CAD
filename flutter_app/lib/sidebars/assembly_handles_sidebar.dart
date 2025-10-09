import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:flutter/gestures.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/material.dart';

import '../app_management/shared_app_state.dart';
import '../graphics/rating_indicator.dart';
import 'layer_manager.dart';
import '../main_windows/alert_window.dart';


class AssemblyHandleDesignTools extends StatefulWidget {
  const AssemblyHandleDesignTools({super.key});

  @override
  State<AssemblyHandleDesignTools> createState() => _AssemblyHandleDesignTools();
}

class _AssemblyHandleDesignTools extends State<AssemblyHandleDesignTools> with WidgetsBindingObserver {
  TextEditingController handleAddTextController = TextEditingController();
  FocusNode handleChangeFocusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      var serverState = context.read<ServerState>(); // Use read instead of watch
      handleAddTextController.text = serverState.evoParams['unique_handle_sequences']!;
      handleChangeFocusNode.addListener(() {
        if (!handleChangeFocusNode.hasFocus) {
          _updateHandleCount(serverState);
        }
      });
    });
  }

  void _updateHandleCount(ServerState serverState) {
    int? newValue = int.tryParse(handleAddTextController.text);
    if (newValue != null &&
        newValue >= 1 &&
        newValue <= 997) {
      serverState.updateEvoParam('unique_handle_sequences', newValue.toString());
    } else if (newValue != null && newValue < 1) {
      serverState.updateEvoParam('unique_handle_sequences', '1');
      handleAddTextController.text = '1';
    } else {
      serverState.updateEvoParam('unique_handle_sequences', '997');
      handleAddTextController.text = '997';
    }
    handleAddTextController.text = serverState.evoParams['unique_handle_sequences']!;
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    var serverState = context.watch<ServerState>();

    return Column(children: [
      Text("Assembly Handle Generation", textAlign: TextAlign.center,
          style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.bold)),
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
                  focusNode: handleChangeFocusNode,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(),
                  ),
                  textInputAction: TextInputAction.done,
                  inputFormatters: <TextInputFormatter>[
                    FilteringTextInputFormatter.digitsOnly
                  ],
                  onSubmitted: (value) {
                    _updateHandleCount(serverState);
                  },
                ),
              ),
            ),
          ),
        ],
      ),
      CheckboxListTile(
        contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 0), // Reduces spacing
        title: const Text('Prevent self-complementary slats', textAlign: TextAlign.center),
        value: serverState.evoParams['split_sequence_handles'] == 'true',
        onChanged: (bool? value) {
          setState(() {
            bool preventSelfComplementarySlats = value ?? false;
            serverState.updateEvoParam("split_sequence_handles", preventSelfComplementarySlats.toString());
          });
        },
      ),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          ElevatedButton.icon(
            onPressed: appState.currentlyComputingHamming ? null : () {
              appState.generateRandomAssemblyHandles(int.parse(serverState.evoParams['unique_handle_sequences']!), serverState.evoParams['split_sequence_handles'] == 'true');
              appState.updateDesignHammingValue();
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
            onPressed: appState.currentlyComputingHamming ? null : () {
              if (!kIsWeb) {
                actionState.activateEvolveMode();
              } else {
                showDialog<String>(
                    context: context,
                    builder: (BuildContext context) =>
                        AlertDialog(
                          title:
                          const Text('Assembly Handle Evolution'),
                          content: RichText(
                            text: TextSpan(
                              style: TextStyle(color: Colors.black87, fontSize: 16),
                              children: [
                                const TextSpan(text: 'To run assembly handle evolution, please download the desktop version of the app ('),
                                TextSpan(
                                  text: 'https://github.com/mattaq31/Hash-CAD/releases',
                                  style: TextStyle(color: Colors.blue, decoration: TextDecoration.underline),
                                  recognizer: TapGestureRecognizer()
                                    ..onTap = () {
                                      launchUrl(Uri.parse('https://github.com/mattaq31/Hash-CAD/releases'));
                                    },
                                ),
                                const TextSpan(text: ')!'),
                              ],
                            ),
                          ),
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
      SizedBox(height: 10),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          FilledButton.icon(
            onPressed: () {
              appState.clearAssemblyHandles();
            },
            icon: Icon(Icons.delete_sweep, size: 18),
            label: Text("Delete All"),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              padding:
              EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
          SizedBox(width: 10),
          FilledButton.icon(
            onPressed: () async {
              bool readStatus = await appState.updateAssemblyHandlesFromFile(context);
              if (!readStatus && context.mounted) {
                showWarning(
                  context,
                  'Error Reading Assembly Handles',
                  'Failed to read assembly handles from file. Do your assembly handle positions match the corresponding locations in your slat array?',
                );
              }
              if(readStatus) {
                appState.updateDesignHammingValue();
                actionState.setAssemblyHandleDisplay(true);
              }
            },
            icon: Icon(Icons.import_contacts, size: 18),
            label: Text("File Import"),
            style: ElevatedButton.styleFrom(
              padding:
              EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
      SizedBox(height: 5),
      Divider(thickness: 2, color: Colors.grey.shade300),
      Text("Assembly Scores", textAlign: TextAlign.center,
          style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 20),
      Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Column(
                children: [
                  Text("Max Pairwise Interactions",
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  Text(
                    appState.currentlyComputingHamming
                        ? 'Computing...'
                        : appState.hammingValueValid
                            ? "Up-to-date"
                            : "Out-of-date",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                        fontSize: 16,
                        color: appState.currentlyComputingHamming
                            ? Colors.yellow
                            : appState.hammingValueValid
                                ? Colors.green
                                : Colors.red),
                  ),
                ],
              ),

              SizedBox(width: 20),
              HammingIndicator(value: appState.currentHamming.toDouble()),
            ],
          ),
          SizedBox(height: 10),
          ElevatedButton.icon(
            onPressed: appState.hammingValueValid || appState.currentlyComputingHamming ? null : () {
              appState.updateDesignHammingValue();
            },
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
      LayerManagerWidget(
        appState: appState,
        actionState: actionState,
      ),
      SizedBox(height: 10),
      Divider(thickness: 2, color: Colors.grey.shade300),
    ]);
  }
}
