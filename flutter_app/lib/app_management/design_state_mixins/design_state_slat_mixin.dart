import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';

/// Mixin containing slat CRUD operations for DesignState
mixin DesignStateSlatMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;

  Map<String, Map<String, dynamic>> get layerMap;

  Map<String, Map<Offset, String>> get occupiedGridPoints;

  Map<String, Map<Offset, String>> get occupiedCargoPoints;

  Map<String, Map<int, String>> get phantomMap;

  List<String> get selectedSlats;

  set selectedSlats(List<String> value);

  List<Offset> get selectedHandlePositions;

  set selectedHandlePositions(List<Offset> value);

  String get slatAdditionType;

  set slatAdditionType(String value);

  int get slatAddCount;

  set slatAddCount(int value);

  bool get hammingValueValid;

  set hammingValueValid(bool value);

  // Methods from other mixins
  void saveUndoState();

  // Methods from seed mixin
  (String, String, Offset)? isHandlePartOfActiveSeed(String layerID, String slatSide, Offset coordinate);

  void dissolveSeed((String, String, Offset) seedKey, {bool skipStateUpdate = false});

  void checkAndReinstateSeeds(String layerID, String slatSide, {bool skipStateUpdate = false});

  bool layerNumberValid(int layerOrder);

  String? getLayerByOrder(int order);

  void clearSelection();

  void setSlatAdditionType(String type) {
    slatAdditionType = type;
    notifyListeners();
  }

  void addSlats(String layer, Map<int, Map<int, Offset>> slatCoordinates) {
    /// Adds slats to the design
    for (var slat in slatCoordinates.entries) {
      slats['$layer-I${layerMap[layer]?["next_slat_id"]}'] = Slat(
          layerMap[layer]?["next_slat_id"], '$layer-I${layerMap[layer]?["next_slat_id"]}', layer, slat.value,
          slatType: slatAdditionType);
      // add the slat to the list by adding a map of all coordinate offsets to the slat ID
      occupiedGridPoints.putIfAbsent(layer, () => {});
      occupiedGridPoints[layer]
          ?.addAll({for (var offset in slat.value.values) offset: '$layer-I${layerMap[layer]?["next_slat_id"]}'});
      layerMap[layer]?["next_slat_id"] += 1;
      layerMap[layer]?["slat_count"] += 1;
    }
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void updateSlatPosition(String slatID, Map<int, Offset> slatCoordinates, {bool skipStateUpdate = false, requestFlip = false}) {
    /// Updates the position of a slat
    /// Uses three-phase approach to prevent data loss when movement paths overlap

    String layer = slatID.split('-')[0];

    // Track which seeds are affected by this move (for dissolution)
    Set<(String, String, Offset)> affectedSeeds = {};
    // Track sides with SEED category handles (for reinstatement check - must include dissolved seeds too)
    Set<String> sidesWithSeedHandles = {};

    // PHASE 1: Collect all cargo handle data before making any changes
    List<({Offset oldCoord, Offset newCoord, String occupancyID, String value, String category, String? seedOccupiedLayer})> handleOperations = [];

    for (var i = 0; i < slats[slatID]!.maxLength; i++) {
      for (var handleType in ['H5', 'H2']) {
        var handleDict = handleType == 'H5' ? slats[slatID]!.h5Handles : slats[slatID]!.h2Handles;
        if (handleDict[i + 1] != null && !handleDict[i + 1]!['category'].contains('ASSEMBLY')) {
          var topHelix = layerMap[layer]?['top_helix'];
          var occupancyID = topHelix == handleType ? 'top' : 'bottom';
          var oldCoord = slats[slatID]!.slatPositionToCoordinate[i + 1]!;
          var newCoord = slatCoordinates[i + 1]!;
          var category = handleDict[i + 1]!['category'];
          var value = handleDict[i + 1]!['value'];

          // Track sides with SEED handles for reinstatement check
          if (category == 'SEED') {
            sidesWithSeedHandles.add(occupancyID);
          }

          // Check if this handle belongs to an active seed
          var seedKey = isHandlePartOfActiveSeed(layer, occupancyID, oldCoord);
          if (seedKey != null) {
            affectedSeeds.add(seedKey);
          }

          // Determine seed-occupied layer if applicable
          String? seedOccupiedLayer;
          if (category == 'SEED') {
            int slatOccupiedLayerOrder = layerMap[layer]?['order'] + (occupancyID == 'top' ? 1 : -1);
            if (layerNumberValid(slatOccupiedLayerOrder)) {
              seedOccupiedLayer = getLayerByOrder(slatOccupiedLayerOrder);
            }
          }

          handleOperations.add((
            oldCoord: oldCoord,
            newCoord: newCoord,
            occupancyID: occupancyID,
            value: value,
            category: category,
            seedOccupiedLayer: seedOccupiedLayer,
          ));
        }
      }
    }

    // PHASE 2: Remove all old cargo entries
    for (var op in handleOperations) {
      occupiedCargoPoints['$layer-${op.occupancyID}']?.remove(op.oldCoord);
      if (op.seedOccupiedLayer != null) {
        occupiedGridPoints[op.seedOccupiedLayer]?.remove(op.oldCoord);
      }
    }

    // PHASE 3: Add all new cargo entries
    for (var op in handleOperations) {
      occupiedCargoPoints.putIfAbsent('$layer-${op.occupancyID}', () => {});
      occupiedCargoPoints['$layer-${op.occupancyID}']![op.newCoord] = op.value;
      if (op.seedOccupiedLayer != null) {
        occupiedGridPoints.putIfAbsent(op.seedOccupiedLayer!, () => {});
        occupiedGridPoints[op.seedOccupiedLayer]![op.newCoord] = 'SEED';
      }
    }

    // Update slat grid positions
    occupiedGridPoints[layer]?.removeWhere((key, value) => value == slatID);
    slats[slatID]?.updateCoordinates(slatCoordinates);
    occupiedGridPoints[layer]?.addAll({for (var offset in slatCoordinates.values) offset: slatID});

    if (requestFlip && slats[slatID]!.slatType == 'tube') {
      // double barrel flips are currently blocked
      slats[slatID]!.reverseDirection();
      if (phantomMap.containsKey(slatID)) {
        for (var phantomID in phantomMap[slatID]!.values) {
          slats[phantomID]!.reverseDirection();
        }
      }
    }

    // Dissolve any affected seeds
    for (var seedKey in affectedSeeds) {
      dissolveSeed(seedKey, skipStateUpdate: true);
    }

    // Check for seed reinstatement on sides that have SEED category handles
    for (var side in sidesWithSeedHandles) {
      checkAndReinstateSeeds(layer, side, skipStateUpdate: true);
    }

    if (skipStateUpdate) {
      return;
    }
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void updateMultiSlatPosition(List<String> slatIDs, List<Map<int, Offset>> allCoordinates,
      {bool requestFlip = false}) {
    /// Updates the position of multiple slats
    for (int i = 0; i < slatIDs.length; i++) {
      String slatID = slatIDs[i];
      Map<int, Offset> slatCoordinates = allCoordinates[i];
      updateSlatPosition(slatID, slatCoordinates, requestFlip: requestFlip, skipStateUpdate: true);
    }

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void removeSlat(String ID, {bool skipStateUpdate = false}) {
    /// Removes a slat from the design
    if (!skipStateUpdate) clearSelection();
    String layer = ID.split('-')[0];

    // Track affected seeds for dissolution
    Set<(String, String, Offset)> affectedSeeds = {};

    // Remove cargo/seed handles from occupancy maps
    for (var i = 0; i < slats[ID]!.maxLength; i++) {
      for (var handleType in ['H5', 'H2']) {
        var handleDict = handleType == 'H5' ? slats[ID]!.h5Handles : slats[ID]!.h2Handles;
        if (handleDict[i + 1] != null && !handleDict[i + 1]!['category'].contains('ASSEMBLY')) {
          var topHelix = layerMap[layer]?['top_helix'];
          var occupancyID = topHelix == handleType ? 'top' : 'bottom';
          var coord = slats[ID]!.slatPositionToCoordinate[i + 1]!;
          var category = handleDict[i + 1]!['category'];

          // Check if this handle belongs to an active seed
          var seedKey = isHandlePartOfActiveSeed(layer, occupancyID, coord);
          if (seedKey != null) {
            affectedSeeds.add(seedKey);
          }

          // Remove from cargo occupancy
          occupiedCargoPoints['$layer-$occupancyID']?.remove(coord);

          // For SEED category handles, also remove from the slat occupancy on the blocked layer
          if (category == 'SEED') {
            int slatOccupiedLayerOrder = layerMap[layer]?['order'] + (occupancyID == 'top' ? 1 : -1);
            if (layerNumberValid(slatOccupiedLayerOrder)) {
              String? seedOccupiedLayer = getLayerByOrder(slatOccupiedLayerOrder);
              if (seedOccupiedLayer != null) {
                occupiedGridPoints[seedOccupiedLayer]?.remove(coord);
              }
            }
          }
        }
      }
    }

    // Dissolve any affected seeds
    for (var seedKey in affectedSeeds) {
      dissolveSeed(seedKey, skipStateUpdate: true);
    }

    if (slats[ID]!.phantomParent == null) layerMap[layer]?["slat_count"] -= 1;

    // deleting the original slat should also delete all phantom slats associated with it
    if (phantomMap.containsKey(ID)) {
      for (var phantomID in phantomMap[ID]!.values) {
        removeSlat(phantomID, skipStateUpdate: true);
      }
      phantomMap.remove(ID);
    }

    // if a phantom slat is deleted and the phantom map is subsequently empty, the phantom map should be emptied
    if (slats[ID]!.phantomParent != null) {
      if (phantomMap[slats[ID]!.phantomParent]!.length == 1) {
        phantomMap.remove(slats[ID]!.phantomParent);
      }
    }

    slats.remove(ID);
    occupiedGridPoints[layer]?.removeWhere((key, value) => value == ID);

    if (skipStateUpdate) return;

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void removeSlats(List<String> IDs) {
    /// Remove multiple slats from the design
    if (IDs.isEmpty) return;

    clearSelection();
    for (var ID in IDs) {
      removeSlat(ID, skipStateUpdate: true);
    }

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void flipSlat(String ID) {
    /// Flips a slat's direction
    if (slats[ID]!.slatType == 'tube') {
      // double barrel flips are currently blocked
      slats[ID]!.reverseDirection();

      if (phantomMap.containsKey(ID)) {
        for (var phantomID in phantomMap[ID]!.values) {
          slats[phantomID]!.reverseDirection();
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }

  void flipSlats(List<String> IDs) {
    /// Flips multiple slats' direction
    for (var ID in IDs) {
      if (slats[ID]!.slatType == 'tube') {
        // double barrel flips are currently blocked
        slats[ID]!.reverseDirection();
        if (phantomMap.containsKey(ID)) {
          for (var phantomID in phantomMap[ID]!.values) {
            slats[phantomID]!.reverseDirection();
          }
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }

  void selectSlat(String ID, {bool addOnly = false}) {
    /// Selects or deselects a slat

    if (ID == 'SEED') return; // Prevent selecting 'SEED' as a slat ID

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

  void updateSlatAddCount(int value) {
    /// Updates the number of slats to be added with the next 'add' click
    slatAddCount = value;
    notifyListeners();
  }
}
