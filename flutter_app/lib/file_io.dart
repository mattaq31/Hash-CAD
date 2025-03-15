import 'package:file_picker/file_picker.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'dart:io';
import 'crisscross_core/slats.dart';
import 'crisscross_core/sparse_to_array_conversion.dart';
import 'crisscross_core/assembly_handles.dart';
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

void exportDesign(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, double gridSize) async{

  // TODO: assembly handles should not be created here - should only be drawn from slat system
  List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, gridSize);
  List<List<List<int>>> handleArray = generateRandomSlatHandles(slatArray, 32); //TODO: this should not be generated randomly but be assigned to slats and then retained

  Offset minPos;
  Offset maxPos;
  (minPos, maxPos) = extractGridBoundary(slats);

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
  metadataSheet.cell(CellIndex.indexByString('B4')).value = DoubleCellValue(minPos.dx);
  metadataSheet.cell(CellIndex.indexByString('C4')).value = DoubleCellValue(minPos.dy);
  metadataSheet.cell(CellIndex.indexByString('B5')).value = DoubleCellValue(maxPos.dx);
  metadataSheet.cell(CellIndex.indexByString('C5')).value = DoubleCellValue(maxPos.dx);

  excel.delete('Sheet1'); // removes useless first sheet

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

