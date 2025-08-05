// modified from https://github.com/maxim-saplin/flutter_python_starter

import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:crypto/crypto.dart';


Future<int> launchServer() async {

  var dir = await getApplicationSupportDirectory();

  var filePath = File(p.join(dir.path, _getAssetName())).path;
  var file = File(filePath);

  ByteData data = await PlatformAssetBundle().load('assets/${_getAssetName()}');
  List<int> bytes = data.buffer.asUint8List();
  // Compute the hash of the asset (SHA-256)
  var hash = sha256.convert(bytes);

  if (!file.existsSync()) {
    await file.writeAsBytes(bytes, flush: true);
  }else {
    List<int> existingFileBytes = await file.readAsBytes();
    var existingFileHash = sha256.convert(existingFileBytes);

    // Only replace the file if the hash is different (asset has changed)
    if (hash != existingFileHash) {
      if (kDebugMode) {
        print('updated python server.');
      }
      await file.writeAsBytes(bytes, flush: true);
    }
  }

  await shutdownServerIfAny();

  if (defaultTargetPlatform == TargetPlatform.macOS || defaultTargetPlatform == TargetPlatform.linux) {
    await Process.run("chmod", ["u+x", filePath]);
  }

  List<String> serverParams = [];

  // if in debug mode, just use the default port 50055, but in a deployment best to check for a free port
  int port = 50055;

  if (!kDebugMode) {
    var serverSocket = await ServerSocket.bind(InternetAddress.loopbackIPv4, 0);
    port = serverSocket.port;
    serverSocket.close();
    serverParams.add(port.toString());
  }

  var process = await Process.start(filePath, serverParams,  environment: {'GRPC_VERBOSITY': 'ERROR'});

  final logFilePath = p.join(dir.path, "python_hamming_server.log");
  final logSink = File(logFilePath).openWrite(mode: FileMode.write);

  process.stdout
      .transform(utf8.decoder)
      .listen((data) {
    logSink.write("PYTHON STDOUT: $data");
  });

  process.stderr
      .transform(utf8.decoder)
      .listen((data) {
    logSink.write("PYTHON STDERR: $data");
  });

  int? exitCode;

  process.exitCode.then((v) {
    exitCode = v;
  });

  await Future.delayed(const Duration(seconds: 3));
  if (exitCode != null) {
    throw 'The python server failed to load. Exit code provided: $exitCode';
  }

  return port;
}

/// Searches for any processes that match the python server and kills them
Future<void> shutdownServerIfAny() async {
  if (kIsWeb) {
    return;
  }

  var name = _getAssetName();

  switch (defaultTargetPlatform) {
    case TargetPlatform.linux:
    case TargetPlatform.macOS:
      await Process.run('pkill', [name]);
      break;
    case TargetPlatform.windows:
      final toKill = <String>{name};

      // Add stripped version without `_win`
      if (name.contains('_win')) {
        toKill.add(name.replaceFirst('_win', ''));
      }

      for (final exe in toKill) {
        await Process.run('taskkill', ['/F', '/IM', exe]);
      }
    default:
      break;
  }
}

String _getAssetName() {
  var name = '';

  if (defaultTargetPlatform == TargetPlatform.windows) {
    name += 'hamming_server_win.exe';
  } else if (defaultTargetPlatform == TargetPlatform.macOS) {
    name += 'hamming_server_osx';
  } else if (defaultTargetPlatform == TargetPlatform.linux) {
    name += 'hamming_server_lnx';
  }
  return name;
}
