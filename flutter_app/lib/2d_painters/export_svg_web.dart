import 'dart:convert';
import 'dart:js_interop';
import 'package:web/web.dart' as web;

Future<void> saveSvg(String svgString, String fileName) async {
  final bytes = utf8.encode(svgString);
  final blob = web.Blob([bytes.toJS].toJS);
  final url = web.URL.createObjectURL(blob);

  final anchor = web.HTMLAnchorElement()
    ..href = url
    ..download = fileName;
  anchor.click();

  web.URL.revokeObjectURL(url);
}