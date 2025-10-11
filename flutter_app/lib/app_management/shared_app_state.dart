import 'dart:collection';

import 'package:flutter/material.dart';
import 'package:grpc/grpc.dart';
import 'package:flutter/foundation.dart';
import 'dart:math';

import '../crisscross_core/slats.dart';
import '../crisscross_core/sparse_to_array_conversion.dart';
import '../crisscross_core/assembly_handles.dart';
import '../crisscross_core/cargo.dart';
import '../crisscross_core/seed.dart';
import '../crisscross_core/handle_plates.dart';

import '../grpc_client_architecture/client_entry.dart';
import '../grpc_client_architecture/health.pbgrpc.dart';

import 'slat_undo_stack.dart';
import 'main_design_io.dart';
import '../main_windows/alert_window.dart';
import '../2d_painters/helper_functions.dart' as utils;


/// Useful function to generate the next capital letter in the alphabet for slat identifier keys
String nextCapitalLetter(String current) {
  int len = current.length;
  List<int> chars = current
      .split('')
      .map((c) => c.codeUnitAt(0) - 'A'.codeUnitAt(0))
      .toList();

  for (int i = len - 1; i >= 0; i--) {
    if (chars[i] < 25) {
      chars[i]++;
      return String.fromCharCodes(chars.map((e) => 'A'.codeUnitAt(0) + e));
    } else {
      chars[i] = 0;
    }
  }
  // If all characters are 'Z', add 'A' to the beginning.
  return 'A${String.fromCharCodes(chars.map((e) => 'A'.codeUnitAt(0) + e))}';
}

// encapsulates all info necessary to describe a transient set of moving slats
// TODO: should also add ability to visualize moving slats and cargo too...
class HoverPreview {

  final String kind; // 'Slat-Add' | 'Slat-Move' | 'Cargo-Add' | 'Cargo-Move'
  final bool isValid;

  // For slats: a list of 32-pt paths (one per slat in multi-add), in REAL space
  final List<List<Offset>> slatPaths;

  // For cargo/seed: points in REAL space (e.g., handle locations)
  final List<Offset> cargoOrSeedPoints;

  const HoverPreview({
    required this.kind,
    required this.isValid,
    this.slatPaths = const [],
    this.cargoOrSeedPoints = const [],
  });
}

/// State management for the design of the current megastructure
class DesignState extends ChangeNotifier {

  final double gridSize = 10.0; // do not change
  late final double y60Jump = gridSize / 2;
  late final double x60Jump = sqrt(pow(gridSize, 2) - pow(y60Jump, 2));
  String gridMode = '60';
  bool standardTilt = true; // just a toggle between the two different tilt types

  HoverPreview? hoverPreview; // current transient set of slats

  Map<(String, int), Offset> slatDirectionGenerators = {
    ('90', 90): Offset(1, 0),
    ('90', 180): Offset(0, 1),

    ('60', 180): Offset(0, 2),
    ('60', 120): Offset(1, 1),
    ('60', 240): Offset(-1, 1),
  };

  Map<(String, int), Offset> multiSlatGenerators = {
    ('90', 90): Offset(0, 1),
    ('90', 180): Offset(1, 0),

    ('60', 180): Offset(1, 1),
    ('60', 120): Offset(0, 2),
    ('60', 240): Offset(0, 2),
  };
  Map<(String, int), Offset> multiSlatGeneratorsAlternate = {
    ('90', 90): Offset(0, -1),
    ('90', 180): Offset(-1, 0),
    ('60', 180): Offset(-1, 1),
    ('60', 120): Offset(1, -1),
    ('60', 240): Offset(-1, -1),
  };

  // trialling a new system for slat addition using a full 360deg rotation and no flips
  Map<(String, int), Offset> multiSlatGeneratorsDB = {
    ('90', 90): Offset(0, 1),
    ('90', 180): Offset(-1, 0),
    ('90', 270): Offset(0, -1),
    ('90', 0): Offset(1, 0),

    ('60', 180): Offset(-1, -1),
    ('60', 120): Offset(-1, 1),
    ('60', 240): Offset(0, -2),
    ('60', 300): Offset(1, -1),
    ('60', 0): Offset(1, 1),
    ('60', 60): Offset(0, 2),
  };

  Map<(String, int), Offset> slatDirectionGeneratorsDB = {
    ('90', 90): Offset(1, 0),
    ('90', 180): Offset(0, 1),
    ('90', 270): Offset(-1, 0),
    ('90', 0): Offset(0, -1),

    ('60', 180): Offset(0, 2),
    ('60', 120): Offset(1, 1),
    ('60', 240): Offset(-1, 1),
    ('60', 300): Offset(-1, -1),
    ('60', 0): Offset(0, -2),
    ('60', 60): Offset(1, -1),
  };

  // when checking seed occupancy, use these values to extend beyond the standard hover position
  Map<String, int> seedOccupancyDimensions = {'width': 5, 'height': 16};

  // good starter colours for distinguishing layers quickly, but user can adjust
  List<String> colorPalette = [
    '#ebac23',
    '#b80058',
    '#008cf9',
    '#006e00',
    '#00bbad',
    '#d163e6',
    '#b24602',
    '#ff9287',
    '#5954d6',
    '#00c6f8',
    '#878500',
    '#00a76c',
    '#bdbdbd'
  ];

  // main properties for each design layer
  Map<String, Map<String, dynamic>> layerMap = {
    'A': {
      "direction": 120, // slat default direction
      "DBDirection": 120, // temporary alternative drawing system
      'order': 0, // draw order - has to be updated when layers are moved
      'top_helix': 'H5',
      'bottom_helix': 'H2',
      'next_slat_id': 1,
      'slat_count': 0,
      "color": Color(int.parse('0xFFebac23')), // default slat color
      "hidden": false
    },
    'B': {
      "direction": 240,
      "DBDirection": 240, // temporary alternative drawing system
      'next_slat_id': 1,
      'slat_count': 0,
      'top_helix': 'H5',
      'bottom_helix': 'H2',
      'order': 1,
      "color": Color(int.parse('0xFFb80058')),
      "hidden": false
    },
  };

  SlatUndoStack undoStack = SlatUndoStack();

  // main slat container
  Map<String, Slat> slats = {};

  // default values for new layers and slats
  String selectedLayerKey = 'A';
  List<String> selectedSlats = [];   // to highlight on grid painter
  String nextLayerKey = 'C';
  String nextSeedID = 'A';
  int nextColorIndex = 2;
  int slatAddCount = 1;
  String slatAddDirection = 'down';
  Color uniqueSlatColor = Colors.blue;
  int currentHamming = 0;
  bool hammingValueValid = true;
  int cargoAddCount = 1;
  String? cargoAdditionType;
  String slatAdditionType = 'tube';
  List<Offset> selectedCargoPositions = [];
  String designName = 'New Megastructure';

  Map<String, Map<Offset, String>> occupiedCargoPoints = {};
  Map<(String, String, Offset), Seed> seedRoster = {};
  Map<String, List<Color>> uniqueSlatColorsByLayer = {};

  bool currentlyLoadingDesign = false;
  bool currentlyComputingHamming = false;

  // useful to keep track of occupancy and speed up grid checks
  Map<String, Map<Offset, String>> occupiedGridPoints = {};

  Map<String, Cargo> cargoPalette = {
    'SEED': Cargo(name: 'SEED', shortName: 'S', color: Color.fromARGB(255, 255, 0, 0)),
  };

  PlateLibrary plateStack = PlateLibrary();

  // GENERAL OPERATIONS //

  void setHoverPreview(HoverPreview? preview) {
    hoverPreview = preview;
    notifyListeners();
  }

  void initializeUndoStack() {
    saveUndoState();
  }

  Offset convertRealSpacetoCoordinateSpace(Offset inputPosition){
    return utils.convertRealSpacetoCoordinateSpace(inputPosition, gridMode, gridSize, x60Jump, y60Jump);
  }

  Offset convertCoordinateSpacetoRealSpace(Offset inputPosition){
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

  bool layerNumberValid(int layerOrder){
    return layerOrder != -1 && layerOrder < layerMap.length ? true : false;
  }

  void resetDefaults(){
    selectedLayerKey = 'A';
    selectedSlats = [];   // to highlight on grid painter
    nextLayerKey = 'C';
    nextSeedID = 'A';
    nextColorIndex = 2;
    slatAddCount = 1;
    currentHamming = 0;
    hammingValueValid = true;
    cargoAddCount = 1;
    cargoAdditionType = null;
    occupiedGridPoints = {};
    seedRoster = {};
    slatAddDirection = 'down';
    uniqueSlatColor = Colors.blue;
    uniqueSlatColorsByLayer = {};
    slatAdditionType = 'tube';
    cargoPalette = {
      'SEED': Cargo(name: 'SEED', shortName: 'S1', color: Color.fromARGB(255, 255, 0, 0)),
    };

    occupiedCargoPoints = {};
    selectedCargoPositions = [];
  }

  /// updates the grid type (60 or 90)
  void setGridMode(String value) {
    gridMode = value;
    clearAll();
    undoStack = SlatUndoStack();
    notifyListeners();
  }

  void setDesignName(String newName) {
    if(newName == ''){
      designName = 'New Megastructure';
    }
    else {
      designName = newName;
    }
    if(designName.contains(',')){
      designName = designName.replaceAll(',', '_');
    }

    notifyListeners();
  }

  void setUniqueSlatColor(Color color) {
    uniqueSlatColor = color;
    notifyListeners();
  }

  void exportCurrentDesign() async {
    /// Exports the current design to an excel file
    exportDesign(slats, layerMap, cargoPalette, occupiedCargoPoints, seedRoster, gridSize, gridMode, designName);
  }

  void importNewDesign() async{

    currentlyLoadingDesign = true;
    notifyListeners();

    var (newSlats, newLayerMap, newGridMode, newCargoPalette, newSeedRoster, newDesignName) = await importDesign();
    // check if the maps are empty
    if (newSlats.isEmpty || newLayerMap.isEmpty) {
      currentlyLoadingDesign = false;
      notifyListeners();
      return;
    }

    undoStack = SlatUndoStack();
    clearAll();

    layerMap = newLayerMap;
    slats = newSlats;
    gridMode = newGridMode;
    cargoPalette = newCargoPalette;
    designName = newDesignName;
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

    for (var slat in slats.values) {
      occupiedGridPoints.putIfAbsent(slat.layer, () => {});
      occupiedGridPoints[slat.layer]?.addAll({
        for (var offset in slat.slatPositionToCoordinate.values) offset: slat.id
      });
    }

    // fill up occupiedCargoPoints (from both the seed and cargo values)
    for (var slat in slats.values) {
      var layer = slat.layer;
      var topHelix = layerMap[layer]?['top_helix'];
      for (var i = 0; i < slat.maxLength; i++) {
        if (slat.h2Handles[i+1] != null && !slat.h2Handles[i+1]!['category'].contains('ASSEMBLY')){
          var occupancyID = topHelix == 'H2' ? 'top' : 'bottom';
          occupiedCargoPoints.putIfAbsent('$layer-$occupancyID', () => {});
          occupiedCargoPoints['$layer-$occupancyID']![slat.slatPositionToCoordinate[i+1]!] =  slat.id;
        }
        if (slat.h5Handles[i+1] != null && !slat.h5Handles[i+1]!['category'].contains('ASSEMBLY')){
          var occupancyID = topHelix == 'H5' ? 'top' : 'bottom';
          occupiedCargoPoints.putIfAbsent('$layer-$occupancyID', () => {});
          occupiedCargoPoints['$layer-$occupancyID']![slat.slatPositionToCoordinate[i+1]!] =  slat.id;
        }
      }
    }

    // fill up seedRoster and slat occupancy map (need to convert to real coordinates as import system doesn't have access to translator functions)
    List<String> seedKeys = [];
    for (var seed in newSeedRoster.entries){
      Map<int, Offset> convertedCoordinates = seed.value.coordinates.map(
            (key, value) => MapEntry(key, convertCoordinateSpacetoRealSpace(value)),
      );
      seedRoster[(seed.key.$1, seed.key.$2, convertedCoordinates[1]!)] = Seed(
        ID: seed.value.ID,
        coordinates: convertedCoordinates);
      seedKeys.add(seed.value.ID);

      int seedOccupancyLayer = layerMap[seed.key.$1]?['order'] + (seed.key.$2 == 'top' ? 1 : -1);
      // apply the new seed to the slat occupancy map
      if (layerNumberValid(seedOccupancyLayer)) {
        String newLayer = getLayerByOrder(seedOccupancyLayer)!;
        for (var coord in seed.value.coordinates.values){
          occupiedGridPoints[newLayer]![coord] =  'SEED';
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
        if (slat.layer == layer && slat.uniqueColor != null && !uniqueSlatColorsByLayer[layer]!.contains(slat.uniqueColor!)) {
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

  void saveUndoState(){
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
    ));
  }

  void undo2DAction({bool redo = false}){
    // reverses actions taken on the 2D portion of the design
    clearSelection();
    hammingValueValid = false;
    DesignSaveState? newState;
    if (redo){
      newState = undoStack.redo();
    }
    else{
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
      if (!cargoPalette.containsKey(cargoAdditionType)){
        cargoAdditionType = null;
      }
    }
    notifyListeners();
  }

  // LAYER OPERATIONS //

  /// Updates the active layer
  void updateActiveLayer(String value) {
    selectedLayerKey = value;
    notifyListeners();
  }

  /// Cycles through the layer list and sets the selected layer (either up or down)
  void cycleActiveLayer(bool upDirection) {
    if (upDirection) {
      selectedLayerKey = layerMap.keys.firstWhere((key) => layerMap[key]!['order'] == (layerMap[selectedLayerKey]!['order'] + 1) % layerMap.length);
    } else {
      selectedLayerKey = layerMap.keys.firstWhere((key) => layerMap[key]!['order'] == (layerMap[selectedLayerKey]!['order'] - 1 + layerMap.length) % layerMap.length);
    }
    notifyListeners();
  }

  /// Updates the color of a layer
  void updateLayerColor(String layer, Color color) {
    layerMap[layer] = {
      ...?layerMap[layer],
      "color": color,
    };
    notifyListeners();
  }

  /// Clears all selected slats
  void clearSelection() {
    selectedSlats = [];
    notifyListeners();
  }

  /// Rotates the direction of a layer through all available directions
  void rotateLayerDirection(String layerKey) {
    if (gridMode == '90'){
      if (layerMap[layerKey]?['direction'] == 90) {
        layerMap[layerKey]?['direction'] = 180;
      } else {
        layerMap[layerKey]?['direction'] = 90;
      }
      layerMap[layerKey]?['DBDirection'] += 90; // fully rotates around the entire range of possible angles
    }
    else if (gridMode == '60'){
      if (layerMap[layerKey]?['direction'] == 180) {
        layerMap[layerKey]?['direction'] = 120;
      }
      else if (layerMap[layerKey]?['direction'] == 120){
        layerMap[layerKey]?['direction'] = 240;
      }
      else {
        layerMap[layerKey]?['direction'] = 180;
      }
      layerMap[layerKey]?['DBDirection'] += 60; // fully rotates around the entire range of possible angles
    }
    else{
      throw Exception('Invalid grid mode: $gridMode');
    }

    if (layerMap[layerKey]?['DBDirection'] == 360){
      layerMap[layerKey]?['DBDirection'] = 0;
    }
    notifyListeners();
  }

  /// flips the H2-H5 direction of a layer
  void flipLayer(String layer, BuildContext context) {

    // The flip operation can be invalid if a seed is transferred to a location where slats are already present.
    // To prevent this, need to check the slat occupancy map prior to allowing the flip to occur.
    final seedKeysToFlip = <(String, String, Offset)>[];
    for (var seed in seedRoster.entries) {
      if (seed.key.$1 == layer) {
        bool flipValid = true;
        // if seed is currently on top, check next layer underneath and vice versa
        int candidateSeedLayerNumber = layerMap[layer]?['order'] + (seed.key.$2 == 'top' ? -1 : 1);
        if (layerNumberValid(candidateSeedLayerNumber)) {
          String candidateSeedOccupancyLayer = getLayerByOrder(candidateSeedLayerNumber)!;
          for (var coord in seed.value.coordinates.values) {
            if (occupiedGridPoints[candidateSeedOccupancyLayer]!.containsKey(convertRealSpacetoCoordinateSpace(coord))) {
              flipValid = false;
              break;
            }
          }
        }
        // if operation invalid, show dialog box and cancel operation
        if(!flipValid){
          showWarning(context, 'Invalid Flip Operation', 'Cannot flip the layer because this would result in a seed colliding with slats in the layer above/below its current position.');
          return;
        }
        seedKeysToFlip.add(seed.key);
      }
    }
    // update layer top/bottom helices
    if (layerMap[layer]?['top_helix'] == 'H5') {
      layerMap[layer]?['top_helix'] = 'H2';
      layerMap[layer]?['bottom_helix'] = 'H5';
    } else {
      layerMap[layer]?['top_helix'] = 'H5';
      layerMap[layer]?['bottom_helix'] = 'H2';
    }

    // swaps occupancy grid points to match layer flip
    occupiedCargoPoints.putIfAbsent('$layer-top', () => {});
    occupiedCargoPoints.putIfAbsent('$layer-bottom', () => {});

    var temp = occupiedCargoPoints['$layer-top']!;
    occupiedCargoPoints['$layer-top'] = occupiedCargoPoints['$layer-bottom']!;
    occupiedCargoPoints['$layer-bottom'] = temp;

    // apply slat and seed occupancy map changes
    if (seedKeysToFlip.isNotEmpty) {
      // seed could either move above or below current layer
      List<int> potentialSeedLayers = [layerMap[layer]?['order'] + 1, layerMap[layer]?['order'] - 1];

      // first, clear the positions of all previous seeds in the layer
      for (int layerPos in potentialSeedLayers){
        if (layerNumberValid(layerPos)) {
          String seedOccupiedLayer = getLayerByOrder(layerPos)!;
          occupiedGridPoints[seedOccupiedLayer]?.removeWhere((key, value) => value == 'SEED');
        }
      }

      // next, apply the new seed positions in both seed and slat occupancy maps
      for (var key in seedKeysToFlip) {
        var newSide = flipSlatSide(key.$2);

        // delete the old seed from the roster, and add the new one
        seedRoster[(key.$1, newSide, key.$3)] = seedRoster[key]!;
        seedRoster.remove(key);

        int newSeedLayerNumber = layerMap[layer]?['order'] + (newSide == 'top' ? 1 : -1);

        // apply the new seed to the slat occupancy map
        if (layerNumberValid(newSeedLayerNumber)) {
          String newLayer = getLayerByOrder(newSeedLayerNumber)!;
          for (var coord in seedRoster[(key.$1, newSide, key.$3)]!.coordinates.values){
            occupiedGridPoints[newLayer]![convertRealSpacetoCoordinateSpace(coord)] =  'SEED';
          }
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }


  /// Changes the visibility of a layer on the 2D grid
  void flipLayerVisibility(String layer) {
    layerMap[layer]?['hidden'] = !layerMap[layer]?['hidden'];
    notifyListeners();
  }

  /// Multi-slat generation can be flipped to achieve different placement systems
  void flipMultiSlatGenerator(){
    Map<(String, int), Offset> settingsTransfer = Map.from(multiSlatGenerators);
    multiSlatGenerators = Map.from(multiSlatGeneratorsAlternate);
    multiSlatGeneratorsAlternate = settingsTransfer;
    standardTilt = !standardTilt;
    notifyListeners();
  }

  /// Slat placement can be flipped to adjust the positions of handles
  void flipSlatAddDirection(){
    if (slatAddDirection == 'down'){
      slatAddDirection = 'up';
    } else {
      slatAddDirection = 'down';
    }
    notifyListeners();
  }

  /// Deletes a layer from the design entirely
  void deleteLayer(String layer) {
    if (!layerMap.containsKey(layer))
      return; // Ensure the layer exists before deleting

    layerMap.remove(layer); // Remove the layer

    // Sort the remaining keys based on their current 'order' values
    final sortedKeys = layerMap.keys.toList()
      ..sort((a, b) => layerMap[a]!['order'].compareTo(layerMap[b]!['order']));

    // Reassign 'order' values to maintain sequence
    for (int i = 0; i < sortedKeys.length; i++) {
      layerMap[sortedKeys[i]]!['order'] = i;
    }

    // Update selectedLayerKey if needed TODO: do not allow the deletion of the last layer or else deal with a null system...
    if (selectedLayerKey == layer) {
      selectedLayerKey = (sortedKeys.isEmpty ? null : sortedKeys.last)!;
    }

    // removes all slats from the deleted layer
    slats.removeWhere((key, value) => value.layer == layer);
    occupiedGridPoints.remove(layer);

    // remove all seeds from the deleted layer
    seedRoster.removeWhere((key, value) => key.$1 == layer);

    // remove all cargo points from the deleted layer
    occupiedCargoPoints.removeWhere((key, value) => key.startsWith('$layer-'));

    saveUndoState();
    notifyListeners();
  }

  /// Reorders the positions of the layers based on a new order
  void reOrderLayers(List<String> newOrder, BuildContext context) {

    // since layers have moved, seed occupancy map needs to be updated, and potentially move should be cancelled if a clash can occur

    // first, create a fake new layer map

    var fakeLayerMap = {
      for (var entry in layerMap.entries)
        entry.key: Map<String, dynamic>.from(entry.value)
    };

    for (int i = 0; i < newOrder.length; i++) {
      fakeLayerMap[newOrder[i]]!['order'] = i; // Assign new order values
    }

    // next, check all seeds to see if they clash in any way
    for (var seed in seedRoster.entries) {
      bool moveValid = true;
      int candidateSeedLayerNumber = fakeLayerMap[seed.key.$1]!['order'] + (seed.key.$2 == 'top' ? 1 : -1);
      int previousSeedLayerNumber = layerMap[seed.key.$1]!['order'] + (seed.key.$2 == 'top' ? 1 : -1);

      if (layerNumberValid(candidateSeedLayerNumber)) {
        String candidateSeedOccupancyLayer = '';
        for (final entry in fakeLayerMap.entries) {
          if (entry.value['order'] == candidateSeedLayerNumber) {
            candidateSeedOccupancyLayer = entry.key;
          }
        }
        String previousSeedOccupancyLayer = layerNumberValid(previousSeedLayerNumber)? getLayerByOrder(previousSeedLayerNumber)! : '';

        if (candidateSeedOccupancyLayer == previousSeedOccupancyLayer) {
          continue; // no change in layer, so no need to check
        }

        for (var coord in seed.value.coordinates.values) {
          if (occupiedGridPoints[candidateSeedOccupancyLayer]!.containsKey(convertRealSpacetoCoordinateSpace(coord))) {
            moveValid = false;
            break;
          }
        }
      }
      // if operation invalid, show dialog box and cancel operation
      if(!moveValid){
        showWarning(context, "Invalid Layer Move Operation", "Cannot move the layer because this would result in a seed colliding with slats in the layer above/below the layer's new position.");
        return;
      }
    }

    // if move is valid, proceed with the operation
    for (int i = 0; i < newOrder.length; i++) {
      layerMap[newOrder[i]]!['order'] = i; // Assign new order values
    }

    // apply slat occupancy map changes

    // first, clear the positions of all previous seeds
    for (var layerID in layerMap.keys){
      occupiedGridPoints[layerID]?.removeWhere((key, value) => value == 'SEED');
    }

    // next, apply the new seed positions in both seed and slat occupancy maps
    for (var seed in seedRoster.entries) {

      int newSeedLayerNumber = layerMap[seed.key.$1]?['order'] + (seed.key.$2 == 'top' ? 1 : -1);

      // apply the new seed to the slat occupancy map
      if (layerNumberValid(newSeedLayerNumber)) {
        String newLayer = getLayerByOrder(newSeedLayerNumber)!;
        for (var coord in seed.value.coordinates.values){
          occupiedGridPoints[newLayer]![convertRealSpacetoCoordinateSpace(coord)] =  'SEED';
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }

  /// Adds an entirely new layer to the design
  void addLayer() {
    layerMap[nextLayerKey] = {
      "direction": layerMap.values.last['direction'],
      "DBDirection": layerMap.values.last['direction'], // temporary alternative drawing system
      'next_slat_id': 1,
      'slat_count': 0,
      'top_helix': 'H5',
      'bottom_helix': 'H2',
      'order': layerMap.length,
      "color":
      Color(int.parse('0xFF${colorPalette[nextColorIndex].substring(1)}')),
      "hidden": false
    };


    // if last last layerMap value has direction horizontal, next direction should be rotated one step forward
    rotateLayerDirection(nextLayerKey);

    if (nextColorIndex == colorPalette.length - 1) {
      nextColorIndex = 0;
    } else {
      nextColorIndex += 1;
    }

    occupiedGridPoints.putIfAbsent(nextLayerKey, () => {});

    // re-apply seed occupancy maps to the layer, if available
    for (var seed in seedRoster.entries) {
      int seedLayerNumber = layerMap[seed.key.$1]?['order'] + (seed.key.$2 == 'top' ? 1 : -1);
      // apply the new seed to the slat occupancy map
      if (layerNumberValid(seedLayerNumber)) {
        String layer = getLayerByOrder(seedLayerNumber)!;
        if (layer == nextLayerKey){
          for (var coord in seed.value.coordinates.values){
            occupiedGridPoints[layer]![convertRealSpacetoCoordinateSpace(coord)] =  'SEED';
          }
        }
      }
    }

    nextLayerKey = nextCapitalLetter(nextLayerKey);
    saveUndoState();
    notifyListeners();
  }

  // SLAT OPERATIONS //

  void setSlatAdditionType(String type){
    slatAdditionType = type;
    notifyListeners();
  }

  /// Adds slats to the design
  void addSlats(String layer, Map<int, Map<int, Offset>> slatCoordinates) {

    for (var slat in slatCoordinates.entries) {
      slats['$layer-I${layerMap[layer]?["next_slat_id"]}'] = Slat(layerMap[layer]?["next_slat_id"], '$layer-I${layerMap[layer]?["next_slat_id"]}',layer, slat.value, slatType: slatAdditionType);
      // add the slat to the list by adding a map of all coordinate offsets to the slat ID
      occupiedGridPoints.putIfAbsent(layer, () => {});
      occupiedGridPoints[layer]?.addAll({
        for (var offset in slat.value.values)
          offset: '$layer-I${layerMap[layer]?["next_slat_id"]}'
      });
      layerMap[layer]?["next_slat_id"] += 1;
      layerMap[layer]?["slat_count"] += 1;
    }
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  /// Updates the position of a slat
  void updateSlatPosition(String slatID, Map<int, Offset> slatCoordinates) {

    // also need to remove old positions from occupiedGridPoints and add new ones
    String layer = slatID.split('-')[0];

    occupiedGridPoints[layer]?.removeWhere((key, value) => value == slatID);

    slats[slatID]?.updateCoordinates(slatCoordinates);
    occupiedGridPoints[layer]?.addAll({for (var offset in slatCoordinates.values) offset: slatID});
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  /// Removes a slat from the design
  void removeSlat(String ID) {

    clearSelection();
    String layer = ID.split('-')[0];
    slats.remove(ID);
    occupiedGridPoints[layer]?.removeWhere((key, value) => value == ID);
    layerMap[layer]?["slat_count"] -= 1;
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  /// Selects or deselects a slat
  void selectSlat(String ID, {bool addOnly = false}) {
    if (selectedSlats.contains(ID) && !addOnly) {
      selectedSlats.remove(ID);
    } else {
      if (selectedSlats.contains(ID)) {
        return;
      }
      selectedSlats.add(ID);
    }
    notifyListeners();
  }

  /// Updates the number of slats to be added with the next 'add' click
  void updateSlatAddCount(int value) {
    slatAddCount = value;
    notifyListeners();
  }

  void assignAssemblyHandleArray(List<List<List<int>>> handleArray, Offset? minPos, Offset? maxPos){
    if (minPos == null || maxPos == null){
      (minPos, maxPos) = extractGridBoundary(slats);
    }

    for (var slat in slats.values) {
      List assemblyLayers = [];
      if (layerMap[slat.layer]!['order'] == 0) {
        assemblyLayers.add(0);
      } else if (layerMap[slat.layer]!['order'] == layerMap.length-1) {
        assemblyLayers.add(handleArray[0][0].length-1);
      } else {
        assemblyLayers.add(layerMap[slat.layer]!['order'] - 1);
        assemblyLayers.add(layerMap[slat.layer]!['order']);
      }
      for (int i = 0; i < slat.maxLength; i++) {
        int x = (slat.slatPositionToCoordinate[i+1]!.dx - minPos.dx).toInt();
        int y = (slat.slatPositionToCoordinate[i+1]!.dy - minPos.dy).toInt();
        for (var aLayer in assemblyLayers) {
          if (handleArray[x][y][aLayer] != 0) {
            int slatSide;
            String category;
            if (aLayer == layerMap[slat.layer]!['order']){
              slatSide = int.parse(layerMap[slat.layer]?['top_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
              category = 'ASSEMBLY_HANDLE';
            }
            else{
              slatSide = int.parse(layerMap[slat.layer]?['bottom_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
              category = 'ASSEMBLY_ANTIHANDLE';
            }
            slat.setPlaceholderHandle(i + 1, slatSide, '${handleArray[x][y][aLayer]}', category);
          }
        }
      }
    }
  }

  void updateDesignHammingValue() async {
    currentlyComputingHamming = true;
    notifyListeners();
    if (slats.isEmpty) {
      currentHamming = 0;
    } else {
      currentHamming = await hammingCompute(slats, layerMap, 32);
      // TODO: this needs to be updated when db logic included
      if (currentHamming == 50 || currentHamming == 32) { // 50 (calculation never attempted) or 32 (no handle overlap) are exception values
        currentHamming = 0;
      }
    }
    hammingValueValid = true;
    currentlyComputingHamming = false;
    notifyListeners();
  }

  void generateRandomAssemblyHandles(int uniqueHandleCount, bool splitLayerHandles) {

    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);
    List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);
    List<List<List<int>>> handleArray;

    if (splitLayerHandles && layerMap.length > 2) {
      handleArray = generateLayerSplitHandles(slatArray, uniqueHandleCount,
          seed: DateTime.now().millisecondsSinceEpoch % 1000);
    } else {
      handleArray = generateRandomSlatHandles(slatArray, uniqueHandleCount,
          seed: DateTime.now().millisecondsSinceEpoch % 1000);
    }

    assignAssemblyHandleArray(handleArray, minPos, maxPos);
    saveUndoState();
    notifyListeners();
  }

  Future<bool> updateAssemblyHandlesFromFile(BuildContext context) async {
    /// Reads assembly handles from a file and applies them to the slats (e.g. generated after evolution)
    ///


    bool readStatus = await importAssemblyHandlesFromFileIntoSlatArray(slats, layerMap, gridSize);
    if (!readStatus) {
      undo2DAction();
      return false;
    }

    saveUndoState();
    notifyListeners();
    return true;
  }

  List<List<List<int>>> getSlatArray(){
    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);
    List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);
    return slatArray;
  }

  List<List<List<int>>> getHandleArray(){
    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);
    return extractAssemblyHandleArray(slats, layerMap, minPos, maxPos, gridSize);
  }

  Map<String, String> getSlatTypes(){
    Map<String, String> slatTypes = {};
    for (var slat in slats.values) {

      var layerNumber = layerMap[slat.layer]!['order'] + 1;
      // replace the layer ID with the layer number
      slatTypes[slat.id.replaceFirst(slat.layer, layerNumber.toString())] = slat.slatType;
    }
    return slatTypes;
  }

  void clearAssemblyHandles(){

    /// Removes all handles from the slats
    for (var slat in slats.values) {
      slat.clearAssemblyHandles();
    }
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void assignColorToSelectedSlats(Color color) {
    /// Assigns a color to all selected slats
    for (var slatID in selectedSlats) {
      if (slats.containsKey(slatID)) {
        slats[slatID]!.uniqueColor = color;
      }
    }

    // add to sidebar viewer system
    uniqueSlatColorsByLayer.putIfAbsent(selectedLayerKey, () => []);
    // check if the color already exists in the list
    if (!uniqueSlatColorsByLayer[selectedLayerKey]!.contains(color)) {
      uniqueSlatColorsByLayer[selectedLayerKey]?.add(color);
    }
    saveUndoState();
    notifyListeners();
  }

  void editSlatColorSearch(String layerKey, int oldColorIndex, Color newColor) {
    /// Edits the color of all slats of a specific color
    Color oldColor = uniqueSlatColorsByLayer[layerKey]![oldColorIndex];
    for (var slat in slats.values) {
      if (slat.layer == layerKey && slat.uniqueColor == oldColor) {
        slat.uniqueColor = newColor;
      }
    }
    // update the uniqueSlatColorsByLayer map
    uniqueSlatColorsByLayer[layerKey]![oldColorIndex] = newColor;

    notifyListeners();
  }

  void removeSlatColorFromLayer(String layerKey, int colorIndex) {
    /// Removes a specific color from the list of unique slat colors in a layer
    Color colorToRemove = uniqueSlatColorsByLayer[layerKey]![colorIndex];
    for (var slat in slats.values) {
      if (slat.layer == layerKey && slat.uniqueColor == colorToRemove) {
        slat.clearColor();
      }
    }
    uniqueSlatColorsByLayer[layerKey]?.removeAt(colorIndex);
    saveUndoState();
    notifyListeners();
  }

  void clearAllSlatColors(){
    /// Clears the color of all slats
    for (var slat in slats.values) {
      slat.clearColor();
    }
    uniqueSlatColorsByLayer.clear();

    saveUndoState();
    notifyListeners();
  }

  void clearSlatColorsFromLayer(String layer) {
    /// Clears the color of all slats in a specific layer
    for (var slat in slats.values) {
      if (slat.layer == layer) {
        slat.clearColor();
      }
    }
    uniqueSlatColorsByLayer.remove(layer);
    saveUndoState();
    notifyListeners();
  }

  // CARGO OPERATIONS //

  // this is just adding another available cargo type to the list (and not attaching it to any slats)
  void addCargoType(Cargo cargo){

    cargoPalette[cargo.name] = cargo;
    saveUndoState();
    notifyListeners();
  }

  void deleteCargoType(String cargoName){


    // need to remove all cargo of this type from the slats and from the cargo occupancy map (otherwise will error out)
    for (var slat in slats.values) {
      for (var side in ['top', 'bottom']) {
        var targetDict = layerMap[slat.layer]!['${side}_helix'] == 'H5' ? slat.h5Handles : slat.h2Handles;
        for (int position = 1; position <= slat.maxLength; position++) {
          if (targetDict[position] != null && targetDict[position]!['descriptor'] == cargoName) {
            targetDict.remove(position);
            occupiedCargoPoints['${slat.layer}-$side']?.remove(slat.slatPositionToCoordinate[position]!);
          }
        }
      }
    }

    cargoPalette.remove(cargoName);
    cargoAdditionType = null;
    saveUndoState();
    notifyListeners();

  }

  void deleteAllCargo(){

    // need to remove all cargo of this type from the slats and from the cargo occupancy map (otherwise will error out)
    for (var slat in slats.values) {
      for (var side in ['top', 'bottom']) {
        var targetDict = layerMap[slat.layer]!['${side}_helix'] == 'H5' ? slat.h5Handles : slat.h2Handles;
        for (int position = 1; position <= slat.maxLength; position++) {
          if (targetDict[position] != null && targetDict[position]!['category'] == 'CARGO') {
            targetDict.remove(position);
            occupiedCargoPoints['${slat.layer}-$side']?.remove(slat.slatPositionToCoordinate[position]!);
          }
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }

  /// Updates the number of cargo to be added with the next 'add' click
  void updateCargoAddCount(int value) {
    if (cargoAdditionType == 'SEED'){
      cargoAddCount = 1;
    }
    else {
      cargoAddCount = value;
    }
    notifyListeners();
  }

  void selectCargoType(String ID){
    if (cargoAdditionType == ID) {
      cargoAdditionType = null;
    } else {
      cargoAdditionType = ID;
    }
    notifyListeners();
  }

  void attachCargo(Cargo cargo, String layerID, String slatSide, Map<int, Offset> coordinates){

    occupiedCargoPoints.putIfAbsent('$layerID-$slatSide', () => {});

    for (var coord in coordinates.values){
      if (!occupiedGridPoints[layerID]!.containsKey(coord)) {
        // no slat at this position
        continue;
      }
      var slat = slats[occupiedGridPoints[layerID]![coord]!]!;
      int position = slat.slatCoordinateToPosition[coord]!;
      int integerSlatSide = int.parse(layerMap[slat.layer]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
      slat.setPlaceholderHandle(position, integerSlatSide, cargo.name, 'CARGO');
      occupiedCargoPoints['$layerID-$slatSide']![coord] =  slat.id;
    }
    saveUndoState();
    notifyListeners();
  }

  void removeCargo(String slatID, String slatSide, Offset coordinate){

    var slat = slats[slatID]!;
    int integerSlatSide = int.parse(layerMap[slat.layer]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
    if (integerSlatSide == 2){
      if (slat.h2Handles[slat.slatCoordinateToPosition[coordinate]!]!['category'] == 'SEED'){
        removeSeed(slat.layer, slatSide, coordinate);
        return;
      }
      slat.h2Handles.remove(slat.slatCoordinateToPosition[coordinate]!);
    }
    else{
      if (slat.h5Handles[slat.slatCoordinateToPosition[coordinate]!]!['category'] == 'SEED'){
        removeSeed(slat.layer, slatSide, coordinate);
        return;
      }
      slat.h5Handles.remove(slat.slatCoordinateToPosition[coordinate]!);
    }
    occupiedCargoPoints['${slat.layer}-$slatSide']?.remove(coordinate);

    saveUndoState();
    notifyListeners();
  }

  void attachSeed(String layerID, String slatSide, Map<int, Offset> coordinates, BuildContext context){
    /// Adds a seed to the design.  This involves:
    /// 1) adding the appropriate handles to all involved slats,
    /// 2) adding blocks to the occupancy grids and
    /// 3) adding an entry to the seed roster that groups all the
    /// coordinates together (makes it easy to delete the seed in one go later).

    for (var coord in coordinates.values) {
      if (!occupiedGridPoints.containsKey(layerID) || !occupiedGridPoints[layerID]!.containsKey(coord)) {
        // no slat at this position - cannot place a seed without full occupancy of all handles
        return;
      }
    }

    Set<String> attachmentSlats = {};
    for (var coord in coordinates.values) {
      var slat = slats[occupiedGridPoints[layerID]![coord]!]!;
      attachmentSlats.add(slat.id);
    }
    if (attachmentSlats.length < 16){
      // not enough slats to place a seed - it's likely seed was placed in parallel to slats rather than at an angle
      showWarning(context, 'Invalid Seed Placement', 'A seed needs to anchor 16 slats to be able to properly initiate crisscross growth.  Rotate your seed and try again.');
      return;
    }

    occupiedCargoPoints.putIfAbsent('$layerID-$slatSide', () => {});

    int slatOccupiedLayerOrder = layerMap[layerID]?['order'] + (slatSide == 'top' ? 1 : -1);

    String occupiedLayer = '';
    if (layerNumberValid(slatOccupiedLayerOrder)){
      occupiedLayer = getLayerByOrder(slatOccupiedLayerOrder)!;
      occupiedGridPoints.putIfAbsent(occupiedLayer, () => {});
    }

    int index = 0;
    for (var coord in coordinates.values){

      int row = index ~/ 16 + 1; // Integer division to get row number
      int col = index % 16 + 1;  // Modulo to get column number

      var slat = slats[occupiedGridPoints[layerID]![coord]!]!;
      int position = slat.slatCoordinateToPosition[coord]!;
      int integerSlatSide = int.parse(layerMap[slat.layer]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
      slat.setPlaceholderHandle(position, integerSlatSide, '$nextSeedID-$row-$col', 'SEED');
      occupiedCargoPoints['$layerID-$slatSide']![coord] =  slat.id;

      // seed takes up space from the slat grid too, not just cargo
      if (occupiedLayer != '') {
        occupiedGridPoints[occupiedLayer]![coord] =  'SEED';
      }

      index += 1;
    }

    // assign a seed to the roster - each seed is uniquely identified by its layer, slat position and unique ID
    Map<int, Offset> convertedCoordinates = coordinates.map(
          (key, value) => MapEntry(key, convertCoordinateSpacetoRealSpace(value)),
    );

    Seed newSeed = Seed(ID: nextSeedID, coordinates: convertedCoordinates);
    nextSeedID = nextCapitalLetter(nextSeedID);

    seedRoster[(layerID, slatSide, coordinates[1]!)] = newSeed;

    saveUndoState();
    notifyListeners();
  }

  void removeSeed(String layerID, String slatSide, Offset coordinate){
    /// Removes a seed from the design.  This involves: 1) remove the handles from the related slats,
    /// 2) removing the blocks from the slat and cargo occupancy grids and 3)
    /// removing the seed and its related coordinates from the seed roster.
    var seedToRemove;
    for (var seed in seedRoster.entries){
      if (seed.value.coordinates.containsValue(convertCoordinateSpacetoRealSpace(coordinate)) && seed.key.$2 == slatSide){
        for (var coord in seed.value.coordinates.values){
          var convCoord = convertRealSpacetoCoordinateSpace(coord);
          var slat = slats[occupiedCargoPoints['$layerID-$slatSide']![convCoord]];

          int integerSlatSide = int.parse(layerMap[layerID]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
          if (integerSlatSide == 2){
            slat!.h2Handles.remove(slat.slatCoordinateToPosition[convCoord]!);
          }
          else{
            slat!.h5Handles.remove(slat.slatCoordinateToPosition[convCoord]!);
          }

          occupiedCargoPoints['$layerID-$slatSide']?.remove(convCoord);

          int slatOccupiedLayerOrder = layerMap[layerID]?['order'] + (slatSide == 'top' ? 1 : -1);

          if (layerNumberValid(slatOccupiedLayerOrder)){
            String occupiedLayer = getLayerByOrder(slatOccupiedLayerOrder)!;
            occupiedGridPoints[occupiedLayer]?.remove(convCoord);
          }

        }
        seedToRemove = seed.key;
      }
    }
    if (seedToRemove != null){
      seedRoster.remove(seedToRemove);
    }
    notifyListeners();
  }

  void importPlates() async{
    await importPlatesFromFile(plateStack);

    // TODO: if plate already exists, show warning dialog
    // TODO: how to handle identical wells
    notifyListeners();
  }

  void removePlate(String plateName) {
    plateStack.removePlate(plateName);
    notifyListeners();
  }
  void removeAllPlates(){
    plateStack.clear();
    notifyListeners();
  }

  void plateAssignAllHandles() {
    void assignHandleIfPresent(Slat slat, int posn, int side, Map<int, Map<String, dynamic>> handles) {

      if (!handles.containsKey(posn)) {
        if (plateStack.contains('FLAT', posn, side, 'BLANK')) {
          final data = plateStack.getOligoData('FLAT', posn, side, 'BLANK');
          slat.setHandle(
            posn,
            side,
            data['sequence'],
            data['well'],
            data['plateName'],
            'BLANK',
            'FLAT',
            data['concentration'],
          );
        }
        return;
      }

      final handle = handles[posn]!;
      final category = handle['category'];
      final originalValue = handle['value'];
      late final String lookupValue;

      if (category == 'SEED') {
        // Format the SEED value for lookup
        lookupValue = originalValue
            .replaceFirst(RegExp(r'^[^-]+-'), '')
            .replaceAll('-', '_');
      } else {
        lookupValue = originalValue;
      }

      if (plateStack.contains(category, posn, side, lookupValue)) {
        final data = plateStack.getOligoData(category, posn, side, lookupValue);
        slat.setHandle(
          posn,
          side,
          data['sequence'],
          data['well'],
          data['plateName'],
          originalValue,
          category,
          data['concentration'],
        );
      }
    }

    for (var slat in slats.values) {
      for (int posn = 1; posn < slat.maxLength + 1; posn++) {
        assignHandleIfPresent(slat, posn, 2, slat.h2Handles);
        assignHandleIfPresent(slat, posn, 5, slat.h5Handles);
      }
    }
    notifyListeners();
  }

}

/// State management for action mode and display settings
class ActionState extends ChangeNotifier {
  String slatMode;
  String cargoMode;
  bool displayAssemblyHandles;
  bool displayCargoHandles;
  bool displaySlatIDs;
  bool extendSlatTips;
  bool displaySeeds;
  bool displayGrid;
  bool drawingAids;
  bool slatNumbering;
  bool displayBorder;
  bool isolateSlatLayerView;
  bool evolveMode;
  bool isSideBarCollapsed;
  int panelMode;
  String cargoAttachMode;
  bool plateValidation;
  double splitScreenDividerWidth = 0.5; // 50% split by default
  bool threeJSViewerActive =  true; // default to true, can be toggled by the user

  Map<int, String> panelMap = {
    0: 'slats',
    1: 'assembly',
    2: 'cargo',
    3: 'settings',
  };

  Map<String, dynamic> echoExportSettings =  {
    'Reference Volume' : 75,
    'Reference Concentration' : 500,
  };

  ActionState({
    this.slatMode = 'Add',
    this.cargoMode = 'Add',
    this.displayAssemblyHandles = false,
    this.displayCargoHandles = true,
    this.displaySlatIDs = false,
    this.isolateSlatLayerView = false,
    this.evolveMode = false,
    this.isSideBarCollapsed = false,
    this.displaySeeds = true,
    this.displayBorder = true,
    this.displayGrid = true,
    this.drawingAids = false,
    this.slatNumbering = false,
    this.plateValidation=false,
    this.extendSlatTips = true,
    this.panelMode = 0,
    this.cargoAttachMode = 'top'
  });

  void updateEchoSetting(String setting, dynamic value){
    echoExportSettings[setting] = value;
    notifyListeners();
  }

  void updateSlatMode(String value) {
    slatMode = value;
    notifyListeners();
  }

  void updateCargoMode(String value) {
    cargoMode = value;
    notifyListeners();
  }

  void setPanelMode(int value) {
    panelMode = value;
    notifyListeners();
  }

  void setSideBarStatus(bool status){
    isSideBarCollapsed = status;
    notifyListeners();
  }

  void setSplitScreenDividerWidth(double value){
    splitScreenDividerWidth = value;
    notifyListeners();
  }

  void setAssemblyHandleDisplay(bool value){
    displayAssemblyHandles = value;
    notifyListeners();
  }

  void setSlatIDDisplay(bool value){
    displaySlatIDs = value;
    notifyListeners();
  }

  void setSeedDisplay(bool value){
    displaySeeds = value;
    notifyListeners();
  }
  void setGridDisplay(bool value){
    displayGrid = value;
    notifyListeners();
  }
  void setBorderDisplay(bool value){
    displayBorder = value;
    notifyListeners();
  }

  void setThreeJSViewerActive(bool value){
    threeJSViewerActive = value;
    notifyListeners();
  }

  void setDrawingAidsDisplay(bool value){
    drawingAids = value;
    notifyListeners();
  }

  void setExtendSlatTips(bool value){
    extendSlatTips = value;
    notifyListeners();
  }

  void setSlatNumberingDisplay(bool value){
    slatNumbering = value;
    notifyListeners();
  }

  void setCargoHandleDisplay(bool value){
    displayCargoHandles = value;
    notifyListeners();
  }

  void setPlateValidation(bool value){
    plateValidation = value;
    notifyListeners();
  }

  void setIsolateSlatLayerView(bool value){
    isolateSlatLayerView = value;
    notifyListeners();
  }

  void activateEvolveMode(){
    evolveMode = true;
    notifyListeners();
  }

  void deactivateEvolveMode(){
    evolveMode = false;
    notifyListeners();
  }

  void updateCargoAttachMode(String value){
    cargoAttachMode = value;
    notifyListeners();
  }
}

/// State management for communicating with python server
class ServerState extends ChangeNotifier {

  CrisscrossClient? hammingClient;
  HealthClient? healthClient;

  int serverPort = 50055;

  bool serverActive = false;
  bool serverCheckInProgress = false;

  List<double> hammingMetrics = [];
  List<double> physicsMetrics = [];

  Map<String, String> evoParams = {
    'mutation_rate': '5',
    'mutation_type_probabilities': '0.425, 0.425, 0.15',
    'evolution_generations': '200',
    'evolution_population': '30',
    'process_count': 'DEFAULT',
    'generational_survivors': '3',
    'random_seed': '8',
    'unique_handle_sequences': '64',
    'early_max_valency_stop': '1',
    'split_sequence_handles': 'true'
  };

  // Human-readable labels for UI display
  final Map<String, String> paramLabels = {
    'mutation_rate': 'Mutation Rate',
    'mutation_type_probabilities': 'Mutation Probabilities',
    'evolution_generations': 'Max Generations',
    'evolution_population': 'Evolution Population',
    'process_count': 'Number of Threads',
    'generational_survivors': 'Generational Survivors',
    'random_seed': 'Random Seed',
    'number_unique_handles': 'Unique Handle Count',
    'split_sequence_handles': 'Split Sequence Handles',
    'early_max_valency_stop': 'Early Stop Target'
  };

  bool evoActive = false;
  String statusIndicator = 'BACKEND INACTIVE';

  ServerState();

  void evolveAssemblyHandles(List<List<List<int>>> slatArray, List<List<List<int>>> handleArray, Map<String, String> slatTypes, String connectionAngle) {
    hammingClient?.initiateEvolve(slatArray, handleArray, evoParams, slatTypes, connectionAngle);
    evoActive = true;
    statusIndicator = 'RUNNING';
    notifyListeners();
  }

  void exportParameters(){
    exportEvolutionParameters(evoParams);
  }

  void pauseEvolve(){
    hammingClient?.pauseEvolve();
    evoActive = false;
    statusIndicator = 'PAUSED';
    notifyListeners();
  }

  void exportRequest(String folderPath){
    hammingClient?.requestExport(folderPath);
  }

  Future<List<List<List<int>>>> stopEvolve(){
    evoActive = false;
    Future<List<List<List<int>>>> finalArray = hammingClient!.stopEvolve();
    hammingMetrics = [];
    physicsMetrics = [];
    statusIndicator = 'IDLE';
    notifyListeners();
    return finalArray;
  }

  void updateEvoParam(String parameter, String value){
    evoParams[parameter] = value;
    notifyListeners();
  }

  void launchClients(int port){
    serverPort = port;
    if (!kIsWeb) {
      hammingClient = CrisscrossClient(serverPort);
      healthClient = HealthClient(ClientChannel('127.0.0.1',
          port: serverPort,
          options:
          const ChannelOptions(credentials: ChannelCredentials.insecure())));

      hammingClient?.updates.listen((update) {
        hammingMetrics.add(update.hamming);
        physicsMetrics.add(update.physics);
        if(update.isComplete){
          statusIndicator = 'EVOLUTION COMPLETE - SAVE RESULTS!';
          evoActive = false;
        }
        notifyListeners(); // Notify UI elements
      });
    }
    notifyListeners();
  }

  @override
  void dispose() {
    if (!kIsWeb) {
      hammingClient?.shutdown();
    }// Clean up resources
    super.dispose();
  }

  // TODO: also implement health checks before sending a direct request to the server...
  Future<void> startupServerHealthCheck() async {

    if (serverCheckInProgress) return; // Prevent starting the check again
    serverCheckInProgress = true;

    while (healthClient == null){
      await Future.delayed(const Duration(seconds: 1));
    }

    var request = HealthCheckRequest();
    while (true) {
      try {
        var r = await healthClient?.check(request);
        if (r?.status == HealthCheckResponse_ServingStatus.SERVING) {
          statusIndicator = 'IDLE';
          serverActive = true;
          break;
        } else {
          serverActive = false;
        }
      } catch (_) {
        serverActive = false;
        await Future.delayed(const Duration(milliseconds: 500));
      }
    }
  }
}