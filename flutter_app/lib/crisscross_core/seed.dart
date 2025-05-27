import 'package:flutter/material.dart';

import '../2d_painters/helper_functions.dart';
import 'dart:math';


Map<int, Offset> generateBasicSeedCoordinates(int cols, int rows, double jump, bool tiltMode){
  /// quick generation of basic seed coordinates for model seeds (not to be used in actual coordinate system)

  final Map<int, Offset> coordinates = {};

  double y60Jump = jump / 2;
  double x60Jump = sqrt(pow(jump, 2) - pow(y60Jump, 2));

  int index = 1;
  for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
      if (tiltMode){
        coordinates[index++] = Offset((i * x60Jump) , (j * y60Jump * 2) + (i * y60Jump));
      }
      else {
        coordinates[index++] = Offset(j * jump, i * jump);
      }
    }

  }
  return coordinates;
}

int getIndexFromSeedText(String seedText) {
  final parts = seedText.split('-');
  if (parts.length != 3) {
    throw FormatException('Invalid seed format: $seedText');
  }
  final row = int.parse(parts[1]);
  final col = int.parse(parts[2]);

  return (row - 1) * 16 + (col - 1) + 1; // 1-based index
}

class Seed {
  String ID;
  Map<int, Offset> coordinates;
  int? rotationAngle;
  int? transverseAngle;
  bool? tiltFlip;

  final int rows;
  final int cols;

  Seed(
      {required this.ID, required this.coordinates,
        this.rows=5, this.cols=16,
        this.tiltFlip}) {

    if(coordinates.isEmpty){
      throw Exception('To create a seed, at least the first coordinate needs to be specified.');
    }

    final (rotA, transA) = detectRotation();
    rotationAngle = rotA;
    transverseAngle = transA;
    tiltFlip ??= isTiltFlipped();

  }

  bool isTiltFlipped() {
   // Used to help with direction to render 3D version of seed.
    Offset topAnchor = coordinates[1]!;
    Offset bottomAnchor = coordinates[cols]!;
    Offset topCorner = coordinates[(cols*rows-1) + 1]!;

    Offset anchorVector = bottomAnchor - topAnchor;
    Offset cornerVector = topCorner - topAnchor;
    double crossProduct = anchorVector.dx * cornerVector.dy - anchorVector.dy * cornerVector.dx;

    return crossProduct > 0 ? true : false;
  }

  (int, int) detectRotation() {
    // detects both the main and transverse angles of the seed, which are important for drawing the seed in the correct orientation.
    Offset topAnchor = coordinates[1]!;
    Offset bottomAnchor = coordinates[cols]!;
    Offset secondRowAnchor = coordinates[cols + 1]!;

    int mainAngle = (calculateSlatAngle(topAnchor, bottomAnchor) * 180/pi).round();
    int transverseAngle = (calculateSlatAngle(topAnchor, secondRowAnchor) * 180/pi).round();

    return (mainAngle, transverseAngle);
  }

  Seed copy() {
    return Seed(
      ID: ID,
      coordinates: Map.from(coordinates),
      rows: rows,
      cols: cols,
      tiltFlip: tiltFlip,
    );
  }

}
