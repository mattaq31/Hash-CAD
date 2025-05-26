import 'dart:math';
import 'package:flutter/material.dart';

import 'package:three_js/three_js.dart';
import 'package:three_js_core/three_js_core.dart' as three;
import 'package:three_js_geometry/three_js_geometry.dart';
import 'package:three_js_math/three_js_math.dart' as tmath;


three.BufferGeometry createHoneyCombSlat(List<List<double>> helixBundlePositions, double helixBundleSize, double gridSize) {

  final mergedGeometry = three.BufferGeometry();
  final mergedPositions = <double>[];
  final mergedNormals = <double>[];
  final mergedIndices = <int>[];

  int indexOffset = 0;

  for (var pos in helixBundlePositions) {

    // Create cylinder geometry
    CylinderGeometry geometry = CylinderGeometry(helixBundleSize/2, helixBundleSize/2, gridSize * 32, 20);

    // Translate the geometry to its position
    geometry.translate(pos[1], 0, pos[0]);

    final posAttr = geometry.attributes['position'] as tmath.BufferAttribute;
    final normAttr = geometry.attributes['normal'] as tmath.BufferAttribute;

    // Copy positions and normals
    for (int i = 0; i < posAttr.count; i++) {
      mergedPositions.add(posAttr.getX(i)!.toDouble());
      mergedPositions.add(posAttr.getY(i)!.toDouble());
      mergedPositions.add(posAttr.getZ(i)!.toDouble());
    }

    for (int i = 0; i < normAttr.count; i++) {
      mergedNormals.add(normAttr.getX(i)!.toDouble());
      mergedNormals.add(normAttr.getY(i)!.toDouble());
      mergedNormals.add(normAttr.getZ(i)!.toDouble());
    }

    if (geometry.index != null) {
      final idx = geometry.index!;
      for (int i = 0; i < idx.count; i++) {
        mergedIndices.add(idx.getX(i)!.toInt() + indexOffset);
      }
    } else {
      for (int i = 0; i < posAttr.count; i++) {
        mergedIndices.add(i + indexOffset);
      }
    }

    indexOffset += posAttr.count;
  }

  // Set attributes and index
  mergedGeometry.setAttributeFromString('position', tmath.Float32BufferAttribute.fromList(mergedPositions, 3));
  mergedGeometry.setAttributeFromString('normal', tmath.Float32BufferAttribute.fromList(mergedNormals, 3));
  mergedGeometry.setIndex(tmath.Uint16BufferAttribute.fromList(mergedIndices, 1));

  return mergedGeometry;
}

three.BufferGeometry createSeedTubeGeometry(
    Map<int, Offset> coordinates,
    double gridSize,
    int rotationAngle,
    int transverseAngle,
    int cols,
    int rows,
    double tubeRadius,
    ) {
  final mergedGeometry = three.BufferGeometry();
  final mergedPositions = <double>[];
  final mergedNormals = <double>[];
  final mergedIndices = <int>[];
  int indexOffset = 0;

  // Build path in 3D
  final pathPoints = <tmath.Vector3>[];

  double extendX = gridSize * cos(rotationAngle * (pi / 180));
  double extendZ = gridSize * sin(rotationAngle * (pi / 180));
  double transExtendX = gridSize * cos(transverseAngle * (pi / 180));
  double transZ = gridSize * sin(transverseAngle * (pi / 180));
  double farTransX = gridSize * rows * cos(transverseAngle * (pi / 180));
  double farTransZ = gridSize * rows * sin(transverseAngle * (pi / 180));

  // Start point (extruded in 3D)
  double startX = coordinates[1]!.dx - extendX;
  double startZ = coordinates[1]!.dy - extendZ;
  pathPoints.add(tmath.Vector3(startX, 0, startZ));

  // Horizontal snake
  for (int i = 1; i < rows + 1; i++) {
    if (i == rows) {
      if (i % 2 != 0) {
        pathPoints.add(
            tmath.Vector3(coordinates[i * cols]!.dx + extendX, 0, coordinates[i * cols]!.dy + extendZ));
        pathPoints.add(
            tmath.Vector3(coordinates[i * cols]!.dx + extendX / 2 + transExtendX / 2, 0, coordinates[i * cols]!.dy + extendZ / 2 + transZ / 2));
      } else {
        pathPoints.add(
            tmath.Vector3(coordinates[(i - 1) * cols + 1]!.dx - extendX, 0, coordinates[(i - 1) * cols + 1]!.dy - extendZ));
        pathPoints.add(
            tmath.Vector3(coordinates[(i - 1) * cols + 1]!.dx - extendX / 2 - transExtendX / 2, 0, coordinates[(i - 1) * cols + 1]!.dy - extendZ / 2 - transZ / 2));
      }
    } else {
      if (i % 2 != 0) {
        pathPoints.add(
            tmath.Vector3(coordinates[i * cols]!.dx + extendX, 0, coordinates[i * cols]!.dy + extendZ));
        pathPoints.add(
            tmath.Vector3(coordinates[(1 + i) * cols]!.dx + extendX, 0, coordinates[(1 + i) * cols]!.dy + extendZ));
      } else {
        pathPoints.add(
            tmath.Vector3(coordinates[(i - 1) * cols + 1]!.dx - extendX, 0, coordinates[(i - 1) * cols + 1]!.dy - extendZ));
        pathPoints.add(
            tmath.Vector3(coordinates[(i) * cols + 1]!.dx - extendX, 0, coordinates[(i) * cols + 1]!.dy - extendZ));
      }
    }
  }

  // Vertical snake
  for (int j = 1; j < cols + 2; j++) {
    if (j == (cols + 1)) {
      if (j % 2 != 0) {
        pathPoints.add(tmath.Vector3(
            pathPoints.last.x - farTransX, 0, pathPoints.last.z - farTransZ));
      } else {
        pathPoints.add(tmath.Vector3(
            pathPoints.last.x + farTransX, 0, pathPoints.last.z + farTransZ));
      }
    } else {
      if (j % 2 != 0) {
        pathPoints.add(tmath.Vector3(
            pathPoints.last.x - farTransX, 0, pathPoints.last.z - farTransZ));
        pathPoints.add(tmath.Vector3(
            pathPoints.last.x - extendX, 0, pathPoints.last.z - extendZ));
      } else {
        pathPoints.add(tmath.Vector3(
            pathPoints.last.x + farTransX, 0, pathPoints.last.z + farTransZ));
        pathPoints.add(tmath.Vector3(
            pathPoints.last.x - extendX, 0, pathPoints.last.z - extendZ));
      }
    }
  }
  pathPoints.add(tmath.Vector3(startX, 0, startZ));
  pathPoints.add(tmath.Vector3(startX + extendX, 0, startZ + extendZ));

  // Generate tube geometry along path
  final curve = CatmullRomCurve3(points: pathPoints, closed: false, curveType: 'catmullrom', tension:0.01);
  final geometry = TubeGeometry(curve, 2000, tubeRadius, 8, false);

  final posAttr = geometry.attributes['position'] as tmath.BufferAttribute;
  final normAttr = geometry.attributes['normal'] as tmath.BufferAttribute;
  final idx = geometry.index!;

  // Copy attributes
  for (int i = 0; i < posAttr.count; i++) {
    mergedPositions.addAll([
      posAttr.getX(i)!.toDouble(),
      posAttr.getY(i)!.toDouble(),
      posAttr.getZ(i)!.toDouble(),
    ]);
    mergedNormals.addAll([
      normAttr.getX(i)!.toDouble(),
      normAttr.getY(i)!.toDouble(),
      normAttr.getZ(i)!.toDouble(),
    ]);
  }

  for (int i = 0; i < idx.count; i++) {
    mergedIndices.add(idx.getX(i)!.toInt() + indexOffset);
  }

  indexOffset += posAttr.count;

  // Build merged geometry
  mergedGeometry.setAttributeFromString(
      'position', tmath.Float32BufferAttribute.fromList(mergedPositions, 3));
  mergedGeometry.setAttributeFromString(
      'normal', tmath.Float32BufferAttribute.fromList(mergedNormals, 3));
  mergedGeometry.setIndex(tmath.Uint16BufferAttribute.fromList(mergedIndices, 1));

  // final anchorPoint = pathPoints.first;
  mergedGeometry.translate(-coordinates[1]!.dx, 0, -coordinates[1]!.dy);
  // tmath.Vector3(startX, 0, startZ)
  // double startX = coordinates[1]!.dx - extendX;
  // double startZ = coordinates[1]!.dy - extendZ;
  return mergedGeometry;
}