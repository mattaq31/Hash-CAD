import 'dart:io';

void main() async {

  String allTags = await _runCommand('git tag --sort=-creatordate');
  List<String> tagList = allTags
      .split('\n')
      .where((tag) => tag.startsWith('v'))
      .toList();

  if (tagList.isEmpty) {
    throw Exception('No tags starting with "v" found.');
  }

  String gitTag = tagList.first; // Most recent tag at the bottom

  String gitCommits = await _runCommand('git rev-list --count HEAD');
  String gitHash = await _runCommand('git rev-parse --short HEAD');
  String buildDate = DateTime.now().toIso8601String();

  // Check if HEAD is exactly at the tag
  String taggedCommit = await _runCommand('git rev-list -n 1 $gitTag');
  String currentCommit = await _runCommand('git rev-parse HEAD');
  bool isExactlyAtTag = taggedCommit == currentCommit;

  // Format the version string
  String version = '$gitTag';
  String buildNumber = gitCommits;

  // Read the template file
  File versionFile = File('./lib/app_management/version_tracker.dart');
  String content = await versionFile.readAsString();

  content = content.replaceAllMapped(
    RegExp(r"static const String version\s*=\s*'.*';"),
        (_) => "static const String version = '$version';",
  );

  content = content.replaceAllMapped(
    RegExp(r"static const String buildNumber\s*=\s*'.*';"),
        (_) => "static const String buildNumber = '$buildNumber';",
  );

  content = content.replaceAllMapped(
    RegExp(r"static const String buildCommit\s*=\s*'.*';"),
        (_) => "static const String buildCommit = '$gitHash';",
  );

  content = content.replaceAllMapped(
    RegExp(r"static const String buildDate\s*=\s*'.*';"),
        (_) => "static const String buildDate = '$buildDate';",
  );

  // Write the updated content back to the file
  await versionFile.writeAsString(content);
  print('Version file updated successfully!');

  // Update pubspec.yaml with or without +buildNumber
  File pubspecFile = File('pubspec.yaml');
  String pubspecContent = await pubspecFile.readAsString();

  String cleanVersion = version.replaceFirst('v', '');
  String pubspecVersion = isExactlyAtTag
      ? cleanVersion
      : '$cleanVersion+$buildNumber';

  pubspecContent = pubspecContent.replaceAllMapped(
    RegExp(r'version:\s*.*'),
        (match) => 'version: $pubspecVersion',
  );

  await pubspecFile.writeAsString(pubspecContent);
  print('Pubspec.yaml file updated successfully!');
}

Future<String> _runCommand(String command) async {
  if (Platform.isWindows) {
    // Windows can execute Git directly
    final result = await Process.run('cmd', ['/c', command]);
    if (result.exitCode != 0) {
      throw Exception('Command failed: $command\n${result.stderr}');
    }
    return (result.stdout as String).trim();
  } else {
    // macOS/Linux: use shell
    final result = await Process.run('sh', ['-c', command]);
    if (result.exitCode != 0) {
      throw Exception('Command failed: $command\n${result.stderr}');
    }
    return (result.stdout as String).trim();
  }
}