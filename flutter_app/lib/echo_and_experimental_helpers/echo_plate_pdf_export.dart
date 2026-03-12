import 'dart:typed_data';
import 'package:flutter/material.dart' show Color;
import 'package:flutter/services.dart' show rootBundle;
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../crisscross_core/slats.dart';
import 'echo_category_colors.dart';
import 'echo_plate_constants.dart' show designColorFor, slatDisplayName, wellWarningState;
import 'plate_layout_state.dart' show WellConfig, baseSlatId, isDuplicateSlatId;

// ---------------------------------------------------------------------------
// Page layout constants (landscape US Letter: 792 x 612 pt)
// ---------------------------------------------------------------------------

const double _margin = 28;
const double _usableWidth = 792 - 2 * _margin; // 736
const double _usableHeight = 612 - 2 * _margin; // 556

const double _titleHeight = 20;
const double _titleGap = 6;
const double _colHeaderHeight = 16;
const double _colGridGap = 12;
const double _gridLegendGap = 8;
const double _legendHeight = 20;

const double _rowHeaderWidth = 32;
const double _cellWidth = (_usableWidth - _rowHeaderWidth) / 12; // ~59.8
const double _cellHeight =
    (_usableHeight - _titleHeight - _titleGap - _colHeaderHeight - _colGridGap - _gridLegendGap - _legendHeight) / 8;

const double _chamfer = 6;
const double _outlineExpansion = 8;

// Grid dimensions
const double _gridWidth = _rowHeaderWidth + 12 * _cellWidth;
const double _gridHeight = 8 * _cellHeight;

// ---------------------------------------------------------------------------
// Legend entries (mirrors PlateColorKeyBar)
// ---------------------------------------------------------------------------

const List<(String, int)> _legendEntries = [
  ('Flat', 0xFFE0E0E0),
  ('Assembly Handle', 0xFFF44336),
  ('Seed', 0xFF4CAF50),
  ('Cargo', 0xFF2196F3),
  ('Manual', 0xFFFF9800),
  ('Undefined', 0xFFE040FB),
];

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

Future<Uint8List> buildPlateLayoutPdf(
  Map<int, Map<String, String?>> plateAssignments,
  Map<String, Slat> slats, {
  Map<int, String>? plateNames,
  Map<int, Map<String, WellConfig>>? wellConfigs,
  Map<String, Set<String>>? duplicateGroups,
  Map<String, Map<String, dynamic>>? layerMap,
  String experimentTitle = 'Experiment',
}) async {
  // Load Roboto fonts for cross-platform Unicode support
  final regularData = await rootBundle.load('fonts/Roboto/Roboto-Regular.ttf');
  final boldData = await rootBundle.load('fonts/Roboto/Roboto-Bold.ttf');
  final regular = pw.Font.ttf(regularData);
  final bold = pw.Font.ttf(boldData);

  final pdf = pw.Document(
    theme: pw.ThemeData.withFont(base: regular, bold: bold),
  );
  final rows = 'ABCDEFGH'.split('');
  final cols = List.generate(12, (i) => i + 1);

  final sortedKeys = plateAssignments.keys.toList()..sort();
  for (var i = 0; i < sortedKeys.length; i++) {
    final plateIndex = sortedKeys[i];
    final assignments = plateAssignments[plateIndex]!;
    final name = plateNames?[plateIndex] ?? 'Plate';
    final plateConfigs = wellConfigs?[plateIndex];

    pdf.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.letter.landscape,
        margin: const pw.EdgeInsets.all(_margin),
        build: (pw.Context context) {
          return pw.Column(
            children: [
              // --- Title row ---
              pw.SizedBox(
                height: _titleHeight,
                child: pw.Stack(
                  children: [
                    pw.Center(
                      child: pw.Text(
                        '$experimentTitle - $name',
                        style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold),
                      ),
                    ),
                    pw.Positioned(
                      right: 0,
                      top: 2,
                      child: pw.Text(
                        'Plate ${i + 1}',
                        style: pw.TextStyle(fontSize: 10, color: PdfColors.grey600),
                      ),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: _titleGap),
              // --- Column headers ---
              pw.Row(
                children: [
                  pw.SizedBox(width: _rowHeaderWidth, height: _colHeaderHeight),
                  for (var col in cols)
                    pw.Container(
                      width: _cellWidth,
                      height: _colHeaderHeight,
                      alignment: pw.Alignment.center,
                      child: pw.Text(
                        '$col',
                        style: pw.TextStyle(fontSize: 13, fontWeight: pw.FontWeight.bold, color: PdfColors.grey600),
                      ),
                    ),
                ],
              ),
              pw.SizedBox(height: _colGridGap),
              // --- Grid with chamfered border ---
              pw.SizedBox(
                width: _gridWidth,
                height: _gridHeight,
                child: pw.Stack(
                  overflow: pw.Overflow.visible,
                  children: [
                    // Well cells
                    pw.Row(
                      crossAxisAlignment: pw.CrossAxisAlignment.start,
                      children: [
                        // Row headers
                        pw.Column(
                          children: [
                            for (var row in rows)
                              pw.Container(
                                width: _rowHeaderWidth,
                                height: _cellHeight,
                                alignment: pw.Alignment.centerLeft,
                                padding: const pw.EdgeInsets.only(left: 4),
                                child: pw.Text(
                                  row,
                                  style: pw.TextStyle(
                                      fontSize: 13, fontWeight: pw.FontWeight.bold, color: PdfColors.grey600),
                                ),
                              ),
                          ],
                        ),
                        // Columns of wells
                        for (var col in cols)
                          pw.Column(
                            children: [
                              for (var row in rows)
                                _buildPdfWellCell(
                                  assignments,
                                  '$row$col',
                                  slats,
                                  plateConfigs,
                                  duplicateGroups,
                                  layerMap,
                                ),
                            ],
                          ),
                      ],
                    ),
                    // Chamfered plate outline — expanded beyond the grid
                    // so the chamfer diagonals clear all corner wells.
                    pw.Positioned(
                      left: _rowHeaderWidth - _outlineExpansion,
                      top: -_outlineExpansion,
                      child: pw.CustomPaint(
                        size: PdfPoint(
                          12 * _cellWidth + 2 * _outlineExpansion,
                          _gridHeight + 2 * _outlineExpansion,
                        ),
                        painter: (PdfGraphics canvas, PdfPoint size) {
                          final w = size.x;
                          final h = size.y;
                          const c = _chamfer;

                          canvas
                            ..moveTo(0, h) // A1 corner: square
                            ..lineTo(w - c, h) // top edge
                            ..lineTo(w, h - c) // A12 chamfer
                            ..lineTo(w, c) // right edge
                            ..lineTo(w - c, 0) // H12 chamfer
                            ..lineTo(c, 0) // bottom edge
                            ..lineTo(0, c) // H1 chamfer
                            ..closePath();
                          canvas.setStrokeColor(PdfColor.fromInt(0xFF616161));
                          canvas.setLineWidth(1.5);
                          canvas.strokePath();
                        },
                      ),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: _gridLegendGap),
              // --- Legend bar ---
              _buildLegendBar(),
            ],
          );
        },
      ),
    );
  }

  return await pdf.save();
}

// ---------------------------------------------------------------------------
// Helper: convert Flutter Color to PdfColor
// ---------------------------------------------------------------------------

PdfColor _toPdfColor(Color c) => PdfColor(c.r, c.g, c.b);

// ---------------------------------------------------------------------------
// Well cell
// ---------------------------------------------------------------------------

pw.Widget _buildPdfWellCell(
  Map<String, String?> assignments,
  String wellName,
  Map<String, Slat> slats,
  Map<String, WellConfig>? plateConfigs,
  Map<String, Set<String>>? duplicateGroups,
  Map<String, Map<String, dynamic>>? layerMap,
) {
  final slatId = assignments[wellName];
  final lookupId = slatId != null ? baseSlatId(slatId) : null;
  final slat = lookupId != null ? slats[lookupId] : null;
  final isOccupied = slat != null;
  final isDuplicate = slatId != null && isDuplicateSlatId(slatId);
  final config = plateConfigs?[wellName];

  // Border color: match UI — use design color (unique or layer), fallback grey
  final designColor = (slat != null && layerMap != null) ? designColorFor(slat, layerMap) : null;
  final borderColor = designColor != null ? _toPdfColor(designColor) : PdfColors.grey400;
  final borderWidth = designColor != null ? 1.5 : 0.75;

  // Slat type label (full name)
  String? slatTypeLabel;
  if (slat != null) {
    slatTypeLabel = slat.slatType;
  }

  // Display name: L{layer}-{number}, with ~N suffix for duplicates
  String displayId = '';
  if (slat != null && layerMap != null) {
    displayId = slatDisplayName(slat, layerMap);
    if (isDuplicate) {
      final tildeIndex = slatId.indexOf('~');
      if (tildeIndex >= 0) displayId += slatId.substring(tildeIndex);
    }
  } else if (slatId != null) {
    displayId = slatId.replaceFirst('-I', '-');
  }

  // Volume/ratio text
  String? volumeText;
  if (isOccupied && config != null) {
    final volStr =
        config.volume == config.volume.truncateToDouble() ? config.volume.toInt().toString() : config.volume.toStringAsFixed(1);
    final ratStr =
        config.ratio == config.ratio.truncateToDouble() ? config.ratio.toInt().toString() : config.ratio.toStringAsFixed(1);
    volumeText = '${volStr}uL ${ratStr}x';
  }

  const wellInset = 1.0; // gap between wells so colored borders don't overlap
  final barcodeWidth = _cellWidth - wellInset * 2 - 15;

  return pw.Container(
    width: _cellWidth,
    height: _cellHeight,
    padding: const pw.EdgeInsets.all(wellInset),
    child: pw.Container(
    decoration: pw.BoxDecoration(
      color: isOccupied ? PdfColors.white : PdfColor.fromInt(0xFFF5F5F5),
      border: pw.Border.all(color: borderColor, width: borderWidth),
    ),
    child: isOccupied
        ? pw.Stack(
            overflow: pw.Overflow.visible,
            children: [
              // Slat type anchored at top-right
              if (slatTypeLabel != null)
                pw.Positioned(
                  top: 1.5,
                  right: 2,
                  child: pw.Text(slatTypeLabel, style: pw.TextStyle(fontSize: 6, color: PdfColors.black)),
                ),
              // Duplicate badge anchored at top-left
              if (isDuplicate)
                pw.Positioned(
                  top: 1.5,
                  left: 1.5,
                  child: _buildDuplicateBadge(),
                ),
              // Warning indicator (top-left, shifted right if duplicate badge present)
              () {
                  final warning = wellWarningState(slat, config);
                  if (!warning.incomplete && !warning.exceedsVolume) return pw.SizedBox();
                  final leftOffset = isDuplicate ? 12.0 : 1.5;
                  final color = warning.incomplete ? PdfColors.red : PdfColors.orange;
                  return pw.Positioned(
                    top: 1.0,
                    left: leftOffset,
                    child: _buildPdfWarningTriangle(color),
                  );
                }(),
              // Centered pictogram block: name sits above, volume sits below
              // Barcodes are centered; H5/H2 labels are positioned absolutely to the left
              pw.Positioned.fill(
                child: pw.Column(
                  mainAxisAlignment: pw.MainAxisAlignment.center,
                  children: [
                    // Slat ID (above the pictogram)
                    pw.Text(
                      displayId,
                      style: pw.TextStyle(fontSize: 6, fontWeight: pw.FontWeight.bold),
                      maxLines: 1,
                      overflow: pw.TextOverflow.clip,
                      textAlign: pw.TextAlign.center,
                    ),
                    pw.SizedBox(height: 1),
                    // Position markers
                    _buildPositionMarkers(slat.maxLength, barcodeWidth),
                    // H5 barcode (top) with label
                    _buildLabeledBarcodeRow('H5', slat.h5Handles, slat.maxLength, barcodeWidth),
                    pw.SizedBox(height: 0.5),
                    // H2 barcode (bottom) with label
                    _buildLabeledBarcodeRow('H2', slat.h2Handles, slat.maxLength, barcodeWidth),
                    // Volume/ratio (below the pictogram)
                    if (volumeText != null) ...[
                      pw.SizedBox(height: 2),
                      pw.Text(volumeText, style: pw.TextStyle(fontSize: 7, color: PdfColors.black)),
                    ],
                  ],
                ),
              ),
            ],
          )
        : pw.SizedBox(),
    ),
  );
}

// ---------------------------------------------------------------------------
// Position markers: show 1, 16, and 32 aligned above the barcode
// ---------------------------------------------------------------------------

pw.Widget _buildPositionMarkers(int maxLength, double totalWidth) {
  final rectWidth = totalWidth / maxLength;
  const markers = [1, 16, 32];
  return pw.SizedBox(
    width: totalWidth,
    height: 6,
    child: pw.Stack(
      overflow: pw.Overflow.visible,
      children: [
        for (var pos in markers)
          if (pos <= maxLength)
            () {
              // Center of the rect for this position
              final center = (pos - 1) * rectWidth + rectWidth / 2;
              // For first marker, left-align; for last, right-align; middle: center
              final pw.TextAlign align;
              final double left;
              const labelWidth = 12.0;
              if (pos == 1) {
                left = 0;
                align = pw.TextAlign.left;
              } else if (pos == maxLength) {
                left = totalWidth - labelWidth;
                align = pw.TextAlign.right;
              } else {
                left = (center - labelWidth / 2).clamp(0.0, totalWidth - labelWidth);
                align = pw.TextAlign.center;
              }
              return pw.Positioned(
                left: left,
                top: 0,
                child: pw.SizedBox(
                  width: labelWidth,
                  child: pw.Text(
                    '$pos',
                    style: pw.TextStyle(fontSize: 4, color: PdfColors.grey500),
                    textAlign: align,
                  ),
                ),
              );
            }(),
      ],
    ),
  );
}

// ---------------------------------------------------------------------------
// Labeled barcode row: barcode with side label (H2/H5) positioned to the left
// ---------------------------------------------------------------------------

pw.Widget _buildLabeledBarcodeRow(String label, Map<int, Map<String, dynamic>> handles, int maxLength, double barcodeWidth) {
  return pw.Stack(
    overflow: pw.Overflow.visible,
    children: [
      _buildPdfBarcodeRow(handles, maxLength, barcodeWidth, 6),
      pw.Positioned(
        left: 1.5,
        top: 0,
        child: pw.Text(label, style: pw.TextStyle(fontSize: 4, color: PdfColors.grey500)),
      ),
    ],
  );
}

// ---------------------------------------------------------------------------
// Warning triangle: small triangle with '!' — mimics Icons.warning in UI
// ---------------------------------------------------------------------------

pw.Widget _buildPdfWarningTriangle(PdfColor color) {
  const size = 8.0;
  return pw.SizedBox(
    width: size,
    height: size,
    child: pw.CustomPaint(
      size: const PdfPoint(size, size),
      painter: (PdfGraphics canvas, PdfPoint s) {
        // Draw filled triangle pointing up
        canvas
          ..moveTo(s.x / 2, s.y) // top center
          ..lineTo(0, 0) // bottom left
          ..lineTo(s.x, 0) // bottom right
          ..closePath();
        canvas.setFillColor(color);
        canvas.fillPath();

        // Draw white '!' in the center of the triangle
        // Triangle centroid is at (w/2, h/3) from bottom in PDF coords
        canvas.setFillColor(PdfColors.white);

        // Exclamation mark stem
        const stemW = 1.0;
        const stemH = 3.2;
        final stemX = s.x / 2 - stemW / 2;
        final stemY = s.y * 0.28; // slightly below centroid
        canvas.drawRect(stemX, stemY, stemW, stemH);
        canvas.fillPath();

        // Exclamation mark dot
        const dotSize = 1.0;
        final dotX = s.x / 2 - dotSize / 2;
        final dotY = stemY - dotSize - 0.6;
        canvas.drawRect(dotX, dotY, dotSize, dotSize);
        canvas.fillPath();
      },
    ),
  );
}

// ---------------------------------------------------------------------------
// Duplicate badge: two small offset rectangles (mimics copy icon)
// ---------------------------------------------------------------------------

pw.Widget _buildDuplicateBadge() {
  return pw.SizedBox(
    width: 9,
    height: 8,
    child: pw.Stack(
      overflow: pw.Overflow.visible,
      children: [
        pw.Positioned(
          left: 0,
          top: 2,
          child: pw.Container(
            width: 5,
            height: 5,
            decoration: pw.BoxDecoration(
              border: pw.Border.all(color: PdfColors.blueGrey600, width: 0.5),
              borderRadius: pw.BorderRadius.circular(0.5),
            ),
          ),
        ),
        pw.Positioned(
          left: 2,
          top: 0,
          child: pw.Container(
            width: 5,
            height: 5,
            decoration: pw.BoxDecoration(
              color: PdfColors.white,
              border: pw.Border.all(color: PdfColors.blueGrey600, width: 0.5),
              borderRadius: pw.BorderRadius.circular(0.5),
            ),
          ),
        ),
      ],
    ),
  );
}

// ---------------------------------------------------------------------------
// Barcode row
// ---------------------------------------------------------------------------

pw.Widget _buildPdfBarcodeRow(Map<int, Map<String, dynamic>> handles, int maxLength, double totalWidth, double height) {
  final rectWidth = totalWidth / maxLength;
  return pw.Row(
    mainAxisAlignment: pw.MainAxisAlignment.center,
    children: [
      for (int i = 0; i < maxLength; i++)
        pw.Container(
          width: rectWidth,
          height: height,
          color: pdfCategoryColor(handles[i + 1]?['category'] as String?),
        ),
    ],
  );
}

// ---------------------------------------------------------------------------
// Legend bar
// ---------------------------------------------------------------------------

pw.Widget _buildLegendBar() {
  return pw.SizedBox(
    height: _legendHeight,
    child: pw.Row(
      mainAxisAlignment: pw.MainAxisAlignment.center,
      children: [
        for (var i = 0; i < _legendEntries.length; i++) ...[
          if (i > 0) pw.SizedBox(width: 14),
          pw.Container(
            width: 10,
            height: 10,
            decoration: pw.BoxDecoration(
              color: PdfColor.fromInt(_legendEntries[i].$2),
              borderRadius: pw.BorderRadius.circular(1),
              border: pw.Border.all(color: PdfColors.grey400, width: 0.5),
            ),
          ),
          pw.SizedBox(width: 3),
          pw.Text(
            _legendEntries[i].$1,
            style: pw.TextStyle(fontSize: 8, color: PdfColors.grey700),
          ),
        ],
      ],
    ),
  );
}
