import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/cargo.dart';

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

  // Methods from other mixins
  void saveUndoState();
  void setSlatHandle(Slat slat, int position, int side, String handlePayload, String category);
  void removeSeed(String layerID, String slatSide, Offset coordinate);

  void addCargoType(Cargo cargo) {
    cargoPalette[cargo.name] = cargo;
    saveUndoState();
    notifyListeners();
  }

  void deleteCargoType(String cargoName) {
    // need to remove all cargo of this type from the slats and from the cargo occupancy map (otherwise will error out)
    for (var slat in slats.values) {
      for (var side in ['top', 'bottom']) {
        var targetDict = layerMap[slat.layer]!['${side}_helix'] == 'H5'
            ? slat.h5Handles
            : slat.h2Handles;
        for (int position = 1; position <= slat.maxLength; position++) {
          if (targetDict[position] != null &&
              targetDict[position]!['value'] == cargoName) {
            targetDict.remove(position); // TODO: also need to remove placeholder list - need to make a slat function...
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

  Cargo getCargoFromCoordinate(Offset coordinate, String layerID, String slatSide) {
    String slatID = occupiedCargoPoints['$layerID-$slatSide']![coordinate]!;
    Slat slat = slats[slatID]!;
    int position = slat.slatCoordinateToPosition[coordinate]!;
    int integerSlatSide = int.parse(
        layerMap[layerID]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
    var handleDict = integerSlatSide == 5 ? slat.h5Handles : slat.h2Handles;
    String cargoName = handleDict[position]!['value'];

    return cargoPalette[cargoName]!;
  }

  void deleteAllCargo() {
    // need to remove all cargo of this type from the slats and from the cargo occupancy map (otherwise will error out)
    for (var slat in slats.values) {
      for (var side in ['top', 'bottom']) {
        var targetDict = layerMap[slat.layer]!['${side}_helix'] == 'H5'
            ? slat.h5Handles
            : slat.h2Handles;
        for (int position = 1; position <= slat.maxLength; position++) {
          if (targetDict[position] != null &&
              targetDict[position]!['category'] == 'CARGO') {
            targetDict.remove(position);
            occupiedCargoPoints['${slat.layer}-$side']
                ?.remove(slat.slatPositionToCoordinate[position]!);
          }
        }
      }
    }
    saveUndoState();
    notifyListeners();
  }

  void moveCargo(Map<Offset, Offset> coordinateTransferMap, String layerID, String slatSide, {bool skipStateUpdate = false}) {
    int integerSlatSide = int.parse(layerMap[layerID]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));

    // TODO: seems to be an issue moving only a subset of cargo - need to debug
    for (var fromCoord in coordinateTransferMap.keys) {
      if (!occupiedCargoPoints['$layerID-$slatSide']!.containsKey(fromCoord)) {
        continue; // no cargo at this position
      }
      // obtains information for the cargo at the 'from' coordinate
      var slatDonor = slats[occupiedGridPoints[layerID]![fromCoord]!]!;
      int donorPosition = slatDonor.slatCoordinateToPosition[fromCoord]!;
      var handleDict = integerSlatSide == 5 ? slatDonor.h5Handles : slatDonor.h2Handles;
      String cargoName = handleDict[donorPosition]!['value'];
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

      // TODO: should use an actual compartmentalized function for this
      // removes cargo from the 'from' coordinate
      handleDict.remove(donorPosition);
      slatDonor.placeholderList.remove('handle-$donorPosition-h$integerSlatSide');

      // adds cargo to the 'to' coordinate
      setSlatHandle(slatReceiver, receiverPosition, integerSlatSide, cargoName, 'CARGO');

      // updates occupancy maps
      occupiedCargoPoints['$layerID-$slatSide']?.remove(fromCoord);
      occupiedCargoPoints['$layerID-$slatSide']![toCoord] = slatReceiver.id;
    }

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

  void attachCargo(Cargo cargo, String layerID, String slatSide,
      Map<int, Offset> coordinates,
      {bool skipStateUpdate = false}) {
    occupiedCargoPoints.putIfAbsent('$layerID-$slatSide', () => {});

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
      int integerSlatSide = int.parse(layerMap[slat.layer]?['${slatSide}_helix']
          .replaceAll(RegExp(r'[^0-9]'), ''));
      setSlatHandle(slat, position, integerSlatSide, cargo.name, 'CARGO');
      occupiedCargoPoints['$layerID-$slatSide']![coord] = slat.id;
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
    int integerSlatSide = int.parse(layerMap[slat.layer]?['${slatSide}_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
    if (integerSlatSide == 2) {
      if (slat.h2Handles[slat.slatCoordinateToPosition[coordinate]!]!['category'] ==
          'SEED') {
        removeSeed(slat.layer, slatSide, coordinate);
        return;
      }
      slat.h2Handles.remove(slat.slatCoordinateToPosition[coordinate]!);
    } else {
      if (slat.h5Handles[slat.slatCoordinateToPosition[coordinate]!]!['category'] == 'SEED') {
        removeSeed(slat.layer, slatSide, coordinate);
        return;
      }
      slat.h5Handles.remove(slat.slatCoordinateToPosition[coordinate]!);
    }
    occupiedCargoPoints['${slat.layer}-$slatSide']?.remove(coordinate);

    if (skipStateUpdate) {
      return;
    }

    saveUndoState();
    notifyListeners();
  }
}
