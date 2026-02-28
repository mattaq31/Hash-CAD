import 'dart:typed_data';
import 'dart:js_interop';
import 'package:web/web.dart' as web;

const Map<String, String> _mimeTypes = {
  'csv': 'text/csv',
  'png': 'image/png',
  'svg': 'image/svg+xml',
  'pdf': 'application/pdf',
};

Future<void> saveFileBytes(Uint8List bytes, String fileName, String extension) async {
  final mimeType = _mimeTypes[extension] ?? 'application/octet-stream';
  final blob = web.Blob([bytes.toJS].toJS, web.BlobPropertyBag(type: mimeType));
  final url = web.URL.createObjectURL(blob);

  final anchor = web.HTMLAnchorElement()
    ..href = url
    ..download = fileName;
  anchor.click();

  web.URL.revokeObjectURL(url);
}
