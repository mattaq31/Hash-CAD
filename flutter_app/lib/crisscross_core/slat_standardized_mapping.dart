import 'dart:math';
import 'parasitic_valency.dart';

/// Convert a square-grid coordinate (row=x, col=y) to triangular coordinates.
/// Python reference: convert_to_triangular(coord) -> (-y, (x+y)/2)
/// We keep the same row/col ordering as in the Python helper.
({int r, int c}) _toTriangular(({int r, int c}) sq) {
  final x = sq.r; // row index
  final y = sq.c; // col index
  final rTri = -y;                 // new row
  final cTri = ((x + y) / 2).floor(); // new col (integer)
  return (r: rTri, c: cTri);
}

/// Convert a list of triangular lattice coordinates (in order) into
/// a compact 2D array where each cell stores the 1-based index of the position.
IntGrid _triCoordsToArray(List<({int r, int c})> coords) {
  if (coords.isEmpty) return [[]];

  int minR = coords.first.r, maxR = coords.first.r;
  int minC = coords.first.c, maxC = coords.first.c;
  for (final p in coords) {
    minR = min(minR, p.r);
    maxR = max(maxR, p.r);
    minC = min(minC, p.c);
    maxC = max(maxC, p.c);
  }

  final h = (maxR - minR + 1);
  final w = (maxC - minC + 1);
  final arr = List.generate(h, (_) => List<int>.filled(w, 0));

  for (int idx = 0; idx < coords.length; idx++) {
    final r = coords[idx].r - minR;
    final c = coords[idx].c - minC;
    arr[r][c] = idx + 1; // 1-based position index
  }
  return arr;
}

/// Base arrays from Python (all_slat_maps). Each row corresponds to a slat position (1..32),
/// and each of the two columns indicates whether that position belongs to column 0 or 1.
/// We copy these exactly so that the downstream triangular transform matches Python.
final Map<String, List<List<int>>> _allSlatMaps = {
  'DB-L-120': [
    [0, 0], [0, 1], [32, 0], [0, 2], [31, 0], [0, 3], [30, 0], [0, 4],
    [29, 0], [0, 5], [28, 0], [0, 6], [27, 0], [0, 7], [26, 0], [0, 8],
    [25, 0], [0, 9], [24, 0], [0, 10], [23, 0], [0, 11], [22, 0], [0, 12],
    [21, 0], [0, 13], [20, 0], [0, 14], [19, 0], [0, 15], [18, 0], [0, 16],
    [17, 0],
  ],
  'DB-L-60': [
    [32, 0], [0, 1], [31, 0], [0, 2], [30, 0], [0, 3], [29, 0], [0, 4],
    [28, 0], [0, 5], [27, 0], [0, 6], [26, 0], [0, 7], [25, 0], [0, 8],
    [24, 0], [0, 9], [23, 0], [0, 10], [22, 0], [0, 11], [21, 0], [0, 12],
    [20, 0], [0, 13], [19, 0], [0, 14], [18, 0], [0, 15], [17, 0], [0, 16],
  ],
  'DB-R-60': [
    [0, 0], [0, 32], [1, 0], [0, 31], [2, 0], [0, 30], [3, 0], [0, 29],
    [4, 0], [0, 28], [5, 0], [0, 27], [6, 0], [0, 26], [7, 0], [0, 25],
    [8, 0], [0, 24], [9, 0], [0, 23], [10, 0], [0, 22], [11, 0], [0, 21],
    [12, 0], [0, 20], [13, 0], [0, 19], [14, 0], [0, 18], [15, 0], [0, 17],
    [16, 0],
  ],
  'DB-R-120': [
    [1, 0], [0, 32], [2, 0], [0, 31], [3, 0], [0, 30], [4, 0], [0, 29],
    [5, 0], [0, 28], [6, 0], [0, 27], [7, 0], [0, 26], [8, 0], [0, 25],
    [9, 0], [0, 24], [10, 0], [0, 23], [11, 0], [0, 22], [12, 0], [0, 21],
    [13, 0], [0, 20], [14, 0], [0, 19], [15, 0], [0, 18], [16, 0], [0, 17],
  ],
};

/// Build the standardized mapping arrays just like Python’s for each slat type.
/// Each grid holds 1..32 in the appropriate triangular coordinates.
final Map<String, IntGrid> standardizedSlatMappings = (() {
  final out = <String, IntGrid>{};

  _allSlatMaps.forEach((slatType, base) {
    // 1) Extract (row, col) of nonzero entries and their value, keeping the row ordering
    final coordsWithVal = <({int r, int c, int v})>[];
    for (int r = 0; r < base.length; r++) {
      for (int c = 0; c < base[r].length; c++) {
        final v = base[r][c];
        if (v > 0) coordsWithVal.add((r: r, c: c, v: v));
      }
    }
    // 2) Sort by the stored value ascending to match Python’s position order
    coordsWithVal.sort((a, b) => a.v.compareTo(b.v));

    // 3) Convert each to triangular coordinates in that order
    final tri = <({int r, int c})>[];
    for (final q in coordsWithVal) {
      tri.add(_toTriangular((r: q.r, c: q.c)));
    }

    // 4) Normalize to 0-based array indices and place 1..N
    out[slatType] = _triCoordsToArray(tri);
  });

  return out;
})();

/// Given a 1D ordered slat array (length 32) and a slat type,
/// place the values onto a standardized 2D grid as per the template.
IntGrid generateStandardizedSlatHandleArray(List<int> slat1D, String slatType) {
  final template = standardizedSlatMappings[slatType];
  if (template == null || template.isEmpty) {
    // Fallback: return a single-row copy
    return [List<int>.from(slat1D)];
  }
  final h = template.length;
  final w = template[0].length;
  final out = List.generate(h, (_) => List<int>.filled(w, 0));

  // For each cell in the template, copy the value at index (template-1)
  for (int r = 0; r < h; r++) {
    for (int c = 0; c < w; c++) {
      final idx = template[r][c];
      if (idx > 0) {
        final p = idx - 1; // 0-based position
        if (p >= 0 && p < slat1D.length) {
          out[r][c] = slat1D[p];
        }
      }
    }
  }
  return out;
}
