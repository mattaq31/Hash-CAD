import 'package:flutter/material.dart';
import '../crisscross_core/slats.dart';
import '../crisscross_core/sparse_to_array_conversion.dart';
import '../crisscross_core/assembly_handles.dart';
import 'file_io.dart';
import '../grpc_client_architecture/client_entry.dart';
import '../grpc_client_architecture/health.pbgrpc.dart';
import 'package:grpc/grpc.dart';
import 'package:flutter/foundation.dart';
import '../2d_painters/helper_functions.dart' as utils;
import 'slat_undo_stack.dart';
import 'dart:math';

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

/// State management for the design of the current megastructure
class DesignState extends ChangeNotifier {
  final double gridSize = 10.0; // do not change
  late final double y60Jump = gridSize / 2;
  late final double x60Jump = sqrt(pow(gridSize, 2) - pow(y60Jump, 2));
  String gridMode = '60';

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

  // good for distinguishing layers quickly, but user can change colours
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

  // to highlight on grid painter
  List<String> selectedSlats = [];

  // default values for new layers and slats
  String selectedLayerKey = 'A';
  String nextLayerKey = 'C';
  int nextColorIndex = 2;
  int slatAddCount = 1;
  int currentHamming = 0;
  bool hammingValueValid = true;

  // useful to keep track of occupancy and speed up grid checks
  Map<String, Map<Offset, String>> occupiedGridPoints = {};
  int minX = -1;
  int minY = -1;
  int maxX = 0;
  int maxY = 0;

  /// Adds slats to the design
  void addSlats(String layer, Map<int, Map<int, Offset>> slatCoordinates) {
    undoStack.saveState(slats, occupiedGridPoints);
    for (var slat in slatCoordinates.entries) {
      slats['$layer-I${layerMap[layer]?["next_slat_id"]}'] = Slat(layerMap[layer]?["next_slat_id"], '$layer-I${layerMap[layer]?["next_slat_id"]}',layer, slat.value);
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
    notifyListeners();
  }

  /// Updates the position of a slat
  void updateSlatPosition(String slatID, Map<int, Offset> slatCoordinates) {
    undoStack.saveState(slats, occupiedGridPoints);
    // also need to remove old positions from occupiedGridPoints and add new ones
    String layer = slatID.split('-')[0];

    occupiedGridPoints[layer]?.removeWhere((key, value) => value == slatID);

    slats[slatID]?.updateCoordinates(slatCoordinates);
    occupiedGridPoints[layer]?.addAll({for (var offset in slatCoordinates.values) offset: slatID});
    hammingValueValid = false;
    notifyListeners();
  }

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

  /// updates the grid type (60 or 90)
  void setGridMode(String value) {
    gridMode = value;
    clearAll();
    notifyListeners();
  }


  /// Updates the number of slats to be added with the next 'add' click
  void updateSlatAddCount(int value) {
    slatAddCount = value;
    notifyListeners();
  }

  /// Updates the color of a layer
  void updateColor(String layer, Color color) {
    layerMap[layer] = {
      ...?layerMap[layer],
      "color": color,
    };
    notifyListeners();
  }

  /// Removes a slat from the design
  void removeSlat(String ID) {
    undoStack.saveState(slats, occupiedGridPoints);
    clearSelection();
    String layer = ID.split('-')[0];
    slats.remove(ID);
    occupiedGridPoints[layer]?.removeWhere((key, value) => value == ID);
    layerMap[layer]?["slat_count"] -= 1;
    hammingValueValid = false;
    notifyListeners();
  }

  /// Selects or deselects a slat
  void selectSlat(String ID) {
    if (selectedSlats.contains(ID)) {
      selectedSlats.remove(ID);
    } else {
      selectedSlats.add(ID);
    }
    notifyListeners();
  }

  void undoSlatAction(){
    clearSelection();
    Map<String, dynamic>? previousState = undoStack.undo();
    if (previousState != null) {
      slats = previousState['slats'];
      occupiedGridPoints = previousState['occupiedGridPoints'];
      notifyListeners();
    }
  }

  /// Clears all selected slats
  void clearSelection() {
    selectedSlats = [];
    notifyListeners();
  }

  /// Rotates the direction of a layer from horizontal to vertical or vice versa
  void rotateLayerDirection(String layerKey) {
    if (gridMode == '90'){
      if (layerMap[layerKey]?['direction'] == 90) {
        layerMap[layerKey]?['direction'] = 180;
      } else {
        layerMap[layerKey]?['direction'] = 90;
      }
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
    }
    else{
      throw Exception('Invalid grid mode: $gridMode');
    }
    notifyListeners();
  }

  /// flips the H2-H5 direction of a layer (currently unused)
  void flipLayer(String layer) {
    if (layerMap[layer]?['top_helix'] == 'H5') {
      layerMap[layer]?['top_helix'] = 'H2';
      layerMap[layer]?['bottom_helix'] = 'H5';
    } else {
      layerMap[layer]?['top_helix'] = 'H5';
      layerMap[layer]?['bottom_helix'] = 'H2';
    }
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

    notifyListeners();
  }

  /// Reorders the positions of the layers based on a new order
  void reOrderLayers(List<String> newOrder) {
    for (int i = 0; i < newOrder.length; i++) {
      layerMap[newOrder[i]]!['order'] = i; // Assign new order values
    }
    notifyListeners();
  }

  /// Adds an entirely new layer to the design
  void addLayer() {

    layerMap[nextLayerKey] = {
      "direction": layerMap.values.last['direction'],
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
    nextLayerKey = nextCapitalLetter(nextLayerKey);
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
            if (aLayer == layerMap[slat.layer]!['order']){
              slatSide = int.parse(layerMap[slat.layer]?['top_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
            }
            else{
              slatSide = int.parse(layerMap[slat.layer]?['bottom_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
            }
            slat.setPlaceholderHandle(i + 1, slatSide, '${handleArray[x][y][aLayer]}', 'Assembly');
          }
        }
      }
    }
  }

  void updateDesignHammingValue() {
    if (slats.isEmpty) {
      currentHamming = 0;
    } else {
      currentHamming = hammingCompute(slats, layerMap, 32);
      if (currentHamming == 50 || currentHamming == 32) { // 50 (calculation never attempted) or 32 (no handle overlap) are exception values
        currentHamming = 0;
      }
    }
    hammingValueValid = true;
    notifyListeners();
  }

  // TODO: assembly handles are still causing performance issues - it's probably the 3D system - need to investigate
  void generateRandomAssemblyHandles(int uniqueHandleCount, bool splitLayerHandles) {
    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);
    List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);
    List<List<List<int>>> handleArray;

    if (splitLayerHandles) {
      handleArray = generateLayerSplitHandles(slatArray, uniqueHandleCount,
          seed: DateTime.now().millisecondsSinceEpoch % 1000);
    } else {
      handleArray = generateRandomSlatHandles(slatArray, uniqueHandleCount,
          seed: DateTime.now().millisecondsSinceEpoch % 1000);
    }

    assignAssemblyHandleArray(handleArray, minPos, maxPos);
    notifyListeners();
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

  void cleanAllHandles(){
    /// Removes all handles from the slats
    /// TODO: PROBLEM WHEN SHIFTING SLAT LAYERS - ASSEMBLY HANDLES ARE CARRIED OVER!
    for (var slat in slats.values) {
      slat.clearAllHandles();
    }
    hammingValueValid = false;
    notifyListeners();
  }
  void exportCurrentDesign() async {
    /// Exports the current design to an excel file
    exportDesign(slats, layerMap, gridSize, gridMode);
  }

  void importNewDesign() async{

    var (newSlats, newLayerMap, newGridMode) = await importDesign();
    // check if the maps are empty
    if (newSlats.isEmpty || newLayerMap.isEmpty) {
      return;
    }
    clearAll();

    layerMap = newLayerMap;
    slats = newSlats;
    gridMode = newGridMode;

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
    updateDesignHammingValue();
    notifyListeners();
  }

  void clearAll() {
    slats = {};
    undoStack = SlatUndoStack();
    layerMap = {
      'A': {
        "direction": gridMode == '90' ? 90 : 120, // slat default direction
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
        'next_slat_id': 1,
        'top_helix': 'H5',
        'bottom_helix': 'H2',
        'order': 1,
        'slat_count': 0,
        "color": Color(int.parse('0xFFb80058')),
        "hidden": false
      },
    };
    selectedLayerKey = 'A';
    occupiedGridPoints = {};
    selectedSlats = [];
    nextLayerKey = 'C';
    nextColorIndex = 2;
    currentHamming = 0;
    hammingValueValid = true;
    notifyListeners();
  }

  Offset convertRealSpacetoCoordinateSpace(Offset inputPosition){
    return utils.convertRealSpacetoCoordinateSpace(inputPosition, gridMode, gridSize, x60Jump, y60Jump);
  }

  Offset convertCoordinateSpacetoRealSpace(Offset inputPosition){
    return utils.convertCoordinateSpacetoRealSpace(inputPosition, gridMode, gridSize, x60Jump, y60Jump);
  }
}

/// State management for action mode and display settings
class ActionState extends ChangeNotifier {
  String slatMode;
  bool displayAssemblyHandles;
  bool evolveMode;
  bool isSideBarCollapsed;
  int panelMode;


  ActionState({
    this.slatMode = 'Add',
    this.displayAssemblyHandles = false,
    this.evolveMode = false,
    this.isSideBarCollapsed = false,
    this.panelMode = 0,
  });

  Map<int, String> panelMap = {
    0: 'slats',
    1: 'assembly',
    2: 'cargo',
    3: 'settings',
  };

  void updateSlatMode(String value) {
    slatMode = value;
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

  void setAssemblyHandleDisplay(bool value){
    displayAssemblyHandles = value;
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
}

/// State management for communicating with python server
class ServerState extends ChangeNotifier {

  // TODO: client channel/port should be customizable
  CrisscrossClient? hammingClient;
  HealthClient? healthClient;

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
    'unique_handle_sequences': '32',
    'early_hamming_stop': '30',
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
  };

  bool evoActive = false;
  String statusIndicator = 'BACKEND INACTIVE';

  ServerState() {
    // Listen to updates from the client

    if (!kIsWeb) {
      hammingClient = CrisscrossClient();
      healthClient = HealthClient(ClientChannel('127.0.0.1',
          port: 50055,
          options:
          const ChannelOptions(credentials: ChannelCredentials.insecure())));

      hammingClient?.updates.listen((update) {
        hammingMetrics.add(update.hamming);
        physicsMetrics.add(update.physics);
        if(update.isComplete){
          statusIndicator = 'EVOLUTION COMPLETE - MAKE SURE TO SAVE RESULT';
          evoActive = false;
        }
        notifyListeners(); // Notify UI elements
      });
    }
  }

  void evolveAssemblyHandles(List<List<List<int>>> slatArray, List<List<List<int>>> handleArray) {
    hammingClient?.initiateEvolve(slatArray, handleArray, evoParams);
    evoActive = true;
    statusIndicator = 'RUNNING';
    notifyListeners();
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