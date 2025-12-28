import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'slats.dart';
import 'slat_standardized_mapping.dart';

// Treat all per-slat arrays as 2D "grids" of ints (even 1D slats as [ [L] ])
typedef IntGrid = List<List<int>>;

List<List<List<int>>> generateRandomSlatHandles(List<List<List<int>>> baseArray, int uniqueSequences, {int seed=8}) {
  int xSize = baseArray.length;
  int ySize = baseArray[0].length;
  int numLayers = baseArray[0][0].length;

  List<List<List<int>>> handleArray = List.generate(xSize, (_) => List.generate(ySize, (_) => List.filled(numLayers-1, 0)));

  Random rand = Random(seed);
  for (int i = 0; i < xSize; i++) {
    for (int j = 0; j < ySize; j++) {
      for (int k = 0; k < numLayers - 1; k++) {
        // Check if slats exist in the current and next layer
        if (baseArray[i][j][k] != 0 && baseArray[i][j][k + 1] != 0) {
          handleArray[i][j][k] = rand.nextInt(uniqueSequences) + 1; // Random value between 1 and uniqueSequences
        }
      }
    }
  }
  return handleArray;
}

List<List<List<int>>> generateLayerSplitHandles(List<List<List<int>>> baseArray, int uniqueSequences, {int seed = 8}) {
  int xSize = baseArray.length;
  int ySize = baseArray[0].length;
  int numLayers = baseArray[0][0].length;

  // Initialize the handle array with zeros
  List<List<List<int>>> handleArray = List.generate(xSize, (_) => List.generate(ySize, (_) => List.filled(numLayers - 1, 0)));

  Random rand = Random(seed);

  for (int i = 0; i < xSize; i++) {
    for (int j = 0; j < ySize; j++) {
      for (int k = 0; k < numLayers - 1; k++) {

        int h1, h2;
        if (k % 2 == 0) {
          h1 = 1;
          h2 = (uniqueSequences ~/ 2) + 1;
        } else {
          h1 = (uniqueSequences ~/ 2) + 1;
          h2 = uniqueSequences + 1;
        }

        // Check if slats exist in the current and next layer
        if (baseArray[i][j][k] != 0 && baseArray[i][j][k + 1] != 0) {
          handleArray[i][j][k] = rand.nextInt(h2 - h1) + h1; // Random value between 1 and uniqueSequences
        }
      }
    }
  }

  return handleArray;
}


Map<int, int> getSlatMatchCounts(List<List<List<int>>> slatArray, List<List<List<int>>> handleArray, Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, Offset minGrid) {

  String? getLayerByOrder(int order) {
    for (final entry in layerMap.entries) {
      if (entry.value['order'] == order) {
        return entry.key;
      }
    }
    return null;
  }

  // Histogram: {number of matches between a pair: number of slat pairs having that many matches}
  final Map<int, int> matchHistogram = <int, int>{};
  final Set<String> completedSlats = <String>{};

  if (slatArray.isEmpty || handleArray.isEmpty) {
    return matchHistogram;
  }

  final layers = slatArray[0][0].length;
  if (layers < 1) return matchHistogram;

  for (final entry in slats.entries) {
    if (entry.value.phantomParent != null) {
      continue; // skip phantom slats
    }
    final sKey = entry.key; // expected like A-I1
    final slat = entry.value;

    // Skip if no coordinates
    if (slat.slatPositionToCoordinate.isEmpty) {
      completedSlats.add(sKey);
      continue;
    }
    final int slatLayer = layerMap[slat.layer]!['order'] + 1; // 1-based

    final Map<String, int> matchesWithOtherSlats = <String, int>{};

    // Check slats in the layer above (interface index = slatLayer - 1)
    if (slatLayer < layers) {
      for (final coord in slat.slatPositionToCoordinate.values) {
        final y = (coord.dy - minGrid.dy).toInt();
        final x = (coord.dx - minGrid.dx).toInt();

        // handle array z-index for above interface
        final z = slatLayer - 1; // 0-based

        if (z < 0 || z >= handleArray[0][0].length) continue;

        final hasHandle = handleArray[x][y][z] != 0;
        if (!hasHandle) continue;

        final otherSlatId = slatArray[x][y][slatLayer]; // layer above: index slatLayer
        if (otherSlatId == 0) continue;

        final otherKey = '${getLayerByOrder(slatLayer)}-I$otherSlatId';
        if (!completedSlats.contains(otherKey)) {
          matchesWithOtherSlats[otherKey] = (matchesWithOtherSlats[otherKey] ?? 0) + 1;
        }
      }
    }

    // Check slats in the layer below (interface index = slatLayer - 2)
    if (slatLayer > 1) {
      for (final coord in slat.slatPositionToCoordinate.values) {
        final y = (coord.dy - minGrid.dy).toInt();
        final x = (coord.dx - minGrid.dx).toInt();

        final z = slatLayer - 2; // 0-based
        if (z < 0 || z >= handleArray[0][0].length) continue;

        final hasHandle = handleArray[x][y][z] != 0;
        if (!hasHandle) continue;

        final otherSlatId = slatArray[x][y][slatLayer - 2]; // layer below: index slatLayer - 2
        if (otherSlatId == 0) continue;

        final otherKey = '${getLayerByOrder(slatLayer - 2)}-I$otherSlatId';
        if (!completedSlats.contains(otherKey)) {
          matchesWithOtherSlats[otherKey] = (matchesWithOtherSlats[otherKey] ?? 0) + 1;
        }
      }
    }

    // Update global histogram: for each pair counted once
    for (final count in matchesWithOtherSlats.values) {
      matchHistogram[count] = (matchHistogram[count] ?? 0) + 1;
    }

    // Prevent double counting this slat with others later
    completedSlats.add(sKey);
  }

  return matchHistogram;
}

/// Count histogram of equality-overlap matches for one A–B pair (2D case).
/// A and B are 2D grids of ints (uint-like); zeros are “don’t care”.
/// We slide B over A across all offsets and, at each overlap window, count
/// the number of positions where (a != 0 && b != 0 && a == b).
Map<int, int> _histForPair2D(IntGrid A, IntGrid B) {
  final Ha = A.length;
  final Wa = A[0].length;
  final Hb = B.length;
  final Wb = B[0].length;

  final Ho = Ha + Hb - 1; // vertical offsets
  final Wo = Wa + Wb - 1; // horizontal offsets

  final hist = <int, int>{};

  for (int oy = 0; oy < Ho; oy++) {
    final by0 = ((Hb - 1) - oy < 0) ? 0 : (Hb - 1) - oy;
    final by1 = ((Ha + Hb - 2 - oy) > (Hb - 1)) ? (Hb - 1) : (Ha + Hb - 2 - oy);
    for (int ox = 0; ox < Wo; ox++) {
      final bx0 = ((Wb - 1) - ox < 0) ? 0 : (Wb - 1) - ox;
      final bx1 = ((Wa + Wb - 2 - ox) > (Wb - 1)) ? (Wb - 1) : (Wa + Wb - 2 - ox);

      int acc = 0;
      if (by1 >= by0 && bx1 >= bx0) {
        for (int by = by0; by <= by1; by++) {
          final ay = oy - (Hb - 1) + by;
          final Arow = A[ay];
          final Brow = B[by];
          for (int bx = bx0; bx <= bx1; bx++) {
            final ax = ox - (Wb - 1) + bx;
            final a = Arow[ax];
            final b = Brow[bx];
            if (a != 0 && b != 0 && a == b) acc++;
          }
        }
      }
      hist[acc] = (hist[acc] ?? 0) + 1;
    }
  }
  return hist;
}

/// Count histogram for a 1D–1D pair (both are single-row grids [[...]]).
/// We compute the classic 1D sliding without zero-padding: there are L+L-1
/// offsets. Zeros are “don’t care”; we count equal nonzero matches.
Map<int, int> _histForPair1D(List<int> aRow, List<int> bRow) {
  final La = aRow.length;
  final Lb = bRow.length;
  final numOffsets = La + Lb - 1; // e.g., 32+32-1 = 63

  final hist = <int, int>{};
  // Shift s in [-(Lb-1) .. (La-1)]: b over a. Convert to ox index 0..numOffsets-1 if needed.
  for (int s = -(Lb - 1); s <= (La - 1); s++) {
    int acc = 0;
    // Overlap indices in a: [max(0, s) .. min(La-1, s+Lb-1)]
    final aStart = (s > 0) ? s : 0;
    final aEnd = ((s + Lb - 1) < (La - 1)) ? (s + Lb - 1) : (La - 1);
    if (aEnd >= aStart) {
      for (int ai = aStart; ai <= aEnd; ai++) {
        final bi = ai - s; // because ai = s + bi
        final av = aRow[ai];
        final bv = bRow[bi];
        if (av != 0 && bv != 0 && av == bv) acc++;
      }
    }
    hist[acc] = (hist[acc] ?? 0) + 1;
  }
  return hist;
}

/// Utility to merge histogram maps by summation of counts per bin.
void _mergeHist(Map<int, int> target, Map<int, int> src) {
  src.forEach((k, v) => target[k] = (target[k] ?? 0) + v);
}

/// Decide if a grid is truly 2D (both dimensions >= 2)
bool _gridIs2D(IntGrid g) => g.isNotEmpty && g.length >= 2 && g[0].length >= 2;

bool _isTruly2D(IntGrid g) => g.isNotEmpty && g.length >= 2 && g[0].length >= 2;

// 1D reverse (used for classic 180° when arrays are single-row)
List<int> _reverse1D(List<int> row) {
  return row.reversed.toList(growable: false);
}

// Generic 2D 90° rotation (k quarter-turns counterclockwise)
IntGrid _rot90(IntGrid g, int k) {
  if (k % 4 == 0) return g.map((r) => List<int>.from(r)).toList();
  IntGrid out = g;
  int times = ((k % 4) + 4) % 4;
  for (int t = 0; t < times; t++) {
    final h = out.length;
    final w = out[0].length;
    final rot = List.generate(w, (_) => List<int>.filled(h, 0));
    for (int r = 0; r < h; r++) {
      for (int c = 0; c < w; c++) {
        rot[w - 1 - c][r] = out[r][c];
      }
    }
    out = rot;
  }
  return out;
}

// Triangular-lattice 60° rotations using axial-like integer coordinates.
// We interpret array indices (row=r, col=q) as axial coordinates (q, r).
// Rotation formulas around origin for k60 in {0..5}:
// k=0: (q, r)
// k=1: (-r, q + r)
// k=2: (-q - r, q)
// k=3: (-q, -r)
// k=4: (r, -q - r)
// k=5: (q + r, -q)
IntGrid _rotTri60(IntGrid g, int k60) {
  final k = ((k60 % 6) + 6) % 6;
  if (k == 0) {
    // Deep-copy to keep semantics consistent
    return g.map((r) => List<int>.from(r)).toList();
  }

  // Collect nonzeros with their coords (q=col, r=row)
  final pts = <({int q, int r, int v})>[];
  for (int r = 0; r < g.length; r++) {
    for (int c = 0; c < g[r].length; c++) {
      final v = g[r][c];
      if (v != 0) pts.add((q: c, r: r, v: v));
    }
  }
  if (pts.isEmpty) return g.map((r) => List<int>.from(r)).toList();

  ({int q, int r}) rotMap(int q, int r) {
    switch (k) {
      case 1: return (q: -r,      r: q + r);
      case 2: return (q: -q - r,  r: q);
      case 3: return (q: -q,      r: -r);
      case 4: return (q: r,       r: -q - r);
      case 5: return (q: q + r,   r: -q);
      default: return (q: q, r: r);
    }
  }

  // Rotate each point and track bounds
  var qMin = 1 << 30, qMax = -(1 << 30);
  var rMin = 1 << 30, rMax = -(1 << 30);
  final rotated = <({int q, int r, int v})>[];
  for (final p in pts) {
    final rr = rotMap(p.q, p.r);
    rotated.add((q: rr.q, r: rr.r, v: p.v));
    if (rr.q < qMin) qMin = rr.q;
    if (rr.q > qMax) qMax = rr.q;
    if (rr.r < rMin) rMin = rr.r;
    if (rr.r > rMax) rMax = rr.r;
  }

  final h = rMax - rMin + 1;
  final w = qMax - qMin + 1;
  final out = List.generate(h, (_) => List<int>.filled(w, 0));

  for (final p in rotated) {
    final rr = p.r - rMin;
    final cc = p.q - qMin;
    // In case of collisions (should not happen for templates), prefer max
    out[rr][cc] = (out[rr][cc] == 0) ? p.v : (out[rr][cc] > p.v ? out[rr][cc] : p.v);
  }
  return out;
}


class ParasiticInnerArgs {
  final Map<String, IntGrid> handleDict2D;
  final Map<String, IntGrid> antihandleDict2D;
  final Map<int, Map<String, IntGrid>> antiRotations;
  final List<int> angles;
  final Map<int, int> slatMatchCount;

  ParasiticInnerArgs(
      this.handleDict2D,
      this.antihandleDict2D,
      this.antiRotations,
      this.angles,
      this.slatMatchCount,
      );
}


Map<String, dynamic> parasiticInnerCompute(ParasiticInnerArgs args) {
  final handleDict2D = args.handleDict2D;
  final antihandleDict2D = args.antihandleDict2D;
  final antiRotations = args.antiRotations;
  final angles = args.angles;
  final slatMatchCount = args.slatMatchCount;

  // Equality-convolution histogram across all pairs and required rotations
  final handleKeys = handleDict2D.keys.toList();
  final antihandleKeys = antihandleDict2D.keys.toList();
  final Map<int, int> globalHist = <int, int>{};

  for (final hKey in handleKeys) {
    final A = handleDict2D[hKey]!;
    final aIs2D = _gridIs2D(A);
    final aIs1D = !aIs2D;

    for (final bKey in antihandleKeys) {
      final B0 = antihandleDict2D[bKey]!;
      final bIs2D = _gridIs2D(B0);
      final bIs1D = !bIs2D;

      final List<int> angleSetForPair = (aIs1D && bIs1D)
          ? <int>[0, 180]
          : angles;

      for (final ang in angleSetForPair) {
        final Brots = antiRotations[ang]!;
        final B = Brots[bKey]!;

        if (aIs1D && bIs1D) {
          final aRow = A.first;
          final bRow = B.first; // 180° already reversed/rotated at prep
          final h = _histForPair1D(aRow, bRow);
          _mergeHist(globalHist, h);
        } else {
          final h = _histForPair2D(A, B);
          _mergeHist(globalHist, h);
        }
      }
    }
  }

  // Compensation: subtract expected matches (>1) from histogram
  slatMatchCount.forEach((matches, pairCount) {
    if (matches > 1) {
      final histCount = globalHist[matches] ?? 0;
      final newCount = histCount - pairCount;
      if (newCount <= 0) {
        globalHist.remove(matches);
      } else {
        globalHist[matches] = newCount;
      }
    }
  });

  // Finishing: worst_match and mean_log_score
  int worstMatch = 1;
  const double fudge = 10.0;
  double sumScore = 0.0;
  final nA = handleDict2D.length;
  final nB = antihandleDict2D.length;

  globalHist.forEach((matches, pairCount) {
    if (pairCount > 0 && matches > worstMatch) worstMatch = matches;
    sumScore += pairCount * exp(fudge * matches);
  });

  final meanLogScore = (nA == 0 || nB == 0 || sumScore == 0.0)
      ? 0.0
      : log(sumScore / (nA * nB)) / fudge;

  return {
    'worst_match': worstMatch,
    'mean_log_score': meanLogScore,
  };
}



Future<Map<String, dynamic>> parasiticInteractionsCompute(Map<String, Slat> slats,
    List<List<List<int>>> slatArray, List<List<List<int>>> handleArray,
    Map<String, Map<String, dynamic>> layerMap, Offset minGrid, String connectionAngle) async {
  /// Computes the parasitic interactions of the current design in view.
  /// Function not optimized but will be infrequently called so slowdown is expected to be minimal.
  ///  Mimics logic in the eqcorr2d python library.

  if (slatArray.isEmpty || handleArray.isEmpty) {
    return {
      'worst_match': 0,
      'mean_log_score': 0.0,
    };
  }

  final int xSize = handleArray.length;
  final int ySize = handleArray[0].length;
  final int numInterfaces = handleArray[0][0].length; // layers - 1
  final int numLayers = slatArray[0][0].length;        // actual layers
  Map<int, int> slatMatchCount = getSlatMatchCounts(slatArray, handleArray, slats, layerMap, minGrid); // actual match counts from design, will be used to compensate histogram

  // Step 1: Build per-slat handle arrays from the grid, 1D for tube, 2D for non-tube (DB) slats
  // Represent 1D slats as a single-row 2D array [[...]] so we have a uniform type.
  final Map<String, List<List<int>>> handleDict2D = <String, List<List<int>>>{};
  final Map<String, List<List<int>>> antihandleDict2D = <String, List<List<int>>>{};

  // Helper that gathers ordered grid coordinates for a slat
  List<Offset> orderedCoordsForSlat(Slat slat) {
    final coords = <Offset>[];
    for (int pos = 1; pos <= slat.maxLength; pos++) {
      final c = slat.slatPositionToCoordinate[pos];
      if (c != null) coords.add(c);
    }
    return coords;
  }

  // Helper to index handleArray safely
  int getHandleAt(int gx, int gy, int gz) {
    if (gx < 0 || gx >= xSize) return 0;
    if (gy < 0 || gy >= ySize) return 0;
    if (gz < 0 || gz >= numInterfaces) return 0;
    return handleArray[gx][gy][gz];
  }


  for (final entry in slats.entries) {
    if (entry.value.phantomParent != null) {
      continue; // skip phantom slats
    }
    final slatKey = entry.key;
    final Slat slat = entry.value;

    // Determine layer indices
    final layerInfo = layerMap[slat.layer]!;
    final int order = layerInfo['order'];            // 0-based
    final int slatLayer1Based = order + 1;           // 1..numLayers

    // Collect all grid indices for this slat
    // We’ll compute both an ordered 1D list and the bounding box for 2D case
    final orderedCoords = orderedCoordsForSlat(slat);

    // Convert real coords to grid indices (int), using minGrid origin
    final orderedXY = orderedCoords.map((coord) {
      final y = (coord.dy - minGrid.dy).toInt();
      final x = (coord.dx - minGrid.dx).toInt();
      return Offset(x.toDouble(), y.toDouble());
    }).toList();

    // Compute bounding box
    int minX = 1 << 30, maxX = -(1 << 30), minY = 1 << 30, maxY = -(1 << 30);
    for (final o in orderedXY) {
      final x = o.dx.toInt();
      final y = o.dy.toInt();
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }

    final bool isTube = (slat.slatType == 'tube');

    // Above interface (handles) exists if slat is not in the last layer
    if (slatLayer1Based < numLayers) {
      final zAbove = slatLayer1Based - 1; // 0-based interface index
      if (isTube) {
        final row = <int>[];
        for (final o in orderedXY) {
          final x = o.dx.toInt();
          final y = o.dy.toInt();
          row.add(getHandleAt(x, y, zAbove));
        }
        handleDict2D[slatKey] = [row];
      } else {
        if (connectionAngle == '60') {
          // Build a 1D ordered list (positions 1..maxLength), then map to standardized 2D
          final row = <int>[];
          for (final o in orderedXY) {
            final x = o.dx.toInt();
            final y = o.dy.toInt();
            row.add(getHandleAt(x, y, zAbove));
          }
          handleDict2D[slatKey] = generateStandardizedSlatHandleArray(row, slat.slatType);
        } else {
          // 90°: extract the exact 2D bounding rectangle from the grid (as before)
          final width = maxX - minX + 1;
          final height = maxY - minY + 1;
          final grid = List.generate(height, (_) => List<int>.filled(width, 0));
          for (final o in orderedXY) {
            final x = o.dx.toInt();
            final y = o.dy.toInt();
            final lx = x - minX;
            final ly = y - minY;
            grid[ly][lx] = getHandleAt(x, y, zAbove);
          }
          handleDict2D[slatKey] = grid;
        }
      }
    }

    // Below interface (antihandles) exists if slat is not in the first layer
    if (slatLayer1Based > 1) {
      final zBelow = slatLayer1Based - 2; // 0-based interface index
      if (isTube) {
        final row = <int>[];
        for (final o in orderedXY) {
          final x = o.dx.toInt();
          final y = o.dy.toInt();
          row.add(getHandleAt(x, y, zBelow));
        }
        antihandleDict2D[slatKey] = [row];
      } else {
        if (connectionAngle == '60') {
          final row = <int>[];
          for (final o in orderedXY) {
            final x = o.dx.toInt();
            final y = o.dy.toInt();
            row.add(getHandleAt(x, y, zBelow));
          }
          antihandleDict2D[slatKey] = generateStandardizedSlatHandleArray(row, slat.slatType);
        } else {
          final width = maxX - minX + 1;
          final height = maxY - minY + 1;
          final grid = List.generate(height, (_) => List<int>.filled(width, 0));
          for (final o in orderedXY) {
            final x = o.dx.toInt();
            final y = o.dy.toInt();
            final lx = x - minX;
            final ly = y - minY;
            grid[ly][lx] = getHandleAt(x, y, zBelow);
          }
          antihandleDict2D[slatKey] = grid;
        }
      }
    }
  }

  // removes any slats that have no handles/antihandles at all
  int gridSum(IntGrid g) => g.fold(0, (s, r) => s + r.fold(0, (s2, v) => s2 + v));
  handleDict2D.removeWhere((_, grid) => gridSum(grid) == 0);
  antihandleDict2D.removeWhere((_, grid) => gridSum(grid) == 0);

  if (handleDict2D.isEmpty || antihandleDict2D.isEmpty) { // if no handles, just return
    return {
      'worst_match': 0,
      'mean_log_score': 0.0,
    };
  }

  // Prepare rotations for antihandles only, mirroring Python behavior
  // Decide if we have any truly 2D arrays among the slats (either side)
  final bool any2DHandle = handleDict2D.values.any((g) => _isTruly2D(g));
  final bool any2DAnti   = antihandleDict2D.values.any((g) => _isTruly2D(g));
  final bool any2D = any2DHandle || any2DAnti;

  // Determine angle sets based on connectionAngle and dimensionality
  late final List<int> angles;
  if (connectionAngle == '60') {
    angles = any2D ? [0, 60, 120, 180, 240, 300] : [0, 180];
  } else { // '90' or default
    angles = any2D ? [0, 90, 180, 270] : [0, 180];
  }

  // Build rotations for antihandles only: Map<angle, Map<slatKey, IntGrid>>
  final Map<int, Map<String, IntGrid>> antiRotations = {};

  // Helper: rotate a single IntGrid by the requested angle set
  IntGrid rotateGridByAngle(IntGrid g, int angle) {
    if (connectionAngle == '60') {
      // 60°-step group on triangular lattice
      final k60 = {0: 0, 60: 1, 120: 2, 180: 3, 240: 4, 300: 5}[angle]!;
      return _rotTri60(g, k60);
    } else {
      // Square grid quarter-turns
      final k = {0: 0, 90: 1, 180: 2, 270: 3}[angle]!;
      return _rot90(g, k);
    }
  }

  // prepares the rotated arrays for all antihandle slats
  for (final ang in angles) {
    final perAngle = <String, IntGrid>{};
    for (final entry in antihandleDict2D.entries) {
      final key = entry.key;
      final grid = entry.value;
      // Special-case pure 1D for classic 180°: reverse the row when angle=180
      if (!_isTruly2D(grid) && (connectionAngle != '60' || ang == 0 || ang == 180)) {
        // 1D arrays are stored as [ [L] ]
        if (ang == 0) {
          perAngle[key] = [List<int>.from(grid.first)];
        } else if (ang == 180) {
          perAngle[key] = [_reverse1D(grid.first)];
        } else {
          // If any2D is true we may still compute quarter-turns; just use 2D rotator
          perAngle[key] = rotateGridByAngle(grid, ang);
        }
      } else {
        perAngle[key] = rotateGridByAngle(grid, ang);
      }
    }
    antiRotations[ang] = perAngle;
  }
  // antiRotations now holds all pre-rotated B-side arrays.
  // Keep them local for now; the convolution step will pick which angles to use.

  // Build args and run the heavy convolution+compensation+scoring in an isolate
  final args = ParasiticInnerArgs(
    Map<String, IntGrid>.from(handleDict2D),
    Map<String, IntGrid>.from(antihandleDict2D),
    antiRotations.map((k, v) => MapEntry(k, Map<String, IntGrid>.from(v))),
    List<int>.from(angles),
    Map<int, int>.from(slatMatchCount),
  );

  return await compute(parasiticInnerCompute, args);

}