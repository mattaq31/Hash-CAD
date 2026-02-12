/// Slat entity class representing DNA origami slats with handles.

import 'package:flutter/material.dart';


/// Rotates a point around a center in coordinate space by a given number of steps.
/// In 90deg mode, each step is 90deg CW (4 steps = full rotation).
/// In 60deg mode, each step is 60deg CW (6 steps = full rotation).
Offset rotateCoordinateSpace(Offset point, Offset center, int steps, String gridMode) {
  int modulus = gridMode == '90' ? 4 : 6;
  steps = steps % modulus;
  if (steps == 0) return point;

  double dx = point.dx - center.dx;
  double dy = point.dy - center.dy;

  for (int i = 0; i < steps; i++) {
    if (gridMode == '90') {
      // 90deg CW: (dx, dy) -> (dy, -dx)
      double newDx = dy;
      double newDy = -dx;
      dx = newDx;
      dy = newDy;
    } else {
      // 60deg CW: (dx, dy) -> (0.5*dx + 0.5*dy, -1.5*dx + 0.5*dy)
      double newDx = 0.5 * dx + 0.5 * dy;
      double newDy = -1.5 * dx + 0.5 * dy;
      dx = newDx.roundToDouble();
      dy = newDy.roundToDouble();
    }
  }

  return Offset(center.dx + dx, center.dy + dy);
}

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
  String? phantomParent;

  Slat(this.numericID, this.id, this.layer, Map<int, Offset> slatCoordinates, {this.maxLength = 32, this.uniqueColor, this.slatType = 'tube', this.phantomParent}) {
      slatCoordinates.forEach((key, coord) {
        slatPositionToCoordinate[key] = coord;
        slatCoordinateToPosition[coord] = key;
      });
      centerCoordinate = calculateCenter(slatCoordinates.values.toList());
  }

  /// Sets a unique color for the slat, used for visualization.
  void setColor(Color color) {
    uniqueColor = color;
  }

  /// Clears the unique color of the slat.
  void clearColor() {
    uniqueColor = null;
  }

  /// Sets the ID of the reference slat this slat is associated with (or clear it).
  /// Setting this also implies this slat is a phantom slat.
  void setPhantom(String newPhantom) {
    phantomParent = newPhantom;
  }

  void updateCoordinates(Map<int, Offset> slatCoordinates){
    slatPositionToCoordinate = slatCoordinates;
    slatCoordinateToPosition = {for (var offset in slatCoordinates.entries) offset.value : offset.key};
    centerCoordinate = calculateCenter(slatCoordinates.values);
  }

  /// Reverses a slat, keeping all handles in the same physical position but changing their logical order.
  void reverseDirection() {
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

  /// Assigns a placeholder to the slat, instead of a full handle.
  void setPlaceholderHandle(int handleId, int slatSide, String value, String category) {
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

  /// Updates a placeholder handle with the actual handle.
  void updatePlaceholderHandle(int handleId, int slatSide, String sequence, String well, String plateName, String value, String category, int concentration) {
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

  /// Defines the full details of a handle on a slat.
  void setHandle(int handleId, int slatSide, String sequence, String well, String plateName, String value, String category, int concentration) {
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

  /// Removes a handle from the slat at the given position and side.
  void removeHandle(int position, int side) {
    if (side == 2) {
      h2Handles.remove(position);
    } else if (side == 5) {
      h5Handles.remove(position);
    }
    placeholderList.remove('handle-$position-h$side');
  }

  /// Removes all handles from the slat.
  void clearAllHandles(){
    h2Handles.clear();
    h5Handles.clear();
    placeholderList.clear();
  }

  /// Removes all assembly handles from the slat.
  void clearAssemblyHandles() {
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

  /// Calculates the molecular weight of the slat, based on the handles assigned.
  double getMolecularWeight() {
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
    final newSlat = Slat(numericID, id, layer, Map.from(slatPositionToCoordinate), maxLength: maxLength, uniqueColor: uniqueColor, slatType: slatType, phantomParent: phantomParent);

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

  void copyHandlesFromSlat(Slat slat){
    h2Handles = {
      for (var entry in slat.h2Handles.entries)
        entry.key: Map.from(entry.value)
    };
    h5Handles = {
      for (var entry in slat.h5Handles.entries)
        entry.key: Map.from(entry.value)
    };
    placeholderList = List.from(slat.placeholderList);
  }

}