import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/seed.dart';
import '../../crisscross_core/handle_utilities.dart';
import '../../main_windows/alert_window.dart';
import '../shared_app_state.dart';

/// Mixin containing layer management operations for DesignState
mixin DesignStateLayerMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;

  Map<String, Map<String, dynamic>> get layerMap;

  Map<String, Map<Offset, String>> get occupiedGridPoints;

  Map<String, Map<Offset, String>> get occupiedCargoPoints;

  Map<(String, String, Offset), Seed> get seedRoster;

  List<String> get colorPalette;

  String get selectedLayerKey;

  set selectedLayerKey(String value);

  List<String> get selectedSlats;

  set selectedSlats(List<String> value);

  List<Offset> get selectedHandlePositions;

  set selectedHandlePositions(List<Offset> value);

  String get nextLayerKey;

  set nextLayerKey(String value);

  int get nextColorIndex;

  set nextColorIndex(int value);

  Map<(String, int), Offset> get multiSlatGenerators;

  set multiSlatGenerators(Map<(String, int), Offset> value);

  Map<(String, int), Offset> get multiSlatGeneratorsAlternate;

  set multiSlatGeneratorsAlternate(Map<(String, int), Offset> value);

  bool get standardTilt;

  set standardTilt(bool value);

  String get slatAddDirection;

  set slatAddDirection(String value);

  String get gridMode;

  // Methods from other mixins
  void saveUndoState();

  bool layerNumberValid(int layerOrder);

  String? getLayerByOrder(int order);

  /// Gets the layer ID for an adjacent layer (above for 'top', below for 'bottom'),
  /// or null if out of bounds.
  String? getAdjacentLayer(String layerID, String slatSide) {
    int adjacentOrder = getAdjacentLayerOrder(layerMap, layerID, slatSide);
    if (!layerNumberValid(adjacentOrder)) return null;
    return getLayerByOrder(adjacentOrder);
  }

  String flipSlatSide(String side);

  Offset convertRealSpacetoCoordinateSpace(Offset inputPosition);

  void updateActiveLayer(String value) {
    /// Updates the active layer
    selectedLayerKey = value;
    clearSelection();
    notifyListeners();
  }

  void cycleActiveLayer(bool upDirection) {
    /// Cycles through the layer list and sets the selected layer (either up or down)
    if (upDirection) {
      selectedLayerKey = layerMap.keys
          .firstWhere((key) => layerMap[key]!['order'] == (layerMap[selectedLayerKey]!['order'] + 1) % layerMap.length);
    } else {
      selectedLayerKey = layerMap.keys.firstWhere((key) =>
          layerMap[key]!['order'] == (layerMap[selectedLayerKey]!['order'] - 1 + layerMap.length) % layerMap.length);
    }
    clearSelection();
    notifyListeners();
  }

  void updateLayerColor(String layer, Color color) {
    /// Updates the color of a layer
    layerMap[layer] = {
      ...?layerMap[layer],
      "color": color,
    };
    notifyListeners();
  }

  void clearSelection() {
    /// Clears all selections
    selectedSlats = [];
    selectedHandlePositions = [];
    notifyListeners();
  }

  void rotateLayerDirection(String layerKey) {
    /// Rotates the direction of a layer through all available directions
    if (gridMode == '90') {
      if (layerMap[layerKey]?['direction'] == 90) {
        layerMap[layerKey]?['direction'] = 180;
      } else {
        layerMap[layerKey]?['direction'] = 90;
      }
      layerMap[layerKey]?['DBDirection'] += 90; // fully rotates around the entire range of possible angles
    } else if (gridMode == '60') {
      if (layerMap[layerKey]?['direction'] == 180) {
        layerMap[layerKey]?['direction'] = 120;
      } else if (layerMap[layerKey]?['direction'] == 120) {
        layerMap[layerKey]?['direction'] = 240;
      } else {
        layerMap[layerKey]?['direction'] = 180;
      }
      layerMap[layerKey]?['DBDirection'] += 60; // fully rotates around the entire range of possible angles
    } else {
      throw Exception('Invalid grid mode: $gridMode');
    }

    if (layerMap[layerKey]?['DBDirection'] == 360) {
      layerMap[layerKey]?['DBDirection'] = 0;
    }
    notifyListeners();
  }

  void flipLayer(String layer, BuildContext context) {
    /// flips the H2-H5 direction of a layer

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
            if (occupiedGridPoints[candidateSeedOccupancyLayer]!
                .containsKey(convertRealSpacetoCoordinateSpace(coord))) {
              flipValid = false;
              break;
            }
          }
        }
        // if operation invalid, show dialog box and cancel operation
        if (!flipValid) {
          showWarning(context, 'Invalid Flip Operation',
              'Cannot flip the layer because this would result in a seed colliding with slats in the layer above/below its current position.');
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
    String topKey = generateLayerSideKey(layer, 'top');
    String bottomKey = generateLayerSideKey(layer, 'bottom');
    occupiedCargoPoints.putIfAbsent(topKey, () => {});
    occupiedCargoPoints.putIfAbsent(bottomKey, () => {});

    var temp = occupiedCargoPoints[topKey]!;
    occupiedCargoPoints[topKey] = occupiedCargoPoints[bottomKey]!;
    occupiedCargoPoints[bottomKey] = temp;

    // apply slat and seed occupancy map changes
    if (seedKeysToFlip.isNotEmpty) {
      // seed could either move above or below current layer
      List<int> potentialSeedLayers = [layerMap[layer]?['order'] + 1, layerMap[layer]?['order'] - 1];

      // first, clear the positions of all previous seeds in the layer
      for (int layerPos in potentialSeedLayers) {
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
          for (var coord in seedRoster[(key.$1, newSide, key.$3)]!.coordinates.values) {
            occupiedGridPoints[newLayer]![convertRealSpacetoCoordinateSpace(coord)] = 'SEED';
          }
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }

  void flipLayerVisibility(String layer) {
    /// Changes the visibility of a layer on the 2D grid
    layerMap[layer]?['hidden'] = !layerMap[layer]?['hidden'];
    notifyListeners();
  }

  void flipMultiSlatGenerator() {
    /// Multi-slat generation can be flipped to achieve different placement systems
    Map<(String, int), Offset> settingsTransfer = Map.from(multiSlatGenerators);
    multiSlatGenerators = Map.from(multiSlatGeneratorsAlternate);
    multiSlatGeneratorsAlternate = settingsTransfer;
    standardTilt = !standardTilt;
    notifyListeners();
  }

  void flipSlatAddDirection() {
    /// Slat placement can be flipped to adjust the positions of handles
    if (slatAddDirection == 'down') {
      slatAddDirection = 'up';
    } else {
      slatAddDirection = 'down';
    }
    notifyListeners();
  }

  void deleteLayer(String layer) {
    /// Deletes a layer from the design entirely
    if (!layerMap.containsKey(layer)) {
      return; // Ensure the layer exists before deleting
    }

    layerMap.remove(layer); // Remove the layer

    // Sort the remaining keys based on their current 'order' values
    final sortedKeys = layerMap.keys.toList()..sort((a, b) => layerMap[a]!['order'].compareTo(layerMap[b]!['order']));

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

  void reOrderLayers(List<String> newOrder, BuildContext context) {
    /// Reorders the positions of the layers based on a new order

    // since layers have moved, seed occupancy map needs to be updated, and potentially move should be cancelled if a clash can occur

    // first, create a fake new layer map
    var fakeLayerMap = {for (var entry in layerMap.entries) entry.key: Map<String, dynamic>.from(entry.value)};

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
        String previousSeedOccupancyLayer =
            layerNumberValid(previousSeedLayerNumber) ? getLayerByOrder(previousSeedLayerNumber)! : '';

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
      if (!moveValid) {
        showWarning(context, "Invalid Layer Move Operation",
            "Cannot move the layer because this would result in a seed colliding with slats in the layer above/below the layer's new position.");
        return;
      }
    }

    // if move is valid, proceed with the operation
    for (int i = 0; i < newOrder.length; i++) {
      layerMap[newOrder[i]]!['order'] = i; // Assign new order values
    }

    // apply slat occupancy map changes

    // first, clear the positions of all previous seeds
    for (var layerID in layerMap.keys) {
      occupiedGridPoints[layerID]?.removeWhere((key, value) => value == 'SEED');
    }

    // next, apply the new seed positions in both seed and slat occupancy maps
    for (var seed in seedRoster.entries) {
      int newSeedLayerNumber = layerMap[seed.key.$1]?['order'] + (seed.key.$2 == 'top' ? 1 : -1);

      // apply the new seed to the slat occupancy map
      if (layerNumberValid(newSeedLayerNumber)) {
        String newLayer = getLayerByOrder(newSeedLayerNumber)!;
        for (var coord in seed.value.coordinates.values) {
          occupiedGridPoints[newLayer]![convertRealSpacetoCoordinateSpace(coord)] = 'SEED';
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }

  void addLayer() {
    /// Adds an entirely new layer to the design
    layerMap[nextLayerKey] = {
      "direction": layerMap.values.last['direction'],
      "DBDirection": layerMap.values.last['direction'], // temporary alternative drawing system
      'next_slat_id': 1,
      'slat_count': 0,
      'top_helix': 'H5',
      'bottom_helix': 'H2',
      'order': layerMap.length,
      "color": Color(int.parse('0xFF${colorPalette[nextColorIndex].substring(1)}')),
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
        if (layer == nextLayerKey) {
          for (var coord in seed.value.coordinates.values) {
            occupiedGridPoints[layer]![convertRealSpacetoCoordinateSpace(coord)] = 'SEED';
          }
        }
      }
    }

    nextLayerKey = nextCapitalLetter(nextLayerKey);
    saveUndoState();
    notifyListeners();
  }
}
