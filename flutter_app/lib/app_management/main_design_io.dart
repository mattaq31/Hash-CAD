import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:excel/excel.dart';
import 'package:flutter/material.dart';
import 'package:hash_cad/crisscross_core/handle_plates.dart';
import 'package:path/path.dart';
import 'package:toml/toml.dart';

import 'dart:math';
import 'dart:io';

import '../crisscross_core/cargo.dart';
import '../crisscross_core/slats.dart';
import '../crisscross_core/sparse_to_array_conversion.dart';
import '../crisscross_core/seed.dart';
import '../crisscross_core/common_utilities.dart';
import 'design_state_mixins/design_state_handle_link_mixin.dart';

// Remember the last directory used for opening files in this session (desktop only)
String? _lastOpenDirectory;

final Random _rand = Random();

final List<Color> qualitativeCargoColors = [
  Color(0xFF1B9E77), // Teal
  Color(0xFFD95F02), // Orange/
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
    initialDirectory: kIsWeb ? null : _lastOpenDirectory,
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
    HandleLinkManager linkManager,
    double gridSize, String gridMode, String suggestedDesignName) async{

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

        String slatId = '$layerID-I${slatArray[row][col][layer]}';
        Slat? slat;
        int? position;

        if (slatArray[row][col][layer] != 0){
          slat = slats[slatId]!;
        }

        // first, assign the slat array
        // column/row are flipped in the internal representation - the flip-back to normal values is done here
        if (slatArray[row][col][layer] != 0) {
          position = slat!.slatCoordinateToPosition[Offset(row.toDouble(), col.toDouble()) + minPos]!;
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = TextCellValue('${slatArray[row][col][layer]}-$position');
          Color layerColor = layerMap.entries.firstWhere((element) => element.value['order'] == layer).value['color'];
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle = CellStyle(backgroundColorHex: layerColor.toHexString().excelColor);
        }
        else{
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
        }

        // next, assign the cargo arrays
        for (var side in ['lower', 'upper']) {
          if (occupiedCargoPoints['$layerID-${side == 'lower' ? 'bottom' : 'top'}'] == null || occupiedCargoPoints['$layerID-${side == 'lower' ? 'bottom' : 'top'}']!.isEmpty) {
            continue; // skip the sheet entirely if there is no cargo on this layer (to reduce file complexity)
          }
          String helixSide = layerMap[layerID]?['${side == 'lower' ? 'bottom' : 'top'}_helix'].toLowerCase();
          Sheet cargoSheet = excel['cargo_layer_${layer + 1}_${side}_$helixSide'];

          Sheet? seedSheet = assessedSeedLayers.contains('seed_layer_${layer + 1}_${side}_$helixSide') ? excel['seed_layer_${layer + 1}_${side}_$helixSide'] : null;

          if (slat == null) {
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
            continue;
          }
          var slatHandleDict = helixSide == 'h2' ? slat.h2Handles : slat.h5Handles;
          if (slatHandleDict.containsKey(position) && slatHandleDict[position]!['category'] == 'CARGO'){
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = TextCellValue(slatHandleDict[position]!['value']);
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle = CellStyle(backgroundColorHex: cargoPalette[slatHandleDict[position]!['value']]!.color.toHexString().excelColor);
          }
          else{
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
          }

          // if seed handle present, save directly to its special sheet
          if (slatHandleDict.containsKey(position) && slatHandleDict[position]!['category'] == 'SEED'){
            seedSheet!.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = TextCellValue(slatHandleDict[position]!['value']);
            seedSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle = CellStyle(backgroundColorHex: cargoPalette['SEED']!.color.toHexString().excelColor);
          }

        }
      }
    }
  }

  // writes phantom slats to the same slat file (if any)
  for (var slat in slats.values){
    if (slat.phantomParent != null){
      int layer = layerMap[slat.layer]!['order'];
      Sheet sheet = excel['slat_layer_${layer+1}'];
      for (int i = 0; i < slat.maxLength; i++) {
        var pos = slat.slatPositionToCoordinate[i + 1]!;
        int x = (pos.dx - minPos.dx).toInt();
        int y = (pos.dy - minPos.dy).toInt();
        // column/row are flipped in the internal representation - the flip-back to normal values is done here
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: x, rowIndex: y)).value = TextCellValue('P${slat.numericID}_${slats[slat.phantomParent]!.numericID}-${i+1}');

        Color layerColor = layerMap.entries.firstWhere((element) => element.value['order'] == layer).value['color'];
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: x, rowIndex: y)).cellStyle = CellStyle(backgroundColorHex: layerColor.toHexString().excelColor);

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
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle = CellStyle(backgroundColorHex: '#1AFF1A'.excelColor);
        }
      }
    }
  }

  // preparing standard metadata (non-complex for now)
  Sheet metadataSheet = excel['metadata'];
  metadataSheet.cell(CellIndex.indexByString('A1')).value = TextCellValue('Layer Interface Orientations');
  metadataSheet.cell(CellIndex.indexByString('A2')).value = TextCellValue('Connection Angle');
  metadataSheet.cell(CellIndex.indexByString('A3')).value = TextCellValue('File Format');
  metadataSheet.cell(CellIndex.indexByString('B3')).value = TextCellValue('#-CAD');
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

  // COLOUR METADATA
  int colorStartPoint = cargoStartPoint + cIndex;
  metadataSheet.merge(CellIndex.indexByString('A$colorStartPoint'), CellIndex.indexByString('G$colorStartPoint'), customValue: TextCellValue('UNIQUE SLAT COLOUR INFO'));
  metadataSheet.cell(CellIndex.indexByString('A$colorStartPoint')).cellStyle = CellStyle(
    horizontalAlign: HorizontalAlign.Center,
  );
  // export all cargo info from the palette (need a loop)
  metadataSheet.cell(CellIndex.indexByString('A${colorStartPoint+1}')).value = TextCellValue('ID');
  metadataSheet.cell(CellIndex.indexByString('B${colorStartPoint+1}')).value = TextCellValue('Colour');
  int colorIndex = 2;
  for (var s in slats.values.where((slat) => slat.uniqueColor != null)) {
    metadataSheet.cell(CellIndex.indexByString('A${colorStartPoint + colorIndex}')).value = TextCellValue(s.id);
    metadataSheet.cell(CellIndex.indexByString('B${colorStartPoint + colorIndex}')).value = TextCellValue('#${s.uniqueColor!.value.toRadixString(16).substring(2).toUpperCase()}');
    colorIndex += 1;
  }

  // export slat type metadata to a separate sheet for easy editing
  Sheet slatTypeSheet = excel['slat_types'];
  slatTypeSheet.cell(CellIndex.indexByString('A1')).value = TextCellValue('Layer');
  slatTypeSheet.cell(CellIndex.indexByString('B1')).value = TextCellValue('Slat ID');
  slatTypeSheet.cell(CellIndex.indexByString('C1')).value = TextCellValue('Type');

  List<List<CellValue>> rows = [];

  for (var slat in slats.values) {
    if(slat.phantomParent != null){
      continue; // skip phantom slats
    }
    int layerNum = layerMap[slat.layer]!['order'] + 1;
    int slatIdNum = int.parse(slat.id.split("-I").last);
    rows.add([
      IntCellValue(layerNum),
      IntCellValue(slatIdNum),
      TextCellValue(slat.slatType),
    ]);
  }
  // Sort by layer, then slat ID
  rows.sort((a, b) {
    int layerA = (a[0] as IntCellValue).value;
    int layerB = (b[0] as IntCellValue).value;
    if (layerA != layerB) return layerA.compareTo(layerB);

    int idA = (a[1] as IntCellValue).value;
    int idB = (b[1] as IntCellValue).value;
    return idA.compareTo(idB);
  });

  // Append sorted rows
  for (var row in rows) {
    slatTypeSheet.appendRow(row);
  }

  // finally, export the link manager to its own sheet
  writeHandleLinksToExcel(excel, slats, linkManager, layerMap);

  excel.delete('Sheet1'); // removes useless first sheet

  if (kIsWeb){
    excel.save(fileName: '$suggestedDesignName.xlsx');
  }  else {
    // Get the directory to save the file
    String? filePath = await selectSaveLocation('$suggestedDesignName.xlsx');
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


bool extractAssemblyHandlesFromExcel(Excel excelFile, List<List<List<int>>> slatArray, Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, double minX, double minY, bool rowColFlipped){
  /// extracts assembly handles from a pre-opened excel workbook and assigns them to slats
  /// An extra flag (rowColFlipped) is used to determine whether the row/column order should be flipped when reading from Excel (to match with internal representations)

  for (var table in excelFile.tables.keys.where((key) =>
      key.startsWith('handle_interface_'))) {
    // runs through each handle layer sheet
    var handleLayerIndex = int.parse(table.split('_').last) - 1;
    var sheet = excelFile.tables[table]!;
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
          CellValue? cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
          Offset positionCoord = Offset(col + minX, row + minY);

          int value = cell is IntCellValue ? cell.value : 0;
          int slatSide;

          // if a handle is found, assign it to the slat
          if (value != 0) {
            String slatID;
            // build up slat ID from layer and slat value
            try {
              if(rowColFlipped){
                // if the row/column order is flipped, then the column is the first value
                slatID = "$layerID-I${slatArray[col][row][layer]}";
              }
              else {
                // if the row/column order is not flipped, then the row is the first value
                slatID = "$layerID-I${slatArray[row][col][layer]}";
              }
              if (slatID.contains('I0')){
                // if the slat ID is 0, this means that there is an error or simply that the assembly handle is only assigned to one slat of the two layers.
                continue;
              }
            }
            catch (e) {
              // if the slat ID is not found, then there is a problem in the file - need to return false
              return false;
            }

            String category = '';

            // determine which side of the slat the handle is on
            if (layer == handleLayerIndex) {
              slatSide = int.parse(layerMap[layerID]?['top_helix'].replaceAll(
                  RegExp(r'[^0-9]'), ''));
              category = 'ASSEMBLY_HANDLE';
            }
            else {
              slatSide = int.parse(
                  layerMap[layerID]?['bottom_helix'].replaceAll(
                      RegExp(r'[^0-9]'), ''));
              category = 'ASSEMBLY_ANTIHANDLE';
            }

            // if slat is not available then something is wrong - either a slat or assembly handle are not aligned
            // TODO: since I'm now allowing slats to have handles on one side only, how do I check for a misaligned handle?
            if (!slats.containsKey(slatID)){
              return false;
            }

            // assign the exact handle to the slat
            slats[slatID]?.setPlaceholderHandle(slats[slatID]!.slatCoordinateToPosition[positionCoord]!, slatSide, '$value', category);
          }
        }
      }
    }
  }
  return true;
}

Future<(Map<String, Slat>, Map<String, Map<String, dynamic>>, String, Map<String, Cargo>, Map<(String, String, Offset), Seed>, Map<String, Map<int, String>>, HandleLinkManager, String)> parseDesignInIsolate(Uint8List fileBytes) async {

  Map<String, Map<String, dynamic>> layerMap = {};
  Map<String, Slat> slats = {};
  Map<String, Map<int, String>> phantomMap = {};
  Map<String, Cargo> cargoPalette = {};
  Map<(String, String, Offset), Seed> seedRoster = {};
  HandleLinkManager linkManager = HandleLinkManager();

  // read in file with Excel package
  var excel = Excel.decodeBytes(fileBytes);

  // Metadata must exist
  if (!excel.tables.containsKey('metadata')) {
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_GENERAL');
  }

  // Read metadata
  var metadataSheet = excel.tables['metadata']!;

  // obtain grid boundary minima
  double minX = readExcelDouble(metadataSheet, 'B4');
  double minY = readExcelDouble(metadataSheet, 'C4');

  // obtain grid mode
  String gridMode = readExcelString(metadataSheet, 'B2').trim();

  // Read slat layers
  int numLayers = excel.tables.keys
      .where((key) => key.startsWith('slat_layer_'))
      .length;

  // if no layers found, return empty maps
  if (numLayers == 0) {
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_SLAT_SHEETS');
  }

  int layerReadStart = 8;
  // read in layer data
  for (int i = 0; i < numLayers; i++) {
    String fullKey = readExcelString(metadataSheet, 'A${i + layerReadStart}');
    layerMap[fullKey.substring('Layer '.length)] = {
      'direction': readExcelInt(metadataSheet, 'B${i + layerReadStart}'),
      'DBDirection': readExcelInt(metadataSheet, 'B${i + layerReadStart}'), // TODO: remove once decided on which type of direction system to use...
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
  while (readExcelString(metadataSheet, 'A${cargoReadStart + cargoCount}').trim().isNotEmpty  && readExcelString(metadataSheet, 'A${cargoReadStart + cargoCount}').trim() != 'UNIQUE SLAT COLOUR INFO') {
    String cargoName = readExcelString(metadataSheet, 'A${cargoReadStart + cargoCount}');
    String cargoShortName = readExcelString(metadataSheet, 'B${cargoReadStart + cargoCount}');
    Color cargoColor = Color(int.parse('0xFF${readExcelString(metadataSheet, 'C${cargoReadStart + cargoCount}').substring(1)}'));
    cargoPalette[cargoName] = Cargo(name: cargoName, shortName: cargoShortName, color: cargoColor);
    cargoCount += 1;
  }
  // read in slat colour data, if available (older design files didn't have this metadata)
  int colorReadStart = cargoReadStart + cargoCount + 2;
  int colorCount = 0;
  Map<String, Color> slatColors = {};

  while (readExcelString(metadataSheet, 'A${colorReadStart + colorCount}').trim().isNotEmpty) {
    String slatID = readExcelString(metadataSheet, 'A${colorReadStart + colorCount}');
    Color slatColor = Color(int.parse('0xFF${readExcelString(metadataSheet, 'B${colorReadStart + colorCount}').substring(1)}'));
    slatColors[slatID] = slatColor;
    colorCount += 1;
  }

  // Read slat type metadata, if available
  Map <(int, int), String> slatTypeMap = {};

  try {
    if (excel.tables.containsKey('slat_types')) {
      var slatTypeSheet = excel.tables['slat_types']!;
      if (slatTypeSheet.rows.isNotEmpty) {
        // First row is headers
        List<String> headers = slatTypeSheet.rows.first.map((cell) => cell?.value.toString() ?? "").toList();

        int layerIndex = headers.indexOf("Layer");
        int slatIdIndex = headers.indexOf("Slat ID");
        int typeIndex = headers.indexOf("Type");

        if (layerIndex == -1 || slatIdIndex == -1 || typeIndex == -1) {
          throw Exception("Missing required columns in slat_types sheet");
        }

        // Iterate over remaining rows
        for (int i = 1; i < slatTypeSheet.rows.length; i++) {
          var row = slatTypeSheet.rows[i];
          if (row.isEmpty) continue;

          var layerStr = row[layerIndex]?.value?.toString();
          var slatIdStr = row[slatIdIndex]?.value?.toString();
          var typeStr = row[typeIndex]?.value?.toString();

          if (layerStr != null && slatIdStr != null && typeStr != null) {
            var layer = int.tryParse(layerStr);
            var slatId = int.tryParse(slatIdStr);
            if (layer != null && slatId != null) {
              slatTypeMap[(layer, slatId)] = typeStr;
            }
          }
        }
      }
    }
  }
  catch (_){
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_GENERAL');
  }

  // prepares slat array from metadata information
  List<List<List<int>>> slatArray;
  try {
    slatArray = List.generate(excel.tables['slat_layer_1']!.maxRows,
        (_) => List.generate(excel.tables['slat_layer_1']!.maxColumns, (_) => List.filled(numLayers, 0)));
  } catch (_) {
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_SLAT_SHEETS');
  }

  // extracts slat positional data into array
  try {
    for (var table in excel.tables.keys.where((key) => key.startsWith('slat_layer_'))) {
      var layerIndex = int.parse(table.split('_').last) - 1;
      String layer = layerMap.entries.firstWhere((element) => element.value['order'] == layerIndex).key;

      Map<int, Map<int, Offset>> slatCoordinates = {}; // slatID -> position -> coordinate
      Map<int, Map<int, Map<int, Offset>>> phantomCoordinates = {};  // ref slatID -> phantomID -> position -> coordinate

      var sheet = excel.tables[table]!;
      for (var row = 0; row < sheet.maxRows; row++) {
        for (var col = 0; col < sheet.maxColumns; col++) {
          var cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
          String value = (cell is TextCellValue) ? cell.value.text ?? '' : '';
          if (value != '' && value != '0') {
            value = value.trim();
            // phantom slats have an _ in their excel representation
            if(value.contains('_')){
              // e.g. Px_y-z
              int phantomID = int.parse(value.split('_')[0].substring(1));
              int slatID = int.parse(value.split('-')[0].split('_')[1]);
              int slatPosition = int.parse(value.split('-')[1]);
              phantomCoordinates.putIfAbsent(slatID, () => {});
              phantomCoordinates[slatID]!.putIfAbsent(phantomID, () => {});
              phantomCoordinates[slatID]![phantomID]![slatPosition] = Offset(col + minX, row + minY);
            }
            else {
              int slatID = int.parse(value.split('-')[0]);
              int slatPosition = int.parse(value.split('-')[1]);
              slatCoordinates.putIfAbsent(slatID, () => {});
              slatCoordinates[slatID]![slatPosition] = Offset(col + minX, row + minY);
              slatArray[row][col][layerIndex] = slatID;
            }

          } else if (cell is IntCellValue && cell.value != 0) {
            // backwards compatibility for old files
            int slatID =cell.value; // slat value extracted directly from the cell
            slatCoordinates.putIfAbsent(slatID, () => {});
            int nextPosition = slatCoordinates[slatID]!.length + 1; // no information on position provided, so just assume its the next available position
            slatCoordinates[slatID]![nextPosition] = Offset(col + minX, row + minY);
            slatArray[row][col][layerIndex] = slatID;
          }
        }
      }

      for (var slatBundle in slatCoordinates.entries) {
        var category = 'tube';
        // get category from metadata, if available
        if (slatTypeMap.containsKey((layerIndex + 1, slatBundle.key))) {
          category = slatTypeMap[(layerIndex + 1, slatBundle.key)]!;
        }
        slats["$layer-I${slatBundle.key}"] = Slat(slatBundle.key,"$layer-I${slatBundle.key}", layer, slatBundle.value, slatType: category);
      }
      layerMap[layer]!['slat_count'] = slatCoordinates.length;

      // phantom slats copy their parent slats directly
      for (var refSlatPhantoms in phantomCoordinates.entries) {
        for (var phantomSlatBundle in refSlatPhantoms.value.entries) {
          String phantomName = "$layer-I${refSlatPhantoms.key}-P${phantomSlatBundle.key}";
          String refSlatName = "$layer-I${refSlatPhantoms.key}";
          String category = slats[refSlatName]!.slatType;
          phantomMap.putIfAbsent(refSlatName, () => {});
          phantomMap[refSlatName]![phantomSlatBundle.key] = phantomName;
          slats[phantomName] = Slat(phantomSlatBundle.key, phantomName, layer, phantomSlatBundle.value, slatType: category, phantomParent: refSlatName);
        }
      }
    }
  }
  catch (_){
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_SLAT_SHEETS');
  }


  // applies unique colors to slats, if available
  for (var slat in slats.values){
    if (slatColors.containsKey(slat.id)){
      slat.setColor(slatColors[slat.id]!);

      // all phantoms also need to be colored in the same way
      if(phantomMap.containsKey(slat.id)){
        for (var phantomID in phantomMap[slat.id]!.values){
          slats[phantomID]?.setColor(slatColors[slat.id]!);
        }
      }

    }
  }

  // assembly handle extraction
  final okHandles = extractAssemblyHandlesFromExcel(excel, slatArray, slats, layerMap, minX, minY, false);
  if (!okHandles) {
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_ASSEMBLY_SHEETS');
  }

  // extracts cargo handles and assigns them to slats
  try {
    for (var table
        in excel.tables.keys.where((key) => key.startsWith('cargo'))) {
      // runs through each handle layer sheet
      int cargoLayerIndex = int.parse(table.split('_')[2]) - 1;
      int cargoLayerSide = parseHelixSide(table.split('_')[4]);
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
          String value =
              (cellValue is TextCellValue) ? cellValue.value.text ?? '' : '';
          if (value == '0' || value == '') {
            continue;
          }

          // this is the case where old design files are used, which didn't have a specific metadata system for cargo
          if (!cargoPalette.containsKey(value)) {
            // choose a random color
            cargoPalette[value] = Cargo(name: value, shortName: generateShortName(value), color: qualitativeCargoColors[_rand.nextInt(qualitativeCargoColors.length)]);
          }

          String slatID = "$layerID-I${slatArray[row][col][cargoLayerIndex]}";
          // convert the array index into the exact grid position using the grid size and minima extracted from the metadata file
          Offset positionCoord = Offset(col + minX, row + minY);

          // assign the exact handle to the slat
          slats[slatID]?.setPlaceholderHandle(slats[slatID]!.slatCoordinateToPosition[positionCoord]!, cargoLayerSide, value, 'CARGO');
        }
      }
    }
  }
  catch (_){
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_CARGO_SHEETS');
  }

  // legacy compatibility with files that didn't contain seed info
  if(!cargoPalette.containsKey('SEED')){
    cargoPalette['SEED'] = Cargo(name: 'SEED', shortName: 'S1', color: Color.fromARGB(255, 255, 0, 0));
  }

  Map <(String, String, String), Map<int, Offset>> partialSeedArrays = {};

  // extracts seed handles and assigns them to slats
   try {
    for (var table in excel.tables.keys.where((key) => key.startsWith('seed'))) {
      // runs through each handle layer sheet
      int seedLayerIndex = int.parse(table.split('_')[2]) - 1;
      int seedLayerSide = parseHelixSide(table.split('_')[4]);
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
          String value =
              (cellValue is TextCellValue) ? cellValue.value.text ?? '' : '';
          if (value == '0' || value == '') {
            continue;
          }

          String slatID = "$layerID-I${slatArray[row][col][seedLayerIndex]}";
          // convert the array index into the exact grid position using the grid size and minima extracted from the metadata file
          Offset positionCoord = Offset(col + minX, row + minY);

          // assign the exact handle to the slat
          slats[slatID]?.setPlaceholderHandle(
              slats[slatID]!.slatCoordinateToPosition[positionCoord]!,
              seedLayerSide,
              value,
              'Seed');

          partialSeedArrays.putIfAbsent(
              (value.split('-')[0], layerID, sideString), () => {});

          partialSeedArrays[(value.split('-')[0], layerID, sideString)]![
              getIndexFromSeedText(value)] = positionCoord;
        }
      }
    }
  }
  catch (_){
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_SEED_SHEETS');
  }

  // prepares seedRoster from partial seed arrays
  // Only register in seedRoster if complete 5x16 pattern (80 handles) and valid formation
  for (var partialSeed in partialSeedArrays.entries) {
    Map<int, Offset> seedCoordinates = partialSeed.value;
    String seedID = partialSeed.key.$1;
    String layerID = partialSeed.key.$2;
    String sideString = partialSeed.key.$3;

    // Must have exactly 80 handles for a complete seed
    if (seedCoordinates.length != 80) {
      // Partial seeds remain as isolated seed handles on slats (already set above)
      continue;
    }

    // Verify no phantom slats and count distinct slats anchored
    Set<String> attachmentSlats = {};
    bool hasPhantom = false;

    for (var coord in seedCoordinates.values) {
      String slatID = "$layerID-I${slatArray[coord.dy.toInt() - minY.toInt()][coord.dx.toInt() - minX.toInt()][layerMap[layerID]!['order']]}";
      var slat = slats[slatID];
      if (slat == null) continue;

      if (slat.phantomParent != null) {
        hasPhantom = true;
        break;
      }

      var uniqueSlatID = slat.id;
      if (slat.slatType != 'tube') {
        uniqueSlatID = slat.id + (slat.slatCoordinateToPosition[coord]! < 17 ? '-first-half' : 'second-half');
      }
      attachmentSlats.add(uniqueSlatID);
    }

    // Skip if handles on phantom slats or not enough distinct slats (parallel placement)
    if (hasPhantom || attachmentSlats.length < 16) {
      continue;
    }

    // Build list of (Offset, row, col) for geometry validation
    List<(Offset, int, int)> handles = [];
    for (var entry in seedCoordinates.entries) {
      int index = entry.key;
      int row = (index - 1) ~/ 16 + 1;
      int col = (index - 1) % 16 + 1;
      handles.add((entry.value, row, col));
    }

    // Verify handles are spatially adjacent in correct grid pattern
    if (!validateSeedGeometry(handles)) {
      continue;
    }

    // Valid complete seed - add to roster
    seedRoster[(layerID, sideString, seedCoordinates[1]!)] = Seed(ID: seedID, coordinates: seedCoordinates);
  }

  // before finishing, copies all handles to phantom slats
  for (var slat in slats.values.where((slat) => slat.phantomParent != null)){
    slat.copyHandlesFromSlat(slats[slat.phantomParent!]!);
  }


  // finally, import handle link data if available
  try {
    String? linkError = extractHandleLinksFromExcel(excel, slats, layerMap, linkManager);
    if (linkError != null) {
      // Return the specific error message for display to user
      return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_LINK_MANAGER: $linkError');
    }
  } catch (e) {
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, 'ERR_LINK_MANAGER: ${e.toString()}');
  }


  return (slats, layerMap, gridMode, cargoPalette, seedRoster, phantomMap, linkManager, '');
}

Future<(Map<String, Slat>, Map<String, Map<String, dynamic>>, String, Map<String, Cargo>, Map<(String, String, Offset), Seed>, Map<String, Map<int, String>>, HandleLinkManager, String, String)>
importDesign({String? inputFileName, Uint8List? inputFileBytes}) async {
  /// Reads in a design from the standard format excel file, and returns maps of slats and layers found in the design.

  Map<String, Map<String, dynamic>> layerMap = {};
  Map<String, Slat> slats = {};
  Map<String, Cargo> cargoPalette = {};
  Map<String, Map<int, String>> phantomMap = {};
  Map<(String, String, Offset), Seed> seedRoster = {};
  HandleLinkManager linkManager = HandleLinkManager();

  String filePath;
  Uint8List fileBytes;
  String fileName;

  if (inputFileBytes != null && inputFileName != null) {
    fileName = basenameWithoutExtension(inputFileName);
    fileBytes = inputFileBytes;
  } else {
    // main user dialog box for file selection
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx'],
      initialDirectory: kIsWeb ? null : _lastOpenDirectory,
    );
    if (result != null) {
      // web has a different file-opening procedure to the desktop app
      if (kIsWeb) {
        fileBytes = result.files.first.bytes!;
      } else {
        filePath = result.files.single.path!;
        fileBytes = File(filePath).readAsBytesSync();
        // Remember directory for next time
        try {
          _lastOpenDirectory = dirname(filePath);
        } catch (_) {}
      }
      fileName = basenameWithoutExtension(result.files.first.name);
    } else {
      // if nothing picked, return empty maps
      return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, '', '');
    }
  }
  // run isolate function
  try {
    final (slatsOut, layerMapOut, layerName, cargoOut, seedOut, phantomMapOut, linkManagerOut, errorCode) =
        await compute(parseDesignInIsolate, fileBytes);
    return (
      slatsOut,
      layerMapOut,
      layerName,
      cargoOut,
      seedOut,
      phantomMapOut,
      linkManagerOut,
      fileName,
      errorCode
    );
  } catch (_) {
    return (slats, layerMap, '', cargoPalette, seedRoster, phantomMap, linkManager, '', 'ERR_GENERAL');
  }
}

Future <bool> importAssemblyHandlesFromFileIntoSlatArray(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, double gridSize) async{

  Uint8List fileBytes;
  String filePath;

  // main user dialog box for file selection
  FilePickerResult? result = await FilePicker.platform.pickFiles(
    type: FileType.custom,
    allowedExtensions: ['xlsx'],
    allowMultiple: false,
    initialDirectory: kIsWeb ? null : _lastOpenDirectory,
  );

  if (result != null) {
    // web has a different file-opening procedure to the desktop app
    if (kIsWeb) {
      fileBytes = result.files.first.bytes!;
    }
    else {
      filePath = result.files.single.path!;
      fileBytes = File(filePath).readAsBytesSync();
      // Remember directory for next time
      try { _lastOpenDirectory = dirname(filePath); } catch (_) {}
    }
  }else{
    return true; // if nothing picked, return
  }

  // clear old handles before importing new ones
  for (var slat in slats.values) {
    slat.clearAssemblyHandles();
  }

  // read in file with Excel package
  var excel = Excel.decodeBytes(fileBytes);

  // extract slat array
  Offset minPos;
  Offset maxPos;
  (minPos, maxPos) = extractGridBoundary(slats);
  List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);

  // assign assembly handles to slats (returns true if successful, false if there is an error)
  return extractAssemblyHandlesFromExcel(excel, slatArray, slats, layerMap, minPos.dx, minPos.dy, true);
}

Future <void> importPlatesFromFile(PlateLibrary plateLibrary) async{

  List<Uint8List> fileBytes = [];
  List<String> plateNames = [];

  // main user dialog box for file selection
  FilePickerResult? result = await FilePicker.platform.pickFiles(
    type: FileType.custom,
    allowedExtensions: ['xlsx'],
    allowMultiple: true,
    initialDirectory: kIsWeb ? null : _lastOpenDirectory,
  );

  if (result != null) {
    // web has a different file-opening procedure to the desktop app
    if (kIsWeb) {
      for (var file in result.files) {
        String plateName = file.name.split('.').first;
        fileBytes.add(file.bytes!);
        plateNames.add(plateName);
      }
    }
    else {
      // desktop app
      for (var file in result.files) {
        String plateName = file.name.split('.').first;
        fileBytes.add(File(file.path!).readAsBytesSync());
        plateNames.add(plateName);
      }
      // Remember directory for next time using the first selected file
      if (result.files.isNotEmpty && result.files.first.path != null) {
        try { _lastOpenDirectory = dirname(result.files.first.path!); } catch (_) {}
      }
    }
  }
  plateLibrary.readPlates(fileBytes, plateNames);
}

/// Exports evolution parameters to a TOML file
Future<void> exportEvolutionParameters(Map<String, String> parameters) async {
  String? filePath = await FilePicker.platform.saveFile(
    dialogTitle: 'Save As',
    fileName: 'evolution_config.toml',
    type: FileType.custom,
    allowedExtensions: ['toml'],
    initialDirectory: kIsWeb ? null : _lastOpenDirectory,
  );

  // if filepath is null, return
  if (filePath == null) {
    return;
  }

  final convertedParams = parameters.map((key, value) {
    final lower = value.toLowerCase().trim();

    // --- Handle booleans ---
    if (lower == 'true') return MapEntry(key, true);
    if (lower == 'false') return MapEntry(key, false);

    // --- Handle comma-separated numeric lists ---
    if (value.contains(',')) {
      final parts = value.split(',').map((s) => s.trim()).toList();

      // Check if all parts are numeric
      final allNumeric = parts.every((p) => num.tryParse(p) != null);
      if (allNumeric) {
        final list = parts.map((p) => double.parse(p)).toList();
        return MapEntry(key, list);
      }
    }

    // --- Handle numeric values ---
    final numValue = num.tryParse(value);
    if (numValue != null) {
      if (numValue == numValue.roundToDouble()) {
        return MapEntry(key, numValue.toInt());
      } else {
        return MapEntry(key, numValue.toDouble());
      }
    }

    // --- Default: keep as string ---
    return MapEntry(key, value);
  });

  // Encode to TOML
  final tomlString = TomlDocument.fromMap(convertedParams).toString();

  // Save to a file
  final file = File(filePath);
  await file.writeAsString(tomlString);
}

/// Extracts handle link data from an Excel file and imports it into the HandleLinkManager.
/// Returns null if successful (even if no link data exists), or an error message string on conflict/error.
String? extractHandleLinksFromExcel(Excel excelFile, Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, HandleLinkManager linkManager) {

  if (!excelFile.tables.containsKey('slat_handle_links')) {
    // No link data sheet (backwards compatibility)
    return null;
  }

  try {
    var sheet = excelFile.tables['slat_handle_links']!;
    List<List<dynamic>> data = [];

    for (var row = 0; row < sheet.maxRows; row++) {
      List<dynamic> rowData = [];
      for (var col = 0; col < sheet.maxColumns; col++) {
        var cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
        if (cell is TextCellValue) {
          rowData.add(cell.value.text ?? '');
        } else if (cell is IntCellValue) {
          rowData.add(cell.value);
        } else if (cell is DoubleCellValue) {
          rowData.add(cell.value);
        } else {
          rowData.add(null);
        }
      }
      data.add(rowData);
    }

    // Validate before importing
    String? validationError = linkManager.validateImport(data, slats, layerMap);
    if (validationError != null) {
      return validationError;
    }

    linkManager.importFromExcelData(data, slats, layerMap);
    return null;
  } catch (e) {
    return 'Error importing handle links: ${e.toString()}';
  }
}

/// Writes handle link data to an Excel workbook.
/// Creates the 'slat_handle_links' sheet with proper formatting.
void writeHandleLinksToExcel(Excel excel, Map<String, Slat> slats, HandleLinkManager linkManager, Map<String, Map<String, dynamic>> layerMap) {

  List<List<dynamic>> linkData = linkManager.exportToExcelData(slats, layerMap);
  if (linkData.isEmpty) {
    return;
  }

  Sheet sheet = excel['slat_handle_links'];

  // Determine max columns
  int maxCols = 0;
  for (var row in linkData) {
    if (row.length > maxCols) maxCols = row.length;
  }

  // Write data to sheet
  for (int rowIdx = 0; rowIdx < linkData.length; rowIdx++) {
    var row = linkData[rowIdx];
    for (int colIdx = 0; colIdx < row.length; colIdx++) {
      var value = row[colIdx];
      if (value == null || value == '') {
        // Leave cell empty
        continue;
      } else if (value is int) {
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: colIdx, rowIndex: rowIdx)).value = IntCellValue(value);
      } else if (value is double) {
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: colIdx, rowIndex: rowIdx)).value = DoubleCellValue(value);
      } else {
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: colIdx, rowIndex: rowIdx)).value = TextCellValue(value.toString());
      }
    }
  }

  // Apply formatting to slat name rows (every 6 rows starting at 0)
  for (int i = 0; i < linkData.length; i += 6) {
    if (i >= linkData.length) break;

    var slatId = linkData[i][0].toString();
    var slat = slats[pythonToDartSlatNameConvert(slatId, layerMap)]!;
    Color layerColor;

    if (slat.uniqueColor != null) {
      layerColor = slat.uniqueColor!;
    } else {
      layerColor = layerMap[slat.layer]?['color'] ?? Color(0xFF808080);
    }

    // Calculate brightness to determine font color
    int r = (layerColor.r * 255.0).round() & 0xFF;
    int g = (layerColor.g * 255.0).round() & 0xFF;
    int b = (layerColor.b * 255.0).round() & 0xFF;
    double brightness = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0;
    String fontColor = brightness < 0.5 ? 'FFFFFF' : '000000';

    // Merge the slat name row across all columns
    if (maxCols > 1) {
      sheet.merge(
        CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: i),
        CellIndex.indexByColumnRow(columnIndex: maxCols - 1, rowIndex: i),
        customValue: TextCellValue(slatId),
      );
    }

    // Apply background color to first cell of the slat name row
    sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: i)).cellStyle = CellStyle(
      backgroundColorHex: layerColor.toHexString().excelColor,
      fontColorHex: fontColor.excelColor,
      horizontalAlign: HorizontalAlign.Center,
    );

  }
}




