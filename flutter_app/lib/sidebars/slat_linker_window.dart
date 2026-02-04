import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import '../app_management/design_state_mixins/design_state_handle_link_mixin.dart';
import '../crisscross_core/slats.dart';
import '../crisscross_core/common_utilities.dart';

/// Natural sort comparison for slat IDs like "A-I1", "A-I2", "A-I10"
int _naturalCompare(String a, String b) {
  final regExp = RegExp(r'(\d+)|(\D+)');
  final matchesA = regExp.allMatches(a).toList();
  final matchesB = regExp.allMatches(b).toList();
  for (int i = 0; i < matchesA.length && i < matchesB.length; i++) {
    final partA = matchesA[i].group(0)!;
    final partB = matchesB[i].group(0)!;
    final numA = int.tryParse(partA);
    final numB = int.tryParse(partB);
    int cmp;
    if (numA != null && numB != null) {
      cmp = numA.compareTo(numB);
    } else {
      cmp = partA.compareTo(partB);
    }
    if (cmp != 0) return cmp;
  }
  return matchesA.length.compareTo(matchesB.length);
}

class SlatLinkerWindow extends StatefulWidget {
  const SlatLinkerWindow({super.key});

  @override
  State<SlatLinkerWindow> createState() => _SlatLinkerWindowState();
}

class _SlatLinkerWindowState extends State<SlatLinkerWindow> {
  String? selectedSlat1ID;
  String? selectedSlat2ID;
  Set<HandleKey> selectedHandles = {};
  final TextEditingController _slat1Controller = TextEditingController();
  final TextEditingController _slat2Controller = TextEditingController();
  bool _hasAutoPopulated = false;

  // Drag-select state
  bool _isDragging = false;
  Offset? _dragStart;
  Offset? _dragEnd;
  final Map<HandleKey, GlobalKey> _handleButtonKeys = {};
  final GlobalKey _handleDisplayAreaKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    // Listen for text changes to clear selection when field is cleared
    _slat1Controller.addListener(() {
      if (_slat1Controller.text.isEmpty && selectedSlat1ID != null) {
        setState(() => selectedSlat1ID = null);
      }
    });
    _slat2Controller.addListener(() {
      if (_slat2Controller.text.isEmpty && selectedSlat2ID != null) {
        setState(() => selectedSlat2ID = null);
      }
    });
  }

  /// Auto-populate slat selectors from selected assembly handles (max 2 unique slats)
  void _autoPopulateFromSelectedHandles(DesignState appState, ActionState actionState) {
    if (_hasAutoPopulated) return;
    if (appState.selectedAssemblyPositions.isEmpty) return;

    Set<String> uniqueSlatIDs = {};
    for (var coord in appState.selectedAssemblyPositions) {
      var slatID = appState.occupiedGridPoints[appState.selectedLayerKey]?[coord];
      if (slatID != null) {
        // Skip phantom slats - get parent instead
        var slat = appState.slats[slatID];
        if (slat != null && slat.phantomParent != null) {
          slatID = slat.phantomParent;
        }
        if (slatID != null) {
          uniqueSlatIDs.add(slatID);
        }
      }
      if (uniqueSlatIDs.length >= 2) break;
    }

    final slatList = uniqueSlatIDs.toList();
    if (slatList.isNotEmpty) {
      selectedSlat1ID = slatList[0];
      _slat1Controller.text = slatList[0].replaceFirst('-I', '-');
    }
    if (slatList.length > 1) {
      selectedSlat2ID = slatList[1];
      _slat2Controller.text = slatList[1].replaceFirst('-I', '-');
    }

    _hasAutoPopulated = true;
  }

  @override
  void dispose() {
    _slat1Controller.dispose();
    _slat2Controller.dispose();
    super.dispose();
  }

  List<String> _getAvailableSlats(DesignState appState) {
    var list = appState.slats.entries.where((e) => e.value.phantomParent == null).map((e) => e.key).toList();
    list.sort(_naturalCompare);
    return list;
  }

  /// toggles whether or not a handle is selected for editing
  void _toggleHandleSelection(HandleKey key, HandleLinkManager linkManager) {
    setState(() {
      if (selectedHandles.contains(key)) {
        selectedHandles.remove(key);
        for(var linkedHandle in linkManager.getLinkedHandles(key)) {
          selectedHandles.remove(linkedHandle);
        }
      } else {
        selectedHandles.add(key);
        for(var linkedHandle in linkManager.getLinkedHandles(key)) {
          selectedHandles.add(linkedHandle);
        }
      }
    });
  }

  /// unselect all handles
  void _clearSelection() {
    setState(() {
      selectedHandles.clear();
    });
  }

  /// toggles the selection of all handles on either one side of the other of a slat
  void _toggleAllHandles(String slatId, int side, DesignState appState) {
    final slat = appState.slats[slatId];
    if (slat == null) return;

    // Check if all handles for this side are already selected
    bool allSelected = true;
    for (int pos = 1; pos <= slat.maxLength; pos++) {
      if (!selectedHandles.contains((slatId, pos, side))) {
        allSelected = false;
        break;
      }
    }

    setState(() {
      for (int pos = 1; pos <= slat.maxLength; pos++) {
        if (allSelected) {
          selectedHandles.remove((slatId, pos, side));
        } else {
          selectedHandles.add((slatId, pos, side));
        }
      }
    });
  }

  /// Creates a global unique index for each handle button for drag-selection purposes
  GlobalKey _getOrCreateHandleKey(HandleKey handleKey) {
    return _handleButtonKeys.putIfAbsent(handleKey, () => GlobalKey());
  }

  /// Builds a slat selector autocomplete widget
  Widget _buildSlatSelector({
    required String label,
    required List<String> availableSlats,
    required TextEditingController controller,
    required void Function(String) onSelected,
  }) {
    return SizedBox(
      width: 160,
      child: Autocomplete<String>(
        displayStringForOption: (option) => option.replaceFirst('-I', '-'),
        optionsBuilder: (textEditingValue) {
          if (textEditingValue.text.isEmpty) {
            return availableSlats;
          }
          final query = textEditingValue.text.toLowerCase();
          return availableSlats.where((s) {
            final displayName = s.replaceFirst('-I', '-').toLowerCase();
            return displayName.contains(query);
          }).toList();
        },
        onSelected: (val) {
          controller.text = val.replaceFirst('-I', '-');
          onSelected(val);
        },
        fieldViewBuilder: (ctx, ctrl, focus, onSubmit) {
          return TextField(
            controller: ctrl,
            focusNode: focus,
            decoration: InputDecoration(labelText: label, isDense: true, border: const OutlineInputBorder()),
            style: const TextStyle(fontSize: 14),
            onSubmitted: (value) {
              final searchValue = value.replaceFirst('-', '-I');
              final match = availableSlats.firstWhere(
                (s) => s == searchValue || s.replaceFirst('-I', '-').toLowerCase() == value.toLowerCase(),
                orElse: () => '',
              );
              if (match.isNotEmpty) {
                ctrl.text = match.replaceFirst('-I', '-');
                controller.text = match.replaceFirst('-I', '-');
                onSelected(match);
                focus.unfocus();
              }
            },
          );
        },
      ),
    );
  }

  /// A user can drag-select handles, making it easier to make block selections.  This is fired on an initiated drag.
  void _onDragStart(DragStartDetails details) {
    final RenderBox? box = _handleDisplayAreaKey.currentContext?.findRenderObject() as RenderBox?;
    if (box == null) return;
    final localPosition = box.globalToLocal(details.globalPosition);
    setState(() {
      _isDragging = true;
      _dragStart = localPosition;
      _dragEnd = localPosition;
    });
  }

  /// A user can drag-select handles, making it easier to make block selections.  This is fired during dragging.
  void _onDragUpdate(DragUpdateDetails details) {
    if (!_isDragging) return;
    final RenderBox? box = _handleDisplayAreaKey.currentContext?.findRenderObject() as RenderBox?;
    if (box == null) return;
    final localPosition = box.globalToLocal(details.globalPosition);
    setState(() {
      _dragEnd = localPosition;
    });
  }

  /// A user can drag-select handles, making it easier to make block selections.  This is fired when a drag-selection is complete.
  void _onDragEnd(DragEndDetails details, HandleLinkManager linkManager, bool isShiftHeld) {

    if (!_isDragging || _dragStart == null || _dragEnd == null) {
      setState(() {
        _isDragging = false;
        _dragStart = null;
        _dragEnd = null;
      });
      return;
    }

    // gets the entire display area for the slat linker window
    final RenderBox? areaBox = _handleDisplayAreaKey.currentContext?.findRenderObject() as RenderBox?;

    if (areaBox == null) {
      setState(() {
        _isDragging = false;
        _dragStart = null;
        _dragEnd = null;
      });
      return;
    }

    // Calculate selection rectangle in global coordinates
    final areaOffset = areaBox.localToGlobal(Offset.zero);
    final dragStartGlobal = areaOffset + _dragStart!;
    final dragEndGlobal = areaOffset + _dragEnd!;

    final selectionRect = Rect.fromPoints(dragStartGlobal, dragEndGlobal);

    // Find all handles within the selection rectangle
    final Set<HandleKey> newlySelected = {};
    for (final entry in _handleButtonKeys.entries) {
      final key = entry.value;

      // gets the render box of an individual key button
      final RenderBox? buttonBox = key.currentContext?.findRenderObject() as RenderBox?;
      if (buttonBox == null) continue;

      // converts to global coords
      final buttonOffset = buttonBox.localToGlobal(Offset.zero);
      final buttonRect = buttonOffset & buttonBox.size;

      // checks if drag box overlaps
      if (selectionRect.overlaps(buttonRect)) {
        newlySelected.add(entry.key);
        // Also add linked handles
        for (var linkedHandle in linkManager.getLinkedHandles(entry.key)) {
          newlySelected.add(linkedHandle);
        }
      }
    }

    setState(() {
      if (isShiftHeld) {
        // Shift held: add to existing selection
        selectedHandles.addAll(newlySelected);
      } else {
        // No shift: replace selection
        selectedHandles = newlySelected;
      }
      _isDragging = false;
      _dragStart = null;
      _dragEnd = null;
    });
  }

  void _linkSelected(DesignState appState) {
    if (selectedHandles.length < 2) return;
    appState.linkHandlesAndPropagate(selectedHandles.toList());
    _clearSelection();
  }

  void _unlinkSelected(DesignState appState) {
    for (var key in selectedHandles) {
      appState.unlinkHandle(key);
    }
    _clearSelection();
  }

  void _blockSelected(DesignState appState) {
    for (var key in selectedHandles) {
      appState.toggleHandleBlockAndApply(key);
    }
    _clearSelection();
  }

  void _showSetValueDialog(BuildContext context, DesignState appState) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Set Enforced Value'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          inputFormatters: [FilteringTextInputFormatter.digitsOnly],
          decoration: const InputDecoration(labelText: 'Value (1-999)'),
          autofocus: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              int? val = int.tryParse(controller.text);
              if (val != null && val > 0) {
                for (var key in selectedHandles) {
                  appState.setHandleEnforcedValueAndApply(key, val);
                }
                _clearSelection();
              }
              Navigator.pop(ctx);
            },
            child: const Text('Set'),
          ),
        ],
      ),
    );
  }

  void _showLinkSlatsDialog(BuildContext context, DesignState appState) {
    if (selectedSlat1ID == null || selectedSlat2ID == null) return;

    final slat1 = appState.slats[selectedSlat1ID];
    final slat2 = appState.slats[selectedSlat2ID];
    if (slat1 == null || slat2 == null) return;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Link Slats by Position'),
        content: const Text('Link handles at matching positions between the two slats.\n\nWhich sides would you like to link?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              _linkSlatsByPosition(appState, slat1, slat2, linkH2: true, linkH5: false);
              Navigator.pop(ctx);
            },
            child: const Text('H2 Only'),
          ),
          TextButton(
            onPressed: () {
              _linkSlatsByPosition(appState, slat1, slat2, linkH2: false, linkH5: true);
              Navigator.pop(ctx);
            },
            child: const Text('H5 Only'),
          ),
          FilledButton(
            onPressed: () {
              _linkSlatsByPosition(appState, slat1, slat2, linkH2: true, linkH5: true);
              Navigator.pop(ctx);
            },
            child: const Text('Both'),
          ),
        ],
      ),
    );
  }

  void _linkSlatsByPosition(DesignState appState, Slat slat1, Slat slat2, {required bool linkH2, required bool linkH5}) {
    final maxPos = slat1.maxLength < slat2.maxLength ? slat1.maxLength : slat2.maxLength;

    for (int pos = 1; pos <= maxPos; pos++) {
      if (linkH5) {
        final key1 = (slat1.id, pos, 5);
        final key2 = (slat2.id, pos, 5);
        appState.linkHandlesAndPropagate([key1, key2]);
      }
      if (linkH2) {
        final key1 = (slat1.id, pos, 2);
        final key2 = (slat2.id, pos, 2);
        appState.linkHandlesAndPropagate([key1, key2]);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();

    if (!actionState.slatLinkerActive) {
      // Reset auto-populate flag when window closes so it can run again next time
      _hasAutoPopulated = false;
      return const SizedBox.shrink();
    }

    // Auto-populate from selected handles when window first opens
    _autoPopulateFromSelectedHandles(appState, actionState);

    // Refresh available slats on every build (reactive to new slats)
    final availableSlats = _getAvailableSlats(appState);

    // Clear selection if selected slats no longer exist
    if (selectedSlat1ID != null && !appState.slats.containsKey(selectedSlat1ID)) {
      selectedSlat1ID = null;
    }
    if (selectedSlat2ID != null && !appState.slats.containsKey(selectedSlat2ID)) {
      selectedSlat2ID = null;
    }

    final screenWidth = MediaQuery.of(context).size.width;
    // final windowHeight = screenHeight * 0.33; // Increased for more rows
    final width = 1100.0;

    // Dynamic height based on slat types - double-barrel needs more room (4 rows vs 2)
    final slat1 = selectedSlat1ID != null ? appState.slats[selectedSlat1ID] : null;
    final slat2 = selectedSlat2ID != null ? appState.slats[selectedSlat2ID] : null;
    final hasDoubleBarrel = (slat1 != null && _isDoubleBarrel(slat1.slatType)) || (slat2 != null && _isDoubleBarrel(slat2.slatType));
    final windowHeight = hasDoubleBarrel ? 450.0 : 400.0;

    return Positioned(
      top: 60,
      left: (screenWidth - width) / 2,
      width: width,
      child: Material(
        elevation: 8,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          height: windowHeight,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade300),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.blueGrey,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                ),
                child:

                Stack(
                  alignment: Alignment.center,
                  children: [
                    Positioned(
                      left: 0,
                      child: IconButton(
                        icon: const Icon(Icons.close, size: 24),
                        color: Colors.white,
                        onPressed: () => actionState.deactivateSlatLinker(),
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(),
                      ),
                    ),
                    Align(
                      alignment: Alignment.center,
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // Icon(Icons.mediation, color: Colors.blueAccent, size: 24),
                          const SizedBox(width: 5),
                          const Text('Slat Linker', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 22)),
                        ],
                      ),
                    ),
                  ],
                ),

              ),
              // Slat selectors and action buttons row
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                child: Row(
                  children: [
                    _buildSlatSelector(
                      label: 'Top Slat',
                      availableSlats: availableSlats,
                      controller: _slat1Controller,
                      onSelected: (val) => setState(() => selectedSlat1ID = val),
                    ),
                    const SizedBox(width: 16),
                    _buildSlatSelector(
                      label: 'Bottom Slat',
                      availableSlats: availableSlats,
                      controller: _slat2Controller,
                      onSelected: (val) => setState(() => selectedSlat2ID = val),
                    ),
                    const Spacer(),
                    // Action buttons
                    FilledButton.tonal(
                      onPressed: (selectedSlat1ID != null && selectedSlat2ID != null)
                          ? () => _showLinkSlatsDialog(context, appState)
                          : null,
                      child: const Text('Link Slats', style: TextStyle(fontSize: 14)),
                    ),
                    const SizedBox(width: 8),
                    FilledButton.tonal(
                      onPressed: selectedHandles.length >= 2 ? () => _linkSelected(appState) : null,
                      child: const Text('Link', style: TextStyle(fontSize: 14)),
                    ),
                    const SizedBox(width: 8),
                    FilledButton.tonal(
                      onPressed: selectedHandles.isNotEmpty ? () => _unlinkSelected(appState) : null,
                      child: const Text('Unlink', style: TextStyle(fontSize: 14)),
                    ),
                    const SizedBox(width: 8),
                    FilledButton.tonal(
                      onPressed: selectedHandles.isNotEmpty ? () => _showSetValueDialog(context, appState) : null,
                      child: const Text('Set Value', style: TextStyle(fontSize: 14)),
                    ),
                    const SizedBox(width: 8),
                    FilledButton.tonal(
                      onPressed: selectedHandles.isNotEmpty ? () => _blockSelected(appState) : null,
                      child: const Text('Block', style: TextStyle(fontSize: 14)),
                    ),
                    const SizedBox(width: 8),
                    TextButton(
                      onPressed: selectedHandles.isNotEmpty ? _clearSelection : null,
                      child: const Text('Clear', style: TextStyle(fontSize: 14)),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              // Slat visualizations - each takes equal vertical space
              Expanded(
                child: GestureDetector(
                  onPanStart: _onDragStart,
                  onPanUpdate: _onDragUpdate,
                  onPanEnd: (details) {
                    final isShiftHeld = HardwareKeyboard.instance.isShiftPressed;
                    _onDragEnd(details, appState.assemblyLinkManager, isShiftHeld);
                  },
                  behavior: HitTestBehavior.translucent,
                  child: Stack(
                    key: _handleDisplayAreaKey,
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            // Top slat area - always takes half the space
                            Expanded(
                              flex: 1,
                              child: selectedSlat1ID != null && appState.slats.containsKey(selectedSlat1ID)
                                  ? Center(
                                      child: _SlatHandleDisplay(
                                        slat: appState.slats[selectedSlat1ID]!,
                                        slatColor: appState.layerMap[appState.slats[selectedSlat1ID]!.layer]?['color'] ?? Colors.grey,
                                        linkManager: appState.assemblyLinkManager,
                                        selectedHandles: selectedHandles,
                                        onHandleTap: _toggleHandleSelection,
                                        label: selectedSlat1ID!,
                                        onSelectAllH5: () => _toggleAllHandles(selectedSlat1ID!, 5, appState),
                                        onSelectAllH2: () => _toggleAllHandles(selectedSlat1ID!, 2, appState),
                                        getHandleKey: _getOrCreateHandleKey,
                                      ),
                                    )
                                  : const Center(
                                      child: Text('Select a top slat', style: TextStyle(color: Colors.grey, fontSize: 15)),
                                    ),
                            ),
                            const Divider(height: 1),
                            // Bottom slat area - always takes half the space
                            Expanded(
                              flex: 1,
                              child: selectedSlat2ID != null && appState.slats.containsKey(selectedSlat2ID)
                                  ? Center(
                                      child: _SlatHandleDisplay(
                                        slat: appState.slats[selectedSlat2ID]!,
                                        slatColor: appState.layerMap[appState.slats[selectedSlat2ID]!.layer]?['color'] ?? Colors.grey,
                                        linkManager: appState.assemblyLinkManager,
                                        selectedHandles: selectedHandles,
                                        onHandleTap: _toggleHandleSelection,
                                        label: selectedSlat2ID!,
                                        onSelectAllH5: () => _toggleAllHandles(selectedSlat2ID!, 5, appState),
                                        onSelectAllH2: () => _toggleAllHandles(selectedSlat2ID!, 2, appState),
                                        getHandleKey: _getOrCreateHandleKey,
                                      ),
                                    )
                                  : const Center(
                                      child: Text('Select a bottom slat', style: TextStyle(color: Colors.grey, fontSize: 15)),
                                    ),
                            ),
                          ],
                        ),
                      ),
                      // Drag selection rectangle overlay
                      if (_isDragging && _dragStart != null && _dragEnd != null)
                        Positioned.fill(
                          child: IgnorePointer(
                            child: CustomPaint(
                              painter: _DragSelectionPainter(
                                start: _dragStart!,
                                end: _dragEnd!,
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Determines if a slat type is double-barrel
bool _isDoubleBarrel(String slatType) {
  return slatType.startsWith('DB-');
}


/// Determines kink direction: true = left (L), false = right (R)
bool _isLeftKink(String slatType) {
  return slatType.contains('-L');
}

class _SlatHandleDisplay extends StatelessWidget {
  final Slat slat;
  final Color slatColor;
  final HandleLinkManager linkManager;
  final Set<HandleKey> selectedHandles;
  final void Function(HandleKey, HandleLinkManager) onHandleTap;
  final String label;
  final VoidCallback? onSelectAllH5;
  final VoidCallback? onSelectAllH2;
  final GlobalKey Function(HandleKey)? getHandleKey;

  const _SlatHandleDisplay({
    required this.slat,
    required this.slatColor,
    required this.linkManager,
    required this.selectedHandles,
    required this.onHandleTap,
    required this.label,
    this.onSelectAllH5,
    this.onSelectAllH2,
    this.getHandleKey,
  });

  @override
  Widget build(BuildContext context) {
    final isDB = _isDoubleBarrel(slat.slatType);
    final halfLength = slat.maxLength ~/ 2; // 16 for standard 32-position slats

    // Calculate the offset for side panel to align with handle center (skip H5 label height)
    const double labelOffset = 16.0; // H5 label (12px font ~14px height) + 2px spacing

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Left side: color box and slat ID - offset to align with handles (not labels)
        Padding(
          padding: const EdgeInsets.only(top: labelOffset),
          child: SizedBox(
            width: 80,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Container(
                  width: 30,
                  height: 30,
                  decoration: BoxDecoration(
                    color: slatColor,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: Colors.black26),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  label.replaceFirst('-I', '-'),
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  slat.slatType,
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                ),
              ],
            ),
          ),
        ),
        // Handle grid
        Expanded(
          child: isDB ? _buildDoubleBarrelLayout(halfLength) : _buildTubeLayout(),
        ),
      ],
    );
  }

  /// Build layout for tube slats: 2 rows (H5 and H2) of 32 positions each
  Widget _buildTubeLayout() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // H5 row label
        _buildSideLabel('H5', onSelectAllH5),
        const SizedBox(height: 2),
        // H5 handles - single row of all positions
        _buildHandleRow(5, 1, slat.maxLength),
        const SizedBox(height: 8),
        // H2 row label
        _buildSideLabel('H2', onSelectAllH2),
        const SizedBox(height: 2),
        // H2 handles - single row of all positions
        _buildHandleRow(2, 1, slat.maxLength),
      ],
    );
  }

  /// Build layout for double-barrel slats: 4 rows (2 for H5, 2 for H2)
  /// DB-L: top row is 1-16, bottom row is 32-17 (reversed, wraps on right)
  /// DB-R: bottom row is 1-16, top row is 32-17 (reversed, wraps on right)
  Widget _buildDoubleBarrelLayout(int halfLength) {
    final isLeft = _isLeftKink(slat.slatType);

    // Calculate offset for kinked types (in handle button widths)
    double kinkOffset = 0;

    if(slat.slatType == 'DB-L-60'){
      kinkOffset = 1;
    } else if(slat.slatType == 'DB-R-60'){
      kinkOffset = 1;
    } else if(slat.slatType == 'DB-L-120'){
      kinkOffset = -1;
    } else if(slat.slatType == 'DB-R-120'){
      kinkOffset = -1;
    }

    // Build the two barrel rows for each side
    // First barrel: positions 1-16 (normal order)
    // Second barrel: positions 32-17 (reversed to wrap around on right)
    Widget buildBarrelPair(int side) {
      final firstBarrel = _buildHandleRow(side, 1, halfLength, offset: kinkOffset);
      final secondBarrel = _buildHandleRow(side, halfLength + 1, slat.maxLength, reversed: true);

      if (isLeft) {
        // DB-L: first barrel on top, second barrel (reversed) on bottom
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            firstBarrel,
            const SizedBox(height: 2),
            secondBarrel,
          ],
        );
      } else {
        // DB-R: second barrel (reversed) on top, first barrel on bottom
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            secondBarrel,
            const SizedBox(height: 2),
            firstBarrel,
          ],
        );
      }
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // H5 label
        _buildSideLabel('H5', onSelectAllH5),
        const SizedBox(height: 2),
        buildBarrelPair(5),
        const SizedBox(height: 8),
        // H2 label
        _buildSideLabel('H2', onSelectAllH2),
        const SizedBox(height: 2),
        buildBarrelPair(2),
      ],
    );
  }

  Widget _buildSideLabel(String text, VoidCallback? onTap) {
    if (onTap != null) {
      return OutlinedButton(
        onPressed: onTap,
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
          minimumSize: Size.zero,
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          side: BorderSide(color: Colors.grey.shade400),
          foregroundColor: Colors.grey.shade700,
          textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        ),
        child: Text(text),
      );
    }
    return Text(
      text,
      style: TextStyle(fontSize: 12, color: Colors.grey.shade600, fontWeight: FontWeight.w500),
    );
  }

  /// Build a row of handle buttons with dividers every 4 positions
  Widget _buildHandleRow(int side, int startPos, int endPos, {double offset = 0, bool reversed = false}) {
    final widgets = <Widget>[];
    final positions = reversed
        ? List.generate(endPos - startPos + 1, (i) => endPos - i)
        : List.generate(endPos - startPos + 1, (i) => startPos + i);

    for (int i = 0; i < positions.length; i++) {
      final pos = positions[i];
      final handleKey = (slat.id, pos, side);
      final handleData = side == 5 ? slat.h5Handles[pos] : slat.h2Handles[pos];
      widgets.add(_HandleButton(
        key: getHandleKey?.call(handleKey),
        handleKey: handleKey,
        handleData: handleData,
        linkManager: linkManager,
        isSelected: selectedHandles.contains(handleKey),
        onTap: () => onHandleTap(handleKey, linkManager),
      ));

      // Add vertical divider after every 4th button (not position), but not at the end
      if ((i + 1) % 4 == 0 && i < positions.length - 1) {
        widgets.add(Container(
          width: 2,
          height: 22,
          margin: const EdgeInsets.symmetric(horizontal: 2),
          color: Colors.grey.shade400,
        ));
      }
    }

    // Position labels for left and right
    final leftPos = positions.first;
    final rightPos = positions.last;
    final labelStyle = TextStyle(fontSize: 11, color: Colors.grey.shade600, fontWeight: FontWeight.w500);

    Widget row = Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Left position label
        SizedBox(
          width: 24,
          child: Text('$leftPos', style: labelStyle, textAlign: TextAlign.right),
        ),
        const SizedBox(width: 4),
        // Handle buttons
        ...widgets,
        const SizedBox(width: 4),
        // Right position label
        SizedBox(
          width: 24,
          child: Text('$rightPos', style: labelStyle, textAlign: TextAlign.left),
        ),
      ],
    );

    // Apply offset for kinked slats
    if (offset != 0) {
      row = Transform.translate(
        offset: Offset(offset * 26, 0), // 26 = button width (24) + spacing (2)
        child: row,
      );
    }

    return row;
  }
}

class _HandleButton extends StatelessWidget {
  final HandleKey handleKey;
  final Map<String, dynamic>? handleData;
  final HandleLinkManager linkManager;
  final bool isSelected;
  final VoidCallback onTap;

  const _HandleButton({
    super.key,
    required this.handleKey,
    required this.handleData,
    required this.linkManager,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isBlocked = linkManager.handleBlocks.contains(handleKey);
    final group = linkManager.getGroup(handleKey);
    final enforcedValue = linkManager.getEnforceValue(handleKey);

    // Determine colors and content
    Color bgColor = Colors.grey.shade200;
    String? displayText;
    Color textColor = Colors.black87;

    if (handleData != null) {
      String category = handleData!['category']?.toString().toUpperCase() ?? '';
      if (category.contains('CARGO')) {
        bgColor = Colors.orange.shade200;
        displayText = 'C';
      } else if (category.contains('SEED')) {
        bgColor = Colors.blue.shade200;
        displayText = 'S';
      } else if (category.contains('ASSEMBLY')) {
        bgColor = Colors.green.shade200;
        displayText = handleData!['value']?.toString();
      }
    }

    if (isBlocked) {
      bgColor = Colors.red.shade100;
      displayText = 'X';
      textColor = Colors.red.shade700;
    }

    // Build the button content
    Widget content = Text(
      displayText ?? '',
      style: TextStyle(fontSize: 10, color: textColor, fontWeight: FontWeight.w600),
      textAlign: TextAlign.center,
    );

    return Padding(
      padding: const EdgeInsets.all(1),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: 24,
          height: 22,
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(3),
            border: Border.all(
              color: isSelected ? Colors.blue : Colors.grey.shade400,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Stack(
            children: [
              // Main content
              Center(child: content),
              // Link indicator (group badge) - top right
              if (group != null && !isBlocked)
                Positioned(
                  top: 1,
                  right: 1,
                  child: Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      color: Colors.purple.shade400,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              // Enforced value indicator - left edge
              if (enforcedValue != null && enforcedValue > 0 && !isBlocked)
                Positioned(
                  left: 0,
                  top: 0,
                  bottom: 0,
                  child: Container(
                    width: 3,
                    decoration: BoxDecoration(
                      color: Colors.amber.shade700,
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(2),
                        bottomLeft: Radius.circular(2),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Painter for the drag selection rectangle
class _DragSelectionPainter extends CustomPainter {
  final Offset start;
  final Offset end;

  _DragSelectionPainter({required this.start, required this.end});

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Rect.fromPoints(start, end);

    // Fill
    final fillPaint = Paint()
      ..color = Colors.blue.withValues(alpha: 0.1)
      ..style = PaintingStyle.fill;
    canvas.drawRect(rect, fillPaint);

    // Border
    final borderPaint = Paint()
      ..color = Colors.blue.withValues(alpha: 0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawRect(rect, borderPaint);
  }

  @override
  bool shouldRepaint(_DragSelectionPainter oldDelegate) {
    return start != oldDelegate.start || end != oldDelegate.end;
  }
}
