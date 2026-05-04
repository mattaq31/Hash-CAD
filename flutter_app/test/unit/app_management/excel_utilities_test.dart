import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:flutter_test/flutter_test.dart';

import 'package:hash_cad/app_management/design_io/excel_utilities.dart';

void main() {
  group('readExcelInt', () {
    test('reads IntCellValue correctly', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByString('A1')).value = IntCellValue(42);

      expect(readExcelInt(sheet, 'A1'), equals(42));
    });

    test('returns 0 for TextCellValue', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByString('A1')).value = TextCellValue('hello');

      expect(readExcelInt(sheet, 'A1'), equals(0));
    });

    test('returns 0 for DoubleCellValue', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByString('A1')).value = DoubleCellValue(3.14);

      expect(readExcelInt(sheet, 'A1'), equals(0));
    });

    test('returns 0 for empty cell', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];

      expect(readExcelInt(sheet, 'A1'), equals(0));
    });
  });

  group('readExcelDouble', () {
    test('reads DoubleCellValue correctly', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByString('A1')).value = DoubleCellValue(3.14);

      expect(readExcelDouble(sheet, 'A1'), closeTo(3.14, 0.001));
    });

    test('coerces IntCellValue to double', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByString('A1')).value = IntCellValue(7);

      expect(readExcelDouble(sheet, 'A1'), equals(7.0));
    });

    test('returns 0.0 for TextCellValue', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByString('A1')).value = TextCellValue('not a number');

      expect(readExcelDouble(sheet, 'A1'), equals(0.0));
    });

    test('returns 0.0 for empty cell', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];

      expect(readExcelDouble(sheet, 'A1'), equals(0.0));
    });
  });

  group('readExcelString', () {
    test('reads TextCellValue correctly', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByString('A1')).value = TextCellValue('hello');

      expect(readExcelString(sheet, 'A1'), equals('hello'));
    });

    test('returns empty string for IntCellValue', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByString('A1')).value = IntCellValue(42);

      expect(readExcelString(sheet, 'A1'), equals(''));
    });

    test('returns empty string for empty cell', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];

      expect(readExcelString(sheet, 'A1'), equals(''));
    });
  });

  group('setCellValue', () {
    test('writes int as IntCellValue', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      setCellValue(sheet, 0, 0, 42);

      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: 0));
      expect(cell.value, isA<IntCellValue>());
      expect((cell.value as IntCellValue).value, equals(42));
    });

    test('writes double as DoubleCellValue', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      setCellValue(sheet, 0, 0, 3.14);

      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: 0));
      expect(cell.value, isA<DoubleCellValue>());
      expect((cell.value as DoubleCellValue).value, closeTo(3.14, 0.001));
    });

    test('writes string as TextCellValue', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      setCellValue(sheet, 0, 0, 'hello');

      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: 0));
      expect(cell.value, isA<TextCellValue>());
    });

    test('applies CellStyle when provided', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      final style = CellStyle(bold: true);
      setCellValue(sheet, 0, 0, 'styled', style: style);

      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: 0));
      expect(cell.cellStyle?.isBold, isTrue);
    });
  });

  group('extractSheetRows', () {
    test('extracts mixed cell types into native Dart types', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: 0)).value = TextCellValue('name');
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 0)).value = IntCellValue(1);
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 0)).value = DoubleCellValue(2.5);
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: 1)).value = TextCellValue('row2');
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: 1)).value = IntCellValue(3);

      final rows = extractSheetRows(sheet);

      expect(rows.length, equals(2));
      expect(rows[0][0], equals('name'));
      expect(rows[0][1], equals(1));
      expect(rows[0][2], closeTo(2.5, 0.001));
      expect(rows[1][0], equals('row2'));
      expect(rows[1][1], equals(3));
    });

    test('returns empty string for null cells', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: 0)).value = TextCellValue('a');
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: 0)).value = TextCellValue('c');

      final rows = extractSheetRows(sheet);

      expect(rows[0][0], equals('a'));
      expect(rows[0][1], equals(''));
      expect(rows[0][2], equals('c'));
    });

    test('handles empty sheet', () {
      final excel = Excel.createExcel();
      final sheet = excel['test'];

      final rows = extractSheetRows(sheet);

      expect(rows, isEmpty);
    });
  });
}
