/// Excel import for #-CAD design files.
///
/// Parses a multi-sheet .xlsx workbook into a [ParsedDesignResult] containing
/// slats, layers, cargo, seeds, assembly handles, handle links, echo plates,
/// input plates, and lab metadata. The heavy parsing runs in an isolate via
/// [compute] to keep the UI responsive.
import 'dart:io';
import 'dart:math';
import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:path/path.dart';

import '../../crisscross_core/cargo.dart';
import '../../crisscross_core/common_utilities.dart';
import '../../crisscross_core/seed.dart';
import '../../crisscross_core/slats.dart';
import '../design_state_mixins/design_state_handle_link_mixin.dart';
import '../design_state_mixins/design_state_grouping_mixin.dart';
import 'assembly_handle_io.dart';
import 'design_io_constants.dart';
import 'excel_utilities.dart';
import 'file_picker_helpers.dart';
import 'handle_link_io.dart';
import 'parsed_design_result.dart';

final Random _rand = Random();

/// Builds a [ParsedDesignResult] with [errorCode] set and all data fields
/// empty. Used for early-return error paths — partial data from a failed
/// parse is not useful to the caller.
ParsedDesignResult _errorResult(String errorCode) {
  return ParsedDesignResult(
    slats: {},
    layerMap: {},
    gridMode: '',
    cargoPalette: {},
    seedRoster: {},
    phantomMap: {},
    linkManager: HandleLinkManager(),
    errorCode: errorCode,
  );
}

/// Parses raw Excel [fileBytes] into a complete [ParsedDesignResult].
///
/// Designed to run inside a [compute] isolate — references only pure/stateless
/// modules and must not touch ChangeNotifier or singleton state.
///
/// Returns a result with an empty [ParsedDesignResult.errorCode] on success.
/// On failure, returns partial data up to the point of failure with one of:
///  - `ERR_GENERAL` — missing metadata sheet or unexpected structure
///  - `ERR_SLAT_SHEETS` — malformed or missing slat layer sheets
///  - `ERR_ASSEMBLY_SHEETS` — assembly handle/slat grid mismatch
///  - `ERR_CARGO_SHEETS` — cargo sheet parsing failure
///  - `ERR_SEED_SHEETS` — seed sheet parsing failure
///  - `ERR_LINK_MANAGER: <detail>` — handle link import error
Future<ParsedDesignResult> parseDesignInIsolate(Uint8List fileBytes) async {
  Map<String, Map<String, dynamic>> layerMap = {};
  Map<String, Slat> slats = {};
  Map<String, Map<int, String>> phantomMap = {};
  Map<String, Cargo> cargoPalette = {};
  Map<(String, String, Offset), Seed> seedRoster = {};
  HandleLinkManager linkManager = HandleLinkManager();

  var excel = Excel.decodeBytes(fileBytes);

  // ── Metadata sheet: grid offsets, grid mode, layer count ──
  if (!excel.tables.containsKey(metadataSheetName)) {
    return _errorResult('ERR_GENERAL');
  }

  var metadataSheet = excel.tables[metadataSheetName]!;

  double minX = readExcelDouble(metadataSheet, metaCellMinX);
  double minY = readExcelDouble(metadataSheet, metaCellMinY);

  String gridMode = readExcelString(metadataSheet, metaCellGridMode).trim();

  int numLayers = excel.tables.keys.where((key) => key.startsWith(slatLayerPrefix)).length;

  if (numLayers == 0) {
    return _errorResult('ERR_SLAT_SHEETS');
  }

  // ── Layer map: helix assignments, directions, colours ──
  int layerReadStart = metaLayerStartRow;
  for (int i = 0; i < numLayers; i++) {
    String fullKey = readExcelString(metadataSheet, 'A${i + layerReadStart}');
    layerMap[fullKey.substring('Layer '.length)] = {
      'direction': readExcelInt(metadataSheet, 'B${i + layerReadStart}'),
      'top_helix': readExcelString(metadataSheet, 'C${i + layerReadStart}'),
      'bottom_helix': readExcelString(metadataSheet, 'D${i + layerReadStart}'),
      'next_slat_id': readExcelInt(metadataSheet, 'E${i + layerReadStart}'),
      'order': i,
      'slat_count': 0,
      'color': Color(int.parse('0xFF${readExcelString(metadataSheet, 'G${i + layerReadStart}').substring(1)}')),
      "hidden": false
    };
  }
  // ── Cargo palette: name, short name, colour per cargo type ──
  int cargoReadStart = layerReadStart + numLayers + 2;
  int cargoCount = 0;

  for (;; cargoCount++) {
    String cargoName = readExcelString(metadataSheet, 'A${cargoReadStart + cargoCount}').trim();
    if (cargoName.isEmpty || cargoName == metaSectionSlatColorInfo) break;
    String cargoShortName = readExcelString(metadataSheet, 'B${cargoReadStart + cargoCount}');
    Color cargoColor = Color(int.parse('0xFF${readExcelString(metadataSheet, 'C${cargoReadStart + cargoCount}').substring(1)}'));
    cargoPalette[cargoName] = Cargo(name: cargoName, shortName: cargoShortName, color: cargoColor);
  }
  // ── Per-slat unique colours (optional overrides) ──
  int colorReadStart = cargoReadStart + cargoCount + 2;
  int colorCount = 0;
  Map<String, Color> slatColors = {};

  for (;; colorCount++) {
    String slatID = readExcelString(metadataSheet, 'A${colorReadStart + colorCount}').trim();
    if (slatID.isEmpty || slatID == metaSectionGroupColorInfo) break;
    Color slatColor = Color(int.parse('0xFF${readExcelString(metadataSheet, 'B${colorReadStart + colorCount}').substring(1)}'));
    slatColors[slatID] = slatColor;
  }

  // ── Group colours (optional): config name + group name + colour per group ──
  // Stored as a map of (configName, groupName) -> Color for later application
  Map<(String, String), Color> groupColorOverrides = {};
  int groupColorReadStart = colorReadStart + colorCount;
  String groupColorMarker = readExcelString(metadataSheet, 'A$groupColorReadStart').trim();
  if (groupColorMarker == metaSectionGroupColorInfo) {
    int gOffset = 2; // skip header row
    for (;; gOffset++) {
      String configName = readExcelString(metadataSheet, 'A${groupColorReadStart + gOffset}').trim();
      if (configName.isEmpty) break;
      String groupName = readExcelString(metadataSheet, 'B${groupColorReadStart + gOffset}').trim();
      String colorHex = readExcelString(metadataSheet, 'C${groupColorReadStart + gOffset}').trim();
      if (groupName.isNotEmpty && colorHex.isNotEmpty) {
        groupColorOverrides[(configName, groupName)] = Color(int.parse('0xFF${colorHex.substring(1)}'));
      }
    }
  }

  // ── Slat types: tube vs double-barrel per (layer, slatID) + group configurations ──
  Map<(int, int), String> slatTypeMap = {};
  Map<String, GroupConfiguration> importedGroupConfigs = {};

  try {
    if (excel.tables.containsKey(slatTypesSheetName)) {
      var slatTypeSheet = excel.tables[slatTypesSheetName]!;
      if (slatTypeSheet.rows.isNotEmpty) {
        List<String> headers = slatTypeSheet.rows.first.map((cell) => cell?.value.toString() ?? "").toList();

        int layerIndex = headers.indexOf("Layer");
        int slatIdIndex = headers.indexOf("Slat ID");
        int typeIndex = headers.indexOf("Type");

        if (layerIndex == -1 || slatIdIndex == -1 || typeIndex == -1) {
          throw Exception("Missing required columns in slat_types sheet");
        }

        // Identify group configuration columns (anything after Layer, Slat ID, Type)
        List<int> groupColIndices = [];
        List<String> groupConfigNames = [];
        for (int ci = 0; ci < headers.length; ci++) {
          if (ci != layerIndex && ci != slatIdIndex && ci != typeIndex && headers[ci].isNotEmpty) {
            groupColIndices.add(ci);
            groupConfigNames.add(headers[ci]);
          }
        }

        // Temporary storage: configIndex -> Map<groupName, List<(layer, slatId)>>
        List<Map<String, List<(int, int)>>> configGroupMembers = List.generate(groupColIndices.length, (_) => {});

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

              // Read group assignments for each configuration
              for (int gi = 0; gi < groupColIndices.length; gi++) {
                int colIdx = groupColIndices[gi];
                if (colIdx < row.length) {
                  var groupName = row[colIdx]?.value?.toString();
                  if (groupName != null && groupName.isNotEmpty) {
                    configGroupMembers[gi].putIfAbsent(groupName, () => []);
                    configGroupMembers[gi][groupName]!.add((layer, slatId));
                  }
                }
              }
            }
          }
        }

        // Build GroupConfiguration objects using layer order -> layer key lookup
        List<String> defaultPalette = [
          '#ebac23', '#b80058', '#008cf9', '#006e00', '#00bbad', '#d163e6',
          '#b24602', '#ff9287', '#5954d6', '#00c6f8', '#878500', '#00a76c', '#bdbdbd'
        ];
        // Map layer order (1-based from file) to layer key
        Map<int, String> orderToLayerKey = {};
        for (var entry in layerMap.entries) {
          orderToLayerKey[(entry.value['order'] as int) + 1] = entry.key;
        }

        for (int gi = 0; gi < groupConfigNames.length; gi++) {
          if (configGroupMembers[gi].isEmpty) continue;
          String configId = 'C${gi + 1}';
          var config = GroupConfiguration(id: configId, name: groupConfigNames[gi]);
          int groupNum = 1;
          for (var entry in configGroupMembers[gi].entries) {
            String groupId = 'G$groupNum';
            // Use saved colour if available, otherwise fall back to default palette
            Color groupColor = groupColorOverrides[(groupConfigNames[gi], entry.key)] ??
                Color(int.parse('0xFF${defaultPalette[((groupNum - 1) % defaultPalette.length)].replaceFirst('#', '')}'));
            var group = SlatGroup(
              id: groupId,
              name: entry.key,
              color: groupColor,
            );
            for (var (layer, slatId) in entry.value) {
              String? layerKey = orderToLayerKey[layer];
              if (layerKey == null) continue;
              String slatKey = '$layerKey-I$slatId';
              group.slatIds.add(slatKey);
              config.slatToGroup[slatKey] = groupId;
            }
            config.groups[groupId] = group;
            groupNum++;
          }
          config.nextGroupNumber = groupNum;
          importedGroupConfigs[configId] = config;
        }
      }
    }
  } catch (_) {
    return _errorResult('ERR_GENERAL');
  }

  // ── Slat grid: allocate 3D array [row][col][layer] from first sheet dimensions ──
  List<List<List<int>>> slatArray;
  try {
    var firstSlatSheet = excel.tables[slatLayerSheetName(0)]!;
    slatArray = List.generate(
        firstSlatSheet.maxRows, (_) => List.generate(firstSlatSheet.maxColumns, (_) => List.filled(numLayers, 0)));
  } catch (_) {
    return _errorResult('ERR_SLAT_SHEETS');
  }

  // ── Slat layer sheets: parse cell values into slat + phantom coordinate maps ──
  try {
    for (var table in excel.tables.keys.where((key) => key.startsWith(slatLayerPrefix))) {
      var layerIndex = int.parse(table.split('_').last) - 1;
      String layer = layerMap.entries.firstWhere((element) => element.value['order'] == layerIndex).key;

      Map<int, Map<int, Offset>> slatCoordinates = {};
      Map<int, Map<int, Map<int, Offset>>> phantomCoordinates = {};

      var sheet = excel.tables[table]!;
      for (var row = 0; row < sheet.maxRows; row++) {
        for (var col = 0; col < sheet.maxColumns; col++) {
          var cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
          Offset coord = Offset(col + minX, row + minY);

          if (cell is TextCellValue) {
            String value = (cell.value.text ?? '').trim();
            if (value.isEmpty || value == '0') continue;

            final parts = value.split('-');
            if (value.contains('_')) {
              // Phantom format: P{phantomID}_{parentID}-{position}
              final idParts = parts[0].split('_');
              int phantomID = int.parse(idParts[0].substring(1));
              int slatID = int.parse(idParts[1]);
              phantomCoordinates.putIfAbsent(slatID, () => {});
              phantomCoordinates[slatID]!.putIfAbsent(phantomID, () => {});
              phantomCoordinates[slatID]![phantomID]![int.parse(parts[1])] = coord;
            } else {
              // Standard format: {slatID}-{position}
              int slatID = int.parse(parts[0]);
              slatCoordinates.putIfAbsent(slatID, () => {});
              slatCoordinates[slatID]![int.parse(parts[1])] = coord;
              slatArray[row][col][layerIndex] = slatID;
            }
          } else if (cell is IntCellValue && cell.value != 0) {
            // Legacy format: bare integer ID, position inferred from order
            int slatID = cell.value;
            slatCoordinates.putIfAbsent(slatID, () => {});
            slatCoordinates[slatID]![slatCoordinates[slatID]!.length + 1] = coord;
            slatArray[row][col][layerIndex] = slatID;
          }
        }
      }

      for (var slatBundle in slatCoordinates.entries) {
        var category = 'tube';
        if (slatTypeMap.containsKey((layerIndex + 1, slatBundle.key))) {
          category = slatTypeMap[(layerIndex + 1, slatBundle.key)]!;
        }
        slats["$layer-I${slatBundle.key}"] = Slat(slatBundle.key, "$layer-I${slatBundle.key}", layer, slatBundle.value, slatType: category);
      }
      layerMap[layer]!['slat_count'] = slatCoordinates.length;

      for (var refSlatPhantoms in phantomCoordinates.entries) {
        for (var phantomSlatBundle in refSlatPhantoms.value.entries) {
          String phantomName = "$layer-I${refSlatPhantoms.key}-P${phantomSlatBundle.key}";
          String refSlatName = "$layer-I${refSlatPhantoms.key}";
          String category = slats[refSlatName]!.slatType;
          phantomMap.putIfAbsent(refSlatName, () => {});
          phantomMap[refSlatName]![phantomSlatBundle.key] = phantomName;
          slats[phantomName] =
              Slat(phantomSlatBundle.key, phantomName, layer, phantomSlatBundle.value, slatType: category, phantomParent: refSlatName);
        }
      }
    }
  } catch (_) {
    return _errorResult('ERR_SLAT_SHEETS');
  }

  // ── Apply unique slat colours (propagate to phantoms) ──
  for (var slat in slats.values) {
    if (slatColors.containsKey(slat.id)) {
      slat.setColor(slatColors[slat.id]!);

      if (phantomMap.containsKey(slat.id)) {
        for (var phantomID in phantomMap[slat.id]!.values) {
          slats[phantomID]?.setColor(slatColors[slat.id]!);
        }
      }
    }
  }

  // ── Assembly handles: bridge adjacent layers via handle_interface sheets ──
  final okHandles = extractAssemblyHandlesFromExcel(excel, slatArray, slats, layerMap, minX, minY, false);
  if (!okHandles) {
    return _errorResult('ERR_ASSEMBLY_SHEETS');
  }

  // ── Cargo handles: assign cargo values to slat positions ──
  try {
    for (var table in excel.tables.keys.where((key) => key.startsWith(cargoLayerPrefix))) {
      int cargoLayerIndex = int.parse(table.split('_')[2]) - 1;
      int cargoLayerSide = parseHelixSide(table.split('_')[4]);
      var sheet = excel.tables[table]!;

      String layerID = layerMap.entries.firstWhere((element) => element.value['order'] == cargoLayerIndex).key;

      for (var row = 0; row < sheet.maxRows; row++) {
        for (var col = 0; col < sheet.maxColumns; col++) {
          var cellValue = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
          String value = (cellValue is TextCellValue) ? cellValue.value.text ?? '' : '';
          if (value == '0' || value == '') {
            continue;
          }

          if (!cargoPalette.containsKey(value)) {
            cargoPalette[value] =
                Cargo(name: value, shortName: generateShortName(value), color: qualitativeCargoColors[_rand.nextInt(qualitativeCargoColors.length)]);
          }

          String slatID = "$layerID-I${slatArray[row][col][cargoLayerIndex]}";
          Offset positionCoord = Offset(col + minX, row + minY);

          slats[slatID]?.setPlaceholderHandle(slats[slatID]!.slatCoordinateToPosition[positionCoord]!, cargoLayerSide, value, categoryCargo);
        }
      }
    }
  } catch (_) {
    return _errorResult('ERR_CARGO_SHEETS');
  }

  if (!cargoPalette.containsKey('SEED')) {
    cargoPalette['SEED'] = Cargo(name: 'SEED', shortName: 'S1', color: Color.fromARGB(255, 255, 0, 0));
  }

  // ── Seed positions: collect per-seed coordinate maps across seed sheets ──
  Map<(String, String, String), Map<int, Offset>> partialSeedArrays = {};

  try {
    for (var table in excel.tables.keys.where((key) => key.startsWith(seedLayerPrefix))) {
      int seedLayerIndex = int.parse(table.split('_')[2]) - 1;
      int seedLayerSide = parseHelixSide(table.split('_')[4]);
      String sideString = positionalToSide(table.split('_')[3]);

      var sheet = excel.tables[table]!;

      String layerID = layerMap.entries.firstWhere((element) => element.value['order'] == seedLayerIndex).key;

      for (var row = 0; row < sheet.maxRows; row++) {
        for (var col = 0; col < sheet.maxColumns; col++) {
          var cellValue = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row)).value;
          String value = (cellValue is TextCellValue) ? cellValue.value.text ?? '' : '';
          if (value == '0' || value == '') {
            continue;
          }

          String slatID = "$layerID-I${slatArray[row][col][seedLayerIndex]}";
          Offset positionCoord = Offset(col + minX, row + minY);

          slats[slatID]?.setPlaceholderHandle(slats[slatID]!.slatCoordinateToPosition[positionCoord]!, seedLayerSide, value, 'Seed');

          partialSeedArrays.putIfAbsent((value.split('-')[0], layerID, sideString), () => {});

          partialSeedArrays[(value.split('-')[0], layerID, sideString)]![getIndexFromSeedText(value)] = positionCoord;
        }
      }
    }
  } catch (_) {
    return _errorResult('ERR_SEED_SHEETS');
  }

  // ── Validate and register complete seeds (must have 80 positions, pass geometry check) ──
  for (var partialSeed in partialSeedArrays.entries) {
    Map<int, Offset> seedCoordinates = partialSeed.value;
    String seedID = partialSeed.key.$1;
    String layerID = partialSeed.key.$2;
    String sideString = partialSeed.key.$3;

    if (seedCoordinates.length != 80) {
      continue;
    }

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

    if (hasPhantom || attachmentSlats.length < 16) {
      continue;
    }

    List<(Offset, int, int)> handles = [];
    for (var entry in seedCoordinates.entries) {
      int index = entry.key;
      int row = (index - 1) ~/ 16 + 1;
      int col = (index - 1) % 16 + 1;
      handles.add((entry.value, row, col));
    }

    if (!validateSeedGeometry(handles)) {
      continue;
    }

    seedRoster[(layerID, sideString, seedCoordinates[1]!)] = Seed(ID: seedID, coordinates: seedCoordinates);
  }

  // ── Phantom slats inherit handles from their parent ──
  for (var slat in slats.values.where((slat) => slat.phantomParent != null)) {
    slat.copyHandlesFromSlat(slats[slat.phantomParent!]!);
  }

  // ── Handle link constraints (linked groups, enforced values) ──
  try {
    String? linkError = extractHandleLinksFromExcel(excel, slats, layerMap, linkManager);
    if (linkError != null) {
      return _errorResult('ERR_LINK_MANAGER: $linkError');
    }
  } catch (e) {
    return _errorResult('ERR_LINK_MANAGER: ${e.toString()}');
  }

  // ── Apply blocked handles as placeholder value='0' on the slats themselves ──
  for (var blockedKey in linkManager.handleBlocks) {
    var slat = slats[blockedKey.$1];
    if (slat != null) {
      String category = blockedKey.$3 == 5 ? categoryAssemblyHandle : categoryAssemblyAntihandle;
      slat.setPlaceholderHandle(blockedKey.$2, blockedKey.$3, '0', category);
    }
  }

  // ── Echo plate, input plate, and lab metadata sheets (optional) ──
  Map<String, List<List<dynamic>>>? echoPlateData;
  final echoSheetNames = excel.tables.keys.where((key) => key.startsWith(echoPlateSheetPrefix)).toList()..sort();
  if (echoSheetNames.isNotEmpty) {
    echoPlateData = {for (var name in echoSheetNames) name: extractSheetRows(excel.tables[name]!)};
  }

  Map<String, String>? labMetadata;
  if (excel.tables.containsKey(labMetadataSheetName)) {
    labMetadata = {};
    final rows = extractSheetRows(excel.tables[labMetadataSheetName]!);
    for (var i = 1; i < rows.length; i++) {
      final row = rows[i];
      if (row.length >= 2 && row[0] != null && row[1] != null) {
        labMetadata[row[0].toString()] = row[1].toString();
      }
    }
  }

  Map<String, List<List<dynamic>>>? inputPlateData;
  if (excel.tables.containsKey(inputPlateSheetName)) {
    inputPlateData = {};
    final rows = extractSheetRows(excel.tables[inputPlateSheetName]!);
    String? currentPlate;
    List<List<dynamic>>? currentRows;

    for (final row in rows) {
      final firstCell = row.isNotEmpty ? row[0].toString() : '';
      if (firstCell.startsWith(inputPlateTitlePrefix) && firstCell.endsWith(inputPlateTitleSuffix)) {
        if (currentPlate != null && currentRows != null && currentRows.isNotEmpty) {
          inputPlateData[currentPlate] = currentRows;
        }
        currentPlate = firstCell.substring(inputPlateTitlePrefix.length, firstCell.length - inputPlateTitleSuffix.length);
        currentRows = [];
      } else if (currentPlate != null && row.any((cell) => cell != null && cell.toString().isNotEmpty)) {
        currentRows!.add(row);
      }
    }
    if (currentPlate != null && currentRows != null && currentRows.isNotEmpty) {
      inputPlateData[currentPlate] = currentRows;
    }
    if (inputPlateData.isEmpty) inputPlateData = null;
  }

  return ParsedDesignResult(
    slats: slats,
    layerMap: layerMap,
    gridMode: gridMode,
    cargoPalette: cargoPalette,
    seedRoster: seedRoster,
    phantomMap: phantomMap,
    linkManager: linkManager,
    errorCode: '',
    echoPlateData: echoPlateData,
    inputPlateData: inputPlateData,
    labMetadata: labMetadata,
    groupConfigurations: importedGroupConfigs,
  );
}

/// Prompts the user to select a .xlsx design file (or accepts pre-loaded bytes)
/// and parses it in an isolate.
///
/// Returns a tuple of ([ParsedDesignResult], design name). If the user cancels
/// the file picker, returns an empty result with an empty name. If parsing
/// fails, the result carries an appropriate error code.
///
/// When [inputFileBytes] and [inputFileName] are both provided (e.g. from
/// drag-and-drop), the file picker is skipped.
Future<(ParsedDesignResult, String)> importDesign({String? inputFileName, Uint8List? inputFileBytes}) async {
  ParsedDesignResult emptyResult({String errorCode = ''}) => _errorResult(errorCode);

  String filePath;
  Uint8List fileBytes;
  String fileName;

  // ── Resolve file bytes: use provided bytes or open a file picker ──
  if (inputFileBytes != null && inputFileName != null) {
    fileName = basenameWithoutExtension(inputFileName);
    fileBytes = inputFileBytes;
  } else {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx'],
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
      fileName = basenameWithoutExtension(result.files.first.name);
    } else {
      return (emptyResult(), '');
    }
  }
  // ── Parse in isolate to keep UI responsive ──
  try {
    final result = await compute(parseDesignInIsolate, fileBytes);
    return (result, fileName);
  } catch (_) {
    return (emptyResult(errorCode: 'ERR_GENERAL'), '');
  }
}
