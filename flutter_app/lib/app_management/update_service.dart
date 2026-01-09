import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as path;

/// Information about a GitHub release
class ReleaseInfo {
  final String tagName;
  final String version;
  final String name;
  final String body;
  final String htmlUrl;
  final DateTime publishedAt;
  final Map<String, String> assetUrls;
  String? platformHash; // SHA256 hash for current platform's asset

  ReleaseInfo({
    required this.tagName,
    required this.version,
    required this.name,
    required this.body,
    required this.htmlUrl,
    required this.publishedAt,
    required this.assetUrls,
    this.platformHash,
  });

  factory ReleaseInfo.fromJson(Map<String, dynamic> json) {
    final assets = json['assets'] as List<dynamic>;
    final assetUrls = <String, String>{};

    for (final asset in assets) {
      final name = asset['name'] as String;
      final url = asset['browser_download_url'] as String;
      assetUrls[name] = url;
    }

    final tagName = json['tag_name'] as String;

    return ReleaseInfo(
      tagName: tagName,
      version: tagName.startsWith('v') ? tagName.substring(1) : tagName,
      name: json['name'] as String? ?? tagName,
      body: json['body'] as String? ?? '',
      htmlUrl: json['html_url'] as String,
      publishedAt: DateTime.parse(json['published_at'] as String),
      assetUrls: assetUrls,
    );
  }

  /// Get the asset URL for the current platform
  String? get platformAssetUrl {
    if (Platform.isMacOS) {
      return assetUrls['Hash-CAD-macOS.zip'];
    } else if (Platform.isWindows) {
      return assetUrls['Hash-CAD-windows.zip'];
    } else if (Platform.isLinux) {
      return assetUrls['Hash-CAD-linux.tar.gz'];
    }
    return null;
  }

  /// Get the SHA256SUMS file URL
  String? get checksumUrl => assetUrls['SHA256SUMS'];

  /// Get the platform-specific asset filename
  String get platformAssetName {
    if (Platform.isMacOS) return 'Hash-CAD-macOS.zip';
    if (Platform.isWindows) return 'Hash-CAD-windows.zip';
    if (Platform.isLinux) return 'Hash-CAD-linux.tar.gz';
    return '';
  }
}

/// Service for checking app updates
class UpdateService {
  static const String _repoOwner = 'mattaq31';
  static const String _repoName = 'Hash-CAD';
  static const String _apiBase = 'https://api.github.com';

  final void Function(String)? onLog;

  UpdateService({this.onLog});

  void _log(String message) {
    debugPrint('[UpdateService] $message');
    onLog?.call(message);
  }

  /// Fetch the latest release info from GitHub (includes pre-releases)
  Future<ReleaseInfo?> fetchLatestRelease() async {
    try {
      final url = Uri.parse('$_apiBase/repos/$_repoOwner/$_repoName/releases');
      final response = await http.get(url, headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Hash-CAD-Updater',
      });

      if (response.statusCode == 200) {
        final releases = jsonDecode(response.body) as List<dynamic>;
        if (releases.isEmpty) {
          _log('No releases found');
          return null;
        }
        final latestRelease = releases.first as Map<String, dynamic>;
        _log('Found ${releases.length} releases, latest: ${latestRelease['tag_name']}');

        final releaseInfo = ReleaseInfo.fromJson(latestRelease);

        // Fetch SHA256 hash for this platform
        if (releaseInfo.checksumUrl != null) {
          releaseInfo.platformHash = await _fetchPlatformHash(releaseInfo.checksumUrl!, releaseInfo.platformAssetName);
        }

        return releaseInfo;
      } else if (response.statusCode == 403) {
        _log('GitHub API rate limit exceeded');
        return null;
      } else if (response.statusCode == 404) {
        _log('Repository not found or no releases');
        return null;
      } else {
        _log('Failed to fetch releases: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      _log('Network error fetching release: $e');
      return null;
    }
  }

  /// Fetch and parse SHA256SUMS to get hash for a specific file
  Future<String?> _fetchPlatformHash(String checksumUrl, String filename) async {
    try {
      final response = await http.get(Uri.parse(checksumUrl), headers: {
        'User-Agent': 'Hash-CAD-Updater',
      });

      if (response.statusCode == 200) {
        final lines = response.body.split('\n');
        for (final line in lines) {
          final parts = line.trim().split(RegExp(r'\s+'));
          if (parts.length >= 2 && parts.last == filename) {
            _log('Found hash for $filename: ${parts.first}');
            return parts.first.toUpperCase();
          }
        }
        _log('Hash not found for $filename in SHA256SUMS');
      }
    } catch (e) {
      _log('Error fetching SHA256SUMS: $e');
    }
    return null;
  }

  /// Compare two version strings (e.g., "0.4.0" vs "0.5.0")
  /// Returns true if remoteVersion is newer than localVersion
  static bool isNewerVersion(String remoteVersion, String localVersion) {
    final remote = remoteVersion.startsWith('v') ? remoteVersion.substring(1) : remoteVersion;
    final local = localVersion.startsWith('v') ? localVersion.substring(1) : localVersion;

    final remoteParts = remote.split('-')[0].split('.').map((e) => int.tryParse(e) ?? 0).toList();
    final localParts = local.split('-')[0].split('.').map((e) => int.tryParse(e) ?? 0).toList();

    while (remoteParts.length < 3) {
      remoteParts.add(0);
    }
    while (localParts.length < 3) {
      localParts.add(0);
    }

    for (var i = 0; i < 3; i++) {
      if (remoteParts[i] > localParts[i]) return true;
      if (remoteParts[i] < localParts[i]) return false;
    }

    return false;
  }

  /// Get the current app installation path
  static String getInstallPath() {
    if (Platform.isMacOS) {
      final executable = Platform.resolvedExecutable;
      // Go up from .app/Contents/MacOS/hash_cad to .app
      return path.dirname(path.dirname(path.dirname(executable)));
    } else if (Platform.isWindows || Platform.isLinux) {
      return path.dirname(Platform.resolvedExecutable);
    }
    return Platform.resolvedExecutable;
  }
}
