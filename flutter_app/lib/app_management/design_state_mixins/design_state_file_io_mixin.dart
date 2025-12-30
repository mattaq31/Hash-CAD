import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/cargo.dart';
import '../../crisscross_core/seed.dart';
import '../slat_undo_stack.dart';
import '../main_design_io.dart';
import '../shared_app_state.dart';

/// Mixin containing file import/export and undo/redo operations for DesignState
mixin DesignStateFileIOMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;
  set slats(Map<String, Slat> value);
  Map<String, Map<String, dynamic>> get layerMap;
  set layerMap(Map<String, Map<String, dynamic>> value);
  Map<String, Cargo> get cargoPalette;
  set cargoPalette(Map<String, Cargo> value);
  Map<String, Map<Offset, String>> get occupiedCargoPoints;
  set occupiedCargoPoints(Map<String, Map<Offset, String>> value);
  Map<(String, String, Offset), Seed> get seedRoster;
  set seedRoster(Map<(String, String, Offset), Seed> value);
  Map<String, Map<Offset, String>> get occupiedGridPoints;
  set occupiedGridPoints(Map<String, Map<Offset, String>> value);
  Map<String, Map<int, String>> get phantomMap;
  set phantomMap(Map<String, Map<int, String>> value);
  Map<String, List<Color>> get uniqueSlatColorsByLayer;
  double get gridSize;
  String get gridMode;
  set gridMode(String value);
  String get designName;
  set designName(String value);
  String get selectedLayerKey;
  set selectedLayerKey(String value);
  String get nextLayerKey;
  set nextLayerKey(String value);
  String get nextSeedID;
  set nextSeedID(String value);
  int get nextColorIndex;
  set nextColorIndex(int value);
  List<String> get colorPalette;
  bool get currentlyLoadingDesign;
  set currentlyLoadingDesign(bool value);
  String? get cargoAdditionType;
  set cargoAdditionType(String? value);
  bool get hammingValueValid;
  set hammingValueValid(bool value);
  SlatUndoStack get undoStack;
  set undoStack(SlatUndoStack value);

  // Methods from other mixins
  void resetDefaults();
  void clearSelection();
  void updateDesignHammingValue();
  Offset convertCoordinateSpacetoRealSpace(Offset inputPosition);

  void exportCurrentDesign() async {
    /// Exports the current design to an excel file
    exportDesign(slats, layerMap, cargoPalette, occupiedCargoPoints, seedRoster, gridSize, gridMode, designName);
  }

  void importNewDesign(BuildContext context, {String? fileName, Uint8List? fileBytes}) async {
    currentlyLoadingDesign = true;
    notifyListeners();

    var (
      newSlats,
      newLayerMap,
      newGridMode,
      newCargoPalette,
      newSeedRoster,
      newPhantomMap,
      newDesignName,
      errorCode
    ) = await importDesign(inputFileName: fileName, inputFileBytes: fileBytes);

    String messageFor(String code) {
      switch (code) {
        case 'ERR_SLAT_SHEETS':
          return 'There seems to be a problem with the slat layer sheets in the selected file - can you check the formatting?';
        case 'ERR_ASSEMBLY_SHEETS':
          return 'There seems to be a problem with the assembly handle sheets in the selected file - can you check the formatting?';
        case 'ERR_SEED_SHEETS':
          return 'There seems to be a problem with the seed sheets in the selected file - can you check the formatting?';
        case 'ERR_CARGO_SHEETS':
          return 'There seems to be a problem with the cargo sheets in the selected file - can you check the formatting?';
        case 'ERR_GENERAL':
          return 'The file could not be imported - are you sure this is a standard design file?';
        default:
          return '';
      }
    }

    if (errorCode.isNotEmpty) {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Text('Import failed'),
          content: Text(messageFor(errorCode)),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text("Close"),
            ),
          ],
        ),
      );
      currentlyLoadingDesign = false;
      notifyListeners();
      return;
    }

    // check if the maps are empty
    if (newSlats.isEmpty || newLayerMap.isEmpty) {
      currentlyLoadingDesign = false;
      notifyListeners();
      return;
    }

    undoStack = SlatUndoStack();
    clearAll();

    // transfer imported values into global state
    layerMap = newLayerMap;
    slats = newSlats;
    gridMode = newGridMode;
    cargoPalette = newCargoPalette;
    designName = newDesignName;
    phantomMap = newPhantomMap;
    selectedLayerKey = layerMap.keys.first;

    // update nextLayerKey based on the largest letter in the new incoming layers (it might not necessarily be the last one)
    // Get the highest letter key
    String maxKey = layerMap.keys.reduce((a, b) => a.compareTo(b) > 0 ? a : b);
    // Compute the next letter key
    nextLayerKey = nextCapitalLetter(maxKey);

    nextColorIndex = layerMap.length;
    if (nextColorIndex > colorPalette.length - 1) {
      nextColorIndex = 0;
    }

    // fill up the standard slat occupancy map
    for (var slat in slats.values) {
      occupiedGridPoints.putIfAbsent(slat.layer, () => {});
      occupiedGridPoints[slat.layer]?.addAll(
          {for (var offset in slat.slatPositionToCoordinate.values) offset: slat.id});
    }

    // fill up occupiedCargoPoints (from both the seed and cargo values)
    for (var slat in slats.values) {
      var layer = slat.layer;
      var topHelix = layerMap[layer]?['top_helix'];
      for (var i = 0; i < slat.maxLength; i++) {
        if (slat.h2Handles[i + 1] != null &&
            !slat.h2Handles[i + 1]!['category'].contains('ASSEMBLY')) {
          var occupancyID = topHelix == 'H2' ? 'top' : 'bottom';
          occupiedCargoPoints.putIfAbsent('$layer-$occupancyID', () => {});
          occupiedCargoPoints['$layer-$occupancyID']![
              slat.slatPositionToCoordinate[i + 1]!] = slat.id;
        }
        if (slat.h5Handles[i + 1] != null &&
            !slat.h5Handles[i + 1]!['category'].contains('ASSEMBLY')) {
          var occupancyID = topHelix == 'H5' ? 'top' : 'bottom';
          occupiedCargoPoints.putIfAbsent('$layer-$occupancyID', () => {});
          occupiedCargoPoints['$layer-$occupancyID']![
              slat.slatPositionToCoordinate[i + 1]!] = slat.id;
        }
      }
    }

    // fill up seedRoster and slat occupancy map (need to convert to real coordinates as import system doesn't have access to translator functions)
    List<String> seedKeys = [];
    for (var seed in newSeedRoster.entries) {

      Map<int, Offset> convertedCoordinates = seed.value.coordinates.map((key, value) => MapEntry(key, convertCoordinateSpacetoRealSpace(value)));
      seedRoster[(seed.key.$1, seed.key.$2, convertedCoordinates[1]!)] = Seed(ID: seed.value.ID, coordinates: convertedCoordinates);
      seedKeys.add(seed.value.ID);

      int seedOccupancyLayer = layerMap[seed.key.$1]?['order'] + (seed.key.$2 == 'top' ? 1 : -1);
      // apply the new seed to the slat occupancy map
      if (layerNumberValid(seedOccupancyLayer)) {
        String newLayer = getLayerByOrder(seedOccupancyLayer)!;
        for (var coord in seed.value.coordinates.values) {
          occupiedGridPoints[newLayer]![coord] = 'SEED';
        }
      }
    }
    // Compute the next seed letter key
    if (seedKeys.isNotEmpty) {
      String maxSeedKey = seedKeys.reduce((a, b) => a.compareTo(b) > 0 ? a : b);
      nextSeedID = nextCapitalLetter(maxSeedKey);
    }

    // update slat Color UI
    for (var layer in layerMap.keys) {
      uniqueSlatColorsByLayer[layer] = [];
      for (var slat in slats.values) {
        if (slat.layer == layer &&
            slat.uniqueColor != null &&
            !uniqueSlatColorsByLayer[layer]!.contains(slat.uniqueColor!)) {
          uniqueSlatColorsByLayer[layer]!.add(slat.uniqueColor!);
        }
      }
    }

    updateDesignHammingValue();
    currentlyLoadingDesign = false;
    notifyListeners();
  }

  void clearAll() {
    slats = {};
    layerMap = {
      'A': {
        "direction": gridMode == '90' ? 90 : 120, // slat default direction
        "DBDirection": gridMode == '90' ? 90 : 120, // temporary alternative drawing system
        'order': 0, // draw order - has to be updated when layers are moved
        'top_helix': 'H5',
        'bottom_helix': 'H2',
        'next_slat_id': 1, // used to give an id to a new slat
        'slat_count': 0,
        "color": Color(int.parse('0xFFebac23')), // default slat color
        "hidden": false
      },
      'B': {
        "direction": 180,
        "DBDirection": 180, // temporary alternative drawing system
        'next_slat_id': 1,
        'top_helix': 'H5',
        'bottom_helix': 'H2',
        'order': 1,
        'slat_count': 0,
        "color": Color(int.parse('0xFFb80058')),
        "hidden": false
      },
    };
    // state reset
    resetDefaults();

    saveUndoState();
    notifyListeners();
  }

  void saveUndoState() {
    undoStack.saveState(DesignSaveState(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: layerMap,
        layerMetaData: {
          'selectedLayerKey': selectedLayerKey,
          'nextLayerKey': nextLayerKey,
          'nextColorIndex': nextColorIndex,
        },
        cargoPalette: cargoPalette,
        occupiedCargoPoints: occupiedCargoPoints,
        seedRoster: seedRoster,
        phantomMap: phantomMap));
  }

  void undo2DAction({bool redo = false}) {
    // reverses actions taken on the 2D portion of the design
    clearSelection();
    hammingValueValid = false;
    DesignSaveState? newState;
    if (redo) {
      newState = undoStack.redo();
    } else {
      newState = undoStack.undo();
    }

    if (newState != null) {
      slats = newState.slats;
      occupiedGridPoints = newState.occupiedGridPoints;
      occupiedCargoPoints = newState.occupiedCargoPoints;
      cargoPalette = newState.cargoPalette;
      layerMap = newState.layerMap;
      selectedLayerKey = newState.layerMetaData['selectedLayerKey'];
      nextLayerKey = newState.layerMetaData['nextLayerKey'];
      nextColorIndex = newState.layerMetaData['nextColorIndex'];
      seedRoster = newState.seedRoster;
      if (!cargoPalette.containsKey(cargoAdditionType)) {
        cargoAdditionType = null;
      }
    }
    notifyListeners();
  }

  // Helper methods that need to be declared as abstract in this mixin
  // since they're implemented in other mixins
  bool layerNumberValid(int layerOrder);
  String? getLayerByOrder(int order);
}
