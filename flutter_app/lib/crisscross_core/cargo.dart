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

  Cargo({required this.name, required this.shortName, required this.color});
}