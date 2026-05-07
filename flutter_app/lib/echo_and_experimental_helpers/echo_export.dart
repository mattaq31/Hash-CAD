import 'dart:convert';
import 'dart:typed_data';
import 'package:csv/csv.dart';

import '../crisscross_core/handle_plates.dart';
import '../crisscross_core/slats.dart';
import 'echo_plate_constants.dart';
import 'plate_layout_state.dart';

List<String> generatePlateLayout96() {
  final rows = 'ABCDEFGH'.split('');
  final cols = List.generate(12, (i) => i + 1);
  return [
    for (var row in rows)
      for (var col in cols) '$row${col.toString()}'
  ];
}

List<String> generatePlateLayout384() {
  final rows = 'ABCDEFGHIJKLMNOP'.split('');
  final cols = List.generate(24, (i) => i + 1);
  return [
    for (var row in rows)
      for (var col in cols) '$row${col.toString()}'
  ];
}

/// Result of CSV generation for Echo liquid handler instructions.
class EchoCsvResult {
  final Uint8List csvBytes;
  final Uint8List? manualCsvBytes;
  final List<String> warnings;
  final double? totalWaterNl;
  final int? waterWellsUsed;

  const EchoCsvResult({required this.csvBytes, this.manualCsvBytes, this.warnings = const [], this.totalWaterNl, this.waterWellsUsed});
}

/// Generates Echo liquid handler CSV instructions from plate layout assignments.
///
/// Each occupied well produces one CSV row per handle, with transfer volumes computed from
/// [WellConfig.materialPerHandle] and the handle's concentration.
///
/// When [normalizeVolumes] is true, water transfer rows are appended so that every destination
/// well receives the same total volume (equal to the maximum across all wells).
EchoCsvResult generateEchoCsv({
  required Map<int, Map<String, String?>> plateAssignments,
  required Map<int, Map<String, WellConfig>> wellConfigs,
  required Map<int, String> plateNames,
  required Map<String, Slat> slats,
  required Map<String, Map<String, dynamic>> layerMap,
  bool normalizeVolumes = false,
  Map<String, Set<(int, int)>>? manualHandles,
}) {
  final List<List<dynamic>> outputRows = [];
  final List<List<dynamic>> manualOutputRows = [];
  final warnings = <String>[];

  // Track total volume per destination well: "plateName_plateDisplayNum:well" → totalNl
  // Manual handles do NOT contribute to wellTotals (excluded from normalization).
  final wellTotals = <String, double>{};
  // Track each well's group key for per-group normalization.
  final wellGroupKeys = <String, (double, double, double)>{};

  final sortedPlateKeys = plateAssignments.keys.toList()..sort();

  for (var plateIndex in sortedPlateKeys) {
    final plate = plateAssignments[plateIndex]!;
    final plateConfigs = wellConfigs[plateIndex] ?? {};
    final destPlateName = plateNames[plateIndex] ?? 'Plate';

    for (var well in generatePlateLayout96()) {
      final slatId = plate[well];
      if (slatId == null) continue;

      final base = baseSlatId(slatId);
      final slat = slats[base];
      if (slat == null) continue;

      final config = plateConfigs[well] ?? const WellConfig();
      final matPerHandle = config.materialPerHandle;
      final destKey = '${destPlateName}_$plateIndex:$well';
      wellGroupKeys[destKey] = (config.ratio, config.volume, config.scaffoldConc);
      final csvName = slatCsvName(slat, layerMap);
      final slatManual = manualHandles?[base];

      double wellTotal = 0;

      for (var (side, helix, handles) in [('h2', 2, slat.h2Handles), ('h5', 5, slat.h5Handles)]) {
        final sorted = handles.entries.toList()..sort((a, b) => a.key.compareTo(b.key));
        for (var entry in sorted) {
          final handleData = entry.value;
          final concentration = (handleData['concentration'] as num?)?.toDouble();
          final position = entry.key;
          final isManual = slatManual != null && slatManual.contains((helix, position));

          if (concentration == null || concentration <= 0) {
            if (isManual) {
              manualOutputRows.add([
                '${csvName}_${side}_staple_${entry.key}',
                '',
                '',
                well,
                '',
                destPlateName,
                '384PP_AQ_BP',
              ]);
            }
            continue;
          }

          final roundedVolume = echoRoundedVolumeNl(matPerHandle, concentration);

          final row = [
            '${csvName}_${side}_staple_${entry.key}',
            sanitizePlateMap(handleData['plate'] as String),
            handleData['well'],
            well,
            roundedVolume,
            destPlateName,
            '384PP_AQ_BP',
          ];

          if (isManual) {
            manualOutputRows.add(row);
          } else {
            wellTotal += roundedVolume;
            outputRows.add(row);
          }
        }
      }

      wellTotals[destKey] = (wellTotals[destKey] ?? 0) + wellTotal;
    }
  }

  // Check for wells exceeding 25000 nL
  final overflowWells = <String>[];
  for (var entry in wellTotals.entries) {
    if (entry.value > echoMaxWellVolumeNl) {
      overflowWells.add(entry.key.split(':').last);
    }
  }
  if (overflowWells.isNotEmpty) {
    final shown = overflowWells.take(5).join(', ');
    final extra = overflowWells.length > 5 ? ' and ${overflowWells.length - 5} more' : '';
    warnings.add('Wells $shown$extra exceed 25 \u00B5L total volume — contents may drip out when the Echo plate is inverted.');
  }

  // Normalize volumes with water plate compensation
  double? totalWaterNl;
  int? waterWellsUsed;

  if (normalizeVolumes && wellTotals.isNotEmpty) {
    // Compute max volume per group (wells with same ratio/volume/scaffoldConc).
    final groupMaxVolumes = <(double, double, double), double>{};
    for (var entry in wellTotals.entries) {
      final groupKey = wellGroupKeys[entry.key];
      if (groupKey == null) continue;
      final current = groupMaxVolumes[groupKey] ?? 0.0;
      if (entry.value > current) groupMaxVolumes[groupKey] = entry.value;
    }

    final waterPlateWells = generatePlateLayout384();
    var waterWellIndex = 0;
    double waterTotal = 0;

    for (var plateIndex in sortedPlateKeys) {
      final plate = plateAssignments[plateIndex]!;
      final destPlateName = plateNames[plateIndex] ?? 'Plate';

      for (var well in generatePlateLayout96()) {
        final slatId = plate[well];
        if (slatId == null) continue;

        final destKey = '${destPlateName}_$plateIndex:$well';
        final groupKey = wellGroupKeys[destKey];
        if (groupKey == null) continue;
        final groupMax = groupMaxVolumes[groupKey] ?? 0;
        final currentTotal = wellTotals[destKey] ?? 0;
        final deficit = groupMax - currentTotal;

        if (deficit > 0) {
          final roundedDeficit = (deficit / 25).ceil() * 25;
          final waterWell = waterPlateWells[waterWellIndex % waterPlateWells.length];
          waterWellIndex++;

          final base = baseSlatId(slatId);
          final waterSlat = slats[base];
          final waterCsvName = waterSlat != null ? slatCsvName(waterSlat, layerMap) : 'water';
          outputRows.add([
            '${waterCsvName}_volume_normalize',
            'WATER_PLATE',
            waterWell,
            well,
            roundedDeficit.toInt(),
            destPlateName,
            '384PP_AQ_BP',
          ]);
          waterTotal += roundedDeficit;
        }
      }
    }

    totalWaterNl = waterTotal;
    waterWellsUsed = waterWellIndex;
  }

  const header = ['Component', 'Source Plate Name', 'Source Well', 'Destination Well', 'Transfer Volume', 'Destination Plate Name', 'Source Plate Type'];

  final csvString = const ListToCsvConverter().convert([header, ...outputRows]);

  Uint8List? manualCsvBytes;
  if (manualOutputRows.isNotEmpty) {
    final manualCsvString = const ListToCsvConverter().convert([header, ...manualOutputRows]);
    manualCsvBytes = Uint8List.fromList(utf8.encode(manualCsvString));
  }

  return EchoCsvResult(
    csvBytes: Uint8List.fromList(utf8.encode(csvString)),
    manualCsvBytes: manualCsvBytes,
    warnings: warnings,
    totalWaterNl: totalWaterNl,
    waterWellsUsed: waterWellsUsed,
  );
}
