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
import '../crisscross_core/assembly_handle_pattern.dart';
import '../graphics/honeycomb_pictogram.dart';
import 'layer_manager.dart';
import '../dialogs/alert_window.dart';
import '../dialogs/fluorophore_library_dialog.dart';
import '../echo_and_experimental_helpers/mass_fluorophore_dialog.dart';


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

class _AssemblyHandleDesignTools extends State<AssemblyHandleDesignTools> {
  TextEditingController handleAddTextController = TextEditingController();
  FocusNode handleChangeFocusNode = FocusNode();
  FocusNode defaultHandleFocusNode = FocusNode();

  // State for new UI mockup segmented controls
  bool preventSelfComplementarySlats = false;
  String _updateScope = 'all'; // 'all' or 'interfaces'
  final TextEditingController _defaultHandleController = TextEditingController();
  final ScrollController _fluorophoreScrollController = ScrollController();
  final ScrollController _patternScrollController = ScrollController();

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

  @override
  void dispose() {
    handleAddTextController.dispose();
    handleChangeFocusNode.dispose();
    defaultHandleFocusNode.dispose();
    _defaultHandleController.dispose();
    _fluorophoreScrollController.dispose();
    _patternScrollController.dispose();
    super.dispose();
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
            onPressed: actionState.lockEdits ? null : () {
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
            onPressed: (actionState.lockEdits || appState.currentlyComputingHamming) ? null : () {
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

      // Section 2: Manual Editing (with fluorophore toggle)
      // Stack keeps the heading centered like the other section titles while
      // the fluorophore toggle stays pinned to the right edge.
      Stack(
        alignment: Alignment.center,
        children: [
          Text("Manual Editing", textAlign: TextAlign.center, style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
          Align(
            alignment: Alignment.centerRight,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildPanelToggleButton(
                  context,
                  icon: Icons.pattern,
                  tooltip: 'Assembly handle patterns',
                  active: actionState.assemblyPatternMode,
                  onPressed: () => actionState.setAssemblyPatternMode(!actionState.assemblyPatternMode),
                ),
                SizedBox(width: 4),
                _buildPanelToggleButton(
                  context,
                  icon: Icons.highlight,
                  tooltip: 'Fluorophore editing',
                  active: actionState.fluorophoreEditMode,
                  onPressed: () => actionState.setFluorophoreEditMode(!actionState.fluorophoreEditMode),
                ),
              ],
            ),
          ),
        ],
      ),
      SizedBox(height: 10),

      // Fluorophore editing panel / assembly handle pattern panel (shown when the corresponding toggle is active)
      if (actionState.fluorophoreEditMode) ...[
        _buildFluorophoreEditPanel(context, appState, actionState),
      ] else if (actionState.assemblyPatternMode) ...[
        _buildAssemblyPatternPanel(context, appState, actionState),
      ] else ...[


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
                    onPressed: (!actionState.lockEdits && appState.selectedAssemblyPositions.length >= 2) ? () {
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
                        // Selection is intentionally preserved so operations can be chained.
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
                    onPressed: (!actionState.lockEdits && appState.selectedAssemblyPositions.isNotEmpty) ? () {
                      int intSide = getSlatSideFromLayer(appState.layerMap, appState.selectedLayerKey, actionState.assemblyAttachMode);
                      for (var coord in appState.selectedAssemblyPositions) {
                        var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[coord];
                        if (slatID != null) {
                          var slat = appState.slats[slatID]!;
                          int position = slat.slatCoordinateToPosition[coord]!;
                          appState.unlinkHandle((slatID, position, intSide));
                        }
                      }
                      // Selection is intentionally preserved so operations can be chained.
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
                    onPressed: (!actionState.lockEdits && appState.selectedAssemblyPositions.isNotEmpty) ? () {
                      int intSide = getSlatSideFromLayer(appState.layerMap, appState.selectedLayerKey, actionState.assemblyAttachMode);
                      for (var coord in appState.selectedAssemblyPositions) {
                        var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[coord];
                        if (slatID != null) {
                          var slat = appState.slats[slatID]!;
                          int position = slat.slatCoordinateToPosition[coord]!;
                          appState.toggleHandleBlockAndApply((slatID, position, intSide));
                        }
                      }
                      // Selection is intentionally preserved so operations can be chained.
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
          Text("Palette:", style: TextStyle(fontSize: 14)),
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
                textInputAction: TextInputAction.done,
                decoration: InputDecoration(
                  border: OutlineInputBorder(),
                  contentPadding: EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                ),
                inputFormatters: <TextInputFormatter>[FilteringTextInputFormatter.digitsOnly],
                onSubmitted: (value) => _updateDefaultHandleCount(actionState),
              ),
            ),
          ),

          SizedBox(width: 8),
          // Random, Enforce, and Block toggle buttons
          Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
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
              SizedBox(width: 4),
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
              SizedBox(width: 4),
              IconButton(
                tooltip: 'Block mode: place/remove blocks at positions',
                onPressed: () => actionState.setAssemblyBlockMode(!actionState.assemblyBlockMode),
                icon: Icon(Icons.block, size: 16),
                style: IconButton.styleFrom(
                  backgroundColor: actionState.assemblyBlockMode
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.primaryContainer,
                  foregroundColor: actionState.assemblyBlockMode
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
          // Honeycomb pictogram + vertical top/bottom toggles
          _buildAttachSideSelector(context, actionState),
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
                onPressed: actionState.lockEdits ? null : () async {
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
                onPressed: actionState.lockEdits ? null : () {
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
                onPressed: actionState.lockEdits ? null : () {
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
                onPressed: actionState.lockEdits ? null : () {
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
      ], // end of else (normal manual editing)
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
                      "Max Bond Count",
                      textAlign: TextAlign.right,
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 14),
                    Text(
                      "Eff. Bond Count",
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

  /// Builds the fluorophore editing panel shown when fluorophoreEditMode is active.
  Widget _buildFluorophoreEditPanel(BuildContext context, DesignState appState, ActionState actionState) {
    final palette = appState.fluorophorePalette;
    final selected = actionState.selectedFluorophore;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Edit Library + Mass Edit buttons (above library)
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FilledButton.icon(
              onPressed: actionState.lockEdits ? null : () async {
                final result = await showFluorophoreLibraryDialog(context, palette);
                if (result != null) {
                  _applyLibraryChanges(appState, actionState, result);
                }
              },
              icon: const Icon(Icons.edit, size: 16),
              label: const Text('Edit Library', style: TextStyle(fontSize: 14)),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                minimumSize: const Size(0, 36),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton.icon(
              onPressed: actionState.lockEdits ? null : () async {
                final result = await showMassFluorophoreDialog(
                  context,
                  slats: appState.slats,
                  fluorophorePalette: palette,
                  activeFluorophore: selected,
                );
                if (result != null) _applyMassResult(appState, result);
              },
              icon: const Icon(Icons.format_paint, size: 16),
              label: const Text('Mass Edit', style: TextStyle(fontSize: 14)),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                minimumSize: const Size(0, 36),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Fluorophore list + helix side selector side by side (centered)
        SizedBox(
          height: 120,
          child: Center(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Fluorophore vertical list
                SizedBox(
                  width: 160,
                  child: palette.isEmpty
                      ? Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Text('No fluorophores defined.\nUse "Edit Library" to add some.',
                              style: TextStyle(fontSize: 14, color: Colors.grey.shade600)),
                        )
                      : Scrollbar(
                          controller: _fluorophoreScrollController,
                          thumbVisibility: palette.length > 4,
                          child: ListView(
                            controller: _fluorophoreScrollController,
                            shrinkWrap: true,
                            children: palette.values.map((f) => InkWell(
                              onTap: () => actionState.setSelectedFluorophore(
                                  selected == f.name ? null : f.name),
                              child: Container(
                                padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                                decoration: BoxDecoration(
                                  color: selected == f.name
                                      ? Theme.of(context).colorScheme.primaryContainer
                                      : null,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    fluorophoreShapeIcon(f.shape, size: 14),
                                    const SizedBox(width: 6),
                                    Text(f.name, style: const TextStyle(fontSize: 14)),
                                  ],
                                ),
                              ),
                            )).toList(),
                          ),
                        ),
                ),
                const SizedBox(width: 12),
                // Helix side selector
                _buildAttachSideSelector(context, actionState),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        // Action buttons
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FilledButton.icon(
              onPressed: (!actionState.lockEdits && selected != null && appState.selectedAssemblyPositions.isNotEmpty) ? () {
                _applyFluorophoreToSelection(appState, actionState);
              } : null,
              icon: const Icon(Icons.check, size: 16),
              label: const Text('Assign', style: TextStyle(fontSize: 14)),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                minimumSize: const Size(0, 36),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton.icon(
              onPressed: (!actionState.lockEdits && appState.selectedAssemblyPositions.isNotEmpty) ? () {
                _clearFluorophoreFromSelection(appState, actionState);
              } : null,
              icon: const Icon(Icons.clear, size: 16),
              label: const Text('Clear', style: TextStyle(fontSize: 14)),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                minimumSize: const Size(0, 36),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),

        // Clear All button
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FilledButton.icon(
              onPressed: (!actionState.lockEdits && palette.isNotEmpty) ? () {
                appState.clearAllFluorophoreAssignments();
              } : null,
              icon: const Icon(Icons.delete_sweep, size: 16),
              label: const Text('Clear All', style: TextStyle(fontSize: 14)),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                minimumSize: const Size(0, 36),
                backgroundColor: Colors.red.shade700,
                foregroundColor: Colors.white,
                disabledBackgroundColor: Colors.grey.shade300,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  /// Builds a header toggle that swaps the manual editing area for an alternate panel.
  /// Highlighted while [active]; the tooltip switches to a 'return' hint when the panel is open.
  Widget _buildPanelToggleButton(BuildContext context,
      {required IconData icon, required String tooltip, required bool active, required VoidCallback onPressed}) {
    final colorScheme = Theme.of(context).colorScheme;
    return IconButton(
      tooltip: active ? 'Return to manual handles' : tooltip,
      onPressed: onPressed,
      icon: Icon(icon, size: 20),
      style: IconButton.styleFrom(
        backgroundColor: active ? colorScheme.primary : colorScheme.primaryContainer,
        foregroundColor: active ? colorScheme.onPrimary : null,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: const EdgeInsets.all(6),
        minimumSize: const Size(32, 32),
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }

  /// Builds the honeycomb pictogram with vertical top/bottom toggles used to pick the slat side for handle placement.
  Widget _buildAttachSideSelector(BuildContext context, ActionState actionState) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        HoneycombCustomPainterWidget(
          color: Colors.grey.shade400,
          size: 8,
          highlightColor: Theme.of(context).colorScheme.primary,
          highlightTop: actionState.assemblyAttachMode == 'top',
          highlightBottom: actionState.assemblyAttachMode == 'bottom',
        ),
        const SizedBox(width: 4),
        Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              tooltip: 'Attach to top of slat',
              onPressed: () {
                actionState.updateAssemblyAttachMode('top');
              },
              icon: const Icon(Icons.arrow_upward, size: 16),
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
            const SizedBox(height: 4),
            IconButton(
              tooltip: 'Attach to bottom of slat',
              onPressed: () {
                actionState.updateAssemblyAttachMode('bottom');
              },
              icon: const Icon(Icons.arrow_downward, size: 16),
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
      ],
    );
  }

  /// Builds the assembly handle pattern panel shown when assemblyPatternMode is active.
  /// Users record the current handle selection as a pattern, then pick a pattern to stamp it onto the canvas.
  Widget _buildAssemblyPatternPanel(BuildContext context, DesignState appState, ActionState actionState) {
    final patterns = appState.assemblyHandlePatterns;
    final selectedId = actionState.selectedAssemblyPatternId;

    // The selected pattern can disappear through undo or import - drop the stale selection after this frame
    if (selectedId != null && !patterns.containsKey(selectedId)) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (actionState.selectedAssemblyPatternId == selectedId) {
          actionState.setSelectedAssemblyPattern(null);
        }
      });
    }
    final bool isPlacing = selectedId != null && patterns.containsKey(selectedId);
    final bool canRecord = !actionState.lockEdits && !isPlacing && appState.selectedAssemblyPositions.isNotEmpty;
    // matches the FilledButton colours (enabled and disabled) so all three record buttons look alike
    final recordIconStyle = IconButton.styleFrom(
      backgroundColor: Theme.of(context).colorScheme.primary,
      foregroundColor: Theme.of(context).colorScheme.onPrimary,
      disabledBackgroundColor: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.12),
      disabledForegroundColor: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      padding: const EdgeInsets.all(8),
      minimumSize: const Size(36, 36),
      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Record buttons (all / handles only / blocks only) - disabled while placing, as the canvas is no longer
        // in selection mode
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FilledButton.icon(
              onPressed: canRecord ? () => _recordPattern(context, appState, actionState) : null,
              icon: const Icon(Icons.fiber_manual_record, size: 16),
              label: const Text('Record Pattern', style: TextStyle(fontSize: 14)),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                minimumSize: const Size(0, 36),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              tooltip: 'Record handles only (ignore blocks)',
              onPressed: canRecord ? () => _recordPattern(context, appState, actionState, includeBlocks: false) : null,
              icon: const Icon(Icons.tag, size: 18),
              style: recordIconStyle,
            ),
            const SizedBox(width: 4),
            IconButton(
              tooltip: 'Record blocks only (ignore handles)',
              onPressed: canRecord ? () => _recordPattern(context, appState, actionState, includeHandles: false) : null,
              icon: const Icon(Icons.block, size: 18),
              style: recordIconStyle,
            ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          isPlacing
              ? 'Click on the canvas to place the pattern${appState.gridMode == '90' ? ' (R to rotate)' : ''}.\nClick the pattern again to return to selection.'
              : 'Select handles on the canvas, then record them.\nClick a pattern to start placing it.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
        ),
        const SizedBox(height: 8),

        // Pattern list
        SizedBox(
          height: 150,
          width: 300,
          child: patterns.isEmpty
              ? Center(
                  child: Text('No patterns recorded yet.',
                      style: TextStyle(fontSize: 14, color: Colors.grey.shade600)),
                )
              : Scrollbar(
                  controller: _patternScrollController,
                  thumbVisibility: patterns.length > 3,
                  child: ListView(
                    controller: _patternScrollController,
                    children: patterns.values
                        .map((pattern) => _buildPatternCard(context, appState, actionState, pattern))
                        .toList(),
                  ),
                ),
        ),
        const SizedBox(height: 8),

        // Placement options: slat side + enforcement of placed values
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildAttachSideSelector(context, actionState),
            const SizedBox(width: 16),
            Tooltip(
              message: 'Mark values placed from a pattern as enforced',
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Checkbox(
                    value: actionState.assemblyPatternEnforce,
                    onChanged: (value) => actionState.setAssemblyPatternEnforce(value ?? false),
                  ),
                  const Text('Enforce values', style: TextStyle(fontSize: 14)),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  /// Records the current handle selection as a pattern, optionally restricted to valued handles or blocks,
  /// and warns if nothing in the selection matched.
  void _recordPattern(BuildContext context, DesignState appState, ActionState actionState,
      {bool includeHandles = true, bool includeBlocks = true}) {
    final id = appState.recordAssemblyHandlePattern(appState.selectedLayerKey, actionState.assemblyAttachMode,
        includeHandles: includeHandles, includeBlocks: includeBlocks);
    if (id != null) return;

    final String what = !includeBlocks ? 'assembly handles' : !includeHandles ? 'blocked handles' : 'assembly handles or blocks';
    showWarning(context, 'Nothing Recorded', 'The current selection does not contain any $what on this side of the layer.');
  }

  /// Single pattern entry: name, handle count, rename and delete actions. Tapping toggles placement of the pattern.
  Widget _buildPatternCard(BuildContext context, DesignState appState, ActionState actionState, AssemblyHandlePattern pattern) {
    final bool isSelected = actionState.selectedAssemblyPatternId == pattern.id;
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 3, horizontal: 2),
      color: isSelected ? colorScheme.primaryContainer : null,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: isSelected ? BorderSide(color: colorScheme.primary, width: 1.5) : BorderSide.none,
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: actionState.lockEdits
            ? null
            : () => actionState.setSelectedAssemblyPattern(isSelected ? null : pattern.id),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 10),
          child: Row(
            children: [
              Icon(Icons.pattern, size: 18, color: isSelected ? colorScheme.primary : Colors.grey.shade600),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(pattern.name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                    Text('${pattern.entries.length} handles', style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.edit, size: 16),
                tooltip: 'Rename pattern',
                onPressed: actionState.lockEdits ? null : () => _showPatternRenameDialog(context, appState, pattern),
                visualDensity: VisualDensity.compact,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
              ),
              IconButton(
                icon: Icon(Icons.close, size: 18, color: Colors.red.shade400),
                tooltip: 'Delete pattern',
                onPressed: actionState.lockEdits ? null : () {
                  if (isSelected) actionState.setSelectedAssemblyPattern(null);
                  appState.deleteAssemblyHandlePattern(pattern.id);
                },
                visualDensity: VisualDensity.compact,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Rename dialog for patterns; shows an inline error if the name is empty or already used by another pattern.
  void _showPatternRenameDialog(BuildContext context, DesignState appState, AssemblyHandlePattern pattern) {
    final controller = TextEditingController(text: pattern.name);
    String? errorText;
    showDialog(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) {
          void submit() {
            if (appState.renameAssemblyHandlePattern(pattern.id, controller.text)) {
              Navigator.pop(dialogContext);
            } else {
              setDialogState(() {
                errorText = controller.text.trim().isEmpty
                    ? 'Name cannot be empty'
                    : 'A pattern with this name already exists';
              });
            }
          }

          return AlertDialog(
            title: const Text('Rename Pattern'),
            content: TextField(
              controller: controller,
              autofocus: true,
              decoration: InputDecoration(border: const OutlineInputBorder(), errorText: errorText),
              onSubmitted: (_) => submit(),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')),
              FilledButton(onPressed: submit, child: const Text('Rename')),
            ],
          );
        },
      ),
    );
  }

  int _selectedAssemblySide(DesignState appState, ActionState actionState) {
    final helixKey = actionState.assemblyAttachMode == 'top' ? 'top_helix' : 'bottom_helix';
    return appState.layerMap[appState.selectedLayerKey]![helixKey] == 'H5' ? 5 : 2;
  }

  Iterable<HandleKey> _selectedAssemblyHandleKeys(DesignState appState, ActionState actionState) sync* {
    final side = _selectedAssemblySide(appState, actionState);
    final occupiedPoints = appState.occupiedGridPoints[appState.selectedLayerKey];
    if (occupiedPoints == null) return;

    for (var coord in appState.selectedAssemblyPositions) {
      final slatId = occupiedPoints[coord];
      if (slatId == null || slatId == 'SEED') continue;

      final slat = appState.slats[slatId];
      final position = slat?.slatCoordinateToPosition[coord];
      if (slat == null || position == null) continue;

      yield (slat.id, position, side);
    }
  }

  /// Applies the selected fluorophore to all currently selected assembly handle positions.
  void _applyFluorophoreToSelection(DesignState appState, ActionState actionState) {
    final fluorName = actionState.selectedFluorophore;
    if (fluorName == null) return;

    for (var key in _selectedAssemblyHandleKeys(appState, actionState)) {
      appState.assignFluorophoreToHandle(key, fluorName);
    }
  }

  /// Clears fluorophore from all currently selected assembly handle positions.
  void _clearFluorophoreFromSelection(DesignState appState, ActionState actionState) {
    for (var key in _selectedAssemblyHandleKeys(appState, actionState)) {
      appState.clearFluorophoreFromHandle(key);
    }
  }

  /// Applies library changes from the dialog, including rename cascades.
  void _applyLibraryChanges(DesignState appState, ActionState actionState, FluorophoreLibraryEditResult result) {
    final selectedName = actionState.selectedFluorophore;

    final pendingRenames = result.renamedNames.entries.where((entry) {
      return appState.fluorophorePalette.containsKey(entry.key) && entry.key != entry.value;
    }).toList();

    final tempRenameTargets = <String, String>{};
    int tempIndex = 0;
    for (var entry in pendingRenames) {
      String tempName = '__fluorophore_tmp_${tempIndex++}__';
      while (appState.fluorophorePalette.containsKey(tempName) || result.palette.containsKey(tempName)) {
        tempName = '__fluorophore_tmp_${tempIndex++}__';
      }
      appState.renameFluorophore(entry.key, tempName);
      tempRenameTargets[tempName] = entry.value;
    }

    for (var entry in tempRenameTargets.entries) {
      appState.renameFluorophore(entry.key, entry.value);
    }

    for (var currentName in appState.fluorophorePalette.keys.toList()) {
      if (!result.palette.containsKey(currentName)) {
        appState.deleteFluorophore(currentName);
      }
    }

    for (var entry in result.palette.entries) {
      if (!appState.fluorophorePalette.containsKey(entry.key)) {
        appState.addFluorophore(entry.value);
      } else if (appState.fluorophorePalette[entry.key]!.shape != entry.value.shape) {
        appState.updateFluorophoreShape(entry.key, entry.value.shape);
      }
    }

    if (selectedName == null) return;

    final updatedSelectedName = result.renamedNames[selectedName] ?? selectedName;
    actionState.setSelectedFluorophore(
      result.palette.containsKey(updatedSelectedName) ? updatedSelectedName : null,
    );
  }

  /// Applies a mass fluorophore edit result.
  void _applyMassResult(DesignState appState, MassFluorophoreEditResult result) {
    if (result.clearAll) {
      appState.clearAllFluorophoreAssignments();
    } else if (result.fluorophoreName != null) {
      appState.massAssignFluorophore(result.perSlatPositions, result.fluorophoreName!);
    } else {
      appState.massClearFluorophore(result.perSlatPositions);
    }
  }
}
