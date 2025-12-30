import 'package:flutter/material.dart';

import '../../crisscross_core/cargo.dart';
import '../../crisscross_core/seed.dart';
import '../../2d_painters/helper_functions.dart' as utils;
import '../shared_app_state.dart';

/// Mixin containing core utility operations for DesignState
mixin DesignStateCoreMixin on ChangeNotifier {
  // Required state - to be provided by DesignState
  double get gridSize;
  double get x60Jump;
  double get y60Jump;
  String get gridMode;
  set gridMode(String value);
  HoverPreview? get hoverPreview;
  set hoverPreview(HoverPreview? value);
  Map<String, Map<String, dynamic>> get layerMap;
  String get designName;
  set designName(String value);
  Color get uniqueSlatColor;
  set uniqueSlatColor(Color value);

  // State that needs setters for resetDefaults
  String get selectedLayerKey;
  set selectedLayerKey(String value);
  List<String> get selectedSlats;
  set selectedSlats(List<String> value);
  String get nextLayerKey;
  set nextLayerKey(String value);
  String get nextSeedID;
  set nextSeedID(String value);
  int get nextColorIndex;
  set nextColorIndex(int value);
  int get slatAddCount;
  set slatAddCount(int value);
  int get currentMaxValency;
  set currentMaxValency(int value);
  double get currentEffValency;
  set currentEffValency(double value);
  bool get hammingValueValid;
  set hammingValueValid(bool value);
  int get cargoAddCount;
  set cargoAddCount(int value);
  String? get cargoAdditionType;
  set cargoAdditionType(String? value);
  Map<String, Map<Offset, String>> get occupiedGridPoints;
  set occupiedGridPoints(Map<String, Map<Offset, String>> value);
  Map<String, Map<int, String>> get phantomMap;
  set phantomMap(Map<String, Map<int, String>> value);
  Map<(String, String, Offset), Seed> get seedRoster;
  set seedRoster(Map<(String, String, Offset), Seed> value);
  String get slatAddDirection;
  set slatAddDirection(String value);
  Map<String, List<Color>> get uniqueSlatColorsByLayer;
  set uniqueSlatColorsByLayer(Map<String, List<Color>> value);
  String get slatAdditionType;
  set slatAdditionType(String value);
  Map<String, Cargo> get cargoPalette;
  set cargoPalette(Map<String, Cargo> value);
  Map<String, Map<Offset, String>> get occupiedCargoPoints;
  set occupiedCargoPoints(Map<String, Map<Offset, String>> value);
  List<Offset> get selectedHandlePositions;
  set selectedHandlePositions(List<Offset> value);

  // Methods from other mixins that this mixin calls
  void clearAll();
  void saveUndoState();

  void setHoverPreview(HoverPreview? preview) {
    hoverPreview = preview;
    notifyListeners();
  }

  void initializeUndoStack() {
    saveUndoState();
  }

  Offset convertRealSpacetoCoordinateSpace(Offset inputPosition) {
    return utils.convertRealSpacetoCoordinateSpace(inputPosition, gridMode, gridSize, x60Jump, y60Jump);
  }

  Offset convertCoordinateSpacetoRealSpace(Offset inputPosition) {
    return utils.convertCoordinateSpacetoRealSpace(inputPosition, gridMode, gridSize, x60Jump, y60Jump);
  }

  String? getLayerByOrder(int order) {
    for (final entry in layerMap.entries) {
      if (entry.value['order'] == order) {
        return entry.key;
      }
    }
    return null;
  }

  String flipSlatSide(String side) => side == 'top' ? 'bottom' : 'top';

  bool layerNumberValid(int layerOrder) {
    return layerOrder != -1 && layerOrder < layerMap.length ? true : false;
  }

  void resetDefaults() {
    selectedLayerKey = 'A';
    selectedSlats = [];
    nextLayerKey = 'C';
    nextSeedID = 'A';
    nextColorIndex = 2;
    slatAddCount = 1;
    currentMaxValency = 0;
    currentEffValency = 0.0;
    hammingValueValid = true;
    cargoAddCount = 1;
    cargoAdditionType = null;
    occupiedGridPoints = {};
    phantomMap = {};
    seedRoster = {};
    slatAddDirection = 'down';
    uniqueSlatColor = Colors.blue;
    uniqueSlatColorsByLayer = {};
    slatAdditionType = 'tube';
    cargoPalette = {
        'SEED': Cargo(name: 'SEED', shortName: 'S1', color: Color.fromARGB(255, 255, 0, 0)),
      };
    occupiedCargoPoints = {};
    selectedHandlePositions = [];
  }

  void setGridMode(String value);

  void setDesignName(String newName) {
    if (newName == '') {
      designName = 'New Megastructure';
    } else {
      designName = newName;
    }
    if (designName.contains(',')) {
      designName = designName.replaceAll(',', '_');
    }
    notifyListeners();
  }

  void setUniqueSlatColor(Color color) {
    uniqueSlatColor = color;
    notifyListeners();
  }
}
