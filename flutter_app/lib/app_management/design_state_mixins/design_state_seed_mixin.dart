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
      setSlatHandle(slat, position, integerSlatSide, '$nextSeedID-$row-$col', 'SEED');

      occupiedCargoPoints['$layerID-$slatSide']![coord] = slat.id;

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

  void removeSeed(String layerID, String slatSide, Offset coordinate) {
    /// Removes a seed from the design.  This involves: 1) remove the handles from the related slats,
    /// 2) removing the blocks from the slat and cargo occupancy grids and 3)
    /// removing the seed and its related coordinates from the seed roster.
    (String, String, Offset)? seedToRemove;
    for (var seed in seedRoster.entries) {
      if (seed.value.coordinates.containsValue(convertCoordinateSpacetoRealSpace(coordinate)) &&
          seed.key.$2 == slatSide) {
        for (var coord in seed.value.coordinates.values) {
          var convCoord = convertRealSpacetoCoordinateSpace(coord);
          var slat = slats[occupiedCargoPoints['$layerID-$slatSide']![convCoord]];

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
    notifyListeners();
  }
}
