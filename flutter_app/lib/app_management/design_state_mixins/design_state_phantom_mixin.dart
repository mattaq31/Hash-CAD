import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/common_utilities.dart';
import '../shared_app_state.dart';
import 'design_state_handle_link_mixin.dart';

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

  void clearSelection();
  void removeSlat(String ID, {bool skipStateUpdate = false});

  HandleLinkManager get assemblyLinkManager;

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
      removeSlat(phantomID, skipStateUpdate: true);
    }

    phantomMap.clear();

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  void clearPhantomSlatSelection() {
    // clears selection of phantom slats
    List<String> phantomSlatIDs = [];
    for (var slatID in phantomMap.keys) {
      if (!selectedSlats.contains(slatID)) continue;
      phantomSlatIDs.addAll(phantomMap[slatID]!.values);
    }
    for (var phantomID in phantomSlatIDs) {
      removeSlat(phantomID, skipStateUpdate: true);
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

  bool selectionInvolvesPhantoms() {
    bool hasPhantoms = false;

    for (var slatID in selectedSlats) {
      if (slats[slatID]!.phantomParent != null) {
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

  void unLinkSelectedPhantoms() {
    // Removes phantom slats and replaces them with normal slats with linked handles (linked to the reference)

    // Step 1: gather phantom slats in selection
    List<String> phantomSlatIDs = [];
    List<String> refSlatIDs = [];
    for (var slatID in selectedSlats) {
      if(slats[slatID]!.phantomParent == null) continue;
      phantomSlatIDs.add(slatID);
      refSlatIDs.add(slats[slatID]!.phantomParent!);
    }

    if (phantomSlatIDs.isEmpty) return;

    // Step 2 & 3: for each phantom slat, create a new independent slat with a new ID
    for (var phantomID in phantomSlatIDs) {
      Slat phantomSlat = slats[phantomID]!;
      String layer = phantomSlat.layer;
      String refSlatID = phantomSlat.phantomParent!;

      // Get new ID from layer's slat pool
      int newNumericID = layerMap[layer]!['next_slat_id'];
      String newSlatID = '$layer-I$newNumericID';

      // Create new slat without phantom parent
      Slat newSlat = Slat(
        newNumericID,
        newSlatID,
        layer,
        Map.from(phantomSlat.slatPositionToCoordinate),
        maxLength: phantomSlat.maxLength,
        uniqueColor: phantomSlat.uniqueColor,
        slatType: phantomSlat.slatType,
      );
      newSlat.copyHandlesFromSlat(phantomSlat);

      // Add new slat to collection
      slats[newSlatID] = newSlat;

      // Update layer slat tracking
      layerMap[layer]!['next_slat_id'] += 1;
      layerMap[layer]!['slat_count'] += 1;

      // Update occupiedGridPoints to point to new slat ID
      for (var coord in newSlat.slatPositionToCoordinate.values) {
        occupiedGridPoints[layer]?[coord] = newSlatID;
      }

      // Remove old phantom slat
      slats.remove(phantomID);

      // Step 4: link all assembly handles between new slat and reference slat
      for (int pos = 1; pos <= newSlat.maxLength; pos++) {
        // Link H2 assembly handles
        if (newSlat.h2Handles[pos] != null && newSlat.h2Handles[pos]!['category']?.contains('ASSEMBLY') == true) {
          HandleKey newKey = (newSlatID, pos, 2);
          HandleKey refKey = (refSlatID, pos, 2);
          assemblyLinkManager.addLink(newKey, refKey);
        }
        // Link H5 assembly handles
        if (newSlat.h5Handles[pos] != null && newSlat.h5Handles[pos]!['category']?.contains('ASSEMBLY') == true) {
          HandleKey newKey = (newSlatID, pos, 5);
          HandleKey refKey = (refSlatID, pos, 5);
          assemblyLinkManager.addLink(newKey, refKey);
        }
      }
    }

    // Clean up phantom map entries
    for (int i = 0; i < phantomSlatIDs.length; i++) {
      String phantomID = phantomSlatIDs[i];
      String parentID = refSlatIDs[i];
      // remove phantomID from phantom map
      int phantomKey = int.parse(phantomID.split('-P')[1]);
      phantomMap[parentID]!.remove(phantomKey);

      // if the map is now empty, remove the parentID entry as well
      if(phantomMap[parentID]!.isEmpty) {
        phantomMap.remove(parentID);
      }
    }

    // Step 5: save and notify listeners
    clearSelection();
    saveUndoState();
    notifyListeners();
  }

}
