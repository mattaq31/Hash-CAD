/// Excel import for DNA source plates (input plate library).
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart';

import '../../crisscross_core/handle_plates.dart';
import 'file_picker_helpers.dart';

/// Prompts the user to select one or more .xlsx plate files and loads them into [plateLibrary].
Future<void> importPlatesFromFile(PlateLibrary plateLibrary) async {
  List<Uint8List> fileBytes = [];
  List<String> plateNames = [];

  FilePickerResult? result = await FilePicker.platform.pickFiles(
    type: FileType.custom,
    allowedExtensions: ['xlsx'],
    allowMultiple: true,
    initialDirectory: kIsWeb ? null : lastOpenDirectory,
  );

  if (result != null) {
    if (kIsWeb) {
      for (var file in result.files) {
        String plateName = file.name.split('.').first;
        fileBytes.add(file.bytes!);
        plateNames.add(plateName);
      }
    } else {
      for (var file in result.files) {
        String plateName = file.name.split('.').first;
        fileBytes.add(File(file.path!).readAsBytesSync());
        plateNames.add(plateName);
      }
      if (result.files.isNotEmpty && result.files.first.path != null) {
        try {
          lastOpenDirectory = dirname(result.files.first.path!);
        } catch (_) {}
      }
    }
  }
  plateLibrary.readPlates(fileBytes, plateNames);
}
