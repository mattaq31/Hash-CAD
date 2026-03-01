import 'dart:typed_data';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../crisscross_core/slats.dart';
import 'echo_category_colors.dart';
import 'plate_layout_state.dart' show baseSlatId;

Future<Uint8List> buildPlateLayoutPdf(
  Map<int, Map<String, String?>> plateAssignments,
  Map<String, Slat> slats, {
  Map<int, String>? plateNames,
}) async {
  final pdf = pw.Document();
  final rows = 'ABCDEFGH'.split('');
  final cols = List.generate(12, (i) => i + 1);

  const double cellWidth = 62;
  const double cellHeight = 48;
  const double headerSize = 18;

  final sortedKeys = plateAssignments.keys.toList()..sort();
  for (var i = 0; i < sortedKeys.length; i++) {
    final plateIndex = sortedKeys[i];
    final assignments = plateAssignments[plateIndex]!;
    final name = plateNames?[plateIndex] ?? 'plate';
    final displayTitle = 'p${plateIndex}_$name';

    pdf.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.letter.landscape,
        margin: const pw.EdgeInsets.all(20),
        build: (pw.Context context) {
          return pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text(displayTitle, style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 8),
              pw.Row(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  // Row labels column
                  pw.Column(
                    children: [
                      pw.SizedBox(width: headerSize, height: headerSize),
                      for (var row in rows)
                        pw.Container(
                          width: headerSize,
                          height: cellHeight,
                          alignment: pw.Alignment.center,
                          child: pw.Text(row, style: pw.TextStyle(fontSize: 8, fontWeight: pw.FontWeight.bold, color: PdfColors.grey700)),
                        ),
                    ],
                  ),
                  // Columns
                  for (var col in cols)
                    pw.Column(
                      children: [
                        pw.Container(
                          width: cellWidth,
                          height: headerSize,
                          alignment: pw.Alignment.center,
                          child: pw.Text('$col', style: pw.TextStyle(fontSize: 8, fontWeight: pw.FontWeight.bold, color: PdfColors.grey700)),
                        ),
                        for (var row in rows)
                          _buildPdfWellCell(assignments, '$row$col', slats, cellWidth, cellHeight),
                      ],
                    ),
                ],
              ),
            ],
          );
        },
      ),
    );
  }

  return await pdf.save();
}

pw.Widget _buildPdfWellCell(Map<String, String?> assignments, String wellName, Map<String, Slat> slats, double cellWidth, double cellHeight) {
  final slatId = assignments[wellName];
  final lookupId = slatId != null ? baseSlatId(slatId) : null;
  final slat = lookupId != null ? slats[lookupId] : null;

  return pw.Container(
    width: cellWidth,
    height: cellHeight,
    decoration: pw.BoxDecoration(
      border: pw.Border.all(color: PdfColors.grey300, width: 0.5),
    ),
    child: slat != null
        ? pw.Column(
            mainAxisAlignment: pw.MainAxisAlignment.center,
            children: [
              pw.Text(
                slatId!.replaceFirst('-I', '-'),
                style: pw.TextStyle(fontSize: 5, fontWeight: pw.FontWeight.bold),
                maxLines: 1,
              ),
              pw.SizedBox(height: 1),
              _buildPdfBarcodeRow(slat.h2Handles, slat.maxLength, cellWidth - 4, 7),
              pw.SizedBox(height: 0.5),
              _buildPdfBarcodeRow(slat.h5Handles, slat.maxLength, cellWidth - 4, 7),
            ],
          )
        : pw.SizedBox(),
  );
}

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
