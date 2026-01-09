import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../app_management/update_state.dart';
import '../app_management/update_service.dart';
import '../app_management/version_tracker.dart';

/// Shows the update dialog
Future<void> showUpdateDialog(BuildContext context, {bool isManualCheck = false}) async {
  final updateState = Provider.of<UpdateState>(context, listen: false);

  if (isManualCheck) {
    final hasUpdate = await updateState.checkForUpdates(silent: false);
    if (!hasUpdate && context.mounted) {
      if (updateState.status == UpdateStatus.error) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(updateState.errorMessage ?? 'Error checking for updates'),
            backgroundColor: Colors.red,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('You are running the latest version'),
            backgroundColor: Colors.green,
          ),
        );
      }
      return;
    }
  }

  if (!context.mounted) return;

  await showDialog(
    context: context,
    barrierDismissible: false,
    builder: (context) => const UpdateDialogContent(),
  );
}

class UpdateDialogContent extends StatefulWidget {
  const UpdateDialogContent({super.key});

  @override
  State<UpdateDialogContent> createState() => _UpdateDialogContentState();
}

class _UpdateDialogContentState extends State<UpdateDialogContent> {
  bool _skipThisVersion = false;

  @override
  Widget build(BuildContext context) {
    final updateState = context.watch<UpdateState>();
    final release = updateState.latestRelease;

    return AlertDialog(
      title: Row(
        children: [
          Icon(
            updateState.status == UpdateStatus.error ? Icons.error : Icons.system_update,
            color: updateState.status == UpdateStatus.error ? Colors.red : Colors.blue,
          ),
          const SizedBox(width: 8),
          Text(updateState.status == UpdateStatus.error ? 'Update Error' : 'Update Available'),
        ],
      ),
      content: SizedBox(
        width: 500,
        child: SingleChildScrollView(
          child: updateState.status == UpdateStatus.error
              ? _buildErrorContent(updateState)
              : _buildAvailableContent(release!, updateState),
        ),
      ),
      actions: _buildActions(updateState),
    );
  }

  Widget _buildAvailableContent(ReleaseInfo release, UpdateState updateState) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('A new version of #-CAD is available!', style: Theme.of(context).textTheme.bodyLarge),
        const SizedBox(height: 16),

        // Version info
        _buildInfoBox([
          _buildInfoRow('Current version:', VersionInfo.version),
          _buildInfoRow('New version:', release.tagName, valueColor: Colors.green),
          _buildInfoRow('Released:', _formatDate(release.publishedAt)),
        ]),

        // Release notes
        if (release.body.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('Release Notes:', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Container(
            constraints: const BoxConstraints(maxHeight: 120),
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey[300]!),
              borderRadius: BorderRadius.circular(4),
            ),
            child: SingleChildScrollView(
              child: SelectableText(
                _formatReleaseNotes(release.body),
                style: const TextStyle(fontSize: 12),
              ),
            ),
          ),
        ],

        const SizedBox(height: 16),

        // Download link
        const Text('Download:', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (release.platformAssetUrl != null)
          InkWell(
            onTap: () => _openUrl(release.platformAssetUrl!),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: Colors.blue),
              ),
              child: Row(
                children: [
                  const Icon(Icons.download, color: Colors.blue),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      release.platformAssetName,
                      style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const Icon(Icons.open_in_new, color: Colors.blue, size: 16),
                ],
              ),
            ),
          ),

        // SHA256 hash
        if (release.platformHash != null) ...[
          const SizedBox(height: 16),
          const Text('SHA256 (for verification):', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: Row(
              children: [
                Expanded(
                  child: SelectableText(
                    release.platformHash!,
                    style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.copy, size: 16),
                  tooltip: 'Copy hash',
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: release.platformHash!));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('SHA256 copied to clipboard'), duration: Duration(seconds: 1)),
                    );
                  },
                ),
              ],
            ),
          ),
        ],

        // Current install location
        const SizedBox(height: 16),
        const Text('Current install location:', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: Colors.grey[300]!),
          ),
          child: Row(
            children: [
              Expanded(
                child: SelectableText(
                  updateState.installPath,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.copy, size: 16),
                tooltip: 'Copy path',
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: updateState.installPath));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Path copied to clipboard'), duration: Duration(seconds: 1)),
                  );
                },
              ),
            ],
          ),
        ),

        // macOS note
        if (Platform.isMacOS) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.amber[50],
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: Colors.amber),
            ),
            child: const Row(
              children: [
                Icon(Icons.info_outline, color: Colors.amber, size: 20),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'After replacing the app, you may need to approve it in System Settings > Privacy & Security.',
                    style: TextStyle(fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
        ],

        // Skip checkbox
        const SizedBox(height: 16),
        Row(
          children: [
            Checkbox(
              value: _skipThisVersion,
              onChanged: (value) => setState(() => _skipThisVersion = value ?? false),
            ),
            const Text('Skip this version'),
          ],
        ),
      ],
    );
  }

  Widget _buildErrorContent(UpdateState updateState) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.error_outline, color: Colors.red, size: 48),
        const SizedBox(height: 16),
        Text(updateState.errorMessage ?? 'An unknown error occurred', textAlign: TextAlign.center),
        const SizedBox(height: 16),
        TextButton.icon(
          icon: const Icon(Icons.open_in_new),
          label: const Text('Check releases on GitHub'),
          onPressed: () => _openUrl('https://github.com/mattaq31/Hash-CAD/releases'),
        ),
      ],
    );
  }

  Widget _buildInfoBox(List<Widget> children) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: children),
    );
  }

  Widget _buildInfoRow(String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(width: 8),
          Text(value, style: TextStyle(color: valueColor, fontWeight: valueColor != null ? FontWeight.bold : null)),
        ],
      ),
    );
  }

  List<Widget> _buildActions(UpdateState updateState) {
    if (updateState.status == UpdateStatus.error) {
      return [
        TextButton(
          onPressed: () {
            updateState.clearError();
            Navigator.of(context).pop();
          },
          child: const Text('Close'),
        ),
        ElevatedButton(
          onPressed: () => updateState.checkForUpdates(),
          child: const Text('Retry'),
        ),
      ];
    }

    return [
      TextButton(
        onPressed: () async {
          if (_skipThisVersion) {
            await updateState.skipCurrentVersion();
          } else {
            updateState.dismiss();
          }
          if (mounted) Navigator.of(context).pop();
        },
        child: Text(_skipThisVersion ? 'Skip Version' : 'Later'),
      ),
      ElevatedButton.icon(
        icon: const Icon(Icons.open_in_new),
        label: const Text('Open Download'),
        onPressed: () {
          final url = updateState.latestRelease?.platformAssetUrl;
          if (url != null) _openUrl(url);
        },
      ),
    ];
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  String _formatReleaseNotes(String body) {
    return body
        .replaceAll(RegExp(r'^#{1,6}\s*', multiLine: true), '')
        .replaceAll('**', '')
        .replaceAll('*', '')
        .trim();
  }

  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
