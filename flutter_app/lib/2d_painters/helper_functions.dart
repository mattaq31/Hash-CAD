import 'dart:math';
import 'package:flutter/material.dart';


Offset multiplyOffsets(Offset a, Offset b) {
  return Offset(a.dx * b.dx, a.dy * b.dy);
}

/// Function to calculate the angle of a slat based on its two end points
double calculateSlatAngle(Offset p1, Offset p2) {
  double dx = p2.dx - p1.dx;
  double dy = p2.dy - p1.dy;
  double angle = atan2(dy, dx); // Angle in radians
  return angle;
}

/// Function to calculate the tiny extension outside of the grid on either side of a slat, based on the slat's angle and the grid size.
Offset calculateSlatExtend(Offset p1, Offset p2, double gridSize){
  double slatAngle = calculateSlatAngle(p1, p2);
  double extX = (gridSize/2) * cos(slatAngle);
  double extY = (gridSize/2) * sin(slatAngle);
  return Offset(extX, extY);
}


Offset convertRealSpacetoCoordinateSpace(Offset inputPosition, String gridMode, double gridSize, double x60Jump, double y60Jump){
  if (gridMode == '90'){
    // converts a position in real space, where a grid point has size gridSize into a coordinate system where each point is 1 gridSize unit
    return Offset((inputPosition.dx / gridSize).roundToDouble(), (inputPosition.dy / gridSize).roundToDouble());
  }
  else if (gridMode == '60'){
    return Offset((inputPosition.dx / x60Jump).roundToDouble(), (inputPosition.dy / y60Jump).roundToDouble());
  }
  else {
    throw Exception('Invalid grid system: $gridMode');
  }
}

Offset convertCoordinateSpacetoRealSpace(Offset inputPosition, String gridMode, double gridSize, double x60Jump, double y60Jump){
  if (gridMode == '90'){
    return Offset(inputPosition.dx * gridSize, inputPosition.dy * gridSize);
  }
  else if (gridMode == '60'){
    return Offset(inputPosition.dx * x60Jump, inputPosition.dy * y60Jump);
  }
  else {
    throw Exception('Invalid grid system: $gridMode');
  }
}


