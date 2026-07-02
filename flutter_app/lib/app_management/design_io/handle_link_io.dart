/// Excel I/O for handle link constraints (linked groups, enforced values, blocked handles).
import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';

import '../../crisscross_core/slats.dart';
import '../design_state_mixins/design_state_handle_link_mixin.dart';
import 'design_io_constants.dart';

/// Reads the handle link sheet from [excelFile] and populates [linkManager].
///
/// Returns null on success (including when no link sheet exists for backwards
/// compatibility), or an error message string if validation fails.
String? extractHandleLinksFromExcel(Excel excelFile, Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, HandleLinkManager linkManager) {
  if (!excelFile.tables.containsKey(slatHandleLinksSheetName)) {
    return null;
  }

  try {
    var sheet = excelFile.tables[slatHandleLinksSheetName]!;
    List<List<dynamic>> data = [];

    for (var row = 0; row < sheet.maxRows; row++) {
      List<dynamic> rowData = [];
      for (var col = 0; col < sheet.maxColumns; col++) {
        var cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
        if (cell is TextCellValue) {
          rowData.add(cell.value.text ?? '');
        } else if (cell is IntCellValue) {
          rowData.add(cell.value);
        } else if (cell is DoubleCellValue) {
          rowData.add(cell.value);
        } else {
          rowData.add(null);
        }
      }
      data.add(rowData);
    }

    String? validationError = linkManager.validateImport(data, slats, layerMap);
    if (validationError != null) {
      return validationError;
    }

    linkManager.importFromExcelData(data, slats, layerMap);
    return null;
  } catch (e) {
    return 'Error importing handle links: ${e.toString()}';
  }
}

/// Writes handle link data from [linkManager] to a new sheet in [excel].
///
/// Formats slat name rows every 6 rows with layer-coloured backgrounds.
/// Does nothing if there are no links to export.
void writeHandleLinksToExcel(Excel excel, Map<String, Slat> slats, HandleLinkManager linkManager, Map<String, Map<String, dynamic>> layerMap) {
  List<List<dynamic>> linkData = linkManager.exportToExcelData(slats, layerMap);
  if (linkData.isEmpty) {
    return;
  }

  Sheet sheet = excel[slatHandleLinksSheetName];

  int maxCols = 0;
  for (var row in linkData) {
    if (row.length > maxCols) maxCols = row.length;
  }

  for (int rowIdx = 0; rowIdx < linkData.length; rowIdx++) {
    var row = linkData[rowIdx];
    for (int colIdx = 0; colIdx < row.length; colIdx++) {
      var value = row[colIdx];
      if (value == null || value == '') {
        continue;
      } else if (value is int) {
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: colIdx, rowIndex: rowIdx)).value = IntCellValue(value);
      } else if (value is double) {
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: colIdx, rowIndex: rowIdx)).value = DoubleCellValue(value);
      } else {
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: colIdx, rowIndex: rowIdx)).value = TextCellValue(value.toString());
      }
    }
  }

  for (int i = 0; i < linkData.length; i += 6) {
    if (i >= linkData.length) break;

    var slatId = linkData[i][0].toString();
    var slat = slats[pythonToDartSlatNameConvert(slatId, layerMap)]!;
    Color layerColor;

    if (slat.uniqueColor != null) {
      layerColor = slat.uniqueColor!;
    } else {
      layerColor = layerMap[slat.layer]?['color'] ?? Color(0xFF808080);
    }

    int r = (layerColor.r * 255.0).round() & 0xFF;
    int g = (layerColor.g * 255.0).round() & 0xFF;
    int b = (layerColor.b * 255.0).round() & 0xFF;
    double brightness = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0;
    String fontColor = brightness < 0.5 ? 'FFFFFF' : '000000';

    if (maxCols > 1) {
      sheet.merge(
        CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: i),
        CellIndex.indexByColumnRow(columnIndex: maxCols - 1, rowIndex: i),
        customValue: TextCellValue(slatId),
      );
    }

    sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: i)).cellStyle = CellStyle(
      backgroundColorHex: layerColor.toHexString().excelColor,
      fontColorHex: fontColor.excelColor,
      horizontalAlign: HorizontalAlign.Center,
    );
  }
}
