import 'package:flutter/material.dart';
import 'crisscross_core/slats.dart';

class MyAppState extends ChangeNotifier {

  List<Map<String, dynamic>> layerList = [
    {"label": "Layer 1",
      "value": "L1",
      "direction": 'horizontal',
      'order': 1,
      'slat_count': 0,
      "color": Colors.blue},
    {"label": "Layer 2",
      "value": "L2",
      "direction": 'vertical',
      'slat_count': 0,
      'order': 2,
      "color": Colors.green},
  ];

  List<Slat> slats = [];

  int selectedLayerIndex = 0; // Default selection

  void updateSelectedLayer(int value) {
    selectedLayerIndex = value;
    notifyListeners();
  }

  void updateColor(int index, Color color) {

    layerList[index] = {
      ...layerList[index],
      "color": color,
    };
    notifyListeners();
  }

  void addSlat(Offset position, int layer, Map<int, Offset> slatCoordinates) {

    slats.add(
      Slat('L$layer-I${layerList[layer]["slat_count"]}', layer, slatCoordinates)
    );

    layerList[layer]["slat_count"] += 1;
    notifyListeners();
  }

}