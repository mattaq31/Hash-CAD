import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:excel/excel.dart';
import 'package:flutter/material.dart';
import 'dart:math';
import 'dart:io';

import '../crisscross_core/cargo.dart';
import '../crisscross_core/slats.dart';
import '../crisscross_core/sparse_to_array_conversion.dart';
import '../crisscross_core/seed.dart';

final Random _rand = Random();

final List<Color> qualitativeCargoColors = [
  Color(0xFF1B9E77), // Teal
  Color(0xFFD95F02), // Orange
  Color(0xFF7570B3), // Purple
  Color(0xFFE7298A), // Pink
  Color(0xFF66A61E), // Green
  Color(0xFFE6AB02), // Mustard
  Color(0xFFA6761D), // Brown
  Color(0xFF0034FF), // Blue
];

Future<String?> selectSaveLocation(String defaultFileName) async {
  String? filePath = await FilePicker.platform.saveFile(
    dialogTitle: 'Save As',
    fileName: defaultFileName,
    type: FileType.custom,
    allowedExtensions: ['xlsx'],
  );

  if (filePath != null) {
    return filePath;
  } else {
    return null;
  }
}

/// hacky function to generate layer map string that matches python system
String generateLayerString(Map<String, Map<String, dynamic>> layerMap) {
  // Sort layers by 'order' field
  var sortedLayers = layerMap.entries.toList()
    ..sort((a, b) => a.value['order'].compareTo(b.value['order']));

  // Extract helix pairs
  List<List<String>> helixPairs = sortedLayers
      .map((entry) => [entry.value['bottom_helix'].toString(), entry.value['top_helix'].toString()])
      .toList();

  // prepare string with first value
  String result = '[${helixPairs[0][0][1]}, ';

  // run through the remaining values and add them in the required pairs
  for (int i = 0; i < helixPairs.length-1; i++) {
    result += '(${helixPairs[i][1][1]}, ${helixPairs[i+1][0][1]}), ';
  }

  result += '${helixPairs.last[1][1]}]';

  return result;
}

void exportDesign(Map<String, Slat> slats,
    Map<String, Map<String, dynamic>> layerMap,
    Map<String, Cargo> cargoPalette,
    Map<String, Map<Offset, String>> occupiedCargoPoints,
    Map<(String, String, Offset), Seed> seedRoster,
    double gridSize, String gridMode) async{

  Offset minPos;
  Offset maxPos;
  (minPos, maxPos) = extractGridBoundary(slats);
  List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);

  List<List<List<int>>> handleArray = extractAssemblyHandleArray(slats, layerMap, minPos, maxPos, gridSize);

  var excel = Excel.createExcel();

  // Prepare individual sheets for seed arrays, if present
  Set<String> assessedSeedLayers = {};
  for (var seed in seedRoster.entries) {
    int layerID = layerMap[seed.key.$1]!['order'];
    String helixSide = layerMap[seed.key.$1]?['${seed.key.$2}_helix'].toLowerCase();
    String positionalName = seed.key.$2 == 'top'? 'upper' : 'lower';
    String sheetName = 'seed_layer_${layerID + 1}_${positionalName}_$helixSide';
    Sheet sheet = excel[sheetName];
    if (!assessedSeedLayers.contains(sheetName)) {
      assessedSeedLayers.add(sheetName);
      for (int row = 0; row < handleArray.length; row++) {
        for (int col = 0; col < handleArray[row].length; col++) {
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
        }
      }
    }
  }

  // Write the slat arrays to individual sheets
  // cargo export is also integrated within this same system
  for (int layer = 0; layer < slatArray[0][0].length; layer++) {
    Sheet sheet = excel['slat_layer_${layer+1}'];
    String layerID = layerMap.entries.firstWhere((element) => element.value['order'] == layer).key;
    for (int row = 0; row < slatArray.length; row++) {
      for (int col = 0; col < slatArray[row].length; col++) {

        // first, assign the slat array
        // column/row are flipped in the internal representation - the flip-back to normal values is done here
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(slatArray[row][col][layer]);
        if (slatArray[row][col][layer] != 0) {
          Color layerColor = layerMap.entries.firstWhere((element) => element.value['order'] == layer).value['color'];
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle = CellStyle(backgroundColorHex: layerColor.toHexString().excelColor);
        }

        // next, assign the cargo arrays
        String slatId = '$layerID-I${slatArray[row][col][layer]}';
        Slat? slat;
        if (slatArray[row][col][layer] != 0){
          slat = slats[slatId]!;
        }
        for (var side in ['lower', 'upper']) {
          if (occupiedCargoPoints['$layerID-${side == 'lower' ? 'bottom' : 'top'}'] == null || occupiedCargoPoints['$layerID-${side == 'lower' ? 'bottom' : 'top'}']!.isEmpty) {
            continue; // skip the sheet entirely if  there is no cargo on this layer (to reduce file complexity)
          }
          String helixSide = layerMap[layerID]?['${side == 'lower' ? 'bottom' : 'top'}_helix'].toLowerCase();
          Sheet cargoSheet = excel['cargo_layer_${layer + 1}_${side}_$helixSide'];

          Sheet? seedSheet = assessedSeedLayers.contains('seed_layer_${layer + 1}_${side}_$helixSide') ? excel['seed_layer_${layer + 1}_${side}_$helixSide'] : null;

          if (slat == null) {
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
            continue;
          }
          var slatHandleDict = helixSide == 'h2' ? slat.h2Handles : slat.h5Handles;
          var position = slat.slatCoordinateToPosition[Offset(row.toDouble(), col.toDouble()) + minPos]!;
          if (slatHandleDict.containsKey(position) && slatHandleDict[position]!['category'] == 'Cargo'){
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = TextCellValue(slatHandleDict[position]!['descriptor']);
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle = CellStyle(backgroundColorHex: cargoPalette[slatHandleDict[position]!['descriptor']]!.color.toHexString().excelColor);
          }
          else{
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
          }

          // if seed handle present, save directly to its special sheet
          if (slatHandleDict.containsKey(position) && slatHandleDict[position]!['category'] == 'Seed'){
            seedSheet!.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = TextCellValue(slatHandleDict[position]!['descriptor']);
            seedSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle = CellStyle(backgroundColorHex: cargoPalette['SEED']!.color.toHexString().excelColor);
          }

        }
      }
    }
  }

  // Write the assembly handle arrays to individual sheets
  for (int layer = 0; layer < handleArray[0][0].length; layer++) {
    Sheet sheet = excel['handle_interface_${layer+1}'];
    for (int row = 0; row < handleArray.length; row++) {
      for (int col = 0; col < handleArray[row].length; col++) {
        // column/row are flipped in the internal representation - the flip-back to normal values is done here
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(handleArray[row][col][layer]);
        if (handleArray[row][col][layer] != 0) {
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle =CellStyle(backgroundColorHex: '#1AFF1A'.excelColor);
        }
      }
    }
  }

  // preparing standard metadata (non-complex for now)
  Sheet metadataSheet = excel['metadata'];
  metadataSheet.cell(CellIndex.indexByString('A1')).value = TextCellValue('Layer Interface Orientations');
  metadataSheet.cell(CellIndex.indexByString('A2')).value = TextCellValue('Connection Angle');
  metadataSheet.cell(CellIndex.indexByString('A3')).value = TextCellValue('Reversed Slats');
  metadataSheet.cell(CellIndex.indexByString('B3')).value = TextCellValue('[]'); // TODO: update with actual reversed slats when this is implemented
  metadataSheet.cell(CellIndex.indexByString('A4')).value = TextCellValue('Canvas Offset (Min)');
  metadataSheet.cell(CellIndex.indexByString('A5')).value = TextCellValue('Canvas Offset (Max)');

  metadataSheet.cell(CellIndex.indexByString('B2')).value = TextCellValue(gridMode);
  metadataSheet.cell(CellIndex.indexByString('B4')).value = DoubleCellValue(minPos.dx);
  metadataSheet.cell(CellIndex.indexByString('C4')).value = DoubleCellValue(minPos.dy);
  metadataSheet.cell(CellIndex.indexByString('B5')).value = DoubleCellValue(maxPos.dx);
  metadataSheet.cell(CellIndex.indexByString('C5')).value = DoubleCellValue(maxPos.dx);

  // starting from the lowermost layer, this prepares a string of format (2, (5,2), (2,5), 5), where each number represents the position of the layer e.g. if layer 1 is (h5, h2) and layer 2 is (h2, h5), the string would be (5, (2,2),5)
  metadataSheet.cell(CellIndex.indexByString('B1')).value = TextCellValue(generateLayerString(layerMap));

  // prepare layer data headers
  metadataSheet.merge(CellIndex.indexByString('A6'), CellIndex.indexByString('G6'), customValue: TextCellValue('LAYER INFO'));
  // Apply style to the top-left cell of the merged range
  metadataSheet.cell(CellIndex.indexByString('A6')).cellStyle = CellStyle(
    horizontalAlign: HorizontalAlign.Center,
  );

  metadataSheet.cell(CellIndex.indexByString('A7')).value = TextCellValue('ID');
  metadataSheet.cell(CellIndex.indexByString('B7')).value = TextCellValue('Default Rotation');
  metadataSheet.cell(CellIndex.indexByString('C7')).value = TextCellValue('Top Helix');
  metadataSheet.cell(CellIndex.indexByString('D7')).value = TextCellValue('Bottom Helix');
  metadataSheet.cell(CellIndex.indexByString('E7')).value = TextCellValue('Next Slat ID');
  metadataSheet.cell(CellIndex.indexByString('F7')).value = TextCellValue('Slat Count');
  metadataSheet.cell(CellIndex.indexByString('G7')).value = TextCellValue('Colour');

  int layerStartPoint = 8;
  for (var l in layerMap.entries){
    metadataSheet.cell(CellIndex.indexByString('A${l.value['order']+layerStartPoint}')).value = TextCellValue("Layer ${l.key}");
    metadataSheet.cell(CellIndex.indexByString('B${l.value['order']+layerStartPoint}')).value = IntCellValue(l.value['direction']);
    metadataSheet.cell(CellIndex.indexByString('C${l.value['order']+layerStartPoint}')).value = TextCellValue(l.value['top_helix']);
    metadataSheet.cell(CellIndex.indexByString('D${l.value['order']+layerStartPoint}')).value = TextCellValue(l.value['bottom_helix']);
    metadataSheet.cell(CellIndex.indexByString('E${l.value['order']+layerStartPoint}')).value = IntCellValue(l.value['next_slat_id']);
    metadataSheet.cell(CellIndex.indexByString('F${l.value['order']+layerStartPoint}')).value = IntCellValue(l.value['slat_count']);
    metadataSheet.cell(CellIndex.indexByString('G${l.value['order']+layerStartPoint}')).value = TextCellValue('#${l.value['color'].value.toRadixString(16).substring(2).toUpperCase()}');
  }

  // CARGO METADATA
  int cargoStartPoint = layerStartPoint + layerMap.length;
  metadataSheet.merge(CellIndex.indexByString('A$cargoStartPoint'), CellIndex.indexByString('G$cargoStartPoint'), customValue: TextCellValue('CARGO INFO'));
  metadataSheet.cell(CellIndex.indexByString('A$cargoStartPoint')).cellStyle = CellStyle(
    horizontalAlign: HorizontalAlign.Center,
  );
  // export all cargo info from the palette (need a loop)
  metadataSheet.cell(CellIndex.indexByString('A${cargoStartPoint+1}')).value = TextCellValue('ID');
  metadataSheet.cell(CellIndex.indexByString('B${cargoStartPoint+1}')).value = TextCellValue('Short Name');
  metadataSheet.cell(CellIndex.indexByString('C${cargoStartPoint+1}')).value = TextCellValue('Colour');
  int cIndex = 2;
  for (var c in cargoPalette.entries){
    metadataSheet.cell(CellIndex.indexByString('A${cargoStartPoint + cIndex}')).value = TextCellValue(c.value.name);
    metadataSheet.cell(CellIndex.indexByString('B${cargoStartPoint + cIndex}')).value = TextCellValue(c.value.shortName);
    metadataSheet.cell(CellIndex.indexByString('C${cargoStartPoint + cIndex}')).value = TextCellValue('#${c.value.color.value.toRadixString(16).substring(2).toUpperCase()}');
    cIndex += 1;
  }

  excel.delete('Sheet1'); // removes useless first sheet

  if (kIsWeb){
    // TODO: allow user to change filename in-app for web somehow
    excel.save(fileName: 'Megastructure.xlsx');
  }
  else {
    // Get the directory to save the file
    String? filePath = await selectSaveLocation('Megastructure.xlsx');
    // if filepath is null, return
    if (filePath == null) {
      return;
    }
    // Save the file
    List<int>? fileBytes = excel.encode();
    if (fileBytes != null) {
      File(filePath)
        ..createSync(recursive: true)
        ..writeAsBytesSync(fileBytes);
    }
  }
}

int readExcelInt(Sheet workSheet, String cell){
  /// The Excel package has an annoying variable format which needs to be
  /// confirmed to be a certain type before Dart allows you to
  /// access the internal value.  This function can be used to read in integers.
  var cellValue = workSheet.cell(CellIndex.indexByString(cell)).value;
  return(cellValue is IntCellValue)
      ? cellValue.value
      : 0;
}

double readExcelDouble(Sheet workSheet, String cell){
  /// The Excel package has an annoying variable format which needs to be
  /// confirmed to be a certain type before Dart allows you to
  /// access the internal value.  This function can be used to read in doubles.
  var cellValue = workSheet.cell(CellIndex.indexByString(cell)).value;
  return(cellValue is IntCellValue)
      ? cellValue.value.toDouble()
      : (cellValue is DoubleCellValue)
      ? cellValue.value
      : 0.0;
}

String readExcelString(Sheet workSheet, String cell){
  /// The Excel package has an annoying variable format which needs to be
  /// confirmed to be a certain type before Dart allows you to
  /// access the internal value.  This function can be used to read in strings.
  var cellValue = workSheet.cell(CellIndex.indexByString(cell)).value;
  return (cellValue is TextCellValue)
      ? cellValue.value.text ?? ''
      : '';
}

Future<(Map<String, Slat>, Map<String, Map<String, dynamic>>, String, Map<String, Cargo>, Map<(String, String, Offset), Seed>)> parseDesignInIsolate(Uint8List fileBytes) async {

  Map<String, Map<String, dynamic>> layerMap = {};
  Map<String, Slat> slats = {};
  Map<String, Cargo> cargoPalette = {};
  Map<(String, String, Offset), Seed> seedRoster = {};

  // read in file with Excel package
  var excel = Excel.decodeBytes(fileBytes);

  // Read metadata
  var metadataSheet = excel.tables['metadata']!;

  // obtain grid boundary minima
  double minX = readExcelDouble(metadataSheet, 'B4');
  double minY = readExcelDouble(metadataSheet, 'C4');

  // obtain grid Mode
  String gridMode = readExcelString(metadataSheet, 'B2').trim();

  // Read slat layers
  int numLayers = excel.tables.keys
      .where((key) => key.startsWith('slat_layer_'))
      .length;

  // if no layers found, return empty maps
  if (numLayers == 0) {
    return (slats, layerMap, '', cargoPalette, seedRoster);
  }


  int layerReadStart = 8;
  // read in layer data
  for (int i = 0; i < numLayers; i++) {
    String fullKey = readExcelString(metadataSheet, 'A${i + layerReadStart}');
    layerMap[fullKey.substring('Layer '.length)] = {
      'direction': readExcelInt(metadataSheet, 'B${i + layerReadStart}'),
      'top_helix': readExcelString(metadataSheet, 'C${i + layerReadStart}'),
      'bottom_helix': readExcelString(metadataSheet, 'D${i + layerReadStart}'),
      'next_slat_id': readExcelInt(metadataSheet, 'E${i + layerReadStart}'),
      'order': i,
      'slat_count': 0,
      'color': Color(int.parse(
          '0xFF${readExcelString(metadataSheet, 'G${i + layerReadStart}')
              .substring(1)}')),
      "hidden": false
    };
  }
  int cargoReadStart = layerReadStart + numLayers + 2;
  int cargoCount = 0;
  // read in cargo data, if available (older design files didn't have this metadata)
  while (readExcelString(metadataSheet, 'A${cargoReadStart + cargoCount}')
      .trim()
      .isNotEmpty) {
    String cargoName = readExcelString(
        metadataSheet, 'A${cargoReadStart + cargoCount}');
    String cargoShortName = readExcelString(
        metadataSheet, 'B${cargoReadStart + cargoCount}');
    Color cargoColor = Color(int.parse(
        '0xFF${readExcelString(metadataSheet, 'C${cargoReadStart + cargoCount}')
            .substring(1)}'));
    cargoPalette[cargoName] =
        Cargo(name: cargoName, shortName: cargoShortName, color: cargoColor);
    cargoCount += 1;
  }

  // prepares slat array from metadata information
  List<List<List<int>>> slatArray = List.generate(
      excel.tables['slat_layer_1']!.maxRows, (_) =>
      List.generate(excel.tables['slat_layer_1']!.maxColumns, (_) =>
          List.filled(numLayers, 0)));

  // set to keep track of slat IDs (both layer ID and slat ID required to ensure a unique ID)
  Set<(int, int)> slatIDs = {};

  // extracts slat positional data into array
  for (var table in excel.tables.keys.where((key) =>
      key.startsWith('slat_layer_'))) {
    var layerIndex = int.parse(table
        .split('_')
        .last) - 1;
    var sheet = excel.tables[table]!;
    for (var row = 0; row < sheet.maxRows; row++) {
      for (var col = 0; col < sheet.maxColumns; col++) {
        var cell = sheet
            .cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row))
            .value;
        int value = cell is IntCellValue ? cell.value : 0;
        slatArray[row][col][layerIndex] = value;
        // adds ID to set if a slat is found
        if (value != 0) {
          slatIDs.add((layerIndex, value));
        }
      }
    }
  }

  // prepares slat class objects from all slats found in the array
  // TODO: could this be combined with the above loops to speed up the operation?
  for (var slatID in slatIDs) {
    // identifies slat layer
    String layer = layerMap.entries
        .firstWhere((element) => element.value['order'] == slatID.$1)
        .key;
    Map<int, Offset> slatCoordinates = {};
    int slatPositionCounter = 1;

    layerMap[layer]!['slat_count'] += 1; // populates slat count from the true number of slats found in the design

    for (int i = 0; i < slatArray.length; i++) {
      for (int j = 0; j < slatArray[i].length; j++) {
        if (slatArray[i][j][slatID.$1] == slatID.$2) {
          // converts the array index into the exact grid position using the grid size and minima extracted from the metadata file

          // column/row are flipped in the internal representation - the flip-back from normal to internal values is done here

          slatCoordinates[slatPositionCounter] = Offset(j + minX, i + minY);
          slatPositionCounter += 1;
        }
      }
    }
    // slats generated using the usual formatting system
    slats["${layer}-I${slatID.$2}"] = Slat(slatID.$2, "${layer}-I${slatID.$2}", layer, slatCoordinates);
  }

  // extracts assembly handles and assigns them to slats
  // TODO: as before, need to handle errors and problematic cases more gracefully...
  for (var table in excel.tables.keys.where((key) =>
      key.startsWith('handle_interface_'))) {
    // runs through each handle layer sheet
    var handleLayerIndex = int.parse(table
        .split('_')
        .last) - 1;
    var sheet = excel.tables[table]!;
    // there are always 2 slat layers to address for each handle (bottom and top)
    for (var layer in [handleLayerIndex, handleLayerIndex + 1]) {
      // extract actual layerID
      String layerID = layerMap.entries
          .firstWhere((element) => element.value['order'] == layer)
          .key;
      // loop through the whole array
      for (var row = 0; row < sheet.maxRows; row++) {
        for (var col = 0; col < sheet.maxColumns; col++) {
          // extract cell handle data
          var cell = sheet
              .cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row))
              .value;
          int value = cell is IntCellValue ? cell.value : 0;
          int slatSide;

          // if a handle is found, assign it to the slat
          if (value != 0) {
            // build up slat ID from layer and slat value
            String slatID = "$layerID-I${slatArray[row][col][layer]}";

            // determine which side of the slat the handle is on
            if (layer == handleLayerIndex) {
              slatSide = int.parse(layerMap[layerID]?['top_helix'].replaceAll(
                  RegExp(r'[^0-9]'), ''));
            }
            else {
              slatSide = int.parse(
                  layerMap[layerID]?['bottom_helix'].replaceAll(
                      RegExp(r'[^0-9]'), ''));
            }

            // convert the array index into the exact grid position using the grid size and minima extracted from the metadata file
            Offset positionCoord = Offset(col + minX, row + minY);

            // assign the exact handle to the slat
            slats[slatID]?.setPlaceholderHandle(
                slats[slatID]!.slatCoordinateToPosition[positionCoord]!,
                slatSide, '$value', 'Assembly');
          }
        }
      }
    }
  }


  // extracts cargo handles and assigns them to slats
  // TODO: as before, need to handle errors and problematic cases more gracefully...
  for (var table in excel.tables.keys.where((key) => key.startsWith('cargo'))) {
    // runs through each handle layer sheet
    int cargoLayerIndex = int.parse(table.split('_')[2])-1;
    int cargoLayerSide = int.parse(table.split('_')[4].replaceAll(RegExp(r'[^0-9]'), ''));
    var sheet = excel.tables[table]!;

    // extract layerID
    String layerID = layerMap.entries
        .firstWhere((element) => element.value['order'] == cargoLayerIndex)
        .key;

    // loop through the whole array
    for (var row = 0; row < sheet.maxRows; row++) {
      for (var col = 0; col < sheet.maxColumns; col++) {
        // extract cell handle data
        var cellValue = sheet
            .cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row))
            .value;
        String value = (cellValue is TextCellValue)
            ? cellValue.value.text ?? ''
            : '';
        if (value == '0' || value == '') {
          continue;
        }

        // this is the case where old design files are used, which didn't have a specific metadata system for cargo
        if (!cargoPalette.containsKey(value)){
          // choose a random color
          cargoPalette[value] = Cargo(name: value, shortName: generateShortName(value), color: qualitativeCargoColors[_rand.nextInt(qualitativeCargoColors.length)]);
        }

        String slatID = "$layerID-I${slatArray[row][col][cargoLayerIndex]}";
        // convert the array index into the exact grid position using the grid size and minima extracted from the metadata file
        Offset positionCoord = Offset(col + minX, row + minY);

        // assign the exact handle to the slat
        slats[slatID]?.setPlaceholderHandle(
            slats[slatID]!.slatCoordinateToPosition[positionCoord]!,
            cargoLayerSide, value, 'Cargo');
      }
    }
  }

  // legacy compatibility with files that didn't contain seed info
  if(!cargoPalette.containsKey('SEED')){
    cargoPalette['SEED'] = Cargo(name: 'SEED', shortName: 'S1', color: Color.fromARGB(255, 255, 0, 0));
  }

  Map <(String, String, String), Map<int, Offset>> partialSeedArrays = {};

  // extracts seed handles and assigns them to slats
  // TODO: as before, need to handle errors and problematic cases more gracefully...
  for (var table in excel.tables.keys.where((key) => key.startsWith('seed'))) {
    // runs through each handle layer sheet
    int seedLayerIndex = int.parse(table.split('_')[2])-1;
    int seedLayerSide = int.parse(table.split('_')[4].replaceAll(RegExp(r'[^0-9]'), ''));
    String sideString = table.split('_')[3] == 'upper' ? 'top' : 'bottom';

    var sheet = excel.tables[table]!;

    // extract layerID
    String layerID = layerMap.entries
        .firstWhere((element) => element.value['order'] == seedLayerIndex)
        .key;

    // loop through the whole array
    for (var row = 0; row < sheet.maxRows; row++) {
      for (var col = 0; col < sheet.maxColumns; col++) {

        // extract cell handle data
        var cellValue = sheet
            .cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row))
            .value;
        String value = (cellValue is TextCellValue)
            ? cellValue.value.text ?? ''
            : '';
        if (value == '0' || value == '') {
          continue;
        }

        String slatID = "$layerID-I${slatArray[row][col][seedLayerIndex]}";
        // convert the array index into the exact grid position using the grid size and minima extracted from the metadata file
        Offset positionCoord = Offset(col + minX, row + minY);

        // assign the exact handle to the slat
        slats[slatID]?.setPlaceholderHandle(
            slats[slatID]!.slatCoordinateToPosition[positionCoord]!,
            seedLayerSide, value, 'Seed');

        partialSeedArrays.putIfAbsent((value.split('-')[0],layerID, sideString), () => {});

        partialSeedArrays[(value.split('-')[0],layerID, sideString)]![getIndexFromSeedText(value)] = positionCoord;
      }
    }
  }

  for (var partialSeed in partialSeedArrays.entries){
    seedRoster[(partialSeed.key.$2, partialSeed.key.$3, partialSeed.value[1]!)] = Seed(ID: partialSeed.key.$1, coordinates: partialSeed.value);
  }

  return (slats, layerMap, gridMode, cargoPalette, seedRoster);
}


Future<(Map<String, Slat>, Map<String, Map<String, dynamic>>, String, Map<String, Cargo>, Map<(String, String, Offset), Seed>)> importDesign() async {
  /// Reads in a design from the standard format excel file, and returns maps of slats and layers found in the design.
  // TODO: there could obviously be many errors here due to an incorrect file type.  Need to catch them and present useful error messages.

  Map<String, Map<String, dynamic>> layerMap = {};
  Map<String, Slat> slats = {};
  Map<String, Cargo> cargoPalette = {};
  Map<(String, String, Offset), Seed> seedRoster = {};

  String filePath;
  Uint8List fileBytes;

  // main user dialog box for file selection
  FilePickerResult? result = await FilePicker.platform.pickFiles(
    type: FileType.custom,
    allowedExtensions: ['xlsx'],
  );


  if (result != null) {
    // web has a different file-opening procedure to the desktop app
    if (kIsWeb) {
      fileBytes = result.files.first.bytes!;
    }
    else {
      filePath = result.files.single.path!;
      fileBytes = File(filePath).readAsBytesSync();
    }
  } else { // if nothing picked, return empty maps
    return (slats, layerMap, '', cargoPalette, seedRoster);
  }
  // run isolate function
  return await compute(parseDesignInIsolate, fileBytes);
}


