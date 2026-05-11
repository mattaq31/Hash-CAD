// Tests for the ensureExtension utility in file_picker_helpers.
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/app_management/design_io/file_picker_helpers.dart';

void main() {
  group('ensureExtension', () {
    test('appends extension when missing', () {
      expect(ensureExtension('/path/to/file', 'xlsx'), '/path/to/file.xlsx');
    });

    test('does not double-append when extension already present', () {
      expect(ensureExtension('/path/to/file.xlsx', 'xlsx'), '/path/to/file.xlsx');
    });

    test('case-insensitive match on existing extension', () {
      expect(ensureExtension('/path/to/file.XLSX', 'xlsx'), '/path/to/file.XLSX');
      expect(ensureExtension('/path/to/file.Xlsx', 'xlsx'), '/path/to/file.Xlsx');
    });

    test('appends when extension differs from expected', () {
      expect(ensureExtension('/path/to/file.txt', 'xlsx'), '/path/to/file.txt.xlsx');
    });

    test('handles Windows-style paths', () {
      expect(ensureExtension(r'C:\Users\user\file', 'svg'), r'C:\Users\user\file.svg');
      expect(ensureExtension(r'C:\Users\user\file.svg', 'svg'), r'C:\Users\user\file.svg');
    });

    test('handles dots in directory names', () {
      expect(ensureExtension(r'C:\Users\my.name\file', 'toml'), r'C:\Users\my.name\file.toml');
    });

    test('works with various extensions', () {
      expect(ensureExtension('/path/file', 'svg'), '/path/file.svg');
      expect(ensureExtension('/path/file', 'toml'), '/path/file.toml');
      expect(ensureExtension('/path/file', 'zip'), '/path/file.zip');
    });
  });
}
