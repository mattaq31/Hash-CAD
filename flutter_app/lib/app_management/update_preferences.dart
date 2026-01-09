import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;

/// Stores user preferences for the update system
class UpdatePreferences {
  static const String _prefsFileName = 'update_preferences.json';

  File? _prefsFile;

  /// Get the preferences file path
  Future<File> _getPrefsFile() async {
    if (_prefsFile != null) return _prefsFile!;

    final appDir = await getApplicationSupportDirectory();
    _prefsFile = File(path.join(appDir.path, _prefsFileName));
    return _prefsFile!;
  }

  /// Load preferences from file
  Future<Map<String, dynamic>> _loadPrefs() async {
    try {
      final file = await _getPrefsFile();
      if (await file.exists()) {
        final content = await file.readAsString();
        return jsonDecode(content) as Map<String, dynamic>;
      }
    } catch (e) {
      debugPrint('Error loading update preferences: $e');
    }
    return {};
  }

  /// Save preferences to file
  Future<void> _savePrefs(Map<String, dynamic> prefs) async {
    try {
      final file = await _getPrefsFile();
      await file.parent.create(recursive: true);
      await file.writeAsString(jsonEncode(prefs));
    } catch (e) {
      debugPrint('Error saving update preferences: $e');
    }
  }

  /// Get the version that the user has chosen to skip
  Future<String?> getSkippedVersion() async {
    final prefs = await _loadPrefs();
    return prefs['skipped_version'] as String?;
  }

  /// Set a version to skip (user chose "Skip this version")
  Future<void> setSkippedVersion(String version) async {
    final prefs = await _loadPrefs();
    prefs['skipped_version'] = version;
    prefs['skipped_at'] = DateTime.now().toIso8601String();
    await _savePrefs(prefs);
  }

  /// Clear the skipped version
  Future<void> clearSkippedVersion() async {
    final prefs = await _loadPrefs();
    prefs.remove('skipped_version');
    prefs.remove('skipped_at');
    await _savePrefs(prefs);
  }

  /// Get the last time updates were checked
  Future<DateTime?> getLastCheckTime() async {
    final prefs = await _loadPrefs();
    final lastCheck = prefs['last_check'] as String?;
    if (lastCheck != null) {
      return DateTime.tryParse(lastCheck);
    }
    return null;
  }

  /// Record that an update check was performed
  Future<void> setLastCheckTime(DateTime time) async {
    final prefs = await _loadPrefs();
    prefs['last_check'] = time.toIso8601String();
    await _savePrefs(prefs);
  }

  /// Check if enough time has passed since last check (default: 1 hour)
  Future<bool> shouldCheckForUpdates({Duration interval = const Duration(hours: 1)}) async {
    final lastCheck = await getLastCheckTime();
    if (lastCheck == null) return true;
    return DateTime.now().difference(lastCheck) > interval;
  }
}
