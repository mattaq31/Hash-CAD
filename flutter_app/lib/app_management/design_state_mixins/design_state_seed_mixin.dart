import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/seed.dart';
import '../../main_windows/alert_window.dart';
import '../shared_app_state.dart';

/// Mixin containing seed attachment and removal operations for DesignState
mixin DesignStateSeedMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;

  Map<String, Map<String, dynamic>> get layerMap;

  Map<String, Map<Offset, String>> get occupiedGridPoints;

  Map<String, Map<Offset, String>> get occupiedCargoPoints;

  Map<(String, String, Offset), Seed> get seedRoster;

  String get nextSeedID;

  set nextSeedID(String value);

  // Methods from other mixins
  void saveUndoState();

  bool layerNumberValid(int layerOrder);

  String? getLayerByOrder(int order);

  Offset convertRealSpacetoCoordinateSpace(Offset inputPosition);

  Offset convertCoordinateSpacetoRealSpace(Offset inputPosition);

  void setSlatHandle(Slat slat, int position, int side, String handlePayload, String category);

  /// Checks if a coordinate belongs to an active seed in the roster.
  /// Returns the seed key (layerID, slatSide, firstCoordinate) if found, null otherwise.
  (String, String, Offset)? isHandlePartOfActiveSeed(String layerID, String slatSide, Offset coordinate) {
    Offset realSpaceCoord = convertCoordinateSpacetoRealSpace(coordinate);
    for (var seedEntry in seedRoster.entries) {
      if (seedEntry.key.$1 == layerID && seedEntry.key.$2 == slatSide) {
        // Check if this coordinate is part of this seed's coordinates
        if (seedEntry.value.coordinates.containsValue(realSpaceCoord)) {
          return seedEntry.key;
        }
      }
    }
    return null;
  }

  /// Returns all coordinate positions (in coordinate space) for a given seed.
  List<Offset> getAllSeedHandleCoordinates((String, String, Offset) seedKey) {
    if (!seedRoster.containsKey(seedKey)) return [];
    return seedRoster[seedKey]!.coordinates.values.map((coord) => convertRealSpacetoCoordinateSpace(coord)).toList();
  }

  /// Removes a seed from the roster but keeps handles as isolated seed handles.
  /// Handles retain their values (e.g., "A-1-1") and 'SEED' category.
  void dissolveSeed((String, String, Offset) seedKey, {bool skipStateUpdate = false}) {
    // Simply remove from seedRoster - handles remain on slats with their original values
    // The occupiedCargoPoints entries also remain unchanged
    seedRoster.remove(seedKey);

    if (skipStateUpdate) {
      return;
    }

    saveUndoState();
    notifyListeners();
  }

  void attachSeed(String layerID, String slatSide, Map<int, Offset> coordinates, BuildContext context) {
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

      if (slat.phantomParent != null) {
        // cannot place seeds on phantom slats
        showWarning(context, 'Invalid Seed Placement',
            'Seeds cannot be placed on phantom slats.  Please place the seed on the original slats instead.');
        return;
      }

      var slatID = slat.id;
      if (slat.slatType != 'tube') {
        slatID = slat.id + (slat.slatCoordinateToPosition[coord]! < 17 ? '-first-half' : 'second-half');
      } else {
        slatID = slat.id;
      }
      attachmentSlats.add(slatID);
    }

    if (attachmentSlats.length < 16) {
      // not enough slats to place a seed - it's likely seed was placed in parallel to slats rather than at an angle
      showWarning(context, 'Invalid Seed Placement',
          'A seed needs to anchor 16 slats to be able to properly initiate crisscross growth.  Rotate your seed and try again.');
      return;
    }

    occupiedCargoPoints.putIfAbsent('$layerID-$slatSide', () => {});

    int slatOccupiedLayerOrder = layerMap[layerID]?['order'] + (slatSide == 'top' ? 1 : -1);

    String occupiedLayer = '';
    if (layerNumberValid(slatOccupiedLayerOrder)) {
      occupiedLayer = getLayerByOrder(slatOccupiedLayerOrder)!;
      occupiedGridPoints.putIfAbsent(occupiedLayer, () => {});
    }

    int index = 0;
    for (var coord in coordinates.values) {
      int row = index ~/ 16 + 1; // Integer division to get row number
      int col = index % 16 + 1; // Modulo to get column number

      var slat = slats[occupiedGridPoints[layerID]![coord]!]!;
      int position = slat.slatCoordinateToPosition[coord]!;
      int integerSlatSide = int.parse(layerMap[slat.layer]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
      String seedHandleValue = '$nextSeedID-$row-$col';
      setSlatHandle(slat, position, integerSlatSide, seedHandleValue, 'SEED');

      occupiedCargoPoints['$layerID-$slatSide']![coord] = seedHandleValue;

      // seed takes up space from the slat grid too, not just cargo
      if (occupiedLayer != '') {
        occupiedGridPoints[occupiedLayer]![coord] = 'SEED';
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

  /// Scans for isolated seed handles that form a valid 5x16 pattern and reinstates them as seeds.
  /// Called after cargo movement to check if handles have reformed a seed.
  void checkAndReinstateSeeds(String layerID, String slatSide, {bool skipStateUpdate = false}) {
    int integerSlatSide = int.parse(layerMap[layerID]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));

    // Collect all SEED-category handles on this layer/side, grouped by seed ID
    // Each entry: seedID -> list of (coordinate, row, col)
    Map<String, List<(Offset, int, int)>> potentialSeeds = {};

    var cargoMap = occupiedCargoPoints['$layerID-$slatSide'];
    if (cargoMap == null) return;

    for (var entry in cargoMap.entries) {
      Offset coord = entry.key;

      // Skip if no slats or cargo at this position
      if (occupiedGridPoints[layerID] == null || !occupiedGridPoints[layerID]!.containsKey(coord)) continue;

      var slat = slats[occupiedGridPoints[layerID]![coord]!]!;

      // Skip handles on phantom slats - they cannot form reinstated seeds
      if (slat.phantomParent != null) continue;

      int position = slat.slatCoordinateToPosition[coord]!;
      var handleDict = integerSlatSide == 5 ? slat.h5Handles : slat.h2Handles;

      // Skip if no handle at this position or not a SEED category
      if (handleDict[position] == null) continue;
      if (handleDict[position]!['category'] != 'SEED') continue;

      String handleValue = handleDict[position]!['value'];

      // Parse seed handle format: "A-1-1" -> seedID="A", row=1, col=1
      var parts = handleValue.split('-');
      if (parts.length != 3) continue;

      String seedID = parts[0];
      int row = int.tryParse(parts[1]) ?? -1;
      int col = int.tryParse(parts[2]) ?? -1;

      if (row < 1 || row > 5 || col < 1 || col > 16) continue;

      // Skip if this seed ID is already in the roster on this layer/side
      bool alreadyInRoster = seedRoster.keys.any(
        (k) => seedRoster[k]!.ID == seedID && k.$1 == layerID && k.$2 == slatSide,
      );
      if (alreadyInRoster) continue;

      potentialSeeds.putIfAbsent(seedID, () => []);
      potentialSeeds[seedID]!.add((coord, row, col));
    }

    // Check each potential seed group for valid formation
    for (var entry in potentialSeeds.entries) {
      String seedID = entry.key;
      List<(Offset, int, int)> handles = entry.value;

      // Must have exactly 80 handles
      if (handles.length != 80) continue;

      // Verify complete 5x16 grid (all row/col combinations present)
      Set<(int, int)> positions = handles.map((e) => (e.$2, e.$3)).toSet();
      if (positions.length != 80) continue;

      // Verify 16+ distinct slats are anchored (not parallel to slat direction)
      Set<String> attachmentSlats = {};
      bool hasPhantom = false;

      for (var handle in handles) {
        Offset coord = handle.$1;
        var slat = slats[occupiedGridPoints[layerID]![coord]!]!;

        if (slat.phantomParent != null) {
          hasPhantom = true;
          break;
        }

        var slatID = slat.id;
        if (slat.slatType != 'tube') {
          slatID = slat.id + (slat.slatCoordinateToPosition[coord]! < 17 ? '-first-half' : 'second-half');
        }
        attachmentSlats.add(slatID);
      }

      if (hasPhantom) continue;
      if (attachmentSlats.length < 16) continue;

      // Verify handles are spatially adjacent in correct grid pattern
      if (!validateSeedGeometry(handles)) continue;

      // All validations passed - reinstate the seed
      // Build the coordinates map (1-indexed, ordered by row then col)
      Map<int, Offset> coordinates = {};
      for (var handle in handles) {
        int row = handle.$2;
        int col = handle.$3;
        int index = (row - 1) * 16 + col; // 1-based index
        coordinates[index] = handle.$1;
      }

      // Convert to real space for storage
      Map<int, Offset> realSpaceCoords = coordinates.map(
        (key, value) => MapEntry(key, convertCoordinateSpacetoRealSpace(value)),
      );

      Seed newSeed = Seed(ID: seedID, coordinates: realSpaceCoords);
      seedRoster[(layerID, slatSide, coordinates[1]!)] = newSeed;
    }

    if (skipStateUpdate) {
      return;
    }

    if (potentialSeeds.isNotEmpty) {
      saveUndoState();
      notifyListeners();
    }
  }

  void removeSeed(String layerID, String slatSide, Offset coordinate) {
    /// Removes a seed from the design.  This involves: 1) remove the handles from the related slats,
    /// 2) removing the blocks from the slat and cargo occupancy grids and 3)
    /// removing the seed and its related coordinates from the seed roster.
    (String, String, Offset)? seedToRemove;
    for (var seed in seedRoster.entries) {
      if (seed.value.coordinates.containsValue(convertCoordinateSpacetoRealSpace(coordinate)) && seed.key.$2 == slatSide) {
        for (var coord in seed.value.coordinates.values) {
          var convCoord = convertRealSpacetoCoordinateSpace(coord);
          var slat = slats[occupiedGridPoints[layerID]![convCoord]];

          int integerSlatSide = int.parse(layerMap[layerID]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
          if (integerSlatSide == 2) {
            slat!.h2Handles.remove(slat.slatCoordinateToPosition[convCoord]!);
          } else {
            slat!.h5Handles.remove(slat.slatCoordinateToPosition[convCoord]!);
          }

          occupiedCargoPoints['$layerID-$slatSide']?.remove(convCoord);

          int slatOccupiedLayerOrder = layerMap[layerID]?['order'] + (slatSide == 'top' ? 1 : -1);

          if (layerNumberValid(slatOccupiedLayerOrder)) {
            String occupiedLayer = getLayerByOrder(slatOccupiedLayerOrder)!;
            occupiedGridPoints[occupiedLayer]?.remove(convCoord);
          }
        }
        seedToRemove = seed.key;
      }
    }
    seedRoster.remove(seedToRemove);
    saveUndoState();
    notifyListeners();
  }

  /// Removes a single seed handle without affecting the seed roster.
  /// Used when dissolving a seed and removing individual handles.
  void removeSingleSeedHandle(String slatID, String slatSide, Offset coordinate, {bool skipStateUpdate = false}) {
    var slat = slats[slatID]!;
    int integerSlatSide = int.parse(layerMap[slat.layer]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));

    // Remove from slat handles
    if (integerSlatSide == 2) {
      slat.h2Handles.remove(slat.slatCoordinateToPosition[coordinate]!);
    } else {
      slat.h5Handles.remove(slat.slatCoordinateToPosition[coordinate]!);
    }

    // Remove from cargo occupancy
    occupiedCargoPoints['${slat.layer}-$slatSide']?.remove(coordinate);

    // Remove from grid occupancy (seeds also block a layer)
    int slatOccupiedLayerOrder = layerMap[slat.layer]?['order'] + (slatSide == 'top' ? 1 : -1);
    if (layerNumberValid(slatOccupiedLayerOrder)) {
      String occupiedLayer = getLayerByOrder(slatOccupiedLayerOrder)!;
      occupiedGridPoints[occupiedLayer]?.remove(coordinate);
    }

    if (skipStateUpdate) {
      return;
    }

    saveUndoState();
    notifyListeners();
  }

}
