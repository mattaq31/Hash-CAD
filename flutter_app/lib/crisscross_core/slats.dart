import 'package:flutter/material.dart';

class Slat {
  /// Wrapper class to hold all of a slat's handles and related details.

  final String id;
  final String layer;
  final int maxLength;
  final int numericID;

  bool reversedSlat = false; // flag to indicate if the slat has been reversed

  // Maps positions on the slat to coordinates on a 2D grid and vice-versa
  Map<int, Offset> slatPositionToCoordinate = {};
  Map<Offset, int> slatCoordinateToPosition = {};

  List<String> placeholderList = [];

  Map<int, Map<String, dynamic>> h2Handles = {};
  Map<int, Map<String, dynamic>> h5Handles = {};

  Slat(this.numericID, this.id, this.layer, Map<int, Offset> slatCoordinates, {this.maxLength = 32}) {
      slatCoordinates.forEach((key, coord) {
        slatPositionToCoordinate[key] = coord;
        slatCoordinateToPosition[coord] = key;
      });
    }

  void updateCoordinates(Map<int, Offset> slatCoordinates){
    slatPositionToCoordinate = slatCoordinates;
    slatCoordinateToPosition = {for (var offset in slatCoordinates.entries) offset.value : offset.key};
  }

  void reverseDirection() {
    /// Reverses the handle order on the slat.
    Map<int, Offset> newSlatPositionToCoordinate = {};
    Map<Offset, int> newSlatCoordinateToPosition = {};

    for (int i = 0; i < maxLength; i++) {
      newSlatPositionToCoordinate[maxLength - i] = slatPositionToCoordinate[i + 1]!;
      newSlatCoordinateToPosition[slatPositionToCoordinate[i + 1]!] = maxLength - i;
    }

    slatPositionToCoordinate = newSlatPositionToCoordinate;
    slatCoordinateToPosition = newSlatCoordinateToPosition;
    reversedSlat = !reversedSlat;
  }

  void setPlaceholderHandle(int handleId, int slatSide, String descriptor, String category) {
    /// Assigns a placeholder to the slat, instead of a full handle.

    // TODO: MORE STREAMLINED PLACEMENT LOGIC and REDUNDANCY/ERROR HANDLING
    if (handleId < 1 || handleId > maxLength) {
      throw Exception('Handle ID out of range');
    }

    if (slatSide == 2) {
      h2Handles[handleId] = {'descriptor': descriptor, 'category': category};
    } else if (slatSide == 5) {
      h5Handles[handleId] = {'descriptor': descriptor, 'category': category};
    } else {
      throw Exception('Wrong slat side specified (only 2 or 5 available)');
    }

    placeholderList.add('handle-$handleId-h$slatSide');
  }

  void updatePlaceholderHandle(
      int handleId, int slatSide, String sequence, String well, String plateName, String descriptor, String category) {
    /// Updates a placeholder handle with the actual handle.

    String inputId = 'handle-$handleId-h$slatSide';
    if (!placeholderList.contains(inputId)) {
      throw Exception('Handle ID not found in placeholder list');
    } else {
      placeholderList.remove(inputId);
    }

    if (slatSide == 2) {
      h2Handles[handleId] = {'sequence': sequence, 'well': well, 'plate': plateName, 'descriptor': descriptor, 'category': category};
    } else if (slatSide == 5) {
      h5Handles[handleId] = {'sequence': sequence, 'well': well, 'plate': plateName, 'descriptor': descriptor, 'category': category};
    }
  }

  void setHandle(int handleId, int slatSide, String sequence, String well, String plateName, String descriptor, String category) {
    /// Defines the full details of a handle on a slat.
    if (handleId < 1 || handleId > maxLength) {
      throw Exception('Handle ID out of range');
    }

    if (slatSide == 2) {
      h2Handles[handleId] = {'sequence': sequence, 'well': well, 'plate': plateName, 'descriptor': descriptor, 'category': category};
    } else if (slatSide == 5) {
      h5Handles[handleId] = {'sequence': sequence, 'well': well, 'plate': plateName, 'descriptor': descriptor, 'category': category};
    } else {
      throw Exception('Wrong slat side specified (only 2 or 5 available)');
    }
  }

  void clearAllHandles(){
    /// Removes all handles from the slat.
    h2Handles.clear();
    h5Handles.clear();
    placeholderList.clear();
  }

  double getMolecularWeight() {
    /// Calculates the molecular weight of the slat, based on the handles assigned.

    int totalBases = 0;

    if (h2Handles.length < maxLength || h5Handles.length < maxLength) {
      throw Exception('Not all handles have been assigned on the slat, so the MW cannot be calculated yet.');
    }

    for (var handle in h2Handles.values) {
      if (handle['sequence'] == null) {
        throw Exception('Not all handles have been assigned on the slat, so the MW cannot be calculated yet.');
      }
      totalBases += (handle['sequence'].length as int);
    }
    for (var handle in h5Handles.values) {
      if (handle['sequence'] == null) {
        throw Exception('Not all handles have been assigned on the slat, so the MW cannot be calculated yet.');
      }
      totalBases += (handle['sequence'].length as int);
    }

    totalBases += 8064; // incorporating scaffold length
    totalBases += 5329; // incorporating length of core staples

    return totalBases * 327 - (totalBases - 1) * 18.015;
  }

  Slat copy() {
    final newSlat = Slat(numericID, id, layer, Map.from(slatPositionToCoordinate), maxLength: maxLength);
    newSlat.reversedSlat = reversedSlat;

    newSlat.h2Handles = {
      for (var entry in h2Handles.entries)
        entry.key: Map.from(entry.value)
    };
    newSlat.h5Handles = {
      for (var entry in h5Handles.entries)
        entry.key: Map.from(entry.value)
    };

    newSlat.placeholderList = List.from(placeholderList);

    return newSlat;
  }
}