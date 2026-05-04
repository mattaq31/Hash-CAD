/// Type-safe wrappers for reading and writing Excel cells.
///
/// The Excel package uses polymorphic [CellValue] types that require runtime
/// type checking before accessing the inner value. These utilities centralise
/// that boilerplate.
import 'package:excel/excel.dart' hide Border, BorderStyle;

/// Extracts all rows from an Excel [sheet], converting each cell to a native Dart type.
List<List<dynamic>> extractSheetRows(Sheet sheet) {
  return sheet.rows.map((row) {
    return row.map((cell) {
      if (cell == null) return '';
      final v = cell.value;
      if (v is TextCellValue) return v.value.text ?? '';
      if (v is IntCellValue) return v.value;
      if (v is DoubleCellValue) return v.value;
      return v.toString();
    }).toList();
  }).toList();
}

/// Writes a dynamic value to an Excel cell, choosing the appropriate [CellValue] subtype.
void setCellValue(Sheet sheet, int col, int row, dynamic val, {CellStyle? style}) {
  final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row));
  if (val is int) {
    cell.value = IntCellValue(val);
  } else if (val is double) {
    cell.value = DoubleCellValue(val);
  } else {
    cell.value = TextCellValue(val.toString());
  }
  if (style != null) {
    cell.cellStyle = style;
  }
}

/// Reads an integer from [cell] (e.g. 'B4'), returning 0 if the cell is not an [IntCellValue].
int readExcelInt(Sheet workSheet, String cell) {
  var cellValue = workSheet.cell(CellIndex.indexByString(cell)).value;
  return (cellValue is IntCellValue) ? cellValue.value : 0;
}

/// Reads a double from [cell], coercing [IntCellValue] to double. Returns 0.0 on type mismatch.
double readExcelDouble(Sheet workSheet, String cell) {
  var cellValue = workSheet.cell(CellIndex.indexByString(cell)).value;
  return (cellValue is IntCellValue)
      ? cellValue.value.toDouble()
      : (cellValue is DoubleCellValue)
          ? cellValue.value
          : 0.0;
}

/// Reads a string from [cell], returning '' if the cell is not a [TextCellValue].
String readExcelString(Sheet workSheet, String cell) {
  var cellValue = workSheet.cell(CellIndex.indexByString(cell)).value;
  return (cellValue is TextCellValue) ? cellValue.value.text ?? '' : '';
}
