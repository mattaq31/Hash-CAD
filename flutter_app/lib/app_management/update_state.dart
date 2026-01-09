import 'package:flutter/foundation.dart';

import 'update_preferences.dart';
import 'update_service.dart';
import 'version_tracker.dart';

/// Status of the update check
enum UpdateStatus {
  idle,
  checking,
  available,
  error,
}

/// State management for app updates
class UpdateState extends ChangeNotifier {
  final UpdatePreferences _preferences = UpdatePreferences();

  UpdateStatus _status = UpdateStatus.idle;
  ReleaseInfo? _latestRelease;
  String? _errorMessage;

  UpdateStatus get status => _status;
  ReleaseInfo? get latestRelease => _latestRelease;
  String? get errorMessage => _errorMessage;

  /// Whether an update is available
  bool get updateAvailable => _status == UpdateStatus.available && _latestRelease != null;

  /// Whether currently checking
  bool get isChecking => _status == UpdateStatus.checking;

  /// Get current app install path
  String get installPath => UpdateService.getInstallPath();

  void _setStatus(UpdateStatus newStatus) {
    _status = newStatus;
    notifyListeners();
  }

  /// Check for available updates
  Future<bool> checkForUpdates({bool silent = false}) async {
    if (kIsWeb) return false;

    _setStatus(UpdateStatus.checking);
    _errorMessage = null;

    final service = UpdateService();
    final release = await service.fetchLatestRelease();

    if (release == null) {
      _errorMessage = 'Could not fetch release information';
      _setStatus(UpdateStatus.error);
      return false;
    }

    _latestRelease = release;

    final isNewer = UpdateService.isNewerVersion(release.tagName, VersionInfo.version);

    if (isNewer) {
      final skippedVersion = await _preferences.getSkippedVersion();
      if (skippedVersion == release.tagName && silent) {
        _setStatus(UpdateStatus.idle);
        return false;
      }

      _setStatus(UpdateStatus.available);
      return true;
    } else {
      _setStatus(UpdateStatus.idle);
      return false;
    }
  }

  /// Skip the current available version
  Future<void> skipCurrentVersion() async {
    if (_latestRelease != null) {
      await _preferences.setSkippedVersion(_latestRelease!.tagName);
      _setStatus(UpdateStatus.idle);
    }
  }

  /// Dismiss the update dialog without skipping
  void dismiss() {
    _setStatus(UpdateStatus.idle);
  }

  /// Reset error state
  void clearError() {
    _errorMessage = null;
    _setStatus(UpdateStatus.idle);
  }
}
