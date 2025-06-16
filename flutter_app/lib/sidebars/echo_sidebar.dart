import 'dart:math';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../app_management/shared_app_state.dart';
import '../crisscross_core/handle_plates.dart';
import '../main_windows/alert_window.dart';

class EchoTools extends StatefulWidget {
  const EchoTools({super.key});

  @override
  State<EchoTools> createState() => _EchoTools();
}

Widget buildCategoryIcon({
  required IconData icon,
  required String label,
  required int count,
  Color? color,
}) {
  return Tooltip(
    message: label,
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: color ?? Colors.grey[700]),
        SizedBox(width: 4),
        Text(
          '$count',
          style: TextStyle(fontSize: 14),
        ),
      ],
    ),
  );
}

class _EchoTools extends State<EchoTools> with WidgetsBindingObserver {
  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    return Column(children: [
      Text("Echo Export Tools",
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 15),
      FilledButton.icon(
        onPressed: () {
          appState.importPlates();
        },
        icon: Icon(Icons.delete_sweep, size: 18),
        label: Text("Import Handle Plates"),
        style: ElevatedButton.styleFrom(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: TextStyle(fontSize: 16),
        ),
      ),
      Divider(thickness: 2, color: Colors.grey.shade300),
      Text("Plate Stack",
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 5),
      Container(
          constraints: BoxConstraints(
            maxHeight: appState.plateStack.plates.isEmpty
                ? 20
                : min(
                    // Height for 5 items, approximating a row having a height of 134
                    6 * 134.0,
                    // If fewer than 5 items, shrink to fit content
                    appState.plateStack.plates.length * 134.0),
          ),
          child: appState.plateStack.plates.isEmpty
              ? Center(
                  child: Text(
                    'Import plates to see them here!',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[600],
                    ),
                  ),
                )
              : ListView(
                  shrinkWrap: true,
                  children: appState.plateStack.plates.entries.map((entry) {
                    String plateName = entry.key;
                    HashCadPlate plate = entry.value;

                    return ExpansionTile(
                      shape: RoundedRectangleBorder( // Shape when expanded
                        side: BorderSide(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      collapsedShape: RoundedRectangleBorder( // Shape when collapsed
                        side: BorderSide(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      key: Key(plateName),
                      title: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(sanitizePlateMap(plateName),
                                    style:
                                        TextStyle(fontWeight: FontWeight.w500)),
                                SizedBox(height: 4),
                                Text('Total staples: ${plate.wells.length}',
                                    style: TextStyle(
                                        fontSize: 12, color: Colors.grey[700])),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: Icon(Icons.info,
                                size: 20, color: Colors.blueAccent),
                            tooltip: 'Further Info',
                            onPressed: () {
                              displayPlateInfo(context, plateName, plate);
                            },
                          ),
                          IconButton(
                            icon: Icon(Icons.close,
                                size: 20, color: Colors.redAccent),
                            tooltip: 'Delete Plate',
                            onPressed: () {
                              appState.removePlate(plateName);
                            },
                          ),
                        ],
                      ),
                      children: [
                        Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16.0, vertical: 4.0),
                          child: Wrap(
                            spacing: 12,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              buildCategoryIcon(
                                icon: Icons.power_input,
                                label: 'Flat Staples',
                                count: plate.countCategory("FLAT"),
                                color: Colors.green,
                              ),
                              buildCategoryIcon(
                                icon: Icons.join_left,
                                label: 'Assembly Handles',
                                count: plate.countCategory("ASSEMBLY_HANDLE"),
                                color: Colors.blue,
                              ),
                              buildCategoryIcon(
                                icon: Icons.join_right,
                                label: 'Assembly AntiHandles',
                                count:
                                    plate.countCategory("ASSEMBLY_ANTIHANDLE"),
                                color: Colors.red,
                              ),
                              buildCategoryIcon(
                                icon: Icons.nature,
                                label: 'Seed Handles',
                                count: plate.countCategory("SEED"),
                                color: Colors.brown,
                              ),
                              buildCategoryIcon(
                                icon: Icons.precision_manufacturing,
                                label: 'Cargo Handles',
                                count: plate.countCategory("CARGO"),
                                color: Colors.orange,
                              ),
                            ],
                          ),
                        ),
                      ],
                    );
                  }).toList(),
                )),
      SizedBox(height: 10),
      FilledButton.icon(
        onPressed: () {
          appState.removeAllPlates();
        },
        label: Text("Clear All"),
        icon: Icon(Icons.delete),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.red, // Red background
          foregroundColor: Colors.white, // White text
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: TextStyle(fontSize: 16),
        ),
      ),
    ]);
  }
}
