import '../crisscross_core/slats.dart';
import 'dart:convert';
import '../crisscross_core/handle_plates.dart';
import 'dart:io';
import 'dart:js_interop';

import 'package:web/web.dart' as web;

import 'package:csv/csv.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:file_picker/file_picker.dart';


List<String> _generatePlateLayout96() {
  final rows = 'ABCDEFGH'.split('');
  final cols = List.generate(12, (i) => i + 1);
  return [
    for (var row in rows)
      for (var col in cols) '$row${col.toString()}'
  ];
}

List<String> _generatePlateLayout384() {
  final rows = 'ABCDEFGHIJKLMNOP'.split('');
  final cols = List.generate(24, (i) => i + 1);
  return [
    for (var row in rows)
      for (var col in cols) '$row${col.toString()}'
  ];
}

Future<void> convertSlatsToEchoCsv({
  required Map<String, Slat> slatDict,
  required Map<String, Map<String, dynamic>> layerMap,
  required String destinationPlateName,
  required String outputFilename,
  int referenceTransferVolumeNl = 75,
  int referenceConcentrationUM = 500,
  String plateSize = '96',
}) async {
  final List<List<dynamic>> outputCommandList = [];

  late List<String> plateFormat;
  if (plateSize == '96') {
    plateFormat = _generatePlateLayout96();
  } else {
    plateFormat = _generatePlateLayout384();
  }

  final outputWellList = <String>[];
  final outputPlateNumList = <int>[];

  for (var i = 0; i < slatDict.length; i++) {
    outputWellList.add(plateFormat[i % plateFormat.length]);
    outputPlateNumList.add(1 + (i ~/ plateFormat.length));
  }

  var index = 0;

  final sortedSlats = slatDict.entries.toList()
    ..sort((a, b) {
      // Sort by layer first, then index
      return layerMap[a.value.layer]!['order']! != layerMap[b.value.layer]!['order']! ? layerMap[a.value.layer]!['order']!.compareTo(layerMap[b.value.layer]!['order']!) : a.value.numericID.compareTo(b.value.numericID);
    });

  for (final entry in sortedSlats) {

    final layerID = (layerMap[entry.key.split('-')[0]]!['order'] + 1).toString();
    final slat = entry.value;
    final slatName = 'layer$layerID-slat${slat.numericID}';

    var sortedH2 = slat.h2Handles.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key));
    var sortedH5 = slat.h5Handles.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key));

    if (slatName.contains(',')) {
      throw Exception('Slat name "$slatName" cannot contain commas.');
    }

    for (final entry in sortedH2 + sortedH5) {
      int id = entry.key;
      var handleData = entry.value;
      String side = sortedH2.contains(entry) ? 'h2' : 'h5';
      final volume = (referenceTransferVolumeNl *
              (referenceConcentrationUM / handleData['concentration']))
          .round();

      if (volume % 25 != 0) {
        throw Exception(
            'Volume $volume for handle ${slatName}_${side}_staple_$id is not a multiple of 25.');
      }

      outputCommandList.add([
        '${slatName}_${side}_staple_$id',
        sanitizePlateMap(handleData['plate']),
        handleData['well'],
        outputWellList[index],
        volume,
        '${destinationPlateName}_${outputPlateNumList[index]}',
        '384PP_AQ_BP'
      ]);
    }
    index++;
  }

  final csvString = const ListToCsvConverter().convert([
    ['Component', 'Source Plate Name', 'Source Well', 'Destination Well', 'Transfer Volume', 'Destination Plate Name', 'Source Plate Type'],
    ...outputCommandList
  ]);

  if (kIsWeb) {
    // Web download logic
    final bytes = utf8.encode(csvString);
    final blob = web.Blob([bytes.toJS].toJS);
    final url = web.URL.createObjectURL(blob);

    final anchor = web.HTMLAnchorElement()
      ..href = url
      ..download = outputFilename;
    anchor.click();

    web.URL.revokeObjectURL(url);
  } else {
    // Desktop app

    // Get the directory to save the file
    String? filePath = await FilePicker.platform.saveFile(
      dialogTitle: 'Save As',
      fileName: outputFilename,
      type: FileType.custom,
      allowedExtensions: ['csv'],
    );

    // if filepath is null, return
    if (filePath == null) {
      return;
    }

    final file = File(filePath);
    file.writeAsStringSync(csvString);
  }
}
