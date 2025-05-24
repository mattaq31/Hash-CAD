import 'package:flutter/material.dart';

import '../2d_painters/helper_functions.dart';
import 'dart:math';


class Seed {
  Map<int, Offset> coordinates;
  int? rotationAngle;
  int? transverseAngle;
  bool? tiltFlip;

  final int rows;
  final int cols;

  Seed(
      {required this.coordinates,
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
   // Function currently unused, but could be useful when considering the mirror images of designs in the future.
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
      coordinates: Map.from(coordinates),
      rows: rows,
      cols: cols,
      tiltFlip: tiltFlip,
    );
  }

}
