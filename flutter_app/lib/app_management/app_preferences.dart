import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;

/// Default assembly handle colors
class AssemblyHandleColors {
  static const Color defaultHandle = Colors.green;
  static const Color defaultAntiHandle = Colors.lightGreen;
  static const Color defaultPhantom = Colors.grey;
  static const Color defaultPhantomAnti = Colors.blueGrey;
  static const Color defaultLinked = Colors.purple;
  static const Color defaultBlocked = Colors.red;
}

/// Stores all app-wide preferences (assembly handle colors, update preferences, etc.)
/// Singleton to ensure consistent caching across the app.
class AppPreferences {
  static final AppPreferences _instance = AppPreferences._internal();
  factory AppPreferences() => _instance;
  AppPreferences._internal();

  static const String _prefsFileName = 'app_preferences.json';

  File? _prefsFile;
  Map<String, dynamic>? _cachedPrefs;

  /// Get the preferences file path
  Future<File> _getPrefsFile() async {
    if (_prefsFile != null) return _prefsFile!;
    final appDir = await getApplicationSupportDirectory();
    _prefsFile = File(path.join(appDir.path, _prefsFileName));
    return _prefsFile!;
  }

  /// Load preferences from file (uses cache after first load)
  Future<Map<String, dynamic>> _loadPrefs() async {
    if (_cachedPrefs != null) return _cachedPrefs!;
    if (kIsWeb) {
      _cachedPrefs = {};
      return _cachedPrefs!;
    }
    try {
      final file = await _getPrefsFile();
      if (await file.exists()) {
        final content = await file.readAsString();
        if (content.trim().isNotEmpty) {
          _cachedPrefs = jsonDecode(content) as Map<String, dynamic>;
          return _cachedPrefs!;
        }
      }
    } catch (e) {
      debugPrint('Error loading app preferences: $e');
    }
    _cachedPrefs = {};
    return _cachedPrefs!;
  }

  /// Save preferences to file
  Future<void> _savePrefs() async {
    if (kIsWeb || _cachedPrefs == null) return;
    try {
      final file = await _getPrefsFile();
      await file.parent.create(recursive: true);
      await file.writeAsString(jsonEncode(_cachedPrefs));
    } catch (e) {
      debugPrint('Error saving app preferences: $e');
    }
  }

  // ============== Color Helpers ==============

  int _colorToInt(Color color) => color.toARGB32();
  Color _intToColor(int value) => Color(value);

  // ============== Assembly Handle Colors ==============

  /// Load assembly handle colors from preferences
  Future<Map<String, Color>> getAssemblyHandleColors() async {
    final prefs = await _loadPrefs();
    final colors = prefs['assemblyHandleColors'] as Map<String, dynamic>?;

    return {
      'handle': colors != null && colors['handle'] != null ? _intToColor(colors['handle']) : AssemblyHandleColors.defaultHandle,
      'antiHandle': colors != null && colors['antiHandle'] != null ? _intToColor(colors['antiHandle']) : AssemblyHandleColors.defaultAntiHandle,
      'phantom': colors != null && colors['phantom'] != null ? _intToColor(colors['phantom']) : AssemblyHandleColors.defaultPhantom,
      'phantomAnti': colors != null && colors['phantomAnti'] != null ? _intToColor(colors['phantomAnti']) : AssemblyHandleColors.defaultPhantomAnti,
      'linked': colors != null && colors['linked'] != null ? _intToColor(colors['linked']) : AssemblyHandleColors.defaultLinked,
      'blocked': colors != null && colors['blocked'] != null ? _intToColor(colors['blocked']) : AssemblyHandleColors.defaultBlocked,
    };
  }

  /// Save a single assembly handle color
  Future<void> setAssemblyHandleColor(String key, Color color) async {
    final prefs = await _loadPrefs();
    final colors = (prefs['assemblyHandleColors'] as Map<String, dynamic>?) ?? {};
    colors[key] = _colorToInt(color);
    prefs['assemblyHandleColors'] = colors;
    await _savePrefs();
  }

  /// Reset all assembly handle colors to defaults
  Future<void> resetAssemblyHandleColors() async {
    final prefs = await _loadPrefs();
    prefs.remove('assemblyHandleColors');
    await _savePrefs();
  }

  // ============== Update Preferences ==============

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
    await _savePrefs();
  }

  /// Clear the skipped version
  Future<void> clearSkippedVersion() async {
    final prefs = await _loadPrefs();
    prefs.remove('skipped_version');
    prefs.remove('skipped_at');
    await _savePrefs();
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
    await _savePrefs();
  }

  /// Check if enough time has passed since last check (default: 1 hour)
  Future<bool> shouldCheckForUpdates({Duration interval = const Duration(hours: 1)}) async {
    final lastCheck = await getLastCheckTime();
    if (lastCheck == null) return true;
    return DateTime.now().difference(lastCheck) > interval;
  }
}
