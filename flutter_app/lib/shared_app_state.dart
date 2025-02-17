import 'package:flutter/material.dart';
import 'crisscross_core/slats.dart';

class DesignState extends ChangeNotifier {
  List<Map<String, dynamic>> layerList = [
    {
      "label": "Layer 1",
      "value": "L1",
      "direction": 'horizontal',
      'order': 1,
      'slat_count': 0,
      "color": Colors.blue
    },
    {
      "label": "Layer 2",
      "value": "L2",
      "direction": 'vertical',
      'slat_count': 0,
      'order': 2,
      "color": Colors.red
    },
  ];

  Map<String, Slat> slats = {};
  List<String> selectedSlats = [];

  int selectedLayerIndex = 0; // Default selection
  int slatAddCount = 1;

  Map<int, Map<Offset, String>> occupiedGridPoints = {};

  void updateSelectedLayer(int value) {
    selectedLayerIndex = value;
    notifyListeners();
  }

  void updateSlatAddCount(int value) {
    slatAddCount = value;
    notifyListeners();
  }

  void updateColor(int index, Color color) {
    layerList[index] = {
      ...layerList[index],
      "color": color,
    };
    notifyListeners();
  }

  void addSlats(Offset position, int layer, Map<int, Map<int, Offset>> slatCoordinates) {

    for (var slat in slatCoordinates.entries){
      slats['L$layer-I${layerList[layer]["slat_count"]}'] = Slat('L$layer-I${layerList[layer]["slat_count"]}', layer, slat.value);
      // add the slat to the list by adding a map of all coordinate offsets to the slat ID
      occupiedGridPoints.putIfAbsent(layer, () => {});
      occupiedGridPoints[layer]?.addAll({for (var offset in slat.value.values) offset : 'L$layer-I${layerList[layer]["slat_count"]}'});
      layerList[layer]["slat_count"] += 1;
    }
    notifyListeners();
  }

  void updateSlatPosition(String slatID, Map<int, Offset> slatCoordinates) {

    // also need to remove old positions from occupiedGridPoints and add new ones
    int layer = int.parse(slatID.substring(1, 2));
    occupiedGridPoints[layer]?.removeWhere((key, value) => value == slatID);
    slats[slatID]?.updateCoordinates(slatCoordinates);
    occupiedGridPoints[layer]?.addAll({for (var offset in slatCoordinates.values) offset : slatID});
    notifyListeners();
  }

  void removeSlat(String ID){
    int layer = int.parse(ID.substring(1, 2));
    slats.remove(ID);
    occupiedGridPoints[layer]?.removeWhere((key, value) => value == ID);
    layerList[layer]["slat_count"] -= 1;
    notifyListeners();
  }

  void selectSlat(String ID){
    if (selectedSlats.contains(ID)){
      selectedSlats.remove(ID);
    } else {
      selectedSlats.add(ID);
    }
    notifyListeners();
  }
  void clearSelection(){
    selectedSlats = [];
    notifyListeners();
  }
}

class ActionState extends ChangeNotifier {
String slatMode = 'Add';
void updateSlatMode(String value) {
  slatMode = value;
  notifyListeners();
}
}