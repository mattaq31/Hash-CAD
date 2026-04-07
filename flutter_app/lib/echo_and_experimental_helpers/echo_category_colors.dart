import 'package:flutter/material.dart';
import 'package:pdf/pdf.dart';

const Color _defaultColor = Colors.purpleAccent;
const int _defaultColorHex = 0xFFE040FB; // Colors.purpleAccent
const int defaultCategoryColorHex = _defaultColorHex;

const Map<String, int> handleCategoryColors = {
  'FLAT': 0xFFE0E0E0, // grey
  'ASSEMBLY_HANDLE': 0xFFF44336, // red
  'ASSEMBLY_ANTIHANDLE': 0xFFF44336, // red
  'SEED': 0xFF4CAF50, // green
  'CARGO': 0xFF2196F3, // blue
  'MANUAL': 0xFFFF9800, // orange
};

const int emptyCategoryColorHex = 0xFFE0E0E0; // grey.shade300

/// Returns a color for direct use
Color categoryColor(String? category) {
  if (category == null) return Color(emptyCategoryColorHex);
  final hex = handleCategoryColors[category.toUpperCase()];
  if (hex == null) return _defaultColor;
  return Color(hex);
}

/// Returns a color for use in PDF report generation
PdfColor pdfCategoryColor(String? category) {
  if (category == null) return PdfColor.fromInt(emptyCategoryColorHex);
  final hex = handleCategoryColors[category.toUpperCase()];
  if (hex == null) return PdfColor.fromInt(_defaultColorHex);
  return PdfColor.fromInt(hex);
}
