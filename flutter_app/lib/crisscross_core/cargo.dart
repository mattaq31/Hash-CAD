/// Cargo entity class for attaching payloads to slats.

import 'package:flutter/material.dart';

String generateShortName(String name) {
  final caps = RegExp(r'[A-Z]').allMatches(name).map((m) => m.group(0)!).toList();

  if (caps.length >= 2) {
    return (caps[0] + caps[1]);
  } else if (caps.length == 1) {
    // Use first char + the first capital letter
    return (name[0].toUpperCase() + caps[0]);
  } else {
    // Fallback to first two letters capitalized
    final trimmed = name.trim();
    if (trimmed.isEmpty) return '';
    return trimmed
        .substring(0, trimmed.length >= 2 ? 2 : trimmed.length)
        .toUpperCase();
  }
}

/// User-selectable cargo categories shown in the add/edit dialog.
/// 'default' renders as the standard block; 'antibody' renders as a sphere in 3D.
/// Extend this list to add further categories (also add matching 3D/palette handling).
/// Note: 'SEED' is a reserved category applied only to the seed entry and is never listed here.
const List<String> selectableCargoCategories = ['default', 'antibody'];

final List<Color> qualitativeCargoColors = [
  Color(0xFF1B9E77), // Teal
  Color(0xFFD95F02), // Orange/
  Color(0xFF7570B3), // Purple
  Color(0xFFE7298A), // Pink
  Color(0xFF66A61E), // Green
  Color(0xFFE6AB02), // Mustard
  Color(0xFFA6761D), // Brown
  Color(0xFF0034FF), // Blue
];

class Cargo {
  final String name;
  final String shortName;
  final Color color;

  /// Visual category of the cargo (e.g. 'default', 'antibody', or the reserved 'SEED').
  /// Controls how the cargo is rendered (e.g. sphere vs block in the 3D view).
  final String category;

  Cargo({required this.name, required this.shortName, required this.color, this.category = 'default'});
}