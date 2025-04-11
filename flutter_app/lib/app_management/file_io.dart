import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'dart:io';
import '../crisscross_core/slats.dart';
import '../crisscross_core/sparse_to_array_conversion.dart';
import 'package:excel/excel.dart';
import 'package:flutter/material.dart';

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

void exportDesign(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, double gridSize, String gridMode) async{

  // TODO: assembly handles should not be created here - should only be drawn from slat system
  Offset minPos;
  Offset maxPos;
  (minPos, maxPos) = extractGridBoundary(slats);
  List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);

  List<List<List<int>>> handleArray = extractAssemblyHandleArray(slats, layerMap, minPos, maxPos, gridSize);

  var excel = Excel.createExcel();

  // Write the array to the sheet
  for (int layer = 0; layer < slatArray[0][0].length; layer++) {
    Sheet sheet = excel['slat_layer_${layer+1}'];
    for (int row = 0; row < slatArray.length; row++) {
      for (int col = 0; col < slatArray[row].length; col++) {
        // TODO: for some reason col/row are flipped - need to investigate
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(slatArray[row][col][layer]);
        if (slatArray[row][col][layer] != 0) {
          Color layerColor = layerMap.entries.firstWhere((element) => element.value['order'] == layer).value['color'];
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle =CellStyle(backgroundColorHex: layerColor.toHexString().excelColor);
        }
      }
    }
  }

  // Write the array to the sheet
  for (int layer = 0; layer < handleArray[0][0].length; layer++) {
    Sheet sheet = excel['handle_interface_${layer+1}'];
    for (int row = 0; row < handleArray.length; row++) {
      for (int col = 0; col < handleArray[row].length; col++) {
        // TODO: for some reason col/row are flipped - need to investigate
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
  metadataSheet.cell(CellIndex.indexByString('A4')).value = TextCellValue('Canvas Offset (Min)');
  metadataSheet.cell(CellIndex.indexByString('A5')).value = TextCellValue('Canvas Offset (Max)');

  metadataSheet.cell(CellIndex.indexByString('B2')).value = TextCellValue(gridMode);
  metadataSheet.cell(CellIndex.indexByString('B4')).value = DoubleCellValue(minPos.dx);
  metadataSheet.cell(CellIndex.indexByString('C4')).value = DoubleCellValue(minPos.dy);
  metadataSheet.cell(CellIndex.indexByString('B5')).value = DoubleCellValue(maxPos.dx);
  metadataSheet.cell(CellIndex.indexByString('C5')).value = DoubleCellValue(maxPos.dx);

  // starting from the lowermost layer, this prepares a string of format (2, (5,2), (2,5), 5), where each number represents the position of the layer e.g. if layer 1 is (h5, h2) and layer 2 is (h2, h5), the string would be (5, (2,2),5)
  metadataSheet.cell(CellIndex.indexByString('B1')).value = TextCellValue(generateLayerString(layerMap));

  int layerStartPoint = 6;
  for (var l in layerMap.entries){
    metadataSheet.cell(CellIndex.indexByString('A${l.value['order']+layerStartPoint}')).value = TextCellValue("Layer ${l.key}");
    metadataSheet.cell(CellIndex.indexByString('B${l.value['order']+layerStartPoint}')).value = IntCellValue(l.value['direction']);
    metadataSheet.cell(CellIndex.indexByString('C${l.value['order']+layerStartPoint}')).value = TextCellValue(l.value['top_helix']);
    metadataSheet.cell(CellIndex.indexByString('D${l.value['order']+layerStartPoint}')).value = TextCellValue(l.value['bottom_helix']);
    metadataSheet.cell(CellIndex.indexByString('E${l.value['order']+layerStartPoint}')).value = IntCellValue(l.value['slat_count']);
    metadataSheet.cell(CellIndex.indexByString('F${l.value['order']+layerStartPoint}')).value = TextCellValue('#${l.value['color'].value.toRadixString(16).substring(2).toUpperCase()}');
  }

  excel.delete('Sheet1'); // removes useless first sheet

  if (kIsWeb){
    // TODO: allow user to change filename in-app somehow
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


Future<(Map<String, Slat>, Map<String, Map<String, dynamic>>, String)> importDesign() async {
  /// Reads in a design from the standard format excel file, and returns maps of slats and layers found in the design.
  // TODO: there could obviously be many errors here due to an incorrect file type.  Need to catch them and present useful error messages.

  Map<String, Map<String, dynamic>> layerMap = {};
  Map<String, Slat> slats = {};
  String filePath;
  Uint8List fileBytes;

  // main user dialog box for file selection
  FilePickerResult? result = await FilePicker.platform.pickFiles(
    type: FileType.custom,
    allowedExtensions: ['xlsx'],
  );


  if (result != null) {
    // web has a different file-opening procedure to the desktop app
    if (kIsWeb){
      fileBytes = result.files.first.bytes!;
    }
    else {
      filePath = result.files.single.path!;
      fileBytes = File(filePath).readAsBytesSync();
    }
  } else { // if nothing picked, return empty maps
    return (slats, layerMap, '');
  }

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
  int numLayers = excel.tables.keys.where((key) => key.startsWith('slat_layer_')).length;

  // if no layers found, return empty maps
  if (numLayers == 0) {
    return (slats, layerMap, '');
  }

  int layerReadStart = 6;
  // read in layer data
  for (int i = 0; i < numLayers; i++) {
    String fullKey = readExcelString(metadataSheet, 'A${i+layerReadStart}');
    layerMap[fullKey.substring('Layer '.length)] = {
      'direction': readExcelInt(metadataSheet, 'B${i+layerReadStart}'),
      'top_helix': readExcelString(metadataSheet, 'C${i+layerReadStart}'),
      'bottom_helix': readExcelString(metadataSheet, 'D${i+layerReadStart}'),
      'slat_count': readExcelInt(metadataSheet, 'E${i+layerReadStart}'),
      'order': i,
      'color': Color(int.parse('0xFF${readExcelString(metadataSheet, 'F${i+layerReadStart}').substring(1)}')),
      "hidden": false
    };
  }

  // prepares slat array from metadata information
  List<List<List<int>>> slatArray = List.generate(excel.tables['slat_layer_1']!.maxRows,(_) => List.generate(excel.tables['slat_layer_1']!.maxColumns, (_) => List.filled(numLayers, 0)));

  // set to keep track of slat IDs (both layer ID and slat ID required to ensure a unique ID)
  Set<(int, int)> slatIDs = {};

  // extracts slat positional data into array
  for (var table in excel.tables.keys.where((key) => key.startsWith('slat_layer_'))) {
    var layerIndex = int.parse(table.split('_').last) - 1;
    var sheet = excel.tables[table]!;
    for (var row = 0; row < sheet.maxRows; row++) {
      for (var col = 0; col < sheet.maxColumns; col++) {
        var cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
        int value = cell is IntCellValue ? cell.value : 0;
        slatArray[row][col][layerIndex] = value;
        // adds ID to set if a slat is found
        if (value != 0){
          slatIDs.add((layerIndex, value));
        }
      }
    }
  }

  // prepares slat class objects from all slats found in the array
  // TODO: could this be combined with the above loops to speed up the operation?
  for (var slatID in slatIDs) {

    // identifies slat layer
    String layer = layerMap.entries.firstWhere((element) => element.value['order'] == slatID.$1).key;
    Map<int, Offset> slatCoordinates = {};
    int slatPositionCounter = 1;

    for (int i = 0; i < slatArray.length; i++) {
      for (int j = 0; j < slatArray[i].length; j++) {
        if (slatArray[i][j][slatID.$1] == slatID.$2) {
          // converts the array index into the exact grid position using the grid size and minima extracted from the metadata file
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
  for (var table in excel.tables.keys.where((key) => key.startsWith('handle_interface_'))) {
    // runs through each handle layer sheet
    var handleLayerIndex = int.parse(table.split('_').last) - 1;
    var sheet = excel.tables[table]!;
    // there are always 2 slat layers to address for each handle (bottom and top)
    for (var layer in [handleLayerIndex, handleLayerIndex + 1]) {
      // extract actual layerID
      String layerID = layerMap.entries.firstWhere((element) => element.value['order'] == layer).key;
      // loop through the whole array
      for (var row = 0; row < sheet.maxRows; row++) {
        for (var col = 0; col < sheet.maxColumns; col++) {
          // extract cell handle data
          var cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
          int value = cell is IntCellValue ? cell.value : 0;
          int slatSide;

          // if a handle is found, assign it to the slat
          if (value != 0){
            // build up slat ID from layer and slat value
            String slatID = "$layerID-I${slatArray[row][col][layer]}";

            // determine which side of the slat the handle is on
            if (layer == handleLayerIndex){
              slatSide = int.parse(layerMap[layerID]?['top_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
            }
            else{
              slatSide = int.parse(layerMap[layerID]?['bottom_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
            }

            // convert the array index into the exact grid position using the grid size and minima extracted from the metadata file
            Offset positionCoord = Offset(col + minX, row + minY);

            // assign the exact handle to the slat
            slats[slatID]?.setPlaceholderHandle(slats[slatID]!.slatCoordinateToPosition[positionCoord]!, slatSide, '$value', 'Assembly');
          }
        }
      }
    }
  }
  return (slats, layerMap, gridMode);
}


