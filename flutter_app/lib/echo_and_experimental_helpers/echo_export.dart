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
  final List<String> warnings;
  final double? totalWaterNl;
  final int? waterWellsUsed;

  const EchoCsvResult({required this.csvBytes, this.warnings = const [], this.totalWaterNl, this.waterWellsUsed});
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
}) {
  final List<List<dynamic>> outputRows = [];
  final warnings = <String>[];

  // Track total volume per destination well: "plateName_plateDisplayNum:well" → totalNl
  final wellTotals = <String, double>{};

  final sortedPlateKeys = plateAssignments.keys.toList()..sort();

  for (var plateIndex in sortedPlateKeys) {
    final plate = plateAssignments[plateIndex]!;
    final plateConfigs = wellConfigs[plateIndex] ?? {};
    final destPlateName = plateNames[plateIndex] ?? 'Plate';

    // Iterate wells in plate order (A1, A2, ... H12)
    for (var well in generatePlateLayout96()) {
      final slatId = plate[well];
      if (slatId == null) continue;

      final base = baseSlatId(slatId);
      final slat = slats[base];
      if (slat == null) continue;

      final config = plateConfigs[well] ?? const WellConfig();
      final matPerHandle = config.materialPerHandle;
      final destKey = '${destPlateName}_$plateIndex:$well';
      final csvName = slatCsvName(slat, layerMap);

      double wellTotal = 0;

      // Process h2 handles then h5 handles
      for (var (side, handles) in [('h2', slat.h2Handles), ('h5', slat.h5Handles)]) {
        final sorted = handles.entries.toList()..sort((a, b) => a.key.compareTo(b.key));
        for (var entry in sorted) {
          final handleData = entry.value;
          final concentration = (handleData['concentration'] as num?)?.toDouble();
          if (concentration == null || concentration <= 0) continue;

          final roundedVolume = echoRoundedVolumeNl(matPerHandle, concentration);

          wellTotal += roundedVolume;
          outputRows.add([
            '${csvName}_${side}_staple_${entry.key}',
            sanitizePlateMap(handleData['plate'] as String),
            handleData['well'],
            well,
            roundedVolume,
            destPlateName,
            '384PP_AQ_BP',
          ]);
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
    final maxVolume = wellTotals.values.reduce((a, b) => a > b ? a : b);
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
        final currentTotal = wellTotals[destKey] ?? 0;
        final deficit = maxVolume - currentTotal;

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

  final csvString = const ListToCsvConverter().convert([
    ['Component', 'Source Plate Name', 'Source Well', 'Destination Well', 'Transfer Volume', 'Destination Plate Name', 'Source Plate Type'],
    ...outputRows,
  ]);

  return EchoCsvResult(
    csvBytes: Uint8List.fromList(utf8.encode(csvString)),
    warnings: warnings,
    totalWaterNl: totalWaterNl,
    waterWellsUsed: waterWellsUsed,
  );
}
