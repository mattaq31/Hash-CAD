/// TOML export for handle evolution configuration parameters.
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:toml/toml.dart';

import 'file_picker_helpers.dart';

/// Exports evolution [parameters] to a .toml file via a save dialog.
///
/// String values are auto-converted to their native TOML types:
/// booleans, comma-separated numeric lists, integers, and floats.
Future<void> exportEvolutionParameters(Map<String, String> parameters) async {
  String? filePath = await FilePicker.platform.saveFile(
    dialogTitle: 'Save As',
    fileName: 'evolution_config.toml',
    type: FileType.custom,
    allowedExtensions: ['toml'],
    initialDirectory: kIsWeb ? null : lastOpenDirectory,
  );

  if (filePath == null) {
    return;
  }

  final convertedParams = parameters.map((key, value) {
    final lower = value.toLowerCase().trim();

    if (lower == 'true') return MapEntry(key, true);
    if (lower == 'false') return MapEntry(key, false);

    if (value.contains(',')) {
      final parts = value.split(',').map((s) => s.trim()).toList();
      final allNumeric = parts.every((p) => num.tryParse(p) != null);
      if (allNumeric) {
        final list = parts.map((p) => double.parse(p)).toList();
        return MapEntry(key, list);
      }
    }

    final numValue = num.tryParse(value);
    if (numValue != null) {
      if (numValue == numValue.roundToDouble()) {
        return MapEntry(key, numValue.toInt());
      } else {
        return MapEntry(key, numValue.toDouble());
      }
    }

    return MapEntry(key, value);
  });

  final tomlString = TomlDocument.fromMap(convertedParams).toString();

  final file = File(filePath);
  await file.writeAsString(tomlString);
}
