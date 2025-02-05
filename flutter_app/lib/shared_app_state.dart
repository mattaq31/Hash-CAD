import 'package:flutter/material.dart';

class MyAppState extends ChangeNotifier {

  List<Map<String, dynamic>> layerList = [
    {"label": "Layer 1", "value": "L1", "direction": 'horizontal', "color": Colors.blue},
    {"label": "Layer 2", "value": "L2", "direction": 'vertical', "color": Colors.green},
  ];

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

}