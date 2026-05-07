/// Web file-save helpers for exporting arbitrary byte data.
///
/// Triggers browser downloads via an anchor element. Multiple files are bundled
/// into a zip archive since browsers have no folder-creation concept.
/// The desktop counterpart is [save_file_desktop.dart].
import 'dart:typed_data';
import 'dart:js_interop';
import 'package:archive/archive.dart';
import 'package:web/web.dart' as web;

const Map<String, String> _mimeTypes = {
  'csv': 'text/csv',
  'png': 'image/png',
  'svg': 'image/svg+xml',
  'pdf': 'application/pdf',
  'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'zip': 'application/zip',
};

/// Triggers a browser download for the given [bytes] with the specified [fileName].
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

/// On web, bundles all files into a zip archive and triggers a single download.
Future<bool> saveMultipleFiles(Map<String, Uint8List> files, String folderName) async {
  if (files.isEmpty) return false;

  final archive = Archive();
  for (var entry in files.entries) {
    archive.addFile(ArchiveFile(entry.key, entry.value.length, entry.value));
  }
  final zipBytes = Uint8List.fromList(ZipEncoder().encode(archive)!);
  await saveFileBytes(zipBytes, '$folderName.zip', 'zip');
  return true;
}
