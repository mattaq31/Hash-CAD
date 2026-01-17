import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import 'design_state_contract.dart';

/// Mixin containing slat CRUD operations for DesignState
mixin DesignStateSlatMixin on ChangeNotifier, DesignStateContract {

  @override
  void setSlatAdditionType(String type) {
    slatAdditionType = type;
    notifyListeners();
  }

  /// Adds slats to the design
  @override
  void addSlats(String layer, Map<int, Map<int, Offset>> slatCoordinates) {
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

  /// Updates the position of a slat
  /// Uses three-phase approach to prevent data loss when movement paths overlap
  @override
  void updateSlatPosition(String slatID, Map<int, Offset> slatCoordinates, {bool skipStateUpdate = false, requestFlip = false}) {
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

  /// Updates the position of multiple slats
  @override
  void updateMultiSlatPosition(List<String> slatIDs, List<Map<int, Offset>> allCoordinates,
      {bool requestFlip = false}) {
    for (int i = 0; i < slatIDs.length; i++) {
      String slatID = slatIDs[i];
      Map<int, Offset> slatCoordinates = allCoordinates[i];
      updateSlatPosition(slatID, slatCoordinates, requestFlip: requestFlip, skipStateUpdate: true);
    }

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  /// Removes a slat from the design
  @override
  void removeSlat(String ID, {bool skipStateUpdate = false}) {
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

    // Clean up link manager entries for this slat
    assemblyLinkManager.removeAllEntriesForSlat(ID);

    if (slats[ID]!.phantomParent == null) layerMap[layer]?["slat_count"] -= 1;

    // deleting the original slat should also delete all phantom slats associated with it
    if (phantomMap.containsKey(ID)) {
      List<String> phantomIDs = phantomMap[ID]!.values.toList(); // create a copy to avoid modification during iteration
      for (var phantomID in phantomIDs) {
        removeSlat(phantomID, skipStateUpdate: true);
      }
      phantomMap.remove(ID);
    }

    if (slats[ID]!.phantomParent != null) {
      // remove phantomID from phantom map
      int phantomKey = int.parse(ID.split('-P')[1]);
      phantomMap[slats[ID]!.phantomParent!]!.remove(phantomKey);
      // if a phantom slat is deleted and the phantom map is subsequently empty, the phantom map should be emptied
      if (phantomMap[slats[ID]!.phantomParent]!.isEmpty) {
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

  /// Remove multiple slats from the design
  @override
  void removeSlats(List<String> IDs) {
    if (IDs.isEmpty) return;

    clearSelection();
    for (var ID in IDs) {
      removeSlat(ID, skipStateUpdate: true);
    }

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  /// Flips a slat's direction
  @override
  void flipSlat(String ID) {
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

  /// Flips multiple slats' direction
  @override
  void flipSlats(List<String> IDs) {
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

  @override
  /// Selects or deselects a slat
  void selectSlat(String ID, {bool addOnly = false}) {
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

  /// Updates the number of slats to be added with the next 'add' click
  @override
  void updateSlatAddCount(int value) {
    slatAddCount = value;
    notifyListeners();
  }
}
