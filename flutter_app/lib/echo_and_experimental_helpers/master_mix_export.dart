import 'dart:typed_data';

import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:excel/excel.dart' as excel_lib show Border, BorderStyle;

import '../crisscross_core/slats.dart';
import 'echo_plate_constants.dart';
import 'master_mix_config.dart';
import 'plate_layout_state.dart';

class _WellEntry {
  final String slatId;
  final Slat slat;
  final WellConfig config;
  final int plateIndex;
  final String well;
  final double totalHandleVolumeNl;
  final double minHandleConcNm;

  _WellEntry({
    required this.slatId,
    required this.slat,
    required this.config,
    required this.plateIndex,
    required this.well,
    required this.totalHandleVolumeNl,
    required this.minHandleConcNm,
  });
}

class _GroupKey {
  final double ratio;
  final double volume;
  final double scaffoldConc;

  _GroupKey(this.ratio, this.volume, this.scaffoldConc);

  @override
  bool operator ==(Object other) =>
      other is _GroupKey && ratio == other.ratio && volume == other.volume && scaffoldConc == other.scaffoldConc;

  @override
  int get hashCode => Object.hash(ratio, volume, scaffoldConc);
}

// ---------------------------------------------------------------------------
// Shared styles
// ---------------------------------------------------------------------------

final _thin = excel_lib.Border(borderStyle: excel_lib.BorderStyle.Thin);

CellStyle _bordered({bool bold = false, String? bg}) {
  final color = bg?.excelColor;
  return CellStyle(
    bold: bold,
    backgroundColorHex: color ?? '#FFFFFF'.excelColor,
    leftBorder: _thin,
    rightBorder: _thin,
    topBorder: _thin,
    bottomBorder: _thin,
  );
}

final _bNormal = _bordered();
final _bBold = _bordered(bold: true);
final _bOrange = _bordered(bg: '#FFF2CC');
final _bOrangeBold = _bordered(bold: true, bg: '#FFF2CC');
final _bRed = _bordered(bg: '#FCE4EC');
final _bHeader = _bordered(bold: true, bg: '#D9E1F2');
final _headerNoBorder = CellStyle(bold: true, backgroundColorHex: '#D9E1F2'.excelColor);

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Generates a master mix Excel workbook (.xlsx bytes) with folding recipes and slat grouping.
Uint8List generateMasterMixExcel({
  required Map<int, Map<String, String?>> plateAssignments,
  required Map<int, Map<String, WellConfig>> wellConfigs,
  required Map<int, String> plateNames,
  required Map<String, Slat> slats,
  required Map<String, Map<String, dynamic>> layerMap,
  required MasterMixConfig mixConfig,
  String experimentTitle = 'Experiment',
}) {
  // Step 1: Build per-well entries
  final entries = <_WellEntry>[];
  for (var plateIndex in plateAssignments.keys.toList()..sort()) {
    final plate = plateAssignments[plateIndex]!;
    final plateConfigs = wellConfigs[plateIndex] ?? {};
    for (var well in plate.keys) {
      final slatId = plate[well];
      if (slatId == null) continue;
      final base = baseSlatId(slatId);
      final slat = slats[base];
      if (slat == null) continue;
      final config = plateConfigs[well] ?? const WellConfig();

      double totalVol = 0;
      double? minProduct;
      for (var handles in [slat.h2Handles, slat.h5Handles]) {
        for (var handle in handles.values) {
          final conc = (handle['concentration'] as num?)?.toDouble();
          if (conc == null || conc <= 0) continue;
          final roundedNl = echoRoundedVolumeNl(config.materialPerHandle, conc).toDouble();
          totalVol += roundedNl;
          final product = roundedNl * conc;
          if (minProduct == null || product < minProduct) minProduct = product;
        }
      }

      final minConc = (totalVol > 0 && minProduct != null) ? minProduct * 1000 / totalVol : 0.0;
      entries.add(_WellEntry(
        slatId: slatId, slat: slat, config: config, plateIndex: plateIndex,
        well: well, totalHandleVolumeNl: totalVol, minHandleConcNm: minConc,
      ));
    }
  }

  if (entries.isEmpty) {
    final excel = Excel.createExcel();
    return Uint8List.fromList(excel.save()!);
  }

  // Step 2: Group by WellConfig triple
  final groups = <_GroupKey, List<_WellEntry>>{};
  for (var e in entries) {
    final key = _GroupKey(e.config.ratio, e.config.volume, e.config.scaffoldConc);
    groups.putIfAbsent(key, () => []).add(e);
  }

  final sortedGroupKeys = groups.keys.toList();
  final useLabels = sortedGroupKeys.length > 1;
  final groupLabels = <_GroupKey, String>{};
  for (var i = 0; i < sortedGroupKeys.length; i++) {
    groupLabels[sortedGroupKeys[i]] = useLabels ? 'Group ${String.fromCharCode(65 + i)}' : '';
  }

  final excel = Excel.createExcel();
  final mmSheet = excel['Slat Folding & Master Mix'];
  if (excel.sheets.containsKey('Sheet1')) excel.delete('Sheet1');

  int row = 0;

  for (var gi = 0; gi < sortedGroupKeys.length; gi++) {
    final gKey = sortedGroupKeys[gi];
    final groupEntries = groups[gKey]!;
    final label = groupLabels[gKey]!;
    final config = groupEntries.first.config;
    final slatCount = groupEntries.length;

    final minConcInGroup = groupEntries.map((e) => e.minHandleConcNm).reduce((a, b) => a < b ? a : b);
    final maxConcInGroup = groupEntries.map((e) => e.minHandleConcNm).reduce((a, b) => a > b ? a : b);
    final concVaries = (maxConcInGroup - minConcInGroup).abs() > 0.01;

    final isDoubleBarrel = mixConfig.coreStaplesMode == CoreStaplesMode.doubleBarrel;

    // =====================================================================
    // Table 1: Single Slat Folding
    // =====================================================================
    final headerText =
        useLabels ? '$label ($slatCount slats): Single Slat Folding' : 'Single Slat Folding ($slatCount slats)';
    _setCell(mmSheet, 0, row, headerText, style: _bHeader);
    _setCell(mmSheet, 1, row, '', style: _bHeader);
    _setCell(mmSheet, 2, row, '', style: _bHeader);
    _setCell(mmSheet, 3, row, '', style: _bHeader);
    row++;

    _setCell(mmSheet, 0, row, 'Component', style: _bBold);
    _setCell(mmSheet, 1, row, 'Stock Conc.', style: _bBold);
    _setCell(mmSheet, 2, row, 'Final Conc.', style: _bBold);
    _setCell(mmSheet, 3, row, 'Amount (\u00B5L)', style: _bBold);
    row++;

    // Handles
    final handlesRow = row;
    _setCell(mmSheet, 0, row, 'H2/H5 Handles (nM)', style: _bNormal);
    _setCell(mmSheet, 1, row, minConcInGroup, style: _bOrange);
    row++;

    // Scaffold
    final scaffoldRow = row;
    _setCell(mmSheet, 0, row, 'P8064 Scaffold (nM)', style: _bNormal);
    _setCell(mmSheet, 1, row, mixConfig.scaffoldStockConc, style: _bRed);
    _setCell(mmSheet, 2, row, config.scaffoldConc, style: _bNormal);
    row++;

    // Handle final conc formula: =C{scaffoldRow}*{handleRatio}
    final sR = scaffoldRow + 1;
    _setFormula(mmSheet, 2, handlesRow, 'C$sR*${config.ratio}', style: _bNormal);

    // Core Staples — standard or double barrel
    final coreStartRow = row;
    if (isDoubleBarrel) {
      for (var i = 0; i < 4; i++) {
        _setCell(mmSheet, 0, row, 'Core Staples ${i + 1} (nM)', style: _bNormal);
        _setCell(mmSheet, 1, row, mixConfig.coreStaplesGroupConcs[i], style: _bNormal);
        _setFormula(mmSheet, 2, row, 'C$sR*${mixConfig.coreStaplesRatio}', style: _bNormal);
        row++;
      }
      // DB-L
      _setCell(mmSheet, 0, row, 'DB-L (nM)', style: _bNormal);
      _setCell(mmSheet, 1, row, mixConfig.dbLStockConc, style: _bNormal);
      _setFormula(mmSheet, 2, row, 'C$sR*${mixConfig.coreStaplesRatio}', style: _bNormal);
      row++;
      // DB-R
      _setCell(mmSheet, 0, row, 'DB-R (nM)', style: _bNormal);
      _setCell(mmSheet, 1, row, mixConfig.dbRStockConc, style: _bNormal);
      _setFormula(mmSheet, 2, row, 'C$sR*${mixConfig.coreStaplesRatio}', style: _bNormal);
      row++;
    } else {
      _setCell(mmSheet, 0, row, 'Core Staples (nM)', style: _bNormal);
      _setCell(mmSheet, 1, row, mixConfig.coreStaplesStockConc, style: _bNormal);
      _setFormula(mmSheet, 2, row, 'C$sR*${mixConfig.coreStaplesRatio}', style: _bNormal);
      row++;
    }
    final coreEndRow = row - 1;

    // TEF
    final tefRow = row;
    _setCell(mmSheet, 0, row, 'TEF (X)', style: _bNormal);
    _setCell(mmSheet, 1, row, mixConfig.tefStock, style: _bNormal);
    _setCell(mmSheet, 2, row, mixConfig.tefFinal, style: _bNormal);
    row++;

    // MgCl2
    final mgcl2Row = row;
    _setCell(mmSheet, 0, row, 'MgCl\u2082 (mM)', style: _bNormal);
    _setCell(mmSheet, 1, row, mixConfig.mgcl2Stock, style: _bNormal);
    _setCell(mmSheet, 2, row, mixConfig.mgcl2Final, style: _bNormal);
    row++;

    // UPW
    final upwRow = row;
    _setCell(mmSheet, 0, row, 'UPW', style: _bNormal);
    _setCell(mmSheet, 1, row, '', style: _bNormal);
    _setCell(mmSheet, 2, row, '', style: _bNormal);
    row++;

    // Total Volume
    final totalRow = row;
    _setCell(mmSheet, 0, row, 'Total Volume (\u00B5L)', style: _bBold);
    _setCell(mmSheet, 1, row, '', style: _bNormal);
    _setCell(mmSheet, 2, row, '', style: _bNormal);
    _setCell(mmSheet, 3, row, config.volume, style: _bBold);
    row++;

    // Total Amount (pmol)
    _setCell(mmSheet, 0, row, 'Total Amount (pmol)', style: _bNormal);
    _setCell(mmSheet, 1, row, '', style: _bNormal);
    _setCell(mmSheet, 2, row, '', style: _bNormal);
    row++;

    // Excel row refs (1-indexed)
    final hR = handlesRow + 1;
    final totalExcelRow = totalRow + 1;
    final tR = tefRow + 1;
    final mR = mgcl2Row + 1;
    final uR = upwRow + 1;

    // Amount formulas
    _setFormula(mmSheet, 3, handlesRow, 'C$hR*D$totalExcelRow/B$hR', style: _bNormal);
    _setFormula(mmSheet, 3, scaffoldRow, 'C$sR*D$totalExcelRow/B$sR', style: _bNormal);

    // Core staples amounts
    for (var r = coreStartRow; r <= coreEndRow; r++) {
      final eR = r + 1;
      _setFormula(mmSheet, 3, r, 'C$eR*D$totalExcelRow/B$eR', style: _bNormal);
    }

    _setFormula(mmSheet, 3, tefRow, 'C$tR*D$totalExcelRow/B$tR', style: _bNormal);
    _setFormula(mmSheet, 3, mgcl2Row, 'C$mR*D$totalExcelRow/B$mR', style: _bNormal);
    // UPW = total - sum of everything above
    _setFormula(mmSheet, 3, upwRow, 'D$totalExcelRow-SUM(D$hR:D$mR)', style: _bNormal);
    // Total Amount = total volume * scaffold final conc / 1000
    _setFormula(mmSheet, 3, totalRow + 1, 'D$totalExcelRow*C$sR/1000', style: _bNormal);

    // Concentration warning (outside border)
    if (concVaries) {
      row++;
      _setCell(mmSheet, 0, row, 'Note: Handle concentrations vary in this group', style: _bOrangeBold);
      _setCell(mmSheet, 1, row, '', style: _bOrange);
      _setCell(mmSheet, 2, row, '', style: _bOrange);
      _setCell(mmSheet, 3, row, '', style: _bOrange);
      row++;
      _setCell(mmSheet, 0, row, 'Min: ${minConcInGroup.toStringAsFixed(1)} nM', style: _bOrange);
      _setCell(mmSheet, 1, row, 'Max: ${maxConcInGroup.toStringAsFixed(1)} nM', style: _bOrange);
      row++;
    }

    row++; // blank spacer

    // =====================================================================
    // Table 2: Master Mix Prep
    // =====================================================================
    _setCell(mmSheet, 0, row, 'Master Mix Prep', style: _bHeader);
    _setCell(mmSheet, 1, row, 'Count / Volume (\u00B5L)', style: _bHeader);
    _setCell(mmSheet, 2, row, '', style: _bHeader);
    _setCell(mmSheet, 3, row, '', style: _bHeader);
    row++;

    final countRow = row;
    final countExcelRow = countRow + 1;
    _setCell(mmSheet, 0, row, 'Number of slats (+${mixConfig.bufferSlats} buffer)', style: _bNormal);
    _setCell(mmSheet, 1, row, slatCount + mixConfig.bufferSlats, style: _bBold);
    row++;

    final mmScaffoldRow = row;
    _setCell(mmSheet, 0, row, 'P8064 Scaffold', style: _bNormal);
    _setFormula(mmSheet, 1, row, 'D$sR*B$countExcelRow', style: _bNormal);
    row++;

    // Core staples master mix rows
    for (var r = coreStartRow; r <= coreEndRow; r++) {
      final label_ = _getCellText(mmSheet, 0, r).replaceAll(' (nM)', '');
      _setCell(mmSheet, 0, row, label_, style: _bNormal);
      _setFormula(mmSheet, 1, row, 'D${r + 1}*B$countExcelRow', style: _bNormal);
      row++;
    }

    _setCell(mmSheet, 0, row, 'TEF', style: _bNormal);
    _setFormula(mmSheet, 1, row, 'D$tR*B$countExcelRow', style: _bNormal);
    row++;

    _setCell(mmSheet, 0, row, 'MgCl\u2082', style: _bNormal);
    _setFormula(mmSheet, 1, row, 'D$mR*B$countExcelRow', style: _bNormal);
    row++;

    final mmUpwRow = row;
    _setCell(mmSheet, 0, row, 'UPW', style: _bNormal);
    _setFormula(mmSheet, 1, row, 'D$uR*B$countExcelRow', style: _bNormal);
    row++;

    final mmTotalRow = row;
    final mmScaffoldExcelRow = mmScaffoldRow + 1;
    final mmTotalExcelRow = mmTotalRow + 1;
    _setCell(mmSheet, 0, row, 'Total Volume', style: _bBold);
    _setFormula(mmSheet, 1, row, 'SUM(B$mmScaffoldExcelRow:B${mmUpwRow + 1})', style: _bBold);
    row++;

    row++; // blank spacer

    // =====================================================================
    // Table 3: Final Slat Mixture (per slat)
    // =====================================================================
    _setCell(mmSheet, 0, row, 'Final Slat Mixture (per slat)', style: _bHeader);
    _setCell(mmSheet, 1, row, 'Volume (\u00B5L)', style: _bHeader);
    _setCell(mmSheet, 2, row, '', style: _bHeader);
    _setCell(mmSheet, 3, row, '', style: _bHeader);
    row++;

    final fmMmRow = row;
    _setCell(mmSheet, 0, row, 'Master Mix', style: _bNormal);
    _setFormula(mmSheet, 1, row, 'B$mmTotalExcelRow/B$countExcelRow', style: _bNormal);
    row++;

    final fmHandlesRow = row;
    _setCell(mmSheet, 0, row, 'Slat Handle Mixture', style: _bNormal);
    _setFormula(mmSheet, 1, row, 'D$hR', style: _bNormal);
    row++;

    _setCell(mmSheet, 0, row, 'Total Volume', style: _bBold);
    _setFormula(mmSheet, 1, row, 'B${fmMmRow + 1}+B${fmHandlesRow + 1}', style: _bBold);
    row++;

    // Spacing between groups
    if (gi < sortedGroupKeys.length - 1) {
      row += 2;
    }
  }

  // Set column widths
  mmSheet.setColumnWidth(0, 32.0);
  mmSheet.setColumnWidth(1, 16.0);
  mmSheet.setColumnWidth(2, 14.0);
  mmSheet.setColumnWidth(3, 14.0);

  // --- Sheet 2: Slat Groups ---
  final groupSheet = excel['Slat Groups'];

  _setCell(groupSheet, 0, 0, 'Group', style: _headerNoBorder);
  _setCell(groupSheet, 1, 0, 'Slat ID', style: _headerNoBorder);
  _setCell(groupSheet, 2, 0, 'Display Name', style: _headerNoBorder);
  _setCell(groupSheet, 3, 0, 'Well', style: _headerNoBorder);
  _setCell(groupSheet, 4, 0, 'Plate', style: _headerNoBorder);

  int gRow = 1;
  for (var gKey in sortedGroupKeys) {
    final label = groupLabels[gKey]!;
    final groupEntries = groups[gKey]!;
    for (var e in groupEntries) {
      _setCell(groupSheet, 0, gRow, label);
      _setCell(groupSheet, 1, gRow, baseSlatId(e.slatId));
      _setCell(groupSheet, 2, gRow, slatDisplayName(e.slat, layerMap));
      _setCell(groupSheet, 3, gRow, e.well);
      _setCell(groupSheet, 4, gRow, plateNames[e.plateIndex] ?? 'Plate');
      gRow++;
    }
  }

  return Uint8List.fromList(excel.save()!);
}

// ---------------------------------------------------------------------------
// Cell helpers
// ---------------------------------------------------------------------------

void _setCell(Sheet sheet, int col, int row, dynamic val, {CellStyle? style}) {
  final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row));
  if (val is int) {
    cell.value = IntCellValue(val);
  } else if (val is double) {
    cell.value = DoubleCellValue(val);
  } else {
    cell.value = TextCellValue(val.toString());
  }
  if (style != null) cell.cellStyle = style;
}

void _setFormula(Sheet sheet, int col, int row, String formula, {CellStyle? style}) {
  final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row));
  cell.value = FormulaCellValue(formula);
  if (style != null) cell.cellStyle = style;
}

/// Reads back the text value of a cell (used to mirror labels into the Master Mix Prep section).
String _getCellText(Sheet sheet, int col, int row) {
  final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: col, rowIndex: row));
  final v = cell.value;
  if (v == null) return '';
  if (v is TextCellValue) return v.value.toString();
  return v.toString();
}
