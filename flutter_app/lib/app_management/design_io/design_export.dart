/// Excel export for #-CAD design files.
///
/// Serialises slats, cargo, seeds, assembly handles, metadata, echo plates,
/// input plates, and lab metadata into a multi-sheet .xlsx workbook.
import 'dart:io';
import 'dart:math';
import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:excel/excel.dart' as excel_lib show Border, BorderStyle;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:hash_cad/crisscross_core/handle_plates.dart';

import '../../crisscross_core/cargo.dart';
import '../../crisscross_core/seed.dart';
import '../../crisscross_core/slats.dart';
import '../../crisscross_core/sparse_to_array_conversion.dart';
import '../../echo_and_experimental_helpers/plate_layout_state.dart';
import '../design_state_mixins/design_state_handle_link_mixin.dart';
import 'design_io_constants.dart';
import 'excel_utilities.dart';
import 'file_picker_helpers.dart';
import 'handle_link_io.dart';

/// Builds a compact string describing helix interface orientations across layers.
///
/// Example output for a two-layer design: `[2, (5, 2), 5]`.
/// Used in the metadata sheet to record the layer interface topology.
String generateLayerString(Map<String, Map<String, dynamic>> layerMap) {
  var sortedLayers = layerMap.entries.toList()..sort((a, b) => a.value['order'].compareTo(b.value['order']));

  List<List<String>> helixPairs =
      sortedLayers.map((entry) => [entry.value['bottom_helix'].toString(), entry.value['top_helix'].toString()]).toList();

  String result = '[${helixPairs[0][0][1]}, ';

  for (int i = 0; i < helixPairs.length - 1; i++) {
    result += '(${helixPairs[i][1][1]}, ${helixPairs[i + 1][0][1]}), ';
  }

  result += '${helixPairs.last[1][1]}]';

  return result;
}

/// Exports the full design state to a .xlsx workbook and prompts the user to save.
///
/// Writes the following sheets (see [design_io_constants.dart] for naming conventions):
///  - `slat_layer_N` — slat placement grids with phantom slats
///  - `cargo_layer_N_side_helix` — cargo handle assignments per layer/side
///  - `seed_layer_N_side_helix` — seed position markers
///  - `handle_interface_N` — assembly handle arrays
///  - `metadata` — layer info, cargo palette, unique slat colours, grid mode
///  - `slat_types` — per-slat tube/db classification
///  - `slat_handle_links` — handle link constraints
///  - `p{index}_{name}` — echo plate layouts (optional, from [echoPlateLayoutState])
///  - `input_source_plates` — all input plates in one sheet (optional, from [plateLibrary])
///  - `lab_metadata` — export flags and master mix config (optional)
///
/// On web, triggers a browser download. On desktop, opens a native save dialog.
void exportDesign(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, Map<String, Cargo> cargoPalette,
    Map<String, Map<Offset, String>> occupiedCargoPoints, Map<(String, String, Offset), Seed> seedRoster, HandleLinkManager linkManager,
    double gridSize, String gridMode, String suggestedDesignName,
    {PlateLayoutState? echoPlateLayoutState, PlateLibrary? plateLibrary}) async {
  Offset minPos;
  Offset maxPos;
  (minPos, maxPos) = extractGridBoundary(slats);
  List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);
  List<List<List<int>>> handleArray = extractAssemblyHandleArray(slats, layerMap, minPos, maxPos, gridSize);

  var excel = Excel.createExcel();

  // ── Seed sheets: pre-fill with zeros so unoccupied positions are explicit ──
  Set<String> assessedSeedLayers = {};
  for (var seed in seedRoster.entries) {
    int layerID = layerMap[seed.key.$1]!['order'];
    String helixSide = layerMap[seed.key.$1]?[sideToHelixKey(seed.key.$2)].toLowerCase();
    String positionalName = sideToPositionalName(seed.key.$2);
    String sheetName = seedSheetName(layerID, positionalName, helixSide);
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

  // ── Slat layer sheets: write slat grid + cargo + seed handles per cell ──
  for (int layer = 0; layer < slatArray[0][0].length; layer++) {
    Sheet sheet = excel[slatLayerSheetName(layer)];
    String layerID = layerMap.entries.firstWhere((element) => element.value['order'] == layer).key;
    for (int row = 0; row < slatArray.length; row++) {
      for (int col = 0; col < slatArray[row].length; col++) {
        String slatId = '$layerID-I${slatArray[row][col][layer]}';
        Slat? slat;
        int? position;

        if (slatArray[row][col][layer] != 0) {
          slat = slats[slatId]!;
        }

        // column/row are flipped in the internal representation - the flip-back to normal values is done here
        if (slatArray[row][col][layer] != 0) {
          position = slat!.slatCoordinateToPosition[Offset(row.toDouble(), col.toDouble()) + minPos]!;
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = TextCellValue('${slatArray[row][col][layer]}-$position');
          Color layerColor = layerMap.entries.firstWhere((element) => element.value['order'] == layer).value['color'];
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle =
              CellStyle(backgroundColorHex: layerColor.toHexString().excelColor);
        } else {
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
        }

        for (var side in ['lower', 'upper']) {
          String internalSide = side == 'lower' ? 'bottom' : 'top';
          if (occupiedCargoPoints['$layerID-$internalSide'] == null || occupiedCargoPoints['$layerID-$internalSide']!.isEmpty) {
            continue;
          }
          String helixSide = layerMap[layerID]?[sideToHelixKey(internalSide)].toLowerCase();
          Sheet cargoSheet = excel[cargoSheetName(layer, side, helixSide)];

          String seedName = seedSheetName(layer, side, helixSide);
          Sheet? seedSheet = assessedSeedLayers.contains(seedName) ? excel[seedName] : null;

          if (slat == null) {
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
            continue;
          }
          var slatHandleDict = helixSide == 'h2' ? slat.h2Handles : slat.h5Handles;
          if (slatHandleDict.containsKey(position) && slatHandleDict[position]!['category'] == categoryCargo) {
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value =
                TextCellValue(slatHandleDict[position]!['value']);
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle =
                CellStyle(backgroundColorHex: cargoPalette[slatHandleDict[position]!['value']]!.color.toHexString().excelColor);
          } else {
            cargoSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(0);
          }

          if (slatHandleDict.containsKey(position) && slatHandleDict[position]!['category'] == categorySeed) {
            seedSheet!.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value =
                TextCellValue(slatHandleDict[position]!['value']);
            seedSheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle =
                CellStyle(backgroundColorHex: cargoPalette['SEED']!.color.toHexString().excelColor);
          }
        }
      }
    }
  }

  // ── Phantom slats: append to parent's slat layer sheet ──
  for (var slat in slats.values) {
    if (slat.phantomParent != null) {
      int layer = layerMap[slat.layer]!['order'];
      Sheet sheet = excel[slatLayerSheetName(layer)];
      for (int i = 0; i < slat.maxLength; i++) {
        var pos = slat.slatPositionToCoordinate[i + 1]!;
        int x = (pos.dx - minPos.dx).toInt();
        int y = (pos.dy - minPos.dy).toInt();
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: x, rowIndex: y)).value =
            TextCellValue(encodePhantomCellValue(slat.numericID, slats[slat.phantomParent]!.numericID, i + 1));

        Color layerColor = layerMap.entries.firstWhere((element) => element.value['order'] == layer).value['color'];
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: x, rowIndex: y)).cellStyle =
            CellStyle(backgroundColorHex: layerColor.toHexString().excelColor);
      }
    }
  }

  // ── Assembly handle interface sheets: one per adjacent layer pair ──
  for (int layer = 0; layer < handleArray[0][0].length; layer++) {
    Sheet sheet = excel[handleInterfaceSheetName(layer)];
    for (int row = 0; row < handleArray.length; row++) {
      for (int col = 0; col < handleArray[row].length; col++) {
        sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).value = IntCellValue(handleArray[row][col][layer]);
        if (handleArray[row][col][layer] != 0) {
          sheet.cell(CellIndex.indexByColumnRow(columnIndex: row, rowIndex: col)).cellStyle =
              CellStyle(backgroundColorHex: handleHighlightHex.excelColor);
        }
      }
    }
  }

  // ── Metadata sheet: grid mode, canvas offsets, layer interface string ──
  Sheet metadataSheet = excel[metadataSheetName];
  metadataSheet.cell(CellIndex.indexByString('A1')).value = TextCellValue('Layer Interface Orientations');
  metadataSheet.cell(CellIndex.indexByString('A2')).value = TextCellValue('Connection Angle');
  metadataSheet.cell(CellIndex.indexByString('A3')).value = TextCellValue('File Format');
  metadataSheet.cell(CellIndex.indexByString(metaCellFileFormat)).value = TextCellValue('#-CAD');
  metadataSheet.cell(CellIndex.indexByString('A4')).value = TextCellValue('Canvas Offset (Min)');
  metadataSheet.cell(CellIndex.indexByString('A5')).value = TextCellValue('Canvas Offset (Max)');

  metadataSheet.cell(CellIndex.indexByString(metaCellGridMode)).value = TextCellValue(gridMode);
  metadataSheet.cell(CellIndex.indexByString(metaCellMinX)).value = DoubleCellValue(minPos.dx);
  metadataSheet.cell(CellIndex.indexByString(metaCellMinY)).value = DoubleCellValue(minPos.dy);
  metadataSheet.cell(CellIndex.indexByString(metaCellMaxX)).value = DoubleCellValue(maxPos.dx);
  metadataSheet.cell(CellIndex.indexByString(metaCellMaxY)).value = DoubleCellValue(maxPos.dx);

  metadataSheet.cell(CellIndex.indexByString(metaCellLayerInterface)).value = TextCellValue(generateLayerString(layerMap));

  // ── Metadata: layer info section (direction, helices, colour per layer) ──
  metadataSheet.merge(CellIndex.indexByString('A6'), CellIndex.indexByString('G6'), customValue: TextCellValue(metaSectionLayerInfo));
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

  int layerStartPoint = metaLayerStartRow;
  for (var l in layerMap.entries) {
    metadataSheet.cell(CellIndex.indexByString('A${l.value['order'] + layerStartPoint}')).value = TextCellValue("Layer ${l.key}");
    metadataSheet.cell(CellIndex.indexByString('B${l.value['order'] + layerStartPoint}')).value = IntCellValue(l.value['direction']);
    metadataSheet.cell(CellIndex.indexByString('C${l.value['order'] + layerStartPoint}')).value = TextCellValue(l.value['top_helix']);
    metadataSheet.cell(CellIndex.indexByString('D${l.value['order'] + layerStartPoint}')).value = TextCellValue(l.value['bottom_helix']);
    metadataSheet.cell(CellIndex.indexByString('E${l.value['order'] + layerStartPoint}')).value = IntCellValue(l.value['next_slat_id']);
    metadataSheet.cell(CellIndex.indexByString('F${l.value['order'] + layerStartPoint}')).value = IntCellValue(l.value['slat_count']);
    metadataSheet.cell(CellIndex.indexByString('G${l.value['order'] + layerStartPoint}')).value =
        TextCellValue('#${l.value['color'].value.toRadixString(16).substring(2).toUpperCase()}');
  }

  // ── Metadata: cargo palette section ──
  int cargoStartPoint = layerStartPoint + layerMap.length;
  metadataSheet.merge(
      CellIndex.indexByString('A$cargoStartPoint'), CellIndex.indexByString('G$cargoStartPoint'), customValue: TextCellValue(metaSectionCargoInfo));
  metadataSheet.cell(CellIndex.indexByString('A$cargoStartPoint')).cellStyle = CellStyle(
    horizontalAlign: HorizontalAlign.Center,
  );
  metadataSheet.cell(CellIndex.indexByString('A${cargoStartPoint + 1}')).value = TextCellValue('ID');
  metadataSheet.cell(CellIndex.indexByString('B${cargoStartPoint + 1}')).value = TextCellValue('Short Name');
  metadataSheet.cell(CellIndex.indexByString('C${cargoStartPoint + 1}')).value = TextCellValue('Colour');
  int cIndex = 2;
  for (var c in cargoPalette.entries) {
    metadataSheet.cell(CellIndex.indexByString('A${cargoStartPoint + cIndex}')).value = TextCellValue(c.value.name);
    metadataSheet.cell(CellIndex.indexByString('B${cargoStartPoint + cIndex}')).value = TextCellValue(c.value.shortName);
    metadataSheet.cell(CellIndex.indexByString('C${cargoStartPoint + cIndex}')).value =
        TextCellValue('#${c.value.color.value.toRadixString(16).substring(2).toUpperCase()}');
    cIndex += 1;
  }

  // ── Metadata: unique slat colour overrides section ──
  int colorStartPoint = cargoStartPoint + cIndex;
  metadataSheet.merge(CellIndex.indexByString('A$colorStartPoint'), CellIndex.indexByString('G$colorStartPoint'),
      customValue: TextCellValue(metaSectionSlatColorInfo));
  metadataSheet.cell(CellIndex.indexByString('A$colorStartPoint')).cellStyle = CellStyle(
    horizontalAlign: HorizontalAlign.Center,
  );
  metadataSheet.cell(CellIndex.indexByString('A${colorStartPoint + 1}')).value = TextCellValue('ID');
  metadataSheet.cell(CellIndex.indexByString('B${colorStartPoint + 1}')).value = TextCellValue('Colour');
  int colorIndex = 2;
  for (var s in slats.values.where((slat) => slat.uniqueColor != null)) {
    metadataSheet.cell(CellIndex.indexByString('A${colorStartPoint + colorIndex}')).value = TextCellValue(s.id);
    metadataSheet.cell(CellIndex.indexByString('B${colorStartPoint + colorIndex}')).value =
        TextCellValue('#${s.uniqueColor!.value.toRadixString(16).substring(2).toUpperCase()}');
    colorIndex += 1;
  }

  // ── Slat types sheet: tube/db classification sorted by layer then ID ──
  Sheet slatTypeSheet = excel[slatTypesSheetName];
  slatTypeSheet.cell(CellIndex.indexByString('A1')).value = TextCellValue('Layer');
  slatTypeSheet.cell(CellIndex.indexByString('B1')).value = TextCellValue('Slat ID');
  slatTypeSheet.cell(CellIndex.indexByString('C1')).value = TextCellValue('Type');

  List<List<CellValue>> rows = [];

  for (var slat in slats.values) {
    if (slat.phantomParent != null) {
      continue;
    }
    int layerNum = layerMap[slat.layer]!['order'] + 1;
    int slatIdNum = int.parse(slat.id.split("-I").last);
    rows.add([
      IntCellValue(layerNum),
      IntCellValue(slatIdNum),
      TextCellValue(slat.slatType),
    ]);
  }
  rows.sort((a, b) {
    int layerA = (a[0] as IntCellValue).value;
    int layerB = (b[0] as IntCellValue).value;
    if (layerA != layerB) return layerA.compareTo(layerB);

    int idA = (a[1] as IntCellValue).value;
    int idB = (b[1] as IntCellValue).value;
    return idA.compareTo(idB);
  });

  for (var row in rows) {
    slatTypeSheet.appendRow(row);
  }

  // ── Handle link constraints sheet ──
  writeHandleLinksToExcel(excel, slats, linkManager, layerMap);

  // ── Echo plate and input plate sheets (optional) ──
  final thinBorder = excel_lib.Border(borderStyle: excel_lib.BorderStyle.Thin);
  final echoHeaderStyle = CellStyle(
    backgroundColorHex: '#D9E1F2'.excelColor,
    bold: true,
    horizontalAlign: HorizontalAlign.Center,
    leftBorder: thinBorder,
    rightBorder: thinBorder,
    topBorder: thinBorder,
    bottomBorder: thinBorder,
  );
  final echoDataStyle = CellStyle(
    leftBorder: thinBorder,
    rightBorder: thinBorder,
    topBorder: thinBorder,
    bottomBorder: thinBorder,
    horizontalAlign: HorizontalAlign.Center,
  );

  if (echoPlateLayoutState != null) {
    final grids = echoPlateLayoutState.exportPlateGrids();
    for (var entry in grids.entries) {
      final sheetName = '$echoPlateSheetPrefix${entry.key}_${entry.value.name}';
      Sheet echoSheet = excel[sheetName];
      for (var r = 0; r < entry.value.grid.length; r++) {
        final row = entry.value.grid[r];
        for (var c = 0; c < row.length; c++) {
          final isHeader = r == 0 || c == 0 || r == 10;
          final style = isHeader ? echoHeaderStyle : echoDataStyle;
          setCellValue(echoSheet, c, r, row[c], style: style);
        }
      }
      echoSheet.setColumnWidth(0, 4.0);
      for (var c = 1; c <= 12; c++) {
        echoSheet.setColumnWidth(c, 16.0);
      }
    }
  }

  // ── Input source plates: all plates in a single sheet, separated by title rows ──
  if (plateLibrary != null && plateLibrary.plates.isNotEmpty) {
    Sheet inputSheet = excel[inputPlateSheetName];
    final titleStyle = CellStyle(
      backgroundColorHex: '#4472C4'.excelColor,
      fontColorHex: 'FFFFFF'.excelColor,
      bold: true,
      horizontalAlign: HorizontalAlign.Center,
    );
    int currentRow = 0;
    final colWidths = <int, int>{};

    for (var plate in plateLibrary.plates.entries) {
      // Title row spanning all data columns
      final titleText = '$inputPlateTitlePrefix${plate.key}$inputPlateTitleSuffix';
      setCellValue(inputSheet, 0, currentRow, titleText, style: titleStyle);
      inputSheet.merge(
        CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: currentRow),
        CellIndex.indexByColumnRow(columnIndex: 3, rowIndex: currentRow),
        customValue: TextCellValue(titleText),
      );
      inputSheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: currentRow)).cellStyle = titleStyle;
      currentRow++;

      // Plate data (header + rows)
      final rawData = plate.value.exportToAllDataFormat();
      for (var r = 0; r < rawData.length; r++) {
        final row = rawData[r];
        for (var c = 0; c < row.length; c++) {
          setCellValue(inputSheet, c, currentRow, row[c], style: r == 0 ? echoHeaderStyle : null);
          final cellLen = row[c].toString().length;
          if (cellLen > (colWidths[c] ?? 0)) colWidths[c] = cellLen;
        }
        currentRow++;
      }

      // 3-row gap between plates
      currentRow += 3;
    }

    for (var col in colWidths.entries) {
      final width = min((col.value + 2) * 1.2, 50.0);
      inputSheet.setColumnWidth(col.key, width);
    }
  }

  // ── Lab metadata sheet: export flags + master mix config key-value pairs ──
  if (echoPlateLayoutState != null) {
    final metadata = echoPlateLayoutState.exportLabMetadata();
    Sheet labSheet = excel[labMetadataSheetName];
    setCellValue(labSheet, 0, 0, 'Key', style: echoHeaderStyle);
    setCellValue(labSheet, 1, 0, 'Value', style: echoHeaderStyle);
    int metaRow = 1;
    for (var entry in metadata.entries) {
      setCellValue(labSheet, 0, metaRow, entry.key);
      setCellValue(labSheet, 1, metaRow, entry.value);
      metaRow++;
    }
    labSheet.setColumnWidth(0, 28.0);
    labSheet.setColumnWidth(1, 16.0);
  }

  // ── Clean up default Sheet1 and save ──
  final firstRealSheet = excel.sheets.keys.firstWhere((k) => k != 'Sheet1', orElse: () => 'Sheet1');
  if (firstRealSheet != 'Sheet1') {
    excel.setDefaultSheet(firstRealSheet);
    excel.delete('Sheet1');
  }

  if (kIsWeb) {
    excel.save(fileName: '$suggestedDesignName.xlsx');
  } else {
    String? filePath = await selectSaveLocation('$suggestedDesignName.xlsx');
    if (filePath == null) {
      return;
    }
    List<int>? fileBytes = excel.encode();
    if (fileBytes != null) {
      File(filePath)
        ..createSync(recursive: true)
        ..writeAsBytesSync(fileBytes);
    }
  }
}
