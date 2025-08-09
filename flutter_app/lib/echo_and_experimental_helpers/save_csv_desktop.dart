// save_csv_io.dart
import 'dart:io';
import 'package:file_picker/file_picker.dart';

Future<void> saveCsv(String csvString, String outputFilename) async {
  String? filePath = await FilePicker.platform.saveFile(
    dialogTitle: 'Save As',
    fileName: outputFilename,
    type: FileType.custom,
    allowedExtensions: ['csv'],
  );

  if (filePath == null) return;

  final file = File(filePath);
  await file.writeAsString(csvString);
}