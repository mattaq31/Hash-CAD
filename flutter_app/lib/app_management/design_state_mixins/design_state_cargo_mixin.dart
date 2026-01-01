import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/cargo.dart';
import '../../crisscross_core/handle_utilities.dart';

/// Mixin containing cargo type management and cargo attachment operations for DesignState
mixin DesignStateCargoMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;

  Map<String, Map<String, dynamic>> get layerMap;

  Map<String, Map<Offset, String>> get occupiedGridPoints;

  Map<String, Map<Offset, String>> get occupiedCargoPoints;

  Map<String, Cargo> get cargoPalette;

  int get cargoAddCount;

  set cargoAddCount(int value);

  String? get cargoAdditionType;

  set cargoAdditionType(String? value);

  List<Offset> get selectedHandlePositions;

  set selectedHandlePositions(List<Offset> value);

  String get selectedLayerKey;

  // Methods from other mixins
  void saveUndoState();

  void setSlatHandle(Slat slat, int position, int side, String handlePayload, String category);

  void removeSeed(String layerID, String slatSide, Offset coordinate);

  void clearSelection();

  void addCargoType(Cargo cargo) {
    cargoPalette[cargo.name] = cargo;
    saveUndoState();
    notifyListeners();
  }

  void deleteCargoType(String cargoName) {
    // need to remove all cargo of this type from the slats and from the cargo occupancy map (otherwise will error out)
    for (var slat in slats.values) {
      for (var side in ['top', 'bottom']) {
        int slatSide = getSlatSideFromLayer(layerMap, slat.layer, side);
        var targetDict = getHandleDict(slat, slatSide);
        for (int position = 1; position <= slat.maxLength; position++) {
          if (targetDict[position] != null && targetDict[position]!['value'] == cargoName) {
            targetDict.remove(position); // TODO: also need to remove placeholder list - need to make a slat function...
            occupiedCargoPoints[generateLayerSideKey(slat.layer, side)]?.remove(slat.slatPositionToCoordinate[position]!);
          }
        }
      }
    }

    cargoPalette.remove(cargoName);
    cargoAdditionType = null;
    saveUndoState();
    notifyListeners();
  }

  Cargo getCargoFromCoordinate(Offset coordinate, String layerID, String slatSide) {
    String cargoName = occupiedCargoPoints[generateLayerSideKey(layerID, slatSide)]![coordinate]!;
    if (cargoName.contains('-')){
      cargoName = 'SEED';
    }
    return cargoPalette[cargoName]!;
  }

  void deleteAllCargo() {
    // need to remove all cargo of this type from the slats and from the cargo occupancy map (otherwise will error out)
    for (var slat in slats.values) {
      for (var side in ['top', 'bottom']) {
        int slatSide = getSlatSideFromLayer(layerMap, slat.layer, side);
        var targetDict = getHandleDict(slat, slatSide);
        for (int position = 1; position <= slat.maxLength; position++) {
          if (targetDict[position] != null && targetDict[position]!['category'] == 'CARGO') {
            targetDict.remove(position);
            occupiedCargoPoints[generateLayerSideKey(slat.layer, side)]?.remove(slat.slatPositionToCoordinate[position]!);
          }
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }

  // Methods from seed mixin
  (String, String, Offset)? isHandlePartOfActiveSeed(String layerID, String slatSide, Offset coordinate);

  void dissolveSeed((String, String, Offset) seedKey, {bool skipStateUpdate = false});

  void checkAndReinstateSeeds(String layerID, String slatSide, {bool skipStateUpdate = false});

  void removeSingleSeedHandle(String slatID, String slatSide, Offset coordinate, {bool skipStateUpdate = false});

  void moveCargo(Map<Offset, Offset> coordinateTransferMap, String layerID, String slatSide, {bool skipStateUpdate = false}) {
    int integerSlatSide = getSlatSideFromLayer(layerMap, layerID, slatSide);

    // Track which active seeds have handles being moved (for dissolution after move)
    Set<(String, String, Offset)> affectedSeeds = {};

    // Calculate the layer that seed handles block (above for 'top', below for 'bottom')
    int slatOccupiedLayerOrder = getAdjacentLayerOrder(layerMap, layerID, slatSide);
    String? seedOccupiedLayer;
    if (layerNumberValid(slatOccupiedLayerOrder)) {
      seedOccupiedLayer = getLayerByOrder(slatOccupiedLayerOrder);
      occupiedGridPoints.putIfAbsent(seedOccupiedLayer!, () => {});
    }

    // PHASE 1: Collect all cargo data before making any changes
    // This prevents issues when move paths overlap (e.g., A->B and B->C)
    List<({Offset fromCoord, Offset toCoord, Slat slatDonor, int donorPosition,
           Slat slatReceiver, int receiverPosition, String cargoName, String cargoCategory})> moveOperations = [];

    String layerSideKey = generateLayerSideKey(layerID, slatSide);

    for (var fromCoord in coordinateTransferMap.keys) {
      if (!occupiedCargoPoints[layerSideKey]!.containsKey(fromCoord)) {
        continue; // no cargo at this position
      }

      // Check if this handle belongs to an active seed
      var seedKey = isHandlePartOfActiveSeed(layerID, slatSide, fromCoord);
      if (seedKey != null) {
        affectedSeeds.add(seedKey);
      }

      // obtains information for the cargo at the 'from' coordinate
      var slatDonor = slats[occupiedGridPoints[layerID]![fromCoord]!]!;
      int donorPosition = slatDonor.slatCoordinateToPosition[fromCoord]!;
      var handleDict = getHandleDict(slatDonor, integerSlatSide);
      String cargoName = handleDict[donorPosition]!['value'];
      String cargoCategory = handleDict[donorPosition]!['category'];
      Offset toCoord = coordinateTransferMap[fromCoord]!;

      if (!occupiedGridPoints[layerID]!.containsKey(toCoord)) {
        continue; // no slat at this position
      }

      // no cargo placement can be made on phantom slats
      if (slats[occupiedGridPoints[layerID]![toCoord]!]!.phantomParent != null) {
        continue;
      }

      var slatReceiver = slats[occupiedGridPoints[layerID]![toCoord]!]!;
      int receiverPosition = slatReceiver.slatCoordinateToPosition[toCoord]!;

      moveOperations.add((
        fromCoord: fromCoord,
        toCoord: toCoord,
        slatDonor: slatDonor,
        donorPosition: donorPosition,
        slatReceiver: slatReceiver,
        receiverPosition: receiverPosition,
        cargoName: cargoName,
        cargoCategory: cargoCategory,
      ));
    }

    // PHASE 2: Remove all cargo from source positions
    for (var op in moveOperations) {
      var handleDict = getHandleDict(op.slatDonor, integerSlatSide);
      handleDict.remove(op.donorPosition);
      op.slatDonor.placeholderList.remove('handle-${op.donorPosition}-h$integerSlatSide');
      occupiedCargoPoints[layerSideKey]?.remove(op.fromCoord);

      // For SEED category handles, also remove from the slat occupancy on the blocked layer
      if (op.cargoCategory == 'SEED' && seedOccupiedLayer != null) {
        occupiedGridPoints[seedOccupiedLayer]?.remove(op.fromCoord);
      }
    }

    // PHASE 3: Add all cargo to destination positions
    for (var op in moveOperations) {
      setSlatHandle(op.slatReceiver, op.receiverPosition, integerSlatSide, op.cargoName, op.cargoCategory);
      occupiedCargoPoints[layerSideKey]![op.toCoord] = op.cargoName;

      // For SEED category handles, also update the slat occupancy on the blocked layer
      if (op.cargoCategory == 'SEED' && seedOccupiedLayer != null) {
        occupiedGridPoints[seedOccupiedLayer]![op.toCoord] = 'SEED';
      }
    }

    // Dissolve any affected seeds (they will be reinstated if handles reform the pattern)
    for (var seedKey in affectedSeeds) {
      dissolveSeed(seedKey, skipStateUpdate: true);
    }

    // Check if any isolated seed handles now form a valid seed pattern
    checkAndReinstateSeeds(layerID, slatSide, skipStateUpdate: true);

    if (skipStateUpdate) {
      return;
    }

    saveUndoState();
    notifyListeners();
  }

  void updateCargoAddCount(int value) {
    /// Updates the number of cargo to be added with the next 'add' click
    if (cargoAdditionType == 'SEED') {
      cargoAddCount = 1;
    } else {
      cargoAddCount = value;
    }
    notifyListeners();
  }

  void selectCargoType(String ID) {
    if (cargoAdditionType == ID) {
      cargoAdditionType = null;
    } else {
      cargoAdditionType = ID;
    }
    notifyListeners();
  }

  void selectHandle(Offset coordinate, {bool addOnly = false}) {
    /// Selects or deselects cargo handles
    if (selectedHandlePositions.contains(coordinate) && !addOnly) {
      selectedHandlePositions.remove(coordinate);
    } else {
      if (selectedHandlePositions.contains(coordinate)) {
        return;
      }
      selectedHandlePositions.add(coordinate);
    }
    notifyListeners();
  }

  void attachCargo(Cargo cargo, String layerID, String slatSide, Map<int, Offset> coordinates,
      {bool skipStateUpdate = false}) {
    String layerSideKey = generateLayerSideKey(layerID, slatSide);
    occupiedCargoPoints.putIfAbsent(layerSideKey, () => {});

    for (var coord in coordinates.values) {
      if (!occupiedGridPoints[layerID]!.containsKey(coord)) {
        // no slat at this position
        continue;
      }

      // no cargo placement can be made on phantom slats
      if (slats[occupiedGridPoints[layerID]![coord]!]!.phantomParent != null) {
        continue;
      }

      var slat = slats[occupiedGridPoints[layerID]![coord]!]!;
      int position = slat.slatCoordinateToPosition[coord]!;
      int integerSlatSide = getSlatSideFromLayer(layerMap, slat.layer, slatSide);
      setSlatHandle(slat, position, integerSlatSide, cargo.name, 'CARGO');
      occupiedCargoPoints[layerSideKey]![coord] = cargo.name;
    }

    if (skipStateUpdate) {
      return;
    }

    saveUndoState();
    notifyListeners();
  }

  void removeCargo(String slatID, String slatSide, Offset coordinate, {bool skipStateUpdate = false}) {
    // TODO: needs a phantom check and link to recursive algorithm
    var slat = slats[slatID]!;
    int integerSlatSide = getSlatSideFromLayer(layerMap, slat.layer, slatSide);
    var handleDict = getHandleDict(slat, integerSlatSide);
    int position = slat.slatCoordinateToPosition[coordinate]!;

    if (handleDict[position]!['category'] == 'SEED') {
      removeSeed(slat.layer, slatSide, coordinate);
      return;
    }
    handleDict.remove(position);
    occupiedCargoPoints[generateLayerSideKey(slat.layer, slatSide)]?.remove(coordinate);

    if (skipStateUpdate) {
      return;
    }

    saveUndoState();
    notifyListeners();
  }

  bool layerNumberValid(int layerOrder);

  String? getLayerByOrder(int order);

  void removeSelectedCargo(String slatSide) {
    // TODO: needs a phantom check and link to recursive algorithm
    String layerID = selectedLayerKey;

    if (selectedHandlePositions.isEmpty) {
      return;
    }
    List<Offset> selectedCoordsCopy = List.from(selectedHandlePositions);
    clearSelection();

    // First, dissolve any active seeds that have handles in the selection
    // This prevents removeSeed from deleting unselected handles
    Set<(String, String, Offset)> seedsToDissolve = {};
    for (var coordinate in selectedCoordsCopy) {
      var seedKey = isHandlePartOfActiveSeed(layerID, slatSide, coordinate);
      if (seedKey != null) {
        seedsToDissolve.add(seedKey);
      }
    }

    for (var seedKey in seedsToDissolve) {
      dissolveSeed(seedKey, skipStateUpdate: true);
    }

    // Now remove each selected handle individually
    for (var coordinate in selectedCoordsCopy) {
      var slatID = occupiedGridPoints[layerID]?[coordinate];
      if (slatID == null) continue; // Handle may have been removed

      var slat = slats[slatID];
      if (slat == null) continue;

      int? position = slat.slatCoordinateToPosition[coordinate];
      if (position == null) continue;

      int integerSlatSide = getSlatSideFromLayer(layerMap, layerID, slatSide);
      var handleDict = getHandleDict(slat, integerSlatSide);

      if (handleDict[position] == null) continue; // Handle already removed

      if (handleDict[position]!['category'] == 'SEED') {
        // Use removeSingleSeedHandle for seed handles (seed already dissolved above)
        removeSingleSeedHandle(slatID, slatSide, coordinate, skipStateUpdate: true);
      } else {
        // Regular cargo
        removeCargo(slatID, slatSide, coordinate, skipStateUpdate: true);
      }
    }

    saveUndoState();
    notifyListeners();
  }
}
