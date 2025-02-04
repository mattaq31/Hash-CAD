import 'package:flutter/material.dart';

class MyAppState extends ChangeNotifier {
  Color slatColor = Colors.blue;

  List<Map<String, dynamic>> layerList = [
    {"label": "Layer 1", "value": "opt1", "color": Colors.blue},
    {"label": "Layer 2", "value": "opt2", "color": Colors.green},
  ];

  void updateColor(int index, Color color) {
    slatColor = color;
    layerList[index] = {
      ...layerList[index],
      "color": color,
    };
    notifyListeners();
  }

}