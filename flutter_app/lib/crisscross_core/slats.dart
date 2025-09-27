import 'package:flutter/material.dart';


Offset calculateCenter(Iterable<Offset> points) {
  double sumX = 0.0;
  double sumY = 0.0;
  int count = 0;

  for (final point in points) {
    sumX += point.dx;
    sumY += point.dy;
    count++;
  }

  if (count == 0) return Offset.zero;
  final inv = 1.0 / count;
  return Offset(sumX * inv, sumY * inv);
}

class Slat {
  /// Wrapper class to hold all of a slat's handles and related details.

  final String id;
  final String layer;
  final int maxLength;
  final int numericID;

  // Maps positions on the slat to coordinates on a 2D grid and vice-versa
  Map<int, Offset> slatPositionToCoordinate = {};
  Map<Offset, int> slatCoordinateToPosition = {};
  Offset centerCoordinate = Offset.zero;

  List<String> placeholderList = [];

  Map<int, Map<String, dynamic>> h2Handles = {};
  Map<int, Map<String, dynamic>> h5Handles = {};

  Color? uniqueColor;
  String slatType;

  Slat(this.numericID, this.id, this.layer, Map<int, Offset> slatCoordinates, {this.maxLength = 32, this.uniqueColor, this.slatType = 'tube'}) {
      slatCoordinates.forEach((key, coord) {
        slatPositionToCoordinate[key] = coord;
        slatCoordinateToPosition[coord] = key;
      });
      centerCoordinate = calculateCenter(slatCoordinates.values.toList());
  }

  void setColor(Color color) {
    /// Sets a unique color for the slat, used for visualization.
    uniqueColor = color;
  }

  void clearColor() {
    /// Clears the unique color of the slat.
    uniqueColor = null;
  }

  void updateCoordinates(Map<int, Offset> slatCoordinates){
    slatPositionToCoordinate = slatCoordinates;
    slatCoordinateToPosition = {for (var offset in slatCoordinates.entries) offset.value : offset.key};
    centerCoordinate = calculateCenter(slatCoordinates.values);
  }

  void reverseDirection() {
    /// Reverses a slat, keeping all handles in the same physical position but changing their logical order.
    Map<int, Offset> newSlatPositionToCoordinate = {};
    Map<Offset, int> newSlatCoordinateToPosition = {};

    // reverse all hande positions in the slat
    for (int i = 0; i < maxLength; i++) {
      newSlatPositionToCoordinate[maxLength - i] = slatPositionToCoordinate[i + 1]!;
      newSlatCoordinateToPosition[slatPositionToCoordinate[i + 1]!] = maxLength - i;
    }

    // updates h2 and h5 handles to match the new positions
    Map<int, Map<String, dynamic>> newH2Handles = {};
    Map<int, Map<String, dynamic>> newH5Handles = {};
    for (var entry in h2Handles.entries) {
      int newKey = maxLength - entry.key + 1;
      newH2Handles[newKey] = Map.from(entry.value);
    }

    for (var entry in h5Handles.entries) {
      int newKey = maxLength - entry.key + 1;
      newH5Handles[newKey] = Map.from(entry.value);
    }

    slatPositionToCoordinate = newSlatPositionToCoordinate;
    slatCoordinateToPosition = newSlatCoordinateToPosition;
    h2Handles = newH2Handles;
    h5Handles = newH5Handles;
  }

  void setPlaceholderHandle(int handleId, int slatSide, String value, String category) {
    /// Assigns a placeholder to the slat, instead of a full handle.

    // TODO: MORE STREAMLINED PLACEMENT LOGIC and REDUNDANCY/ERROR HANDLING
    if (handleId < 1 || handleId > maxLength) {
      throw Exception('Handle ID out of range');
    }

    if (slatSide == 2) {
      h2Handles[handleId] = {'value': value, 'category': category.toUpperCase(), 'placeholder': true};
    } else if (slatSide == 5) {
      h5Handles[handleId] = {'value': value, 'category': category.toUpperCase(), 'placeholder': true};
    } else {
      throw Exception('Wrong slat side specified (only 2 or 5 available)');
    }

    placeholderList.add('handle-$handleId-h$slatSide');
  }

  void updatePlaceholderHandle(int handleId, int slatSide, String sequence, String well, String plateName, String value, String category, int concentration) {
    /// Updates a placeholder handle with the actual handle.

    String inputId = 'handle-$handleId-h$slatSide';
    if (!placeholderList.contains(inputId)) {
      throw Exception('Handle ID not found in placeholder list');
    } else {
      placeholderList.remove(inputId);
    }

    if (slatSide == 2) {
      h2Handles[handleId] = {'sequence': sequence, 'well': well, 'plate': plateName, 'value': value, 'category': category.toUpperCase(), 'concentration': concentration};
    } else if (slatSide == 5) {
      h5Handles[handleId] = {'sequence': sequence, 'well': well, 'plate': plateName, 'value': value, 'category': category.toUpperCase(), 'concentration': concentration};
    }
  }

  void setHandle(int handleId, int slatSide, String sequence, String well, String plateName, String value, String category, int concentration) {
    /// Defines the full details of a handle on a slat.
    if (handleId < 1 || handleId > maxLength) {
      throw Exception('Handle ID out of range');
    }

    String inputId = 'handle-$handleId-h$slatSide';
    if (placeholderList.contains(inputId)) {
      placeholderList.remove(inputId);
    }

    if (slatSide == 2) {
      h2Handles[handleId] = {'sequence': sequence, 'well': well, 'plate': plateName, 'value': value, 'category': category.toUpperCase(), 'concentration': concentration};
    } else if (slatSide == 5) {
      h5Handles[handleId] = {'sequence': sequence, 'well': well, 'plate': plateName, 'value': value, 'category': category.toUpperCase(), 'concentration': concentration};
    } else {
      throw Exception('Wrong slat side specified (only 2 or 5 available)');
    }
  }

  bool checkPlaceholder(int handleID, int slatSide){
    return placeholderList.contains('handle-$handleID-h$slatSide');
  }

  void clearAllHandles(){
    /// Removes all handles from the slat.
    h2Handles.clear();
    h5Handles.clear();
    placeholderList.clear();
  }

  void clearAssemblyHandles() {
    /// Removes all assembly handles from the slat.

    // Collect keys to remove from h2Handles
    final keysToRemoveH2 = h2Handles.entries
        .where((entry) => entry.value['category'].contains('ASSEMBLY'))
        .map((entry) => entry.key)
        .toList();

    for (final key in keysToRemoveH2) {
      h2Handles.remove(key);
      final inputId = 'handle-$key-h2';
      placeholderList.remove(inputId);
    }

    // Collect keys to remove from h5Handles
    final keysToRemoveH5 = h5Handles.entries
        .where((entry) => entry.value['category'].contains('ASSEMBLY'))
        .map((entry) => entry.key)
        .toList();

    for (final key in keysToRemoveH5) {
      h5Handles.remove(key);
      final inputId = 'handle-$key-h5';
      placeholderList.remove(inputId);
    }
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
    final newSlat = Slat(numericID, id, layer, Map.from(slatPositionToCoordinate), maxLength: maxLength, uniqueColor: uniqueColor, slatType: slatType);

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