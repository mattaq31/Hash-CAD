// save_csv_web.dart
import 'dart:convert';
import 'dart:js_interop';
import 'package:web/web.dart' as web;

Future<void> saveCsv(String csvString, String outputFilename) async {
  final bytes = utf8.encode(csvString);
  final blob = web.Blob([bytes.toJS].toJS);
  final url = web.URL.createObjectURL(blob);

  final anchor = web.HTMLAnchorElement()
    ..href = url
    ..download = outputFilename;
  anchor.click();

  web.URL.revokeObjectURL(url);
}