import 'dart:io';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';

Future<void> saveFileBytes(Uint8List bytes, String fileName, String extension) async {
  String? filePath = await FilePicker.platform.saveFile(
    dialogTitle: 'Save As',
    fileName: fileName,
    type: FileType.custom,
    allowedExtensions: [extension],
  );

  if (filePath == null) return;

  final file = File(filePath);
  await file.writeAsBytes(bytes);
}

/// Saves multiple files into a named subfolder chosen by the user.
Future<bool> saveMultipleFiles(Map<String, Uint8List> files, String folderName) async {
  final dirPath = await FilePicker.platform.getDirectoryPath(dialogTitle: 'Choose export folder location');
  if (dirPath == null) return false;

  final outputDir = Directory('$dirPath/$folderName');
  if (!await outputDir.exists()) {
    await outputDir.create(recursive: true);
  }
  for (var entry in files.entries) {
    await File('${outputDir.path}/${entry.key}').writeAsBytes(entry.value);
  }
  return true;
}
