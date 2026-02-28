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
