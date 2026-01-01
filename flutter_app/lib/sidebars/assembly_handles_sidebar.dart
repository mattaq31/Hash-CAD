import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:flutter/gestures.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/material.dart';

import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import '../app_management/server_state.dart';
import 'layer_manager.dart';
import '../main_windows/alert_window.dart';


Color getValencyColor(int valency) {
  if (valency >= 8) return Colors.redAccent;
  if (valency >= 5) return Colors.orangeAccent;
  if (valency >= 3) return Colors.yellowAccent;
  return Colors.greenAccent;
}


class AssemblyHandleDesignTools extends StatefulWidget {
  const AssemblyHandleDesignTools({super.key});

  @override
  State<AssemblyHandleDesignTools> createState() => _AssemblyHandleDesignTools();
}

class _AssemblyHandleDesignTools extends State<AssemblyHandleDesignTools> with WidgetsBindingObserver {
  TextEditingController handleAddTextController = TextEditingController();
  FocusNode handleChangeFocusNode = FocusNode();

  // State for new UI mockup segmented controls
  bool preventSelfComplementarySlats = false;
  String _updateScope = 'all'; // 'all' or 'interfaces'
  String _handleAttachment = 'top'; // 'top' or 'bottom'
  final TextEditingController _defaultHandleController = TextEditingController(text: '1');

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
      Text("Assembly Handles", textAlign: TextAlign.center,
          style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 10),
      // Section 1: Automated Generation
      Text("Automated Generation", style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
      SizedBox(height: 10),

      // Library size row
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text("Library size", style: TextStyle(fontSize: 14)),
          SizedBox(width: 10),
          SizedBox(
            width: 60,
            height: 36,
            child: TextField(
              controller: handleAddTextController,
              focusNode: handleChangeFocusNode,
              decoration: InputDecoration(
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              ),
              keyboardType: TextInputType.number,
              textAlign: TextAlign.center,
              textInputAction: TextInputAction.done,
              inputFormatters: <TextInputFormatter>[
                FilteringTextInputFormatter.digitsOnly
              ],
              onSubmitted: (value) {
                _updateHandleCount(serverState);
              },
            ),
          ),
        ],
      ),

      SizedBox(height: 10),
      // Toggle buttons row (icon-based, highlight when active)
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Self-binding toggle - single button that highlights when on
          IconButton(
            tooltip: 'Prevent slat self-binding',
            onPressed: () {
              setState(() {
              preventSelfComplementarySlats = !preventSelfComplementarySlats;
              serverState.updateEvoParam("split_sequence_handles", preventSelfComplementarySlats.toString());
              });
            },
            icon: Icon(Icons.do_not_disturb_alt, size: 20),
            style: IconButton.styleFrom(
              backgroundColor: preventSelfComplementarySlats
                  ? Theme.of(context).colorScheme.primary
                  : Theme.of(context).colorScheme.primaryContainer,
              foregroundColor: preventSelfComplementarySlats
                  ? Theme.of(context).colorScheme.onPrimary
                  : null,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              padding: const EdgeInsets.all(8),
              minimumSize: const Size(36, 36),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          SizedBox(width: 15),
          // Update scope toggles - two buttons, one highlighted based on selection
          IconButton(
            tooltip: 'Update all layer interfaces and handles already in place',
            onPressed: () {
              setState(() {
                _updateScope = 'all';
              });
            },
            icon: Icon(Icons.select_all, size: 20),
            style: IconButton.styleFrom(
              backgroundColor: _updateScope == 'all'
                  ? Theme.of(context).colorScheme.primary
                  : Theme.of(context).colorScheme.primaryContainer,
              foregroundColor: _updateScope == 'all'
                  ? Theme.of(context).colorScheme.onPrimary
                  : null,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              padding: const EdgeInsets.all(8),
              minimumSize: const Size(36, 36),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          SizedBox(width: 8),
          IconButton(
            tooltip: 'Update only layer interface locations',
            onPressed: () {
              setState(() {
                _updateScope = 'interfaces';
              });
            },
            icon: Icon(Icons.layers, size: 20),
            style: IconButton.styleFrom(
              backgroundColor: _updateScope == 'interfaces'
                  ? Theme.of(context).colorScheme.primary
                  : Theme.of(context).colorScheme.primaryContainer,
              foregroundColor: _updateScope == 'interfaces'
                  ? Theme.of(context).colorScheme.onPrimary
                  : null,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              padding: const EdgeInsets.all(8),
              minimumSize: const Size(36, 36),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
        ],
      ),
      SizedBox(height: 10),

      // Randomize and Evolve buttons
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          ElevatedButton.icon(
            onPressed: () {
              int uniqueHandleCount = int.tryParse(handleAddTextController.text) ?? 10;
              appState.generateRandomAssemblyHandles(
                uniqueHandleCount,
                preventSelfComplementarySlats,
                allAvailableHandles: _updateScope == 'all',
              );
              appState.updateDesignHammingValue();
            },
            icon: Icon(Icons.shuffle, size: 18),
            label: Text("Randomize"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
          SizedBox(width: 10),
          ElevatedButton.icon(
            onPressed: null, // Non-functional for now
            icon: Icon(Icons.auto_awesome, size: 18),
            label: Text("Evolve"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
      SizedBox(height: 10),
      Divider(thickness: 1, color: Colors.grey.shade200),

      // Section 2: Manual Editing
      Text("Manual Editing", style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
      SizedBox(height: 10),

      // Row containing: 6 icon buttons | numerical input | top/bottom toggles
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // 6 icon buttons in 2x3 grid
          Column(
            children: [
              // Row 1
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    tooltip: 'Place handle',
                    onPressed: null,
                    icon: const Icon(Icons.add_location_alt, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.all(8),
                      minimumSize: const Size(36, 36),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                  SizedBox(width: 8),
                  IconButton(
                    tooltip: 'Delete handle',
                    onPressed: null,
                    icon: const Icon(Icons.wrong_location, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.all(8),
                      minimumSize: const Size(36, 36),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                  SizedBox(width: 8),
                  IconButton(
                    tooltip: 'Move handle',
                    onPressed: null,
                    icon: const Icon(Icons.open_with, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.all(8),
                      minimumSize: const Size(36, 36),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
              SizedBox(height: 8),
              // Row 2
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    tooltip: 'Link handles',
                    onPressed: null,
                    icon: const Icon(Icons.link, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.all(8),
                      minimumSize: const Size(36, 36),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                  SizedBox(width: 8),
                  IconButton(
                    tooltip: 'Delete links',
                    onPressed: null,
                    icon: const Icon(Icons.link_off, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.all(8),
                      minimumSize: const Size(36, 36),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                  SizedBox(width: 8),
                  IconButton(
                    tooltip: 'Block handle placement',
                    onPressed: null,
                    icon: const Icon(Icons.block, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.all(8),
                      minimumSize: const Size(36, 36),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ),
            ],
          ),
          SizedBox(width: 12),
          // Numerical input for default handle value
          Tooltip(
            message: 'Default handle value for placement',
            child: SizedBox(
              width: 50,
              height: 36,
              child: TextField(
                controller: _defaultHandleController,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.center,
                decoration: InputDecoration(
                  border: OutlineInputBorder(),
                  contentPadding: EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                ),
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              ),
            ),
          ),
          SizedBox(width: 8),
          // Vertical top/bottom toggles
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                tooltip: 'Attach to top',
                onPressed: () {
                  setState(() {
                    _handleAttachment = 'top';
                  });
                },
                icon: Icon(Icons.arrow_upward, size: 16),
                style: IconButton.styleFrom(
                  backgroundColor: _handleAttachment == 'top'
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.primaryContainer,
                  foregroundColor: _handleAttachment == 'top'
                      ? Theme.of(context).colorScheme.onPrimary
                      : null,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                  padding: const EdgeInsets.all(4),
                  minimumSize: const Size(28, 28),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
              SizedBox(height: 4),
              IconButton(
                tooltip: 'Attach to bottom',
                onPressed: () {
                  setState(() {
                    _handleAttachment = 'bottom';
                  });
                },
                icon: Icon(Icons.arrow_downward, size: 16),
                style: IconButton.styleFrom(
                  backgroundColor: _handleAttachment == 'bottom'
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.primaryContainer,
                  foregroundColor: _handleAttachment == 'bottom'
                      ? Theme.of(context).colorScheme.onPrimary
                      : null,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                  padding: const EdgeInsets.all(4),
                  minimumSize: const Size(28, 28),
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
            ],
          ),
        ],
      ),
      SizedBox(height: 15),

      // Slat Linker card (prominent styling)
      InkWell(
        onTap: null, // Non-functional for now
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Theme.of(context).colorScheme.primary, width: 2),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.hub, size: 28, color: Theme.of(context).colorScheme.primary),
              SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text("Slat Linker", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text("Define assembly links", style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
                ],
              ),
            ],
          ),
        ),
      ),
      SizedBox(height: 15),

      // Utility buttons - stacked in two rows
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          FilledButton.icon(
            onPressed: null, // Non-functional for now
            icon: Icon(Icons.delete_sweep, size: 18),
            label: Text("Delete All"),
            style: FilledButton.styleFrom(
              backgroundColor: Colors.red,
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              textStyle: TextStyle(fontSize: 14),
            ),
          ),
          SizedBox(width: 8),
          FilledButton.icon(
            onPressed: null, // Non-functional for now
            icon: Icon(Icons.link_off, size: 18),
            label: Text("Delete Links"),
            style: FilledButton.styleFrom(
              backgroundColor: Colors.red,
              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              textStyle: TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
      SizedBox(height: 8),
      FilledButton.icon(
        onPressed: null, // Non-functional for now
        icon: Icon(Icons.import_contacts, size: 18),
        label: Text("File Import"),
        style: FilledButton.styleFrom(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          textStyle: TextStyle(fontSize: 14),
        ),
      ),
      SizedBox(height: 5),
      Divider(thickness: 2, color: Colors.grey.shade300),
      // Row(
      //   mainAxisAlignment: MainAxisAlignment.end,
      //   children: [
      //     Text("Handle library size", style: TextStyle(fontSize: 16)),
      //     SizedBox(width: 10),
      //     Padding(
      //       padding: const EdgeInsets.only(right: 25.0),
      //       child: Align(
      //         alignment: Alignment.centerRight,
      //         child: SizedBox(
      //           width: 60,
      //           child: TextField(
      //             controller: handleAddTextController,
      //             focusNode: handleChangeFocusNode,
      //             keyboardType: TextInputType.number,
      //             decoration: InputDecoration(
      //               border: OutlineInputBorder(),
      //             ),
      //             textInputAction: TextInputAction.done,
      //             inputFormatters: <TextInputFormatter>[
      //               FilteringTextInputFormatter.digitsOnly
      //             ],
      //             onSubmitted: (value) {
      //               _updateHandleCount(serverState);
      //             },
      //           ),
      //         ),
      //       ),
      //     ),
      //   ],
      // ),
      // CheckboxListTile(
      //   contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 0), // Reduces spacing
      //   title: const Text('Prevent slat self-binding', textAlign: TextAlign.center),
      //   value: serverState.evoParams['split_sequence_handles'] == 'true',
      //   onChanged: (bool? value) {
      //     setState(() {
      //       bool preventSelfComplementarySlats = value ?? false;
      //       serverState.updateEvoParam("split_sequence_handles", preventSelfComplementarySlats.toString());
      //     });
      //   },
      // ),
      // SizedBox(height: 10),
      // Row(
      //   mainAxisAlignment: MainAxisAlignment.center,
      //   children: [
      //     ElevatedButton.icon(
      //       onPressed: appState.currentlyComputingHamming ? null : () {
      //         appState.generateRandomAssemblyHandles(int.parse(serverState.evoParams['unique_handle_sequences']!), serverState.evoParams['split_sequence_handles'] == 'true');
      //         appState.updateDesignHammingValue();
      //         actionState.setAssemblyHandleDisplay(true);
      //       },
      //       icon: Icon(Icons.shuffle, size: 18),
      //       label: Text("Randomize"),
      //       style: ElevatedButton.styleFrom(
      //         padding: EdgeInsets.symmetric(
      //             horizontal: 16, vertical: 12),
      //         textStyle: TextStyle(fontSize: 16),
      //       ),
      //     ),
      //     SizedBox(width: 10),
      //     ElevatedButton.icon(
      //       onPressed: appState.currentlyComputingHamming ? null : () {
      //         if (!kIsWeb) {
      //           actionState.activateEvolveMode();
      //         } else {
      //           showDialog<String>(
      //               context: context,
      //               builder: (BuildContext context) =>
      //                   AlertDialog(
      //                     title:
      //                     const Text('Assembly Handle Evolution'),
      //                     content: RichText(
      //                       text: TextSpan(
      //                         style: TextStyle(color: Colors.black87, fontSize: 16),
      //                         children: [
      //                           const TextSpan(text: 'To run assembly handle evolution, please download the desktop version of the app ('),
      //                           TextSpan(
      //                             text: 'https://github.com/mattaq31/Hash-CAD/releases',
      //                             style: TextStyle(color: Colors.blue, decoration: TextDecoration.underline),
      //                             recognizer: TapGestureRecognizer()
      //                               ..onTap = () {
      //                                 launchUrl(Uri.parse('https://github.com/mattaq31/Hash-CAD/releases'));
      //                               },
      //                           ),
      //                           const TextSpan(text: ')!'),
      //                         ],
      //                       ),
      //                     ),
      //                     actions: <Widget>[
      //                       TextButton(
      //                         onPressed: () =>
      //                             Navigator.pop(context, 'OK'),
      //                         child: const Text('OK'),
      //                       ),
      //                     ],
      //                   ));
      //         }
      //       },
      //       icon: Icon(Icons.auto_awesome, size: 18),
      //       label: Text("Evolve"),
      //       style: ElevatedButton.styleFrom(
      //         padding: EdgeInsets.symmetric(
      //             horizontal: 16, vertical: 12),
      //         textStyle: TextStyle(fontSize: 16),
      //       ),
      //     ),
      //   ],
      // ),
      // SizedBox(height: 10),
      // Row(
      //   mainAxisAlignment: MainAxisAlignment.center,
      //   children: [
      //     FilledButton.icon(
      //       onPressed: () {
      //         appState.clearAssemblyHandles();
      //       },
      //       icon: Icon(Icons.delete_sweep, size: 18),
      //       label: Text("Delete All"),
      //       style: ElevatedButton.styleFrom(
      //         backgroundColor: Colors.red,
      //         padding:
      //         EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      //         textStyle: TextStyle(fontSize: 16),
      //       ),
      //     ),
      //     SizedBox(width: 10),
      //     FilledButton.icon(
      //       onPressed: () async {
      //         bool readStatus = await appState.updateAssemblyHandlesFromFile(context);
      //         if (!readStatus && context.mounted) {
      //           showWarning(
      //             context,
      //             'Error Reading Assembly Handles',
      //             'Failed to read assembly handles from file. Do your assembly handle positions match the corresponding locations in your slat array?',
      //           );
      //         }
      //         if(readStatus) {
      //           appState.updateDesignHammingValue();
      //           actionState.setAssemblyHandleDisplay(true);
      //         }
      //       },
      //       icon: Icon(Icons.import_contacts, size: 18),
      //       label: Text("File Import"),
      //       style: ElevatedButton.styleFrom(
      //         padding:
      //         EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      //         textStyle: TextStyle(fontSize: 16),
      //       ),
      //     ),
      //   ],
      // ),
      // SizedBox(height: 5),
      // Divider(thickness: 2, color: Colors.grey.shade300),
      Text("Parasitic Interactions", textAlign: TextAlign.center,
          style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 10),
      Container(
        width: 300,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: getValencyColor(appState.currentMaxValency), // depends on max valency
            width: 3,
          ),
          boxShadow: [
            BoxShadow(
              color: getValencyColor(appState.currentMaxValency).withValues(alpha: 0.6),
              blurRadius: 8,
              spreadRadius: 2,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end, // right-align text
                  children: const [
                    Text(
                      "Maximum Valency",
                      textAlign: TextAlign.right,
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 14),
                    Text(
                      "Effective Valency",
                      textAlign: TextAlign.right,
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                // const SizedBox(width: 2), // smaller gap between labels and numbers
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      appState.currentMaxValency.toString(),
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      // set to 3dp
                      appState.currentEffValency.toStringAsFixed(2),
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              appState.currentlyComputingHamming
                  ? 'Computing...'
                  : appState.hammingValueValid
                  ? "Up-to-date"
                  : "Out-of-date",
              style: TextStyle(
                fontSize: 16,
                color: appState.currentlyComputingHamming
                    ? Colors.yellow
                    : appState.hammingValueValid
                    ? Colors.green
                    : Colors.red,
              ),
            ),
          ],
        ),
      ),
      const SizedBox(height: 10),
      ElevatedButton.icon(
        onPressed: appState.hammingValueValid || appState.currentlyComputingHamming
            ? null
            : () => appState.updateDesignHammingValue(),
        label: const Text("Recalculate Score"),
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: const TextStyle(fontSize: 16),
        ),
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
