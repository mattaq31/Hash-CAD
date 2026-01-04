import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:flutter/gestures.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/material.dart';

import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import '../app_management/server_state.dart';
import '../crisscross_core/common_utilities.dart';
import '../graphics/honeycomb_pictogram.dart';
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
  FocusNode defaultHandleFocusNode = FocusNode();

  // State for new UI mockup segmented controls
  bool preventSelfComplementarySlats = false;
  String _updateScope = 'all'; // 'all' or 'interfaces'
  String _handleAttachment = 'top'; // 'top' or 'bottom'
  final TextEditingController _defaultHandleController = TextEditingController();

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
      var actionState = context.read<ActionState>();
      _defaultHandleController.text = actionState.assemblyHandleValue;
      defaultHandleFocusNode.addListener(() {
        if (!defaultHandleFocusNode.hasFocus) {
          _updateDefaultHandleCount(actionState);
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
  
  // could consider limiting this below the library size...
  void _updateDefaultHandleCount(ActionState actionState){
    int? newValue = int.tryParse(_defaultHandleController.text);
    if (newValue != null && newValue >= 1 && newValue <= 999) {
      actionState.updateAssemblyHandleValue(newValue.toString());
    } else if (newValue != null && newValue < 1) {
      actionState.updateAssemblyHandleValue('1');
      _defaultHandleController.text = '1';
    } else {
      actionState.updateAssemblyHandleValue('999');
      _defaultHandleController.text = '999';
    }
    _defaultHandleController.text = actionState.assemblyHandleValue;
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
              serverState.updateEvoParam('update_scope', 'all');
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
              serverState.updateEvoParam('update_scope', 'interfaces');
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
          FilledButton.icon(
            onPressed: () {
              int uniqueHandleCount = int.tryParse(handleAddTextController.text) ?? 64;
              appState.generateRandomAssemblyHandles(
                uniqueHandleCount,
                preventSelfComplementarySlats,
                allAvailableHandles: _updateScope == 'all',
              );
              appState.updateDesignHammingValue();
            },
            icon: Icon(Icons.shuffle, size: 18),
            label: Text("Randomize"),
            style: FilledButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
          SizedBox(width: 10),
          FilledButton.icon(
            onPressed: appState.currentlyComputingHamming ? null : () {
              if (!kIsWeb) {
                actionState.activateEvolveMode();
              } else {
                showDialog<String>(
                  context: context,
                  builder: (BuildContext context) => AlertDialog(
                    title: const Text('Assembly Handle Evolution'),
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
                        onPressed: () => Navigator.pop(context, 'OK'),
                        child: const Text('OK'),
                      ),
                    ],
                  ),
                );
              }
            },
            icon: Icon(Icons.auto_awesome, size: 18),
            label: Text("Evolve"),
            style: FilledButton.styleFrom(
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


      // Row 1: Add/Delete/Move | Slat Linker | Link/Unlink/Block
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(width:20),
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Add/Delete/Move buttons
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    tooltip: 'Place handle',
                    onPressed: () => actionState.updateAssemblyMode('Add'),
                    icon: const Icon(Icons.add_location_alt, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: actionState.assemblyMode == 'Add'
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(context).colorScheme.primaryContainer,
                      foregroundColor: actionState.assemblyMode == 'Add'
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
                    tooltip: 'Delete handle',
                    onPressed: () => actionState.updateAssemblyMode('Delete'),
                    icon: const Icon(Icons.wrong_location, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: actionState.assemblyMode == 'Delete'
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(context).colorScheme.primaryContainer,
                      foregroundColor: actionState.assemblyMode == 'Delete'
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
                    tooltip: 'Move or edit handles',
                    onPressed: () => actionState.updateAssemblyMode('Move'),
                    icon: const Icon(Icons.pan_tool, size: 20),
                    style: IconButton.styleFrom(
                      backgroundColor: actionState.assemblyMode == 'Move'
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(context).colorScheme.primaryContainer,
                      foregroundColor: actionState.assemblyMode == 'Move'
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
              SizedBox(height: 12),
              // Link/Unlink/Block buttons
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    tooltip: 'Link selected handles',
                    onPressed: appState.selectedAssemblyPositions.length >= 2 ? () {
                      List<HandleKey> keys = [];
                      int intSide = getSlatSideFromLayer(appState.layerMap, appState.selectedLayerKey, actionState.assemblyAttachMode);
                      for (var coord in appState.selectedAssemblyPositions) {
                        var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[coord];
                        if (slatID != null) {
                          var slat = appState.slats[slatID]!;
                          int position = slat.slatCoordinateToPosition[coord]!;
                          keys.add((slatID, position, intSide));
                        }
                      }
                      if (keys.length >= 2) {
                        appState.linkHandlesAndPropagate(keys);
                        appState.clearAssemblySelection();
                      }
                    } : null,
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
                    tooltip: 'Remove links from selected handles',
                    onPressed: appState.selectedAssemblyPositions.isNotEmpty ? () {
                      int intSide = getSlatSideFromLayer(appState.layerMap, appState.selectedLayerKey, actionState.assemblyAttachMode);
                      for (var coord in appState.selectedAssemblyPositions) {
                        var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[coord];
                        if (slatID != null) {
                          var slat = appState.slats[slatID]!;
                          int position = slat.slatCoordinateToPosition[coord]!;
                          appState.unlinkHandle((slatID, position, intSide));
                        }
                      }
                      appState.clearAssemblySelection();
                    } : null,
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
                    tooltip: 'Block/unblock selected handle positions',
                    onPressed: appState.selectedAssemblyPositions.isNotEmpty ? () {
                      int intSide = getSlatSideFromLayer(appState.layerMap, appState.selectedLayerKey, actionState.assemblyAttachMode);
                      for (var coord in appState.selectedAssemblyPositions) {
                        var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[coord];
                        if (slatID != null) {
                          var slat = appState.slats[slatID]!;
                          int position = slat.slatCoordinateToPosition[coord]!;
                          appState.toggleHandleBlockAndApply((slatID, position, intSide));
                        }
                      }
                      appState.clearAssemblySelection();
                    } : null,
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
          SizedBox(width: 20),
          // Slat Linker button (icon only)
          IconButton(
            tooltip: 'Open Slat Linker',
            onPressed: () => actionState.activateSlatLinker(),
            icon: Icon(Icons.mediation, size: 30),
            style: IconButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              foregroundColor: Theme.of(context).colorScheme.primary,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              padding: const EdgeInsets.all(8),
              minimumSize: const Size(40, 40),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              side: BorderSide(color: Theme.of(context).colorScheme.primary, width: 2),
            ),
          ),
        ],
      ),
      SizedBox(height: 10),
      // Row 2: Handle value input | Random/Lock | Honeycomb | Top/Bottom arrows
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // Numerical input for default handle value
          Text("Handle ID", style: TextStyle(fontSize: 14)),
          SizedBox(width: 10),
          Tooltip(
            message: 'Default handle value for placement',
            child: SizedBox(
              width: 50,
              height: 36,
              child: TextField(
                controller: _defaultHandleController,
                focusNode: defaultHandleFocusNode,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.center,
                decoration: InputDecoration(
                  border: OutlineInputBorder(),
                  contentPadding: EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                ),
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                onChanged: (value) => _updateDefaultHandleCount(actionState),
              ),
            ),
          ),
          SizedBox(width: 8),
          // Random and Enforce toggle buttons
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                tooltip: 'Random mode: place random handle values',
                onPressed: () => actionState.setAssemblyRandomMode(!actionState.assemblyRandomMode),
                icon: Icon(Icons.shuffle, size: 16),
                style: IconButton.styleFrom(
                  backgroundColor: actionState.assemblyRandomMode
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.primaryContainer,
                  foregroundColor: actionState.assemblyRandomMode
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
                tooltip: 'Enforce mode: lock placed handle values',
                onPressed: () => actionState.setAssemblyEnforceMode(!actionState.assemblyEnforceMode),
                icon: Icon(Icons.lock, size: 16),
                style: IconButton.styleFrom(
                  backgroundColor: actionState.assemblyEnforceMode
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.primaryContainer,
                  foregroundColor: actionState.assemblyEnforceMode
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
          SizedBox(width: 8),
          // Honeycomb pictogram showing handle attachment position
          HoneycombCustomPainterWidget(
            color: Colors.grey.shade400,
            size: 8,
            highlightColor: Theme.of(context).colorScheme.primary,
            highlightTop: actionState.assemblyAttachMode == 'top',
            highlightBottom: actionState.assemblyAttachMode == 'bottom',
          ),
          SizedBox(width: 4),
          // Vertical top/bottom toggles
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                tooltip: 'Attach to top of slat',
                onPressed: () {
                  setState(() => _handleAttachment = 'top');
                  actionState.updateAssemblyAttachMode('top');
                },
                icon: Icon(Icons.arrow_upward, size: 16),
                style: IconButton.styleFrom(
                  backgroundColor: actionState.assemblyAttachMode == 'top'
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.primaryContainer,
                  foregroundColor: actionState.assemblyAttachMode == 'top'
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
                tooltip: 'Attach to bottom of slat',
                onPressed: () {
                  setState(() => _handleAttachment = 'bottom');
                  actionState.updateAssemblyAttachMode('bottom');
                },
                icon: Icon(Icons.arrow_downward, size: 16),
                style: IconButton.styleFrom(
                  backgroundColor: actionState.assemblyAttachMode == 'bottom'
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.primaryContainer,
                  foregroundColor: actionState.assemblyAttachMode == 'bottom'
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
          SizedBox(width: 10),

        ],
      ),
      SizedBox(height: 15),

      // Utility buttons - stacked in two columns
      Row(
        children: [
          SizedBox(width: 15),
          Column(
            children: [
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
                  if (readStatus) {
                    appState.updateDesignHammingValue();
                    actionState.setAssemblyHandleDisplay(true);
                  }
                },
                icon: Icon(Icons.import_contacts, size: 18),
                label: Text("File Import"),
                style: FilledButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  textStyle: TextStyle(fontSize: 14),
                ),
              ),
              SizedBox(height: 10),
              FilledButton.icon(
                onPressed: () {
                  appState.clearAssemblyHandles();
                },
                icon: Icon(Icons.delete_sweep, size: 18),
                label: Text("Delete All"),
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.red,
                  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  textStyle: TextStyle(fontSize: 14),
                ),
              ),
            ],
          ),
          SizedBox(width: 5),
          Column(
            children: [
              FilledButton.icon(
                onPressed: () {
                  appState.syncAllAssemblyHandles();
                  appState.updateDesignHammingValue();
                },
                icon: Icon(Icons.sync, size: 18),
                label: Text("Sync Handles"),
                style: FilledButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  textStyle: TextStyle(fontSize: 14),
                ),
              ),
              SizedBox(height: 10),
              FilledButton.icon(
                onPressed: () {
                  appState.clearAllHandleLinks();
                },
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
        ],
      ),
      SizedBox(height: 5),
      Divider(thickness: 2, color: Colors.grey.shade300),
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
      FilledButton.icon(
        onPressed: appState.hammingValueValid || appState.currentlyComputingHamming
            ? null
            : () => appState.updateDesignHammingValue(),
        label: const Text("Recalculate Score"),
        style: FilledButton.styleFrom(
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
