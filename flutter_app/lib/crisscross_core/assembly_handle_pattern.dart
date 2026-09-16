// Assembly handle pattern model: a named, reusable arrangement of assembly handles that can be stamped onto a design.

import 'package:flutter/material.dart';

import 'slats.dart';

/// A single handle within an [AssemblyHandlePattern].
///
/// [offset] is in grid coordinate space, relative to the pattern anchor (the top-left handle, which sits at
/// [Offset.zero]). Blocked handles are stored with [blocked] set and a value of '0'.
class AssemblyHandlePatternEntry {
  /// Grid-coordinate offset of this handle relative to the pattern anchor.
  final Offset offset;

  /// Assembly handle value (as a string, matching how values are stored on slats).
  final String value;

  /// Whether this position is a blocked handle rather than a regular value.
  final bool blocked;

  /// Creates a pattern entry at [offset] with [value], optionally marked as [blocked].
  const AssemblyHandlePatternEntry({required this.offset, required this.value, this.blocked = false});
}

/// A named group of assembly handles recorded from a selection, which can be placed repeatedly on the design.
///
/// Patterns are immutable; use [copyWith] to derive a renamed version.
class AssemblyHandlePattern {
  /// Session-unique identifier (not persisted to file - regenerated on import).
  final String id;

  /// User-facing name (unique within a design, as the Excel sheet groups rows by name).
  final String name;

  /// Handles making up the pattern, with offsets relative to the top-left anchor handle.
  final List<AssemblyHandlePatternEntry> entries;

  /// Creates a pattern; [entries] is stored as an unmodifiable list.
  AssemblyHandlePattern({required this.id, required this.name, required List<AssemblyHandlePatternEntry> entries})
      : entries = List.unmodifiable(entries);

  /// Returns a copy of this pattern with an updated [name].
  AssemblyHandlePattern copyWith({String? name}) {
    return AssemblyHandlePattern(id: id, name: name ?? this.name, entries: entries);
  }

  /// Returns the absolute grid coordinates of every entry (in entry order) when the anchor is placed at [anchorCoord].
  ///
  /// The pattern is rotated about its anchor by [rotationSteps] 90° steps using [rotateCoordinateSpace]. Rotation is
  /// only supported on the square ('90') grid, so [rotationSteps] is ignored for other grid modes.
  List<Offset> coordinatesAt(Offset anchorCoord, {int rotationSteps = 0, String gridMode = '90'}) {
    final steps = gridMode == '90' ? rotationSteps : 0;
    return entries.map((e) => rotateCoordinateSpace(anchorCoord + e.offset, anchorCoord, steps, gridMode)).toList();
  }
}

/// Returns the anchor of a set of grid coordinates: the top-left point (minimum y, then minimum x).
Offset findPatternAnchor(Iterable<Offset> coordinates) {
  return coordinates.reduce((a, b) {
    if (a.dy != b.dy) return a.dy < b.dy ? a : b;
    return a.dx <= b.dx ? a : b;
  });
}
