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

List<List<List<int>>> convertSparseSlatBundletoArray(
    Map<String, Slat> slats,
    Map<String, Map<String, dynamic>> layerMap,
    Offset minGrid,
    Offset maxGrid,
    double gridSize) {
  int xSize = (maxGrid.dx - minGrid.dx).toInt() + 1;
  int ySize = (maxGrid.dy - minGrid.dy).toInt() + 1;

  List<List<List<int>>> slatArray = List.generate(xSize,(_) => List.generate(ySize, (_) => List.filled(layerMap.length, 0)));

  for (var slat in slats.values) {
    for (var i = 0; i < slat.maxLength; i++) {
      var pos = slat.slatPositionToCoordinate[i + 1]!;
      int x = (pos.dx - minGrid.dx).toInt();
      int y = (pos.dy - minGrid.dy).toInt();
      slatArray[x][y][layerMap[slat.layer]!['order']] = slat.numericID;
    }
  }
  return slatArray;
}

List<List<List<int>>> extractAssemblyHandleArray(
    Map<String, Slat> slats,
    Map<String, Map<String, dynamic>> layerMap,
    Offset minGrid,
    Offset maxGrid,
    double gridSize) {

  int xSize = (maxGrid.dx - minGrid.dx).toInt() + 1;
  int ySize = (maxGrid.dy - minGrid.dy).toInt() + 1;
  List<List<List<int>>> handleArray = List.generate(xSize,(_) => List.generate(ySize, (_) => List.filled(layerMap.length-1, 0)));

  for (var slat in slats.values) {
    final topBottomOrder = (layerMap[slat.layer]?['top_helix'] == 'H5') ? ['H5', 'H2'] : ['H2', 'H5'];
    for (var i = 0; i < slat.maxLength; i++) {
      var pos = slat.slatPositionToCoordinate[i + 1]!;
      int x = (pos.dx - minGrid.dx).toInt();
      int y = (pos.dy - minGrid.dy).toInt();
      for (var handleSide in topBottomOrder.asMap().entries){
        if (handleSide.value == 'H5'){
          if (slat.h5Handles[i + 1] != null && slat.h5Handles[i + 1]!['category'].contains('ASSEMBLY')){
            handleArray[x][y][layerMap[slat.layer]!['order']-handleSide.key] = int.parse(slat.h5Handles[i + 1]!['value']);
          }
        }
        else if (handleSide.value == 'H2'){
          if (slat.h2Handles[i + 1] != null && slat.h2Handles[i + 1]!['category'].contains('ASSEMBLY')){
            handleArray[x][y][layerMap[slat.layer]!['order']-handleSide.key] = int.parse(slat.h2Handles[i + 1]!['value']);
          }
        }
      }
    }
  }
  return handleArray;
}

