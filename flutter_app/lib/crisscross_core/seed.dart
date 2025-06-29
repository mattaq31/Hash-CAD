import 'package:flutter/material.dart';

import '../2d_painters/helper_functions.dart';
import 'dart:math';


Map<int, Offset> generateBasicSeedCoordinates(int cols, int rows, double jump, bool tiltMode, bool invertMode){
  /// quick generation of basic seed coordinates for model seeds (not to be used in actual coordinate system)

  final Map<int, Offset> coordinates = {};

  double y60Jump = jump / 2;
  double x60Jump = sqrt(pow(jump, 2) - pow(y60Jump, 2));

  int index = 1;
  double multiplier = invertMode ? -1 : 1;

  for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
      if (tiltMode){
        coordinates[index++] = Offset(multiplier * (i * x60Jump), (j * y60Jump * 2) + multiplier * (i * y60Jump));
      }
      else {
        coordinates[index++] = Offset(multiplier * j * jump, multiplier * i * jump);
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
  bool? transposeFlip;

  final int rows;
  final int cols;

  Seed(
      {required this.ID, required this.coordinates,
        this.rows=5, this.cols=16,
        this.tiltFlip, this.transposeFlip}) {

    if(coordinates.isEmpty){
      throw Exception('To create a seed, at least the first coordinate needs to be specified.');
    }

    final (rotA, transA) = detectRotation();
    rotationAngle = rotA;
    transverseAngle = transA;
    tiltFlip ??= isTiltFlipped();
    transposeFlip ??= isTransposeFlipped();

  }

  bool isTiltFlipped() {
   // Used to help with direction to render 3D version of seed.
    // This checks to see which direction the cross product of the vectors is pointing.
    Offset originAnchor = coordinates[1]!;
    Offset longEdgeAnchor = coordinates[cols]!;
    Offset shortEdgeAnchor = coordinates[(cols*(rows-1)) + 1]!;

    Offset longVector = longEdgeAnchor - originAnchor;
    Offset shortVector = shortEdgeAnchor - originAnchor;
    double crossProduct = longVector.dx * shortVector.dy - longVector.dy * shortVector.dx;

    return crossProduct > 0 ? true : false;
  }

  bool isTransposeFlipped() {
    // Used to help with direction to render 3D version of seed.
    // This checks to see whether the angle at the origin is large (> 30 degrees) or small (< 30 degrees).
    // Only useful for 60deg seeds.
    Offset originAnchor = coordinates[1]!;
    Offset longEdgeAnchor = coordinates[cols]!;
    Offset shortEdgeAnchor = coordinates[(cols*(rows-1)) + 1]!;

    Offset longVector = longEdgeAnchor - originAnchor;
    Offset shortVector = shortEdgeAnchor - originAnchor;
    double dotProduct = longVector.dx * shortVector.dx + longVector.dy * shortVector.dy;
    double magnitudeA = sqrt(pow(longVector.dx, 2) + pow(longVector.dy, 2));
    double magnitudeB = sqrt(pow(shortVector.dx, 2) + pow(shortVector.dy, 2));
    double cosTheta = dotProduct / (magnitudeA * magnitudeB);

    if (magnitudeA == 0 || magnitudeB == 0) return false;

    double thetaDeg = (acos(cosTheta) * (180 / pi)).abs();

    return thetaDeg > 70;
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
