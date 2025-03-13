import 'dart:math';
import 'package:flutter/material.dart';
import 'slats.dart';

(Offset, Offset) extractGridBoundary(Map<String, Slat> slats) {
  double minX = double.infinity;
  double minY = double.infinity;
  double maxX = double.negativeInfinity;
  double maxY = double.negativeInfinity;

  for (var slat in slats.values) {
    var positions = [
      slat.slatPositionToCoordinate[1]!,
      slat.slatPositionToCoordinate[32]!,
      // TODO: parameterize if slat length changes
    ];
    for (var pos in positions) {
      minX = pos.dx < minX ? pos.dx : minX;
      minY = pos.dy < minY ? pos.dy : minY;
      maxX = pos.dx > maxX ? pos.dx : maxX;
      maxY = pos.dy > maxY ? pos.dy : maxY;
    }
  }
  return (Offset(minX, minY), Offset(maxX, maxY));
}

List<List<List<int>>> convertSparseSlatBundletoArray(Map<String, Slat> slats,
    Map<String, Map<String, dynamic>> layerMap, double gridSize) {
  Offset minPos;
  Offset maxPos;
  (minPos, maxPos) = extractGridBoundary(slats);
  return extractSlatArray(slats, layerMap, minPos, maxPos, gridSize);
}

List<List<List<int>>> extractSlatArray(
    Map<String, Slat> slats,
    Map<String, Map<String, dynamic>> layerMap,
    Offset minGrid,
    Offset maxGrid,
    double gridSize) {
  int xSize = ((maxGrid.dx - minGrid.dx) / gridSize).ceil() + 1;
  int ySize = ((maxGrid.dy - minGrid.dy) / gridSize).ceil() + 1;
  List<List<List<int>>> slatArray = List.generate(xSize,(_) => List.generate(ySize, (_) => List.filled(layerMap.length, 0)));

  for (var slat in slats.values) {
    for (var i = 0; i < slat.maxLength; i++) {
      var pos = slat.slatPositionToCoordinate[i + 1]!;
      int x = ((pos.dx - minGrid.dx) / gridSize).floor();
      int y = ((pos.dy - minGrid.dy) / gridSize).floor();
      slatArray[x][y][layerMap[slat.layer]!['order']] = slat.numericID;
    }
  }

  return slatArray;
}
