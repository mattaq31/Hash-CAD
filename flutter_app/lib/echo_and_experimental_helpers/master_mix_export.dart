// Master mix Excel export with per-slat-type sheets and horizontal group layout.
import 'dart:typed_data';

import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:excel/excel.dart' as excel_lib show Border, BorderStyle;

import '../crisscross_core/slats.dart';
import 'echo_plate_constants.dart';
import 'master_mix_config.dart';
import 'plate_layout_state.dart';

/// Per-well entry used to compute volumes and group slats.
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

/// Grouping key: slats with identical WellConfig triples share a recipe.
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
// Shared border definitions
// ---------------------------------------------------------------------------

final _hairBorder = excel_lib.Border(borderStyle: excel_lib.BorderStyle.Hair);
final _mediumBorder = excel_lib.Border(borderStyle: excel_lib.BorderStyle.Medium);

/// Internal cell style: hair-weight borders on all sides.
CellStyle _inner({bool bold = false, String? bg, NumFormat? numFmt}) {
  final color = bg?.excelColor;
  return CellStyle(
    bold: bold,
    backgroundColorHex: color ?? '#FFFFFF'.excelColor,
    leftBorder: _hairBorder,
    rightBorder: _hairBorder,
    topBorder: _hairBorder,
    bottomBorder: _hairBorder,
    numberFormat: numFmt ?? NumFormat.standard_0,
  );
}

// Text/label styles (General format)
final _sNormal = _inner();
final _sBold = _inner(bold: true);
final _sOrange = _inner(bg: '#FFF2CC');
final _sOrangeBold = _inner(bold: true, bg: '#FFF2CC');
final _sHeader = _inner(bold: true, bg: '#D9E1F2');

// Numeric styles (0.00 format — for formula results and numeric values)
final _sNum = _inner(numFmt: NumFormat.standard_2);
final _sNumBold = _inner(bold: true, numFmt: NumFormat.standard_2);
final _sNumOrange = _inner(bg: '#FFF2CC', numFmt: NumFormat.standard_2);

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Result of master mix Excel generation, including any volume warnings.
class MasterMixResult {
  final Uint8List bytes;
  final List<String> warnings;

  const MasterMixResult({required this.bytes, this.warnings = const []});
}

/// Generates a master mix Excel workbook (.xlsx bytes) with per-slat-type sheets
/// and horizontally-arranged recipe groups.
MasterMixResult generateMasterMixExcel({
  required Map<int, Map<String, String?>> plateAssignments,
  required Map<int, Map<String, WellConfig>> wellConfigs,
  required Map<int, String> plateNames,
  required Map<String, Slat> slats,
  required Map<String, Map<String, dynamic>> layerMap,
  required MasterMixConfig mixConfig,
  bool normalizeVolumes = false,
  double maxWellVolumeNl = 25000,
  String experimentTitle = 'Experiment',
  Map<String, Set<(int, int)>>? manualHandles,
}) {
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
    return MasterMixResult(bytes: Uint8List.fromList(excel.encode()!));
  }

  final standardEntries = entries.where((e) => !_isDoubleBarrel(e.slat)).toList();
  final dbEntries = entries.where((e) => _isDoubleBarrel(e.slat)).toList();

  final excel = Excel.createExcel();

  if (standardEntries.isNotEmpty) {
    _buildTypeSheet(
      excel: excel,
      sheetName: 'Standard Slat Master Mixes',
      entries: standardEntries,
      mixConfig: mixConfig,
      normalizeVolumes: normalizeVolumes,
      useSingleStock: mixConfig.coreStaplesUseSingleStock,
      stockConc: mixConfig.coreStaplesStockConc,
      helixConcs: mixConfig.coreStaplesHelixConcs,
      coreRatio: mixConfig.coreStaplesRatio,
      bufferMode: mixConfig.bufferSlatsMode,
      bufferPct: mixConfig.bufferSlatsPercentage,
      bufferCount: mixConfig.bufferSlats,
      layerMap: layerMap,
      plateNames: plateNames,
      slats: slats,
      manualHandles: manualHandles,
    );
  }

  if (dbEntries.isNotEmpty) {
    _buildTypeSheet(
      excel: excel,
      sheetName: 'Double Barrel Slat Master Mixes',
      entries: dbEntries,
      mixConfig: mixConfig,
      normalizeVolumes: normalizeVolumes,
      useSingleStock: mixConfig.dbCoreStaplesUseSingleStock,
      stockConc: mixConfig.dbCoreStaplesStockConc,
      helixConcs: mixConfig.dbCoreStaplesHelixConcs,
      coreRatio: mixConfig.dbCoreStaplesRatio,
      bufferMode: mixConfig.dbBufferSlatsMode,
      bufferPct: mixConfig.dbBufferSlatsPercentage,
      bufferCount: mixConfig.dbBufferSlats,
      layerMap: layerMap,
      plateNames: plateNames,
      slats: slats,
      manualHandles: manualHandles,
    );
  }

  if (excel.sheets.containsKey('Sheet1')) excel.delete('Sheet1');

  // Check for manual handles that are placeholders (no plate assigned).
  final warnings = <String>[];
  int manualPlaceholderHandleCount = 0;
  final manualPlaceholderSlatIds = <String>{};
  if (manualHandles != null) {
    for (var entry in entries) {
      final base = baseSlatId(entry.slatId);
      final slatManual = manualHandles[base];
      if (slatManual == null || slatManual.isEmpty) continue;
      for (var (helix, position) in slatManual) {
        final handles = helix == 2 ? entry.slat.h2Handles : entry.slat.h5Handles;
        final handleData = handles[position];
        if (handleData == null) continue;
        final conc = (handleData['concentration'] as num?)?.toDouble();
        if (conc == null || conc <= 0) {
          manualPlaceholderHandleCount++;
          manualPlaceholderSlatIds.add(base);
        }
      }
    }
  }
  if (manualPlaceholderHandleCount > 0) {
    warnings.add(
      '$manualPlaceholderHandleCount handle(s) across ${manualPlaceholderSlatIds.length} slat(s) '
      'are marked manual without plate assignments — total handle volume is underestimated.',
    );
  }

  // Check for slats exceeding the max well volume threshold.
  final overflowSlats = entries.where((e) => e.totalHandleVolumeNl > maxWellVolumeNl).toList();
  if (overflowSlats.isNotEmpty) {
    final shown = overflowSlats.take(5).map((e) => slatDisplayName(e.slat, layerMap, slats: slats)).join(', ');
    final extra = overflowSlats.length > 5 ? ' and ${overflowSlats.length - 5} more' : '';
    final thresholdUl = (maxWellVolumeNl / 1000).toStringAsFixed(1);
    warnings.add('${overflowSlats.length} slat(s) exceed the $thresholdUl µL well volume threshold: $shown$extra');
  }

  return MasterMixResult(bytes: Uint8List.fromList(excel.encode()!), warnings: warnings);
}

// ---------------------------------------------------------------------------
// Per-type sheet builder
// ---------------------------------------------------------------------------

/// Builds a single sheet with horizontally-arranged groups (one group per 5-column block).
void _buildTypeSheet({
  required Excel excel,
  required String sheetName,
  required List<_WellEntry> entries,
  required MasterMixConfig mixConfig,
  required bool normalizeVolumes,
  required bool useSingleStock,
  required double stockConc,
  required List<double> helixConcs,
  required double coreRatio,
  required BufferSlatsMode bufferMode,
  required double bufferPct,
  required int bufferCount,
  required Map<String, Map<String, dynamic>> layerMap,
  required Map<int, String> plateNames,
  required Map<String, Slat> slats,
  Map<String, Set<(int, int)>>? manualHandles,
}) {
  final sheet = excel[sheetName];

  final groups = <_GroupKey, List<_WellEntry>>{};
  for (var e in entries) {
    final key = _GroupKey(e.config.ratio, e.config.volume, e.config.scaffoldConc);
    groups.putIfAbsent(key, () => []).add(e);
  }
  final sortedKeys = groups.keys.toList();

  for (var gi = 0; gi < sortedKeys.length; gi++) {
    final gKey = sortedKeys[gi];
    final groupEntries = groups[gKey]!;
    final config = groupEntries.first.config;
    final slatCount = groupEntries.length;
    final colBase = gi * 5;

    final resolvedBuffer = bufferMode == BufferSlatsMode.percentage
        ? (slatCount * bufferPct / 100).ceil()
        : bufferCount;

    // Reference volume is the max handle volume within this group.
    // With normalization ON, water fills every well to this level.
    // Without normalization, we use the worst case (highest volume = lowest conc).
    final maxVolumeInGroup = groupEntries.map((e) => e.totalHandleVolumeNl).reduce((a, b) => a > b ? a : b);
    final minVolumeInGroup = groupEntries.map((e) => e.totalHandleVolumeNl).reduce((a, b) => a < b ? a : b);
    final volumeVaries = (maxVolumeInGroup - minVolumeInGroup).abs() > 25;

    // Effective concentration accounts for dilution to the reference volume.
    final effectiveConcs = groupEntries.map((e) {
      if (maxVolumeInGroup <= 0) return 0.0;
      return e.minHandleConcNm * e.totalHandleVolumeNl / maxVolumeInGroup;
    }).toList();
    final minConcInGroup = effectiveConcs.reduce((a, b) => a < b ? a : b);
    final maxConcInGroup = effectiveConcs.reduce((a, b) => a > b ? a : b);
    final concVaries = (maxConcInGroup - minConcInGroup).abs() > 0.01;

    final cB = _colLetter(colBase + 1);
    final cC = _colLetter(colBase + 2);
    final cD = _colLetter(colBase + 3);

    int row = 0;

    // ===== Title row (spans 4 cols, only first cell gets header style) =====
    final title = '${config.ratio}x, ${config.scaffoldConc}nM, ${config.volume}µL ($slatCount slats)';
    _setCell(sheet, colBase, row, title, style: _sHeader);
    _setCell(sheet, colBase + 1, row, '', style: _sHeader);
    _setCell(sheet, colBase + 2, row, '', style: _sHeader);
    _setCell(sheet, colBase + 3, row, '', style: _sHeader);
    row++;

    // ===== Table 1: Single Slat Folding =====
    final t1Start = row;
    _setCell(sheet, colBase, row, 'Component', style: _sBold);
    _setCell(sheet, colBase + 1, row, 'Stock Conc.', style: _sBold);
    _setCell(sheet, colBase + 2, row, 'Final Conc.', style: _sBold);
    _setCell(sheet, colBase + 3, row, 'Amount (µL)', style: _sBold);
    row++;

    final handlesRow = row;
    _setCell(sheet, colBase, row, 'H2/H5 Handles (nM)', style: _sNormal);
    _setCell(sheet, colBase + 1, row, minConcInGroup, style: _sNumOrange);
    _setCell(sheet, colBase + 2, row, '', style: _sNum);
    _setCell(sheet, colBase + 3, row, '', style: _sNum);
    row++;

    final scaffoldRow = row;
    _setCell(sheet, colBase, row, 'P8064 Scaffold (nM)', style: _sNormal);
    _setCell(sheet, colBase + 1, row, mixConfig.scaffoldStockConc, style: _sNum);
    _setCell(sheet, colBase + 2, row, config.scaffoldConc, style: _sNum);
    _setCell(sheet, colBase + 3, row, '', style: _sNum);
    row++;

    final sR = scaffoldRow + 1;
    _setFormula(sheet, colBase + 2, handlesRow, '$cC$sR*${config.ratio}', style: _sNum);

    final coreStartRow = row;
    if (useSingleStock) {
      _setCell(sheet, colBase, row, 'Core Staples (nM)', style: _sNormal);
      _setCell(sheet, colBase + 1, row, stockConc, style: _sNum);
      _setFormula(sheet, colBase + 2, row, '$cC$sR*$coreRatio', style: _sNum);
      _setCell(sheet, colBase + 3, row, '', style: _sNum);
      row++;
    } else {
      final helixLabels = ['Core Staples Helix 0 (nM)', 'Core Staples Helix 1 (nM)', 'Core Staples Helix 3 (nM)', 'Core Staples Helix 4 (nM)'];
      for (var i = 0; i < 4; i++) {
        _setCell(sheet, colBase, row, helixLabels[i], style: _sNormal);
        _setCell(sheet, colBase + 1, row, helixConcs[i], style: _sNum);
        _setFormula(sheet, colBase + 2, row, '$cC$sR*$coreRatio', style: _sNum);
        _setCell(sheet, colBase + 3, row, '', style: _sNum);
        row++;
      }
    }
    final coreEndRow = row - 1;

    final tefRow = row;
    _setCell(sheet, colBase, row, 'TEF (X)', style: _sNormal);
    _setCell(sheet, colBase + 1, row, mixConfig.tefStock, style: _sNum);
    _setCell(sheet, colBase + 2, row, mixConfig.tefFinal, style: _sNum);
    _setCell(sheet, colBase + 3, row, '', style: _sNum);
    row++;

    final mgcl2Row = row;
    _setCell(sheet, colBase, row, 'MgCl₂ (mM)', style: _sNormal);
    _setCell(sheet, colBase + 1, row, mixConfig.mgcl2Stock, style: _sNum);
    _setCell(sheet, colBase + 2, row, mixConfig.mgcl2Final, style: _sNum);
    _setCell(sheet, colBase + 3, row, '', style: _sNum);
    row++;

    final upwRow = row;
    _setCell(sheet, colBase, row, 'UPW', style: _sNormal);
    _setCell(sheet, colBase + 1, row, '', style: _sNormal);
    _setCell(sheet, colBase + 2, row, '', style: _sNormal);
    _setCell(sheet, colBase + 3, row, '', style: _sNum);
    row++;

    final totalRow = row;
    _setCell(sheet, colBase, row, 'Total Volume (µL)', style: _sBold);
    _setCell(sheet, colBase + 1, row, '', style: _sNormal);
    _setCell(sheet, colBase + 2, row, '', style: _sNormal);
    _setCell(sheet, colBase + 3, row, config.volume, style: _sNumBold);
    row++;

    final pmolRow = row;
    _setCell(sheet, colBase, row, 'Total Amount (pmol)', style: _sNormal);
    _setCell(sheet, colBase + 1, row, '', style: _sNormal);
    _setCell(sheet, colBase + 2, row, '', style: _sNormal);
    _setCell(sheet, colBase + 3, row, '', style: _sNum);
    row++;
    final t1End = row - 1;

    // Formulas for Table 1
    final hR = handlesRow + 1;
    final totalExcelRow = totalRow + 1;
    final tR = tefRow + 1;
    final mR = mgcl2Row + 1;

    _setFormula(sheet, colBase + 3, handlesRow, '$cC$hR*$cD$totalExcelRow/$cB$hR', style: _sNum);
    _setFormula(sheet, colBase + 3, scaffoldRow, '$cC$sR*$cD$totalExcelRow/$cB$sR', style: _sNum);
    for (var r = coreStartRow; r <= coreEndRow; r++) {
      final eR = r + 1;
      _setFormula(sheet, colBase + 3, r, '$cC$eR*$cD$totalExcelRow/$cB$eR', style: _sNum);
    }
    _setFormula(sheet, colBase + 3, tefRow, '$cC$tR*$cD$totalExcelRow/$cB$tR', style: _sNum);
    _setFormula(sheet, colBase + 3, mgcl2Row, '$cC$mR*$cD$totalExcelRow/$cB$mR', style: _sNum);
    _setFormula(sheet, colBase + 3, upwRow, '$cD$totalExcelRow-SUM($cD$hR:$cD$mR)', style: _sNum);
    _setFormula(sheet, colBase + 3, pmolRow, '$cD$totalExcelRow*$cC$sR/1000', style: _sNum);

    _applyOuterBorder(sheet, colBase, colBase + 3, t1Start, t1End);

    // Volume inconsistency warning (only relevant without normalization)
    if (!normalizeVolumes && volumeVaries) {
      row++;
      _setCell(sheet, colBase, row, 'WARNING: Handle volumes vary', style: _sOrangeBold);
      _setCell(sheet, colBase + 1, row, 'Min: ${(minVolumeInGroup / 1000).toStringAsFixed(2)} µL', style: _sOrange);
      _setCell(sheet, colBase + 2, row, 'Max: ${(maxVolumeInGroup / 1000).toStringAsFixed(2)} µL', style: _sOrange);
      row++;
      _setCell(sheet, colBase, row, 'Recipe uses max vol. Minor per-slat variations.', style: _sOrange);
      row++;
    }

    // Concentration variation note
    if (concVaries) {
      row++;
      _setCell(sheet, colBase, row, 'Note: Effective handle concs vary', style: _sOrangeBold);
      _setCell(sheet, colBase + 1, row, 'Min: ${minConcInGroup.toStringAsFixed(2)} nM', style: _sOrange);
      _setCell(sheet, colBase + 2, row, 'Max: ${maxConcInGroup.toStringAsFixed(2)} nM', style: _sOrange);
      row++;
      _setCell(sheet, colBase, row, 'May stem from volume normalization being off or 25 nL rounding by the Echo.', style: _sOrange);
      row++;
    }

    // Manual handles without plate assignments warning
    if (manualHandles != null) {
      int groupManualCount = 0;
      for (var e in groupEntries) {
        final base = baseSlatId(e.slatId);
        final slatManual = manualHandles[base];
        if (slatManual == null || slatManual.isEmpty) continue;
        for (var (helix, position) in slatManual) {
          final handles = helix == 2 ? e.slat.h2Handles : e.slat.h5Handles;
          final handleData = handles[position];
          if (handleData == null) continue;
          final conc = (handleData['concentration'] as num?)?.toDouble();
          if (conc == null || conc <= 0) groupManualCount++;
        }
      }
      if (groupManualCount > 0) {
        row++;
        _setCell(sheet, colBase, row, 'WARNING: $groupManualCount manual handle(s) lack plate assignments', style: _sOrangeBold);
        row++;
        _setCell(sheet, colBase, row, 'Total handle volume is underestimated.', style: _sOrange);
        row++;
      }
    }

    row++; // spacer

    // ===== Table 2: Master Mix Prep =====
    final t2Start = row;
    _setCell(sheet, colBase, row, 'Master Mix Prep', style: _sHeader);
    _setCell(sheet, colBase + 1, row, 'Volume (µL)', style: _sHeader);
    row++;

    final countRow = row;
    final countExcelRow = countRow + 1;
    _setCell(sheet, colBase, row, 'Number of slats (+$resolvedBuffer buffer)', style: _sNormal);
    _setCell(sheet, colBase + 1, row, slatCount + resolvedBuffer, style: _sBold);
    row++;

    _setCell(sheet, colBase, row, 'P8064 Scaffold', style: _sNormal);
    _setFormula(sheet, colBase + 1, row, '$cD$sR*$cB$countExcelRow', style: _sNum);
    row++;

    for (var r = coreStartRow; r <= coreEndRow; r++) {
      final label = _getCellText(sheet, colBase, r).replaceAll(' (nM)', '');
      _setCell(sheet, colBase, row, label, style: _sNormal);
      _setFormula(sheet, colBase + 1, row, '$cD${r + 1}*$cB$countExcelRow', style: _sNum);
      row++;
    }

    _setCell(sheet, colBase, row, 'TEF', style: _sNormal);
    _setFormula(sheet, colBase + 1, row, '$cD$tR*$cB$countExcelRow', style: _sNum);
    row++;

    _setCell(sheet, colBase, row, 'MgCl₂', style: _sNormal);
    _setFormula(sheet, colBase + 1, row, '$cD$mR*$cB$countExcelRow', style: _sNum);
    row++;

    final mmUpwRow = row;
    _setCell(sheet, colBase, row, 'UPW', style: _sNormal);
    final uR = upwRow + 1;
    _setFormula(sheet, colBase + 1, row, '$cD$uR*$cB$countExcelRow', style: _sNum);
    row++;

    final mmScaffoldExcelRow = countRow + 2;
    _setCell(sheet, colBase, row, 'Total Volume', style: _sBold);
    _setFormula(sheet, colBase + 1, row, 'SUM($cB$mmScaffoldExcelRow:$cB${mmUpwRow + 1})', style: _sNumBold);
    final mmTotalExcelRow = row + 1;
    final t2End = row;
    row++;

    _applyOuterBorder(sheet, colBase, colBase + 1, t2Start, t2End);

    row++; // spacer

    // ===== Table 3: Final Slat Mixture (per slat) =====
    final t3Start = row;
    _setCell(sheet, colBase, row, 'Final Slat Mixture (per slat)', style: _sHeader);
    _setCell(sheet, colBase + 1, row, 'Volume (µL)', style: _sHeader);
    row++;

    final fmMmRow = row;
    _setCell(sheet, colBase, row, 'Master Mix', style: _sNormal);
    _setFormula(sheet, colBase + 1, row, '$cB$mmTotalExcelRow/$cB$countExcelRow', style: _sNum);
    row++;

    final fmHandlesRow = row;
    _setCell(sheet, colBase, row, 'Slat Handle Mixture', style: _sNormal);
    _setFormula(sheet, colBase + 1, row, '$cD$hR', style: _sNum);
    row++;

    _setCell(sheet, colBase, row, 'Total Volume', style: _sBold);
    _setFormula(sheet, colBase + 1, row, '$cB${fmMmRow + 1}+$cB${fmHandlesRow + 1}', style: _sNumBold);
    final t3End = row;
    row++;

    _applyOuterBorder(sheet, colBase, colBase + 1, t3Start, t3End);

    row++; // spacer

    // ===== Table 4: Slat List =====
    final t4Start = row;
    _setCell(sheet, colBase, row, 'Slats in Group', style: _sHeader);
    _setCell(sheet, colBase + 1, row, 'Well', style: _sHeader);
    _setCell(sheet, colBase + 2, row, 'Plate', style: _sHeader);
    row++;

    for (var e in groupEntries) {
      _setCell(sheet, colBase, row, slatDisplayName(e.slat, layerMap, slats: slats), style: _sNormal);
      _setCell(sheet, colBase + 1, row, e.well, style: _sNormal);
      _setCell(sheet, colBase + 2, row, plateNames[e.plateIndex] ?? 'Plate', style: _sNormal);
      row++;
    }
    final t4End = row - 1;

    _applyOuterBorder(sheet, colBase, colBase + 2, t4Start, t4End);
  }

  for (var gi = 0; gi < sortedKeys.length; gi++) {
    final colBase = gi * 5;
    sheet.setColumnWidth(colBase, 30.0);
    sheet.setColumnWidth(colBase + 1, 16.0);
    sheet.setColumnWidth(colBase + 2, 14.0);
    sheet.setColumnWidth(colBase + 3, 14.0);
    sheet.setColumnWidth(colBase + 4, 3.0);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

bool _isDoubleBarrel(Slat slat) => slat.slatType.startsWith('DB-');

/// Converts a 0-based column index to an Excel column letter (A, B, ..., Z, AA, AB, ...).
String _colLetter(int col) {
  var result = '';
  var c = col;
  while (true) {
    result = String.fromCharCode(65 + (c % 26)) + result;
    c = c ~/ 26 - 1;
    if (c < 0) break;
  }
  return result;
}

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

/// Applies a strong (Medium) outer border around a rectangular table region.
/// Interior borders are left as-is (Hair weight from the cell styles).
void _applyOuterBorder(Sheet sheet, int colStart, int colEnd, int rowStart, int rowEnd) {
  for (var r = rowStart; r <= rowEnd; r++) {
    for (var c = colStart; c <= colEnd; c++) {
      final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: c, rowIndex: r));
      final existing = cell.cellStyle;

      final needsTop = r == rowStart;
      final needsBottom = r == rowEnd;
      final needsLeft = c == colStart;
      final needsRight = c == colEnd;

      if (!needsTop && !needsBottom && !needsLeft && !needsRight) continue;

      cell.cellStyle = CellStyle(
        bold: existing?.isBold ?? false,
        backgroundColorHex: existing?.backgroundColor ?? '#FFFFFF'.excelColor,
        numberFormat: existing?.numberFormat ?? NumFormat.standard_0,
        topBorder: needsTop ? _mediumBorder : (existing?.topBorder ?? _hairBorder),
        bottomBorder: needsBottom ? _mediumBorder : (existing?.bottomBorder ?? _hairBorder),
        leftBorder: needsLeft ? _mediumBorder : (existing?.leftBorder ?? _hairBorder),
        rightBorder: needsRight ? _mediumBorder : (existing?.rightBorder ?? _hairBorder),
      );
    }
  }
}
