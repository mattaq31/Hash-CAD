import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';

import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';


class SlatEditPanel extends StatefulWidget {
  const SlatEditPanel({super.key});

  @override
  State<SlatEditPanel> createState() => _SlatEditPanel();
}


class _SlatEditPanel extends State<SlatEditPanel> {

  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    final colorScheme = Theme.of(context).colorScheme;
    return Column(
      children: [
        Divider(thickness: 1, color: Colors.grey.shade200),
        Text("Selected Slat Actions",style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
        SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FilledButton.icon(
              onPressed: appState.selectedSlats.isEmpty ? null: () {
                appState.flipSlats(appState.selectedSlats);
              },
              label: Text("Flip"),
              icon: Icon(Icons.flip),
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                textStyle: TextStyle(fontSize: 14),
              ),
            ),
            SizedBox(width: 10),
            FilledButton.icon(
              onPressed: appState.selectedSlats.isEmpty ? null: () {
                appState.removeSlats(appState.selectedSlats);
              },
              label: Text("Delete"),
              icon: Icon(Icons.delete),
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                textStyle: TextStyle(fontSize: 14),
                backgroundColor: Colors.red,
              ),
            ),
          ],
        ),
        SizedBox(height: 10),
        Divider(thickness: 1, color: Colors.grey.shade200),
        Text("Adjust Slat Colors",
            style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
        SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 110, // Fixed width to align colons
              child: Text("Set Colour:",
                  textAlign: TextAlign.right,
                  style: TextStyle(fontSize: 14, color: Colors.black87)),
            ),
            SizedBox(width: 5),
            IconButton(
              tooltip: 'Assign colour to selected slats',
              onPressed: () {
                appState.assignColorToSelectedSlats(appState.uniqueSlatColor);
              },
              icon: const Icon(Icons.format_paint, size: 20, color: Colors.white),
              style: IconButton.styleFrom(
                backgroundColor: colorScheme.primary,
                shape: RoundedRectangleBorder(
                  borderRadius:
                  BorderRadius.circular(8), // Adjust radius as needed
                ),
                padding: const EdgeInsets.all(8),
                minimumSize: const Size(36, 36),
                // Ensures square shape
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            ),
            SizedBox(width: 5),
            PopupMenuButton(
              constraints: BoxConstraints(
                minWidth: 200,
                // Set min width to prevent overflow
                maxWidth: 780, // Adjust as needed
              ),
              offset: Offset(0, 40),
              // Position below the button
              itemBuilder: (context) {
                return [
                  PopupMenuItem(
                    child: ColorPicker(
                      hexInputBar: true,
                      pickerColor: appState.uniqueSlatColor,
                      onColorChanged: (color) {
                        appState.setUniqueSlatColor(color);
                      },
                      pickerAreaHeightPercent: 0.5,
                    ),
                  ),
                ];
              },
              child: Container(
                width: 35, // Width of the rectangle
                height: 20, // Height of the rectangle
                decoration: BoxDecoration(
                  color: appState.uniqueSlatColor,
                  // Use the color from the list
                  border: Border.all(color: Colors.black, width: 1),
                  borderRadius:
                  BorderRadius.circular(4), // Optional rounded corners
                ),
              ),
            ),
          ],
        ),
        SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 110, // Fixed width to align colons
              child: Text("Reset Colours:",
                  textAlign: TextAlign.right,
                  style: TextStyle(fontSize: 14, color: Colors.black87)),
            ),
            SizedBox(width: 5),
            IconButton(
              tooltip: 'Reset current layer',
              onPressed: () {
                appState.clearSlatColorsFromLayer(appState.selectedLayerKey);
              },
              icon: const Icon(Icons.format_color_reset_outlined,
                  size: 20, color: Colors.black87),
              style: IconButton.styleFrom(
                backgroundColor: Colors.grey[300],
                shape: RoundedRectangleBorder(
                  borderRadius:
                  BorderRadius.circular(8), // Adjust radius as needed
                ),
                padding: const EdgeInsets.all(8),
                minimumSize: const Size(36, 36),
                // Ensures square shape
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            ),
            SizedBox(width: 5),
            IconButton(
              tooltip: 'Reset all layers',
              onPressed: () {
                appState.clearAllSlatColors();
              },
              icon: const Icon(Icons.format_color_reset,
                  size: 20, color: Colors.black87),
              style: IconButton.styleFrom(
                backgroundColor: Colors.grey[300],
                shape: RoundedRectangleBorder(
                  borderRadius:
                  BorderRadius.circular(8), // Adjust radius as needed
                ),
                padding: const EdgeInsets.all(8),
                minimumSize: const Size(36, 36),
                // Ensures square shape
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            )
          ],
        ),
        SizedBox(height: 10),
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            SizedBox(
              width: 110,
              child: Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: Text(
                  "Layer Colours:",
                  textAlign: TextAlign.right,
                  style: TextStyle(fontSize: 14, color: Colors.black87),
                ),
              ),
            ),
            SizedBox(width: 5),
            Expanded(
              child: Builder(
                builder: (context) {
                  final colorSet = appState.uniqueSlatColorsByLayer[appState.selectedLayerKey] ?? [];

                  if (colorSet.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: EdgeInsets.only(bottom: 15),
                        child: Text(
                          'No colors assigned yet',
                          style: TextStyle(fontSize: 14, color: Colors.black54),
                        ),
                      ),
                    );
                  }

                  return Scrollbar(
                    controller: _scrollController,
                    thumbVisibility: true,
                    trackVisibility: true,
                    thickness: 8,
                    radius: Radius.circular(4),
                    scrollbarOrientation: ScrollbarOrientation.bottom,
                    child: SingleChildScrollView(
                      controller: _scrollController,
                      scrollDirection: Axis.horizontal,
                      padding: EdgeInsets.only(bottom: 16),
                      child: Row(
                        children: colorSet.asMap().entries.map((entry) {
                          int index = entry.key;
                          Color oldColor = entry.value;
                          return Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4.0),
                            child: Tooltip(
                              message: 'Click to edit slats in this layer with this color',
                              child: Stack(
                                clipBehavior: Clip.none,
                                children: [
                                  PopupMenuButton(
                                    tooltip: '',
                                    constraints: const BoxConstraints(minWidth: 300, maxWidth: 780),
                                    offset: const Offset(0, 40),
                                    itemBuilder: (_) => [
                                      PopupMenuItem(
                                        enabled: false,
                                        padding: EdgeInsets.zero,
                                        child: SingleChildScrollView(
                                          child: ColorPicker(
                                            hexInputBar: true,
                                            pickerColor: oldColor,
                                            onColorChanged: (newColor) {
                                              appState.editSlatColorSearch(appState.selectedLayerKey, index, newColor);
                                            },
                                            pickerAreaHeightPercent: 0.5,
                                          ),
                                        ),
                                      ),
                                    ],
                                    child: Container(
                                      width: 35,
                                      height: 20,
                                      decoration: BoxDecoration(
                                        color: oldColor,
                                        border: Border.all(color: Colors.black, width: 1),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                    ),
                                  ),
                                  Positioned(
                                    top: -4,
                                    right: -6,
                                    child: SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: Material(
                                        color: Colors.white,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: IconButton(
                                          padding: EdgeInsets.zero,
                                          iconSize: 14,
                                          icon: Icon(Icons.close, color: Colors.black54),
                                          onPressed: () {
                                            appState.removeSlatColorFromLayer(appState.selectedLayerKey, index);
                                          },
                                          tooltip: 'Reset color to layer color',
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
        Divider(thickness: 1, color: Colors.grey.shade200),
        SizedBox(height: 5),
        Text("Phantom Slats",style: TextStyle(fontSize: 16, color: Colors.grey.shade600)),
        SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 110, // Fixed width to align colons
              child: Text("Create & link:",
                  textAlign: TextAlign.right,
                  style: TextStyle(fontSize: 14, color: Colors.black87)),
            ),
            SizedBox(width: 5),
            IconButton(
              tooltip: 'Spawn phantoms from the selected slats',
              onPressed: appState.selectedSlats.isEmpty ? null: () {
                appState.spawnAndPlacePhantomSlats();
              },
              icon: const Icon(Icons.link, size: 20),
              style: IconButton.styleFrom(
                backgroundColor: colorScheme.primaryContainer,
                shape: RoundedRectangleBorder(
                  borderRadius:
                  BorderRadius.circular(8), // Adjust radius as needed
                ),
                padding: const EdgeInsets.all(8),
                minimumSize: const Size(36, 36),
                // Ensures square shape
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            ),
            SizedBox(width: 5),
            IconButton(
              tooltip: 'Convert selected phantoms to normal slats with linked assembly handles',
              onPressed: !appState.selectionInvolvesPhantoms() ? null:  () {
                appState.unLinkSelectedPhantoms();
              },
              icon: const Icon(Icons.link_off,
                  size: 20, color: Colors.black87),
              style: IconButton.styleFrom(
                backgroundColor: colorScheme.primaryContainer,
                shape: RoundedRectangleBorder(
                  borderRadius:
                  BorderRadius.circular(8), // Adjust radius as needed
                ),
                padding: const EdgeInsets.all(8),
                minimumSize: const Size(36, 36),
                // Ensures square shape
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            )
          ],
        ),
        SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 110, // Fixed width to align colons
              child: Text("Delete:",
                  textAlign: TextAlign.right,
                  style: TextStyle(fontSize: 14, color: Colors.black87)),
            ),
            SizedBox(width: 5),
            IconButton(
              tooltip: 'Delete phantoms linked to selected slat(s)',
              onPressed: !appState.selectionHasPhantoms() ? null:  () {
                appState.clearPhantomSlatSelection();
              },
              icon: const Icon(Icons.layers_clear,
                  size: 20),
              style: IconButton.styleFrom(
                backgroundColor: colorScheme.primaryContainer,
                shape: RoundedRectangleBorder(
                  borderRadius:
                  BorderRadius.circular(8), // Adjust radius as needed
                ),
                padding: const EdgeInsets.all(8),
                minimumSize: const Size(36, 36),
                // Ensures square shape
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            ),
            SizedBox(width: 5),
            IconButton(
              tooltip: 'Delete all phantoms',
              onPressed: appState.phantomMap.isEmpty ? null : () {
                appState.removeAllPhantomSlats();
              },
              icon: const Icon(Icons.blur_off,
                  size: 20),
              style: IconButton.styleFrom(
                backgroundColor: Colors.red.shade400,
                shape: RoundedRectangleBorder(
                  borderRadius:
                  BorderRadius.circular(8), // Adjust radius as needed
                ),
                padding: const EdgeInsets.all(8),
                minimumSize: const Size(36, 36),
                // Ensures square shape
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            )
          ],
        ),
      ]
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }
}