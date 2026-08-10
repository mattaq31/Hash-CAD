import 'dart:math';
import 'package:flutter/material.dart';

import 'package:three_js/three_js.dart';
import 'package:three_js_core/three_js_core.dart' as three;
import 'package:three_js_math/three_js_math.dart' as tmath;


List<three.BufferGeometry> drawTube(List<Vector3> pathPoints, double tubeRadius, {String curveType = "catmullrom", double tension = 0.01}){

  final curve = CatmullRomCurve3(points: pathPoints, closed: false, curveType: curveType, tension: tension);

  int radiusSegments = 20; // radial segments affect the smoothness of the tube
  // Tube around path
  final tube = TubeGeometry(
    curve,
    200,       // tubular segments
    tubeRadius,   // radius of slat
    radiusSegments,
    false,    // not closed (do not loop the path)
  );

  // To visually "close" the tube ends, add caps at the two ends
  // Determine end positions from centered path
  final startPoint = pathPoints.first;
  final endPoint = pathPoints.last;

  // Build flat disk caps using very thin cylinders aligned along Y (faces in XZ plane)
  final capSegments = radiusSegments; // higher segment count for a smoother circle
  final double capThickness = 0.002; // very thin to remain flat
  final double capRadius = tubeRadius; // match tube radius for honeycomb bundle size

  final startCap = CylinderGeometry(capRadius, capRadius, capThickness, capSegments);
  // Move slightly inside along +Y so the outer face is flush and does not protrude
  startCap.translate(startPoint.x, startPoint.y + capThickness / 2.0, startPoint.z);

  final endCap = CylinderGeometry(capRadius, capRadius, capThickness, capSegments);
  // Move slightly inside along -Y at the end
  endCap.translate(endPoint.x, endPoint.y - capThickness / 2.0, endPoint.z);

  return [tube, startCap, endCap];
}


three.BufferGeometry createDBSlat(double radius, double slatLength, double gridSize,
    double x60jump, double y60jump, bool tipExtensions, bool hexaTilt,
    {List<List<double>>? helixBundlePositions, bool honeyCombVariant = false,
      bool drawBVariant = false}) {

  List<Vector3> pathPoints;
  List<three.BufferGeometry> geometries = [];

  if (!honeyCombVariant) {
    // slightly tilted variant to match 60deg grid
    if (hexaTilt) {
      pathPoints = [
        // start
        if (tipExtensions)
          tmath.Vector3(0, -gridSize, 0)
        else
          tmath.Vector3(0, 0, 0),
        // go up
        tmath.Vector3(0, slatLength, 0),
        // across (now towards negative Z)
        if (drawBVariant)
          tmath.Vector3(0, slatLength - y60jump, -x60jump)
        else
          tmath.Vector3(0, slatLength + y60jump, -x60jump),
        // down to end
        if (drawBVariant)
          tmath.Vector3(0, -y60jump - (tipExtensions ? gridSize : 0), -x60jump)
        else
          tmath.Vector3(0, y60jump - (tipExtensions ? gridSize : 0), -x60jump),
      ];
    }
    // standard 90deg variant
    else {
      pathPoints = [
        // start
        if (tipExtensions)
          tmath.Vector3(0, -gridSize * 0.5, 0)
        else
          tmath.Vector3(0, 0, 0),
        // go up
        tmath.Vector3(0, slatLength, 0),
        // across (now towards negative Z)
        tmath.Vector3(0, slatLength, -gridSize),
        // down to end
        if (tipExtensions)
          tmath.Vector3(0, -gridSize * 0.5, -gridSize)
        else
          tmath.Vector3(0, 0, -gridSize),
      ];
    }
    geometries = drawTube(pathPoints, radius);
  }
  else {
    for (final pos in helixBundlePositions!) {
      List<three.BufferGeometry> localGeometries = [];
      if (pos[0] != 0){
        // do not connect tubes together for side helices
        if (hexaTilt) {
          // Construct two vertical legs (up and down) with proper offset so they don't overlap
          // Up leg: from startY to slatLength

          // Down leg: from (slatLength + y60jump - offset) down to endY2
          double bOffset = (pos[0] < 0 && drawBVariant) ? radius * 2.0 : 0.0;
          final double startY1 = tipExtensions ? -gridSize : 0.0;
          final double endY1 = slatLength - bOffset;
          final double height1 = (endY1 - startY1).abs();

          var c1 = CylinderGeometry(radius, radius, height1, 20);

          // place at midpoint between start and end (the geometry's placement origin is at its center)
          c1.translate(0, (startY1 + endY1) / 2.0, 0);
          localGeometries.add(c1);

          // Down leg: from (slatLength + y60jump - offset) down to endY2
          double offset = (pos[0] > 0 && !drawBVariant) ? radius * 2.0 : 0.0;

          final double startY2 = slatLength + (drawBVariant? -y60jump : y60jump) - offset; // higher or lower Y
          double endY2 = tipExtensions ? (y60jump - gridSize) : y60jump; // lower Y
          if (drawBVariant){ // B variant goes further down
            endY2 -= 2*y60jump;
          }

          final double height2 = (startY2 - endY2);

          var c2 = CylinderGeometry(radius, radius, height2, 20);
          c2.translate(0, (startY2 + endY2) / 2.0, -x60jump); // the x60jump moves it to the other leg
          localGeometries.add(c2);
        }
        // standard 90deg variant (same system as above)
        else {
          // Construct two vertical legs (up and down) with proper offset so they don't overlap

          // Up leg: from startY to slatLength
          final double startY1 = tipExtensions ? -gridSize : 0.0;
          final double endY1 = slatLength;
          final double height1 = (endY1 - startY1).abs();

          var c1 = CylinderGeometry(radius, radius, height1, 20);
          // place at midpoint between start and end (the geometry's placement origin is at its center)
          c1.translate(0, (startY1 + endY1) / 2.0, 0);
          localGeometries.add(c1);

          // Down leg
          final double startY2 = slatLength; // higher Y
          final double endY2 = tipExtensions ? - gridSize : 0; // lower Y
          final double height2 = (startY2 - endY2);

          var c2 = CylinderGeometry(radius, radius, height2, 20);
          c2.translate(0, (startY2 + endY2) / 2.0, -gridSize);
          localGeometries.add(c2);
        }
      }
      else {
        // run the normal u-connection pathing for the top/bottom helices
        // slightly tilted variant to match 60deg grid
        if (hexaTilt) {
          pathPoints = [
            // start
            if (tipExtensions)
              tmath.Vector3(0, -gridSize, 0)
            else
              tmath.Vector3(0, 0, 0),
            // go up
            tmath.Vector3(0, slatLength, 0),
            // across (now towards negative Z)
            if (drawBVariant)
              tmath.Vector3(0, slatLength - y60jump, -x60jump)
            else
              tmath.Vector3(0, slatLength + y60jump, -x60jump),
            // down to end
            if (drawBVariant)
            tmath.Vector3(0, -y60jump - (tipExtensions ? gridSize : 0), -x60jump)
            else
            tmath.Vector3(0, y60jump - (tipExtensions ? gridSize : 0), -x60jump),
          ];
        }
        // standard 90deg variant
        else {
          pathPoints = [
            // start
            if (tipExtensions)
              tmath.Vector3(0, -gridSize, 0)
            else
              tmath.Vector3(0, 0, 0),
            // go up
            tmath.Vector3(0, slatLength, 0),
            // across (now towards negative Z)
            tmath.Vector3(0, slatLength, -gridSize),
            // down to end
            if (tipExtensions)
              tmath.Vector3(0, -gridSize, -gridSize)
            else
              tmath.Vector3(0, 0, -gridSize),
          ];
        }
        localGeometries = drawTube(pathPoints, radius);
      }

      for (var geometry in localGeometries) {
        // Translate the geometry to its position
        geometry.translate(pos[1], 0, pos[0]);
        geometries.add(geometry);
      }
    }
  }
  // Merge tube and caps into one BufferGeometry
  final merged = three.BufferGeometry();
  final mergedPositions = <double>[];
  final mergedNormals = <double>[];
  final mergedIndices = <int>[];
  int indexOffset = 0;

  void appendGeometry(three.BufferGeometry g) {
    final posAttr = g.attributes['position'] as tmath.BufferAttribute;
    final normAttr = g.attributes['normal'] as tmath.BufferAttribute;
    // copy vertices
    for (int i = 0; i < posAttr.count; i++) {
      mergedPositions.add(posAttr.getX(i)!.toDouble());
      mergedPositions.add(posAttr.getY(i)!.toDouble());
      mergedPositions.add(posAttr.getZ(i)!.toDouble());
      mergedNormals.add(normAttr.getX(i)!.toDouble());
      mergedNormals.add(normAttr.getY(i)!.toDouble());
      mergedNormals.add(normAttr.getZ(i)!.toDouble());
    }
    if (g.index != null) {
      final idx = g.index!;
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

  // put all the geometry parts together
  for (var geom in geometries){
    appendGeometry(geom);
  }

  merged.setAttributeFromString('position', tmath.Float32BufferAttribute.fromList(mergedPositions, 3));
  merged.setAttributeFromString('normal', tmath.Float32BufferAttribute.fromList(mergedNormals, 3));
  merged.setIndex(tmath.Uint32BufferAttribute.fromList(mergedIndices, 1));

  // Center the geometry around origin for easier manipulation later
  double minX = double.infinity, minY = double.infinity, minZ = double.infinity;
  double maxX = -double.infinity, maxY = -double.infinity, maxZ = -double.infinity;

  for (int i = 0; i < mergedPositions.length; i += 3) {
    final x = mergedPositions[i];
    final y = mergedPositions[i + 1];
    final z = mergedPositions[i + 2];
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (z < minZ) minZ = z;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
    if (z > maxZ) maxZ = z;
  }
  final cx = (minX + maxX) * 0.5;
  final cy = (minY + maxY) * 0.5;
  final cz = (minZ + maxZ) * 0.5;

  merged.translate(-cx, -cy, -cz);

  return merged;
}


three.BufferGeometry createHoneyCombSlat(List<List<double>> helixBundlePositions, double helixBundleSize, double gridSize, bool tipExtensions) {

  final mergedGeometry = three.BufferGeometry();
  final mergedPositions = <double>[];
  final mergedNormals = <double>[];
  final mergedIndices = <int>[];

  int indexOffset = 0;

  for (var pos in helixBundlePositions) {

    // Create cylinder geometry
    CylinderGeometry geometry = CylinderGeometry(helixBundleSize/2, helixBundleSize/2, tipExtensions? gridSize * 32 : gridSize * 31, 20);

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

/// Builds a stylised Y-shaped IgG antibody as a single merged [three.BufferGeometry].
///
/// The molecule is assembled from rounded capsule "domains" arranged in the classic
/// antibody Y: a two-legged Fc stem pointing down, a central hinge, and two Fab arms
/// angled up in a V. Each Fab arm is made of an inner (heavy-chain) capsule pair and a
/// shorter outer (light-chain) capsule, giving the 12-domain look of a typical antibody
/// cartoon. The whole geometry is centred on the origin and stands upright along +Y so
/// it can be dropped into the cargo instance system in place of the default box.
///
/// [scale] uniformly scales the whole molecule (default sizes it to roughly match the
/// standard cargo box footprint).
three.BufferGeometry createAntibody({double scale = 1.0}) {
  // Collected sub-geometries that will be merged into a single buffer at the end.
  final List<three.BufferGeometry> parts = [];

  // ── Base dimensions (before [scale]) ──
  const double domainRadius = 0.7;   // thickness of each capsule domain
  const double domainLength = 2.2;   // length of a single capsule domain
  const double domainStep = 2.4;     // centre-to-centre spacing of stacked domains
  const double armAngle = 0.75;      // Fab arm splay from vertical (radians, ~43°)

  /// Adds a capsule domain of the given [length] whose local +Y axis is first rotated by
  /// [angleZ] (around Z, so the arm splays in the X-Y plane) and then translated so its
  /// centre sits at ([cx], [cy]).
  ///
  /// [radius] controls the capsule thickness (defaults to a full protein domain); the thin
  /// disulfide bridge passes a smaller value.
  ///
  /// The capsule is built by hand from a Y-aligned cylinder plus two hemispherical caps
  /// (rather than [CapsuleGeometry], whose factory throws a type-cast error in this
  /// version of three_js_geometry).
  void addDomain(double cx, double cy, double length, double angleZ, {double radius = domainRadius}) {
    final List<three.BufferGeometry> capParts = [];

    // Central cylinder along Y, centred on the origin.
    final body = CylinderGeometry(radius, radius, length, 16);
    capParts.add(body);

    // Rounded caps at each end (full spheres are cheap and read as smooth caps).
    final topCap = three.SphereGeometry(radius, 12, 12);
    topCap.translate(0, length / 2, 0);
    capParts.add(topCap);

    final bottomCap = three.SphereGeometry(radius, 12, 12);
    bottomCap.translate(0, -length / 2, 0);
    capParts.add(bottomCap);

    for (final geom in capParts) {
      if (angleZ != 0) geom.rotateZ(angleZ);
      geom.translate(cx, cy, 0);
      parts.add(geom);
    }
  }

  // Half-height of the open hinge gap that separates the Fc stem (below) from the Fab
  // arms (above). The disulfide bridge lives inside this gap so the two halves read as
  // distinct sub-structures rather than one squished blob.
  const double hingeGapHalf = 1.1;
  // Y of the top of the Fc stem / bottom of the hinge gap.
  const double stemTopY = -hingeGapHalf;
  // Y of the arm hinge point / top of the hinge gap.
  const double armHingeY = hingeGapHalf;

  // ── Fc stem: two parallel vertical legs, each two domains tall, pointing down ──
  const double legOffsetX = domainRadius * 1.1; // half-gap between the two stem legs
  for (final sign in [-1.0, 1.0]) {
    final double x = sign * legOffsetX;
    // Upper domain of the leg (its top meets the bottom of the hinge gap).
    final double upperCentre = stemTopY - domainLength * 0.5;
    addDomain(x, upperCentre, domainLength, 0);
    // Lower domain of the leg, stacked below the upper one.
    addDomain(x, upperCentre - domainStep, domainLength, 0);
  }

  // Thin radius reused for all disulfide bonds (inter-chain bridge + H–L bonds).
  const double bridgeRadius = domainRadius * 0.28; // thin compared to a full domain

  // ── Two Fab arms: each an inner (heavy) domain pair plus an outer (light) domain pair,
  //    joined by a short inter-chain disulfide bond. ──
  for (final sign in [-1.0, 1.0]) {
    final double angle = sign * armAngle; // splay left/right

    // Direction of the arm (unit vector) so we can stack domains along it.
    final double dirX = sin(angle);
    final double dirY = cos(angle);

    // Unit vector perpendicular to the arm, pointing to the outer (light-chain) side.
    final double perpX = cos(angle);
    final double perpY = -sin(angle);

    // Hinge point where the arm leaves the stem (top of the open hinge gap). Each arm
    // starts directly above its own stem leg (±legOffsetX) so the two arms are separated
    // rather than converging into a single V at the centre.
    final double hingeX = sign * legOffsetX;
    const double hingeY = armHingeY;

    // Perpendicular offset from the heavy chain to the parallel light chain. Kept above a
    // full domain diameter (2 × radius) so the two chains sit side-by-side with a visible
    // gap rather than overlapping.
    final double sideOffset = sign * domainRadius * 2.6;

    // Inner (heavy-chain) arm: two domains stacked along the arm direction.
    for (int i = 0; i < 2; i++) {
      final double dist = domainStep * (0.5 + i);
      addDomain(hingeX + dirX * dist, hingeY + dirY * dist, domainLength, -angle);
    }

    // Outer (light-chain) arm: two domains running parallel to the heavy chain, offset
    // perpendicular so they read as a distinct second chain (as in a real Fab).
    for (int i = 0; i < 2; i++) {
      final double dist = domainStep * (0.5 + i);
      addDomain(
        hingeX + dirX * dist + perpX * sideOffset,
        hingeY + dirY * dist + perpY * sideOffset,
        domainLength,
        -angle,
      );
    }

    // Inter-chain disulfide bond: a short rung across the gap linking the light and heavy
    // chains at the middle of the outer (second) segment, perpendicular to the arm.
    final double bondDist = domainStep / 1.7;
    addDomain(
      hingeX + dirX * bondDist + perpX * sideOffset * 0.5,
      hingeY + dirY * bondDist + perpY * sideOffset * 0.5,
      sideOffset.abs(),
      -angle - pi / 2,
      radius: bridgeRadius,
    );
  }

  // ── Inter-heavy-chain disulfide bridge: two vertical strands spanning the hinge gap,
  //    aligned with the two stem legs and linked by horizontal rungs into a ladder. ──
  const double bridgeLength = hingeGapHalf * 2; // strands span the full open gap
  const double bridgeHalfSep = legOffsetX;      // strands sit above the two stem legs
  for (final sign in [-1.0, 1.0]) {
    addDomain(sign * bridgeHalfSep, 0, bridgeLength, 0, radius: bridgeRadius);
  }
  // Horizontal rungs linking the two strands.
  for (final rungY in [-hingeGapHalf * 0.35, hingeGapHalf * 0.35]) {
    addDomain(0, rungY, bridgeHalfSep * 2, pi / 2, radius: bridgeRadius);
  }

  // ── Merge all parts into a single BufferGeometry (positions, normals, indices) ──
  final merged = three.BufferGeometry();
  final mergedPositions = <double>[];
  final mergedNormals = <double>[];
  final mergedIndices = <int>[];
  int indexOffset = 0;

  void appendGeometry(three.BufferGeometry g) {
    final posAttr = g.attributes['position'] as tmath.BufferAttribute;
    final normAttr = g.attributes['normal'] as tmath.BufferAttribute;
    for (int i = 0; i < posAttr.count; i++) {
      mergedPositions.add(posAttr.getX(i)!.toDouble());
      mergedPositions.add(posAttr.getY(i)!.toDouble());
      mergedPositions.add(posAttr.getZ(i)!.toDouble());
      mergedNormals.add(normAttr.getX(i)!.toDouble());
      mergedNormals.add(normAttr.getY(i)!.toDouble());
      mergedNormals.add(normAttr.getZ(i)!.toDouble());
    }
    if (g.index != null) {
      final idx = g.index!;
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

  for (final part in parts) {
    appendGeometry(part);
  }

  merged.setAttributeFromString('position', tmath.Float32BufferAttribute.fromList(mergedPositions, 3));
  merged.setAttributeFromString('normal', tmath.Float32BufferAttribute.fromList(mergedNormals, 3));
  merged.setIndex(tmath.Uint32BufferAttribute.fromList(mergedIndices, 1));

  // Centre the merged geometry around the origin so it positions like the other cargo.
  double minX = double.infinity, minY = double.infinity, minZ = double.infinity;
  double maxX = -double.infinity, maxY = -double.infinity, maxZ = -double.infinity;
  for (int i = 0; i < mergedPositions.length; i += 3) {
    final x = mergedPositions[i];
    final y = mergedPositions[i + 1];
    final z = mergedPositions[i + 2];
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (z < minZ) minZ = z;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
    if (z > maxZ) maxZ = z;
  }
  merged.translate(-(minX + maxX) * 0.5, -(minY + maxY) * 0.5, -(minZ + maxZ) * 0.5);

  // Apply the overall scale factor.
  if (scale != 1.0) merged.scale(scale, scale, scale);

  return merged;
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