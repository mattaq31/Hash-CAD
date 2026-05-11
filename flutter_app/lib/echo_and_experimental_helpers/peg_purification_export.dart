// PEG purification helper sheet Excel export.
//
// Generates a standalone Excel workbook with per-group columns containing
// calculations for PEG purification of DNA origami slats. Mirrors the Python
// `prepare_peg_purification_sheet()` function but sources groups from the
// Flutter app's slat grouping system.
import 'dart:typed_data';
import 'dart:ui' show Color;

import 'package:excel/excel.dart' hide Border, BorderStyle;
import 'package:excel/excel.dart' as excel_lib show Border, BorderStyle;

import '../crisscross_core/slats.dart';
import 'echo_plate_constants.dart' show slatDisplayName;
import 'peg_purification_config.dart';
import 'plate_layout_state.dart';

// ---------------------------------------------------------------------------
// Cell styles (same pattern as master_mix_export.dart)
// ---------------------------------------------------------------------------

final _hairBorder = excel_lib.Border(borderStyle: excel_lib.BorderStyle.Hair);
final _mediumBorder = excel_lib.Border(borderStyle: excel_lib.BorderStyle.Medium);

CellStyle _inner({bool bold = false, String? bg, NumFormat? numFmt, HorizontalAlign? hAlign}) {
  final color = bg?.excelColor;
  return CellStyle(
    bold: bold,
    backgroundColorHex: color ?? '#FFFFFF'.excelColor,
    leftBorder: _hairBorder,
    rightBorder: _hairBorder,
    topBorder: _hairBorder,
    bottomBorder: _hairBorder,
    numberFormat: numFmt ?? NumFormat.standard_0,
    horizontalAlign: hAlign ?? HorizontalAlign.Left,
  );
}

final _sNormal = _inner();
final _sBold = _inner(bold: true);
final _sOrange = _inner(bg: '#FFF2CC');
final _sBlue = _inner(bg: '#ADD8E6');
final _sGreen = _inner(bg: '#C6EFCE');
final _sRed = _inner(bg: '#FFC7CE');
final _sHeader = _inner(bold: true, bg: '#D9E1F2');
final _sNum = _inner(numFmt: NumFormat.standard_2);
final _sNumBold = _inner(bold: true, numFmt: NumFormat.standard_2);

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Result of PEG purification Excel generation, including any warnings.
class PegPurificationResult {
  final Uint8List bytes;
  final List<String> warnings;

  const PegPurificationResult({required this.bytes, this.warnings = const []});
}

/// Generates a PEG purification helper sheet Excel workbook.
///
/// Each group in [groups] becomes one column. The sheet contains Excel formulas
/// so that users can adjust input values (orange/blue/green cells) and see
/// recalculated results in real time.
PegPurificationResult generatePegPurificationExcel({
  required Map<String, List<String>> groups,
  required Map<String, Slat> slats,
  required Map<String, Map<String, dynamic>> layerMap,
  required Map<int, Map<String, String?>> plateAssignments,
  required Map<int, Map<String, WellConfig>> wellConfigs,
  required Map<int, String> plateNames,
  required PegPurificationConfig pegConfig,
  required String experimentTitle,
  Map<String, Color>? groupColors,
}) {
  final warnings = <String>[];
  final excel = Excel.createExcel();
  final sheetName = 'PEG Purification';
  excel.rename(excel.getDefaultSheet()!, sheetName);
  final sheet = excel[sheetName];

  if (groups.isEmpty) {
    return PegPurificationResult(bytes: Uint8List.fromList(excel.encode()!), warnings: ['No groups provided.']);
  }

  final pegConc = pegConfig.pegConcentration;
  final targetMg = 10.0 * (pegConc / (pegConc - 1));

  // Build a reverse lookup: slatId → (plateIndex, well)
  final slatWellLookup = <String, (int, String)>{};
  for (var plateIndex in plateAssignments.keys) {
    final plate = plateAssignments[plateIndex]!;
    for (var well in plate.keys) {
      final slatId = plate[well];
      if (slatId != null) slatWellLookup[baseSlatId(slatId)] = (plateIndex, well);
    }
  }

  // Filter each group to only include slats assigned to output plates.
  final filteredGroups = <String, List<String>>{};
  for (var groupName in groups.keys) {
    final slatIds = groups[groupName]!;
    final assigned = slatIds.where((id) => slatWellLookup.containsKey(baseSlatId(id))).toList();
    if (assigned.isEmpty) {
      warnings.add('Group "$groupName" has no slats on output plates; excluded from PEG sheet.');
    } else {
      if (assigned.length < slatIds.length) {
        warnings.add(
          'Group "$groupName": ${assigned.length}/${slatIds.length} slats on output plates; '
          'PEG calculations use only those ${assigned.length}.',
        );
      }
      filteredGroups[groupName] = assigned;
    }
  }

  // Collect plate-assigned slats that don't belong to any group into per-layer leftover groups.
  final allGroupedSlatIds = <String>{};
  for (var ids in filteredGroups.values) {
    allGroupedSlatIds.addAll(ids.map(baseSlatId));
  }
  final leftoversByLayer = <String, List<String>>{};
  for (var slatId in slatWellLookup.keys) {
    if (!allGroupedSlatIds.contains(slatId)) {
      final slat = slats[slatId];
      final layer = slat?.layer ?? '?';
      leftoversByLayer.putIfAbsent(layer, () => []).add(slatId);
    }
  }
  if (leftoversByLayer.isNotEmpty) {
    final sortedLayers = leftoversByLayer.keys.toList()
      ..sort((a, b) => (layerMap[a]?['order'] as int? ?? 0).compareTo(layerMap[b]?['order'] as int? ?? 0));
    for (var layer in sortedLayers) {
      final layerOrder = (layerMap[layer]?['order'] as int? ?? 0) + 1;
      filteredGroups['Leftover L$layerOrder Slats'] = leftoversByLayer[layer]!;
    }
  }

  if (filteredGroups.isEmpty) {
    return PegPurificationResult(
      bytes: Uint8List.fromList(excel.encode()!),
      warnings: [...warnings, 'No slats assigned to output plates; PEG sheet is empty.'],
    );
  }

  // Split groups with mixed volumes into subgroups by volume.
  // Each subgroup becomes its own column in the output sheet.
  final resolvedGroups = <String, List<String>>{}; // subgroupName → slatIds
  final subgroupParent = <String, String>{}; // subgroupName → original group name

  for (var groupName in filteredGroups.keys) {
    final slatIds = filteredGroups[groupName]!;
    final volumeBuckets = <double, List<String>>{};
    for (var slatId in slatIds) {
      final base = baseSlatId(slatId);
      final lookup = slatWellLookup[base];
      double vol;
      if (lookup != null) {
        vol = (wellConfigs[lookup.$1] ?? {})[lookup.$2]?.volume ?? const WellConfig().volume;
      } else {
        vol = const WellConfig().volume;
      }
      volumeBuckets.putIfAbsent(vol, () => []).add(slatId);
    }

    if (volumeBuckets.length <= 1) {
      resolvedGroups[groupName] = slatIds;
      subgroupParent[groupName] = groupName;
    } else {
      // Split into subgroups with -A, -B, -C suffixes
      final suffixes = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
      var idx = 0;
      for (var entry in volumeBuckets.entries) {
        final subName = '$groupName-${suffixes[idx % suffixes.length]}';
        resolvedGroups[subName] = entry.value;
        subgroupParent[subName] = groupName;
        idx++;
      }
      warnings.add(
        'Group "$groupName" has mixed volumes (${volumeBuckets.keys.map((v) => '${v.toInt()} µL').join(', ')}); '
        'split into ${volumeBuckets.length} PEG subgroups.',
      );
    }
  }

  final groupNames = resolvedGroups.keys.toList();
  final numGroups = groupNames.length;

  // Pre-compute per-subgroup data
  final groupVolumes = <String, double>{};
  final groupScaffoldConcs = <String, double>{};
  final groupMWs = <String, double?>{};
  final groupSlatCount = <String, int>{};

  for (var groupName in groupNames) {
    final slatIds = resolvedGroups[groupName]!;
    groupSlatCount[groupName] = slatIds.length;

    final volumes = <double>[];
    final scaffoldConcs = <double>[];
    final mws = <double>[];

    for (var slatId in slatIds) {
      final base = baseSlatId(slatId);
      final lookup = slatWellLookup[base];
      if (lookup != null) {
        final config = (wellConfigs[lookup.$1] ?? {})[lookup.$2] ?? const WellConfig();
        volumes.add(config.volume);
        scaffoldConcs.add(config.scaffoldConc);
      } else {
        volumes.add(const WellConfig().volume);
        scaffoldConcs.add(const WellConfig().scaffoldConc);
      }

      final slat = slats[base];
      if (slat != null) {
        final mw = _safeMolecularWeight(slat);
        if (mw != null) mws.add(mw);
      }
    }

    groupVolumes[groupName] = _mode(volumes);
    groupScaffoldConcs[groupName] = _mode(scaffoldConcs);

    if (mws.isEmpty) {
      groupMWs[groupName] = null;
      warnings.add('Group "$groupName": could not calculate molecular weight (handles not fully assigned).');
    } else {
      groupMWs[groupName] = mws.reduce((a, b) => a + b) / mws.length;
      if (mws.length < slatIds.length) {
        warnings.add(
          'Group "$groupName": MW averaged from ${mws.length}/${slatIds.length} slats (some handles missing).',
        );
      }
    }
  }

  // =========================================================================
  // Write the sheet
  // =========================================================================

  // Set column A wider to accommodate label text
  sheet.setColumnWidth(0, 42.0);

  // --- Row 0: Header ---
  _setCell(sheet, 0, 0, 'PEG Purification', style: _sBold);
  for (var i = 0; i < numGroups; i++) {
    _setCell(sheet, i + 1, 0, groupNames[i], style: _sHeader);
  }

  // --- Row 1: Step 0 instruction (merged, centered) ---
  _mergeCentered(sheet, 0, numGroups, 1, 'Step 0: Combine all slats in group into one tube');

  // --- Row 2: Volume per well (orange) ---
  _setCell(sheet, 0, 2, 'Volume per well (µL)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    _setCell(sheet, i + 1, 2, groupVolumes[groupNames[i]]!, style: _sOrange);
  }

  // --- Row 3: # of slats ---
  _setCell(sheet, 0, 3, '# of slats', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    _setCell(sheet, i + 1, 3, groupSlatCount[groupNames[i]]!, style: _sNormal);
  }

  // --- Row 4: Total volume expected (formula) ---
  _setCell(sheet, 0, 4, 'Total volume expected (µL)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    _setFormula(sheet, i + 1, 4, '${c}3*${c}4', style: _sNum);
  }

  // --- Row 5: Scaffold conc per slat (orange) ---
  _setCell(sheet, 0, 5, 'Scaffold conc per slat (nM)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    _setCell(sheet, i + 1, 5, groupScaffoldConcs[groupNames[i]]!, style: _sOrange);
  }

  // --- Row 6: Expected total origami (formula) ---
  _setCell(sheet, 0, 6, 'Expected total origami (pmol)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    _setFormula(sheet, i + 1, 6, '${c}5*${c}6/1000', style: _sNum);
  }

  // --- Row 7: Original Mg conc (orange) ---
  _setCell(sheet, 0, 7, 'Original Mg conc (mM)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    _setCell(sheet, i + 1, 7, 6, style: _sOrange);
  }

  // --- Row 8: Target final Mg conc (computed constant) ---
  _setCell(sheet, 0, 8, 'Target final Mg conc (mM)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    _setCell(sheet, i + 1, 8, _roundTo2(targetMg), style: _sNormal);
  }

  // --- Row 9: Step 1 instruction (merged, centered) ---
  _mergeCentered(sheet, 0, numGroups, 9, 'Step 1: Add 1M MgCl₂');

  // --- Row 10: Amount of 1M Mg to add (formula) ---
  _setCell(sheet, 0, 10, 'Amount of 1M Mg to add (µL)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    _setFormula(sheet, i + 1, 10, 'ROUND((${c}9-${c}8)*${c}5/(1000-${c}9),2)', style: _sNum);
  }

  // --- Row 11: Step 2 instruction (merged, centered) ---
  _mergeCentered(sheet, 0, numGroups, 11, 'Step 2: Add ${pegConc}X PEG');

  // --- Row 12: Amount PEG to add (formula) ---
  _setCell(sheet, 0, 12, 'Amount of PEG to add (µL)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    _setFormula(sheet, i + 1, 12, '(${c}11+${c}5)/${pegConc - 1}', style: _sNum);
  }

  // --- Row 13: Final volume (formula, bold) ---
  _setCell(sheet, 0, 13, 'Final volume (µL)', style: _sBold);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    _setFormula(sheet, i + 1, 13, '${c}11+${c}5+${c}13', style: _sNumBold);
  }

  // --- Rows 14-17: Steps 3-6 instructions (merged, centered) ---
  final steps = [
    'Step 3: Spin at 16000g, RT for 30 min',
    'Step 4: Remove supernatant, add 150 µL Resus1, do not vortex or resuspend',
    'Step 5: Spin at 16000g, RT for 30 min',
    'Step 6: Remove supernatant carefully, then resuspend in the below volumes of Resus2',
  ];
  for (var s = 0; s < steps.length; s++) {
    _mergeCentered(sheet, 0, numGroups, 14 + s, steps[s]);
  }

  // --- Row 18: Desired final conc (blue, user editable) ---
  _setCell(sheet, 0, 18, 'Desired final conc (nM/slat)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    _setCell(sheet, i + 1, 18, 100, style: _sBlue);
  }

  // --- Row 19: Resuspend with Resus2 (formula) ---
  _setCell(sheet, 0, 19, 'Resuspend with Resus2 (µL)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    _setFormula(sheet, i + 1, 19, 'ROUND(((${c}7/${c}4)/${c}19)*1000,1)', style: _sNum);
  }

  // --- Row 20: Expected total slat conc (formula, conditionally red) ---
  _setCell(sheet, 0, 20, 'Expected total slat conc (µM)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    final count = groupSlatCount[groupNames[i]]!;
    final wouldExceed = (100.0 * count) / 1000 > 2.0;
    _setFormula(sheet, i + 1, 20, '(${c}19*${c}4)/1000', style: wouldExceed ? _sRed : _sNum);
  }

  // --- Row 21: Step 7 instruction (merged, centered) ---
  _mergeCentered(sheet, 0, numGroups, 21, 'Step 7: Shake at 33C for 1 hour with 1000RPM shaking, then Nanodrop');

  // --- Row 22: Nanodrop reading (green, default 0) ---
  _setCell(sheet, 0, 22, 'Nanodrop (ng/µL dsDNA)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    _setCell(sheet, i + 1, 22, 0, style: _sGreen);
  }

  // --- Row 23: Average slat MW (static value or N/A) ---
  _setCell(sheet, 0, 23, 'Average slat MW (Da)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final mw = groupMWs[groupNames[i]];
    if (mw != null) {
      _setCell(sheet, i + 1, 23, _roundTo0(mw), style: _sNormal);
    } else {
      _setCell(sheet, i + 1, 23, 'N/A', style: _sNormal);
    }
  }

  // --- Row 24: Total conc from Nanodrop (formula) ---
  _setCell(sheet, 0, 24, 'Total conc from Nanodrop (µM)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    if (groupMWs[groupNames[i]] != null) {
      _setFormula(sheet, i + 1, 24, 'ROUND((${c}23*1000)/${c}24,2)', style: _sNum);
    } else {
      _setCell(sheet, i + 1, 24, '—', style: _sNormal);
    }
  }

  // --- Row 25: Conc per slat (formula) ---
  _setCell(sheet, 0, 25, 'Conc per individual slat (nM)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    if (groupMWs[groupNames[i]] != null) {
      _setFormula(sheet, i + 1, 25, 'ROUND(${c}25/${c}4*1000,2)', style: _sNum);
    } else {
      _setCell(sheet, i + 1, 25, '—', style: _sNormal);
    }
  }

  // --- Row 26: Amount each slat (formula) ---
  _setCell(sheet, 0, 26, 'Total amount each slat (pmol)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    if (groupMWs[groupNames[i]] != null) {
      _setFormula(sheet, i + 1, 26, 'ROUND(${c}26*${c}20/1000,2)', style: _sNum);
    } else {
      _setCell(sheet, i + 1, 26, '—', style: _sNormal);
    }
  }

  // --- Row 27: Total origami (formula) ---
  _setCell(sheet, 0, 27, 'Total origami (pmol)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    if (groupMWs[groupNames[i]] != null) {
      _setFormula(sheet, i + 1, 27, '${c}27*${c}4', style: _sNum);
    } else {
      _setCell(sheet, i + 1, 27, '—', style: _sNormal);
    }
  }

  // --- Row 28: PEG Yield (formula) ---
  _setCell(sheet, 0, 28, 'PEG Yield (%)', style: _sNormal);
  for (var i = 0; i < numGroups; i++) {
    final c = _colLetter(i + 1);
    if (groupMWs[groupNames[i]] != null) {
      _setFormula(sheet, i + 1, 28, '${c}28/${c}7*100', style: _sNum);
    } else {
      _setCell(sheet, i + 1, 28, '—', style: _sNormal);
    }
  }

  // --- Row 30: Resus buffer section header ---
  _setCell(sheet, 0, 30, 'Resus Buffer Components', style: _sBold);
  _setCell(sheet, 1, 30, 'Stock Conc', style: _sHeader);
  _setCell(sheet, 2, 30, 'Target Conc', style: _sHeader);
  _setCell(sheet, 3, 30, 'Resus1 (µL)', style: _sHeader);
  _setCell(sheet, 4, 30, 'Resus2 (µL)', style: _sHeader);

  // Buffer table: Resus1 = 150 µL total wash, Resus2 = 2000 µL resuspension
  _setCell(sheet, 0, 31, '10X TEF', style: _sNormal);
  _setCell(sheet, 1, 31, '10X', style: _sNormal);
  _setCell(sheet, 2, 31, '1X', style: _sNormal);
  _setCell(sheet, 3, 31, 15, style: _sNormal);
  _setCell(sheet, 4, 31, 200, style: _sNormal);

  _setCell(sheet, 0, 32, '1M MgCl₂', style: _sNormal);
  _setCell(sheet, 1, 32, '1000 mM', style: _sNormal);
  _setCell(sheet, 2, 32, '200 mM / 100 mM', style: _sNormal);
  _setCell(sheet, 3, 32, 30, style: _sNormal);
  _setCell(sheet, 4, 32, 200, style: _sNormal);

  _setCell(sheet, 0, 33, 'UPW', style: _sNormal);
  _setCell(sheet, 1, 33, '—', style: _sNormal);
  _setCell(sheet, 2, 33, '—', style: _sNormal);
  _setCell(sheet, 3, 33, 105, style: _sNormal);
  _setCell(sheet, 4, 33, 1600, style: _sNormal);

  _setCell(sheet, 0, 34, 'Total', style: _sBold);
  _setCell(sheet, 1, 34, '', style: _sNormal);
  _setCell(sheet, 2, 34, '', style: _sNormal);
  _setCell(sheet, 3, 34, 150, style: _sBold);
  _setCell(sheet, 4, 34, 2000, style: _sBold);

  // --- Row 36: Slat group reference table header ---
  _setCell(sheet, 0, 36, 'Slat Group Components', style: _sBold);
  _setCell(sheet, 0, 37, 'Group', style: _sHeader);
  _setCell(sheet, 1, 37, 'Slat ID', style: _sHeader);
  _setCell(sheet, 2, 37, 'Well', style: _sHeader);
  _setCell(sheet, 3, 37, 'Plate', style: _sHeader);

  // Group color legend (adjacent to the slat table)
  _setCell(sheet, 5, 36, 'Group Colors', style: _sBold);
  _setCell(sheet, 5, 37, 'Group', style: _sHeader);
  _setCell(sheet, 6, 37, 'Color', style: _sHeader);

  var colorRow = 38;
  for (var groupName in groupNames) {
    _setCell(sheet, 5, colorRow, groupName, style: _sNormal);
    final parentName = subgroupParent[groupName] ?? groupName;
    final groupColor = groupColors?[parentName];
    if (groupColor != null) {
      final argb = groupColor.toARGB32();
      final hex = '#${argb.toRadixString(16).padLeft(8, '0').substring(2).toUpperCase()}';
      final colorStyle = _inner(bg: hex);
      _setCell(sheet, 6, colorRow, '', style: colorStyle);
    } else {
      _setCell(sheet, 6, colorRow, '', style: _sNormal);
    }
    colorRow++;
  }

  // Write per-slat reference rows using LX-V display names
  var refRow = 38;
  for (var groupName in groupNames) {
    final slatIds = resolvedGroups[groupName]!;
    final groupStartRow = refRow;
    for (var slatId in slatIds) {
      final base = baseSlatId(slatId);
      final slat = slats[base];
      final displayName = slat != null ? slatDisplayName(slat, layerMap) : slatId;
      final lookup = slatWellLookup[base];
      final well = lookup != null ? lookup.$2 : '—';
      final plate = lookup != null ? (plateNames[lookup.$1] ?? 'P${lookup.$1 + 1}') : '—';

      _setCell(sheet, 0, refRow, groupName, style: _sNormal);
      _setCell(sheet, 1, refRow, displayName, style: _sNormal);
      _setCell(sheet, 2, refRow, well, style: _sNormal);
      _setCell(sheet, 3, refRow, plate, style: _sNormal);
      refRow++;
    }
    // Apply bottom border to last row of group for visual separation
    if (groupStartRow < refRow) {
      for (var c = 0; c <= 3; c++) {
        final cell = sheet.cell(CellIndex.indexByColumnRow(columnIndex: c, rowIndex: refRow - 1));
        final existing = cell.cellStyle;
        cell.cellStyle = CellStyle(
          bold: existing?.isBold ?? false,
          backgroundColorHex: existing?.backgroundColor ?? '#FFFFFF'.excelColor,
          leftBorder: existing?.leftBorder ?? _hairBorder,
          rightBorder: existing?.rightBorder ?? _hairBorder,
          topBorder: existing?.topBorder ?? _hairBorder,
          bottomBorder: _mediumBorder,
        );
      }
    }
  }

  // Apply outer borders to the main calculation block (rows 0-28)
  _applyOuterBorder(sheet, 0, numGroups, 0, 28);

  // Apply outer border to buffer table (rows 30-34)
  _applyOuterBorder(sheet, 0, 4, 30, 34);

  return PegPurificationResult(bytes: Uint8List.fromList(excel.encode()!), warnings: warnings);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Safely attempts to get molecular weight; returns null on failure.
double? _safeMolecularWeight(Slat slat) {
  try {
    return slat.getMolecularWeight();
  } catch (_) {
    return null;
  }
}

/// Returns the mode (most common value) of a list of doubles.
double _mode(List<double> values) {
  if (values.isEmpty) return const WellConfig().volume;
  final counts = <double, int>{};
  for (var v in values) {
    counts[v] = (counts[v] ?? 0) + 1;
  }
  return counts.entries.reduce((a, b) => a.value >= b.value ? a : b).key;
}

double _roundTo2(double v) => (v * 100).roundToDouble() / 100;
int _roundTo0(double v) => v.round();

/// Converts a 0-based column index to an Excel column letter (A, B, ..., Z, AA, ...).
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

/// Merges cells across a row with a text value and applies centered bold style.
void _mergeCentered(Sheet sheet, int colStart, int colEnd, int row, String text) {
  sheet.merge(
    CellIndex.indexByColumnRow(columnIndex: colStart, rowIndex: row),
    CellIndex.indexByColumnRow(columnIndex: colEnd, rowIndex: row),
    customValue: TextCellValue(text),
  );
  sheet.cell(CellIndex.indexByColumnRow(columnIndex: colStart, rowIndex: row)).cellStyle = CellStyle(
    bold: true,
    horizontalAlign: HorizontalAlign.Center,
    leftBorder: _hairBorder,
    rightBorder: _hairBorder,
    topBorder: _hairBorder,
    bottomBorder: _hairBorder,
  );
}

/// Applies a strong (Medium) outer border around a rectangular table region.
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
        horizontalAlign: existing?.horizontalAlignment ?? HorizontalAlign.Left,
        topBorder: needsTop ? _mediumBorder : (existing?.topBorder ?? _hairBorder),
        bottomBorder: needsBottom ? _mediumBorder : (existing?.bottomBorder ?? _hairBorder),
        leftBorder: needsLeft ? _mediumBorder : (existing?.leftBorder ?? _hairBorder),
        rightBorder: needsRight ? _mediumBorder : (existing?.rightBorder ?? _hairBorder),
      );
    }
  }
}
