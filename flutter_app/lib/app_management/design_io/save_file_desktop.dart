/// Desktop file-save helpers for exporting arbitrary byte data.
///
/// Provides platform-specific implementations for saving single or multiple
/// files via native file picker dialogs. The web counterpart is [save_file_web.dart].
import 'dart:io';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' show dirname;

import 'file_picker_helpers.dart';

/// Prompts the user with a save dialog, then writes [bytes] to the chosen path.
Future<void> saveFileBytes(Uint8List bytes, String fileName, String extension) async {
  String? filePath = await FilePicker.platform.saveFile(
    dialogTitle: 'Save As',
    fileName: fileName,
    type: FileType.custom,
    allowedExtensions: [extension],
    initialDirectory: lastOpenDirectory,
  );

  if (filePath == null) return;

  lastOpenDirectory = dirname(filePath);
  final file = File(filePath);
  await file.writeAsBytes(bytes);
}

/// Saves multiple files into a named subfolder chosen by the user.
Future<bool> saveMultipleFiles(Map<String, Uint8List> files, String folderName) async {
  final dirPath = await FilePicker.platform.getDirectoryPath(
    dialogTitle: 'Choose export folder location',
    initialDirectory: lastOpenDirectory,
  );
  if (dirPath == null) return false;

  lastOpenDirectory = dirPath;
  final outputDir = Directory('$dirPath/$folderName');
  if (!await outputDir.exists()) {
    await outputDir.create(recursive: true);
  }
  for (var entry in files.entries) {
    await File('${outputDir.path}/${entry.key}').writeAsBytes(entry.value);
  }
  return true;
}
