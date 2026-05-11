/// File picker utilities and session-level directory memory.
///
/// Tracks the last directory the user opened or saved to (desktop only)
/// so that subsequent file dialogs start in the same location.
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;

/// Session-level memory of the last directory opened or saved to (desktop only).
String? _lastOpenDirectory;

/// The last directory used for file operations, or null if none set.
String? get lastOpenDirectory => _lastOpenDirectory;

/// Updates the last-used directory for file picker dialogs.
set lastOpenDirectory(String? value) => _lastOpenDirectory = value;

/// Ensures [filePath] ends with .[ext], appending it if missing.
/// Case-insensitive to match Windows filesystem behavior.
String ensureExtension(String filePath, String ext) {
  final dotExt = '.$ext';
  if (p.extension(filePath).toLowerCase() == dotExt.toLowerCase()) {
    return filePath;
  }
  return '$filePath$dotExt';
}

/// Shows a save dialog for an .xlsx file, returning the chosen path or null if cancelled.
Future<String?> selectSaveLocation(String defaultFileName) async {
  String? filePath = await FilePicker.platform.saveFile(
    dialogTitle: 'Save As',
    fileName: defaultFileName,
    type: FileType.custom,
    allowedExtensions: ['xlsx'],
    initialDirectory: kIsWeb ? null : _lastOpenDirectory,
  );

  if (filePath != null) {
    return ensureExtension(filePath, 'xlsx');
  } else {
    return null;
  }
}
