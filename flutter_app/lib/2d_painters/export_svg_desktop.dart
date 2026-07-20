import 'dart:io';
import 'package:file_picker/file_picker.dart';

import '../app_management/design_io/file_picker_helpers.dart';

Future<void> saveSvg(String svgString, String fileName) async {
  String? filePath = await FilePicker.platform.saveFile(
    dialogTitle: 'Save As',
    fileName: fileName,
    type: FileType.custom,
    allowedExtensions: ['svg'],
  );

  if (filePath != null) {
    final file = File(ensureExtension(filePath, 'svg'));
    await file.writeAsString(svgString);
  }
}