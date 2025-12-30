import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../shared_app_state.dart';

/// Mixin containing phantom slat operations for DesignState
mixin DesignStatePhantomMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;

  Map<String, Map<String, dynamic>> get layerMap;

  Map<String, Map<Offset, String>> get occupiedGridPoints;

  Map<String, Map<int, String>> get phantomMap;

  List<String> get selectedSlats;

  String get selectedLayerKey;

  String get gridMode;

  bool get hammingValueValid;

  set hammingValueValid(bool value);

  // Methods from other mixins
  void saveUndoState();

  bool layerNumberValid(int layerOrder);

  String? getLayerByOrder(int order);

  void addPhantomSlats(String layer, Map<int, Map<int, Offset>> slatCoordinates, Map<int, Slat> referenceSlats) {
    /// Adds phantom slats (which are linked to real slats)
    for (var iterID in slatCoordinates.keys) {
      Slat slat = referenceSlats[iterID]!;
      Map<int, Offset> coords = slatCoordinates[iterID]!;

      // assigns a new key from the reference slat's phantom map
      if (!phantomMap.containsKey(slat.id)) phantomMap[slat.id] = {};
      int phantomKey = firstFreeKey(phantomMap[slat.id]!);

      // creates a new slat with a new ID, copies handles and then links it to the original slat via phantomID
      slats['${slat.id}-P$phantomKey'] = Slat(phantomKey, '${slat.id}-P$phantomKey', layer, coords,
          uniqueColor: slat.uniqueColor, slatType: slat.slatType, phantomParent: slat.id);
      slats['${slat.id}-P$phantomKey']!.copyHandlesFromSlat(slat);
      phantomMap[slat.id]![phantomKey] = '${slat.id}-P$phantomKey';

      // add the slat to the list by adding a map of all coordinate offsets to the slat ID
      occupiedGridPoints.putIfAbsent(layer, () => {});
      occupiedGridPoints[layer]?.addAll({for (var offset in coords.values) offset: '${slat.id}-P$phantomKey'});
    }

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void removeAllPhantomSlats() {
    // removes all phantom slats from the design
    List<String> phantomSlatIDs = [];
    for (var slatID in phantomMap.keys) {
      phantomSlatIDs.addAll(phantomMap[slatID]!.values);
    }
    for (var phantomID in phantomSlatIDs) {
      String layer = phantomID.split('-')[0];
      slats.remove(phantomID);
      occupiedGridPoints[layer]?.removeWhere((key, value) => value == phantomID);
    }
    phantomMap.clear();
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void clearPhantomSlatSelection() {
    // clears selection of phantom slats
    List<String> phantomSlatIDs = [];
    List<String> refSlatIDs = [];
    for (var slatID in phantomMap.keys) {
      if (!selectedSlats.contains(slatID)) continue;
      phantomSlatIDs.addAll(phantomMap[slatID]!.values);
      refSlatIDs.add(slatID);
    }
    for (var phantomID in phantomSlatIDs) {
      String layer = phantomID.split('-')[0];
      slats.remove(phantomID);
      occupiedGridPoints[layer]?.removeWhere((key, value) => value == phantomID);
    }
    for (var refID in refSlatIDs) {
      phantomMap.remove(refID);
    }
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  bool selectionHasPhantoms() {
    bool hasPhantoms = false;

    for (var slatID in selectedSlats) {
      if (phantomMap.containsKey(slatID)) {
        hasPhantoms = true;
        break;
      }
    }

    return hasPhantoms;
  }

  void spawnAndPlacePhantomSlats() {
    List<Offset> allCoordinates = [];
    for (var slatID in selectedSlats) {
      var slat = slats[slatID];
      allCoordinates.addAll(slat!.slatPositionToCoordinate.values);
    }

    // Phantom slats are spawned in next to the original slats, allowing a user
    // to place them wherever they like.  The below finds the best place to spawn them to

    // get layers to check - need to check current layer, layer above and layer below
    List<String> obstructionLayers = [selectedLayerKey];
    int layerOrder = layerMap[selectedLayerKey]!['order'];
    if (layerNumberValid(layerOrder + 1)) {
      occupiedGridPoints.putIfAbsent(getLayerByOrder(layerOrder + 1)!, () => {});
      obstructionLayers.add(getLayerByOrder(layerOrder + 1)!);
    }
    if (layerNumberValid(layerOrder - 1)) {
      occupiedGridPoints.putIfAbsent(getLayerByOrder(layerOrder - 1)!, () => {});
      obstructionLayers.add(getLayerByOrder(layerOrder - 1)!);
    }

    double magnitudeJump = gridMode == '90' ? 1 : 2;
    Offset finalOffset = Offset(0, 0);
    double bestDistance = double.infinity;

    // compute candidate positions in all 4 cardinal directions until a valid position is found
    for (Offset direction in [
      Offset(0, magnitudeJump),
      Offset(0, -magnitudeJump),
      Offset(magnitudeJump, 0),
      Offset(-magnitudeJump, 0)
    ]) {
      bool positionValid = false;
      Offset candidateOffset = Offset(0, 0);
      double iter = 1;
      List<Offset> testCoordinates = [];
      while (!positionValid) {
        candidateOffset = candidateOffset + direction * iter;
        // add the offset to all input coords
        testCoordinates = allCoordinates.map((e) => e + candidateOffset).toList();
        // check if any of the new coordinates clash with existing slats (same layer, below and top)
        positionValid = true;
        for (var coord in testCoordinates) {
          for (var layerID in obstructionLayers) {
            if (occupiedGridPoints[layerID]!.containsKey(coord)) {
              positionValid = false;
              break;
            }
          }
          if (!positionValid) {
            break;
          }
        }
      }
      // best candidate chosen based on center to center distance from reference slats
      double centerToCenterDistance = (calculateCenter(testCoordinates) - calculateCenter(allCoordinates)).distance;
      if (centerToCenterDistance < bestDistance) {
        bestDistance = centerToCenterDistance;
        finalOffset = candidateOffset;
      }
    }

    // now actually generate and place the phantom slats
    Map<int, Map<int, Offset>> phantomSlatCoordinates = {};
    Map<int, Slat> referenceSlats = {};
    int iter = 1;
    for (var slatID in selectedSlats) {
      var slat = slats[slatID];
      for (var position in slat!.slatPositionToCoordinate.keys) {
        phantomSlatCoordinates.putIfAbsent(iter, () => {});
        phantomSlatCoordinates[iter]![position] = slat.slatPositionToCoordinate[position]! + finalOffset;
      }
      referenceSlats[iter] = slat;
      iter += 1;
    }
    addPhantomSlats(selectedLayerKey, phantomSlatCoordinates, referenceSlats);
  }
}
