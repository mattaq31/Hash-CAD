/// Excel I/O for assembly handle arrays (handle_interface_N sheets).
import 'dart:io';
import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:path/path.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/sparse_to_array_conversion.dart';
import 'design_io_constants.dart';
import 'file_picker_helpers.dart';

/// Reads assembly handles from [excelFile] and assigns them as placeholders on [slats].
///
/// Each handle_interface sheet bridges two adjacent slat layers. The [rowColFlipped]
/// flag controls axis convention: false during main parse, true when importing
/// from a separate assembly file (which uses the opposite row/col order).
///
/// Returns true on success, false if any handle cannot be matched to a slat.
bool extractAssemblyHandlesFromExcel(Excel excelFile, List<List<List<int>>> slatArray, Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, double minX, double minY, bool rowColFlipped) {
  for (var table in excelFile.tables.keys.where((key) => key.startsWith(handleInterfacePrefix))) {
    var handleLayerIndex = int.parse(table.split('_').last) - 1;
    var sheet = excelFile.tables[table]!;
    for (var layer in [handleLayerIndex, handleLayerIndex + 1]) {
      String layerID = layerMap.entries.firstWhere((element) => element.value['order'] == layer).key;
      for (var row = 0; row < sheet.maxRows; row++) {
        for (var col = 0; col < sheet.maxColumns; col++) {
          CellValue? cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
          Offset positionCoord = Offset(col + minX, row + minY);

          int value = cell is IntCellValue ? cell.value : 0;
          int slatSide;

          if (value != 0) {
            String slatID;
            try {
              if (rowColFlipped) {
                slatID = "$layerID-I${slatArray[col][row][layer]}";
              } else {
                slatID = "$layerID-I${slatArray[row][col][layer]}";
              }
              if (slatID.contains('I0')) {
                continue;
              }
            } catch (e) {
              return false;
            }

            String category = '';

            if (layer == handleLayerIndex) {
              slatSide = int.parse(layerMap[layerID]?['top_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
              category = categoryAssemblyHandle;
            } else {
              slatSide = int.parse(layerMap[layerID]?['bottom_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
              category = categoryAssemblyAntihandle;
            }

            // TODO: since I'm now allowing slats to have handles on one side only, how do I check for a misaligned handle?
            if (!slats.containsKey(slatID)) {
              return false;
            }

            slats[slatID]?.setPlaceholderHandle(slats[slatID]!.slatCoordinateToPosition[positionCoord]!, slatSide, '$value', category);
          }
        }
      }
    }
  }
  return true;
}

/// Prompts the user for an Excel file, clears existing assembly handles, and imports new ones.
///
/// Used after running handle evolution on the Python backend.
/// Returns true on success, false if the imported handles are misaligned.
Future<bool> importAssemblyHandlesFromFileIntoSlatArray(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, double gridSize) async {
  Uint8List fileBytes;
  String filePath;

  FilePickerResult? result = await FilePicker.platform.pickFiles(
    type: FileType.custom,
    allowedExtensions: ['xlsx'],
    allowMultiple: false,
    initialDirectory: kIsWeb ? null : lastOpenDirectory,
  );

  if (result != null) {
    if (kIsWeb) {
      fileBytes = result.files.first.bytes!;
    } else {
      filePath = result.files.single.path!;
      fileBytes = File(filePath).readAsBytesSync();
      try {
        lastOpenDirectory = dirname(filePath);
      } catch (_) {}
    }
  } else {
    return true;
  }

  // Backup fluorophore assignments before clearing handles
  final fluorophoreBackup = <String, Map<int, Map<int, String>>>{};
  for (var slat in slats.values) {
    for (var side in [2, 5]) {
      final handleDict = side == 2 ? slat.h2Handles : slat.h5Handles;
      for (var entry in handleDict.entries) {
        final fluor = entry.value['fluorophore'] as String?;
        if (fluor != null) {
          fluorophoreBackup.putIfAbsent(slat.id, () => {}).putIfAbsent(side, () => {})[entry.key] = fluor;
        }
      }
    }
  }

  for (var slat in slats.values) {
    slat.clearAssemblyHandles();
  }

  var excel = Excel.decodeBytes(fileBytes);

  Offset minPos;
  Offset maxPos;
  (minPos, maxPos) = extractGridBoundary(slats);
  List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);

  final importSuccess = extractAssemblyHandlesFromExcel(excel, slatArray, slats, layerMap, minPos.dx, minPos.dy, true);

  // Restore fluorophore assignments to handles that still exist
  for (var entry in fluorophoreBackup.entries) {
    final slat = slats[entry.key];
    if (slat == null) continue;
    for (var sideEntry in entry.value.entries) {
      final handleDict = sideEntry.key == 2 ? slat.h2Handles : slat.h5Handles;
      for (var posEntry in sideEntry.value.entries) {
        if (handleDict.containsKey(posEntry.key)) {
          handleDict[posEntry.key]!['fluorophore'] = posEntry.value;
        }
      }
    }
  }

  return importSuccess;
}
