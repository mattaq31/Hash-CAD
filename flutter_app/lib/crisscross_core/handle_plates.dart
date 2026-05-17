/// Handle plate library for DNA source plate mapping and lookup.

import 'dart:typed_data';
import 'package:excel/excel.dart';
import 'cargo.dart';

const String defaultPlateCompatibility = '__default__';

const Map<String, int> _plateCategoryOrder = {
  'FLAT': 0,
  'ASSEMBLY_HANDLE': 1,
  'ASSEMBLY_ANTIHANDLE': 2,
  'SEED': 3,
  'CARGO': 4,
};

String sanitizePlateMap(String name) {
  final parts = name.split('_');
  return parts.length >= 2 ? '${parts[0]}_${parts[1]}' : name;
}

/// Normalizes optional plate compatibility text into a canonical lookup token.
String normalizePlateCompatibility(dynamic compatibility) {
  final text = compatibility?.toString().trim().toLowerCase() ?? '';
  return text.isEmpty ? defaultPlateCompatibility : text;
}

/// Returns whether [compatibility] points to the default tube-compatible staple.
bool isDefaultPlateCompatibility(String compatibility) => compatibility == defaultPlateCompatibility;

/// Human-readable label for a normalized compatibility token.
String plateCompatibilityLabel(String compatibility) {
  return isDefaultPlateCompatibility(compatibility) ? 'Default / tube-compatible' : compatibility;
}

dynamic _readRowValue(Map<String, dynamic> row, String key) {
  for (final entry in row.entries) {
    if (entry.key.toString().trim().toLowerCase() == key.toLowerCase()) {
      return entry.value;
    }
  }
  return null;
}

String _makePlateBaseKey(String category, int pos, int side, dynamic id) {
  return '$category|$pos|$side|$id';
}

String _makePlateVariantKey(String category, int pos, int side, dynamic id, String compatibility) {
  return '${_makePlateBaseKey(category, pos, side, id)}|$compatibility';
}

typedef _PlateKeyParts = ({String category, int position, int side, String id, String compatibility});

_PlateKeyParts _parsePlateVariantKey(String key) {
  final parts = key.split('|');
  if (parts.length < 4) {
    throw FormatException('Invalid plate key: $key');
  }
  return (
    category: parts[0],
    position: int.tryParse(parts[1]) ?? 0,
    side: int.tryParse(parts[2]) ?? 0,
    id: parts[3],
    compatibility: parts.length >= 5 ? parts[4] : defaultPlateCompatibility,
  );
}

/// Summary record for a unique plate entry shown in the detailed plate dialog.
class PlateDisplayEntry {
  final String category;
  final String id;
  final String compatibility;

  const PlateDisplayEntry({required this.category, required this.id, required this.compatibility});

  bool get isDefaultCompatibility => isDefaultPlateCompatibility(compatibility);
  String get compatibilityLabel => plateCompatibilityLabel(compatibility);
}

/// Reads an Excel file and returns a list of maps (one per row),
/// simulating what pandas would do with read_excel.
List<Map<String, dynamic>> readDnaPlateMapping(Uint8List fileBytes) {

  final excel = Excel.decodeBytes(fileBytes);
  final sheet = excel.tables['All Data']!;

  final List<Map<String, dynamic>> rows = [];

  final headers = sheet.rows.first.map((e) => e?.value?.toString().trim()).toList();

  for (var i = 1; i < sheet.rows.length; i++) {
    final row = sheet.rows[i];
    final rowData = <String, dynamic>{};

    for (int j = 0; j < headers.length; j++) {
      final key = headers[j];
      final cell = j < row.length ? row[j] : null;

      if (cell == null || cell.value == null) {
        rowData[key ?? ''] = null;
      } else {
        final value = cell.value;
        if (value is TextCellValue) {
          rowData[key ?? ''] = value.value.text ?? '';
        } else if (value is IntCellValue) {
          rowData[key ?? ''] = value.value;
        } else if (value is DoubleCellValue) {
          rowData[key ?? ''] = value.value;
        } else {
          rowData[key ?? ''] = value.toString();
        }
      }
    }
    rows.add(rowData);
  }
  return rows;
}


class PlateLibrary {
  final Map<String, HashCadPlate> plates = {};
  final Map<String, String> globalSequences = {};
  final Map<String, String> globalWells = {};
  final Map<String, dynamic> globalConcentrations = {};
  final Map<String, String> globalPlates = {};
  final Map<String, Map<String, int>> globalCompatibilityCountsByBase = {};

  void readPlates(List<Uint8List> plateFiles, List<String> plateNames) {
    for (int i = 0; i < plateFiles.length; i++) {
      final name = plateNames[i];
      if (plates.containsKey(name)) {
        removePlate(name);
      }
      final plate = HashCadPlate(plateFiles[i], name);
      plates[name] = plate;

      _registerPlateGlobals(plate, name);
    }
  }

  /// Reconstructs the plate library from raw row data (as stored in design files).
  void readPlatesFromRawData(Map<String, List<List<dynamic>>> rawDataMap) {
    for (var entry in rawDataMap.entries) {
      final name = entry.key;
      final rows = entry.value;
      if (rows.isEmpty) continue;
      if (plates.containsKey(name)) {
        removePlate(name);
      }

      // Convert raw rows (with header) back to List<Map<String, dynamic>>
      final headers = rows.first.map((e) => e.toString()).toList();
      final parsedRows = <Map<String, dynamic>>[];
      for (var i = 1; i < rows.length; i++) {
        final rowData = <String, dynamic>{};
        for (var j = 0; j < headers.length && j < rows[i].length; j++) {
          rowData[headers[j]] = rows[i][j];
        }
        parsedRows.add(rowData);
      }

      final plate = HashCadPlate.fromParsedData(parsedRows, name);
      plates[name] = plate;
      _registerPlateGlobals(plate, name);
    }
  }

  void _registerPlateGlobals(HashCadPlate plate, String name) {
    for (final key in plate.sequences.keys) {
      globalSequences[key] = plate.getSequence(key);
      globalConcentrations[key] = plate.getConcentration(key);
      globalWells[key] = plate.getWell(key);
      globalPlates[key] = name;
      final parts = _parsePlateVariantKey(key);
      final baseKey = _makePlateBaseKey(parts.category, parts.position, parts.side, parts.id);
      globalCompatibilityCountsByBase.putIfAbsent(baseKey, () => <String, int>{}).update(parts.compatibility, (count) => count + 1, ifAbsent: () => 1);
    }
  }

  // Public methods using full key
  String getSequence(String key) => globalSequences[key] ?? '';
  String getWell(String key) => globalWells[key] ?? '';
  dynamic getConcentration(String key) => globalConcentrations[key];
  String getPlateName(String key) => globalPlates[key] ?? '';

  bool contains(String category, int pos, int side, dynamic id, {String? compatibility}) {
    return globalSequences.containsKey(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));
  }
  List<String> listPlateNames() => plates.keys.toList();

  // Overloads using components
  String getSequenceByComponents(String category, int pos, int side, dynamic id, {String? compatibility}) =>
      getSequence(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));

  String getWellByComponents(String category, int pos, int side, dynamic id, {String? compatibility}) =>
      getWell(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));

  dynamic getConcentrationByComponents(String category, int pos, int side, dynamic id, {String? compatibility}) =>
      getConcentration(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));

  String getPlateNameByComponents(String category, int pos, int side, dynamic id, {String? compatibility}) =>
      getPlateName(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));

  /// Returns the set of compatibility tokens available for a given base position.
  Set<String> availableCompatibilities(String category, int pos, int side, dynamic id) {
    final baseKey = _makePlateBaseKey(category, pos, side, id);
    return Set<String>.from(globalCompatibilityCountsByBase[baseKey]?.keys ?? const <String>{});
  }

  Map<String, dynamic> getOligoData(String category, int pos, int side, dynamic id, {String? compatibility}) {
    final normalizedCompatibility = normalizePlateCompatibility(compatibility);
    final key = _makePlateVariantKey(category, pos, side, id, normalizedCompatibility);
    return {
      'well': globalWells[key] ?? '',
      'sequence': globalSequences[key] ?? '',
      'concentration': globalConcentrations[key] ?? 0,
      'plateName': globalPlates[key] ?? '',
      'compatibility': normalizedCompatibility,
    };
  }

  // Plate deletion
  void removePlate(String name) {
    final plate = plates.remove(name);
    if (plate == null) return;

    for (final key in plate.sequences.keys) {
      globalSequences.remove(key);
      globalConcentrations.remove(key);
      globalWells.remove(key);
      globalPlates.remove(key);

      final parts = _parsePlateVariantKey(key);
      final baseKey = _makePlateBaseKey(parts.category, parts.position, parts.side, parts.id);
      final compatibilities = globalCompatibilityCountsByBase[baseKey];
      if (compatibilities != null) {
        final updatedCount = (compatibilities[parts.compatibility] ?? 0) - 1;
        if (updatedCount <= 0) {
          compatibilities.remove(parts.compatibility);
        } else {
          compatibilities[parts.compatibility] = updatedCount;
        }
      }
      if (compatibilities != null && compatibilities.isEmpty) {
        globalCompatibilityCountsByBase.remove(baseKey);
      }
    }
  }

  void clear() {
    plates.clear();
    globalSequences.clear();
    globalWells.clear();
    globalConcentrations.clear();
    globalPlates.clear();
    globalCompatibilityCountsByBase.clear();
  }

  /// Returns unique cargo IDs found across all loaded plates.
  Set<String> get allCargoIds {
    final ids = <String>{};
    for (final key in globalSequences.keys) {
      final parts = _parsePlateVariantKey(key);
      if (parts.category == 'CARGO') {
        ids.add(parts.id);
      }
    }
    return ids;
  }
}

/// Adds any cargo IDs found in [plateLibrary] that are missing from [cargoPalette].
void syncCargoFromPlates(PlateLibrary plateLibrary, Map<String, Cargo> cargoPalette) {
  for (final cargoId in plateLibrary.allCargoIds) {
    if (!cargoPalette.containsKey(cargoId)) {
      final colorIndex = (cargoPalette.length - 1) % qualitativeCargoColors.length;
      cargoPalette[cargoId] = Cargo(
        name: cargoId,
        shortName: generateShortName(cargoId),
        color: qualitativeCargoColors[colorIndex],
      );
    }
  }
}

class HashCadPlate {
  final Map<String, List<String>> wells = {};
  final Map<String, String> sequences = {};
  final Map<String, dynamic> concentrations = {};
  final Map<String, Set<String>> compatibilitiesByBase = {};
  String plateName;

  /// Raw row data for re-export into design files.
  final List<String> rawHeaders = [];
  final List<List<dynamic>> rawData = [];

  HashCadPlate(Uint8List plateData, this.plateName, {int plateSize = 384}) {
    List<Map<String, dynamic>> rawPlateData = readDnaPlateMapping(plateData);
    _storeRawData(rawPlateData);
    identifyWellsAndSequences(rawPlateData);
  }

  /// Creates a HashCadPlate from pre-parsed row data (e.g. from a design file).
  HashCadPlate.fromParsedData(List<Map<String, dynamic>> parsedData, this.plateName) {
    _storeRawData(parsedData);
    identifyWellsAndSequences(parsedData);
  }

  void _storeRawData(List<Map<String, dynamic>> parsedData) {
    rawHeaders.clear();
    rawData.clear();

    if (parsedData.isEmpty) {
      rawHeaders.addAll(['well', 'name', 'sequence', 'concentration']);
      return;
    }

    rawHeaders.addAll(parsedData.first.keys.map((key) => key.toString()));
    for (var row in parsedData) {
      rawData.add(rawHeaders.map((header) => row[header]).toList());
    }
  }

  /// Returns raw data in the standard "All Data" format (header + data rows).
  List<List<dynamic>> exportToAllDataFormat() {
    final headers = rawHeaders.isEmpty ? ['well', 'name', 'sequence', 'concentration'] : rawHeaders;
    final result = <List<dynamic>>[
      List<dynamic>.from(headers),
      ...rawData.map((row) {
        if (row.length == headers.length) {
          return List<dynamic>.from(row);
        }
        final padded = List<dynamic>.filled(headers.length, null);
        for (var i = 0; i < headers.length && i < row.length; i++) {
          padded[i] = row[i];
        }
        return padded;
      }),
    ];
    return result;
  }

  void identifyWellsAndSequences(List<Map<String, dynamic>> rawPlateData) {
    String? assemblyHandleStatementMade;

    for (final row in rawPlateData) {
      final pattern = _readRowValue(row, 'name');
      if (pattern == 'NON-SLAT OLIGO' || pattern is! String) {
        continue;
      }

      final well = (_readRowValue(row, 'well') ?? '').toString();
      final seq = (_readRowValue(row, 'sequence') ?? '').toString();
      final conc = _readRowValue(row, 'concentration') ?? 0;
      final compatibility = normalizePlateCompatibility(_readRowValue(row, 'compatibility'));

      final parts = pattern.split('-');
      if (parts.length != 4) continue;

      String category = parts[0];
      final id = parts[1];
      final orientation = int.tryParse(parts[2].replaceAll(RegExp(r'[^0-9]'), '')) ?? 0;
      final position = int.tryParse(parts[3].split('_')[1]) ?? 0;

      if (category.contains('ASSEMBLY')) {
        final version = category.split('_').last;
        category = category.split('_v').first;

        if (assemblyHandleStatementMade == null) {
          assemblyHandleStatementMade = version;
        } else if (assemblyHandleStatementMade != version) {
          throw Exception(
            'Assembly handle library version mismatch: $assemblyHandleStatementMade vs $version',
          );
        }
      }
      final baseKey = _makePlateBaseKey(category, position, orientation, id);
      final variantKey = _makePlateVariantKey(category, position, orientation, id, compatibility);

      compatibilitiesByBase.putIfAbsent(baseKey, () => <String>{}).add(compatibility);
      wells.putIfAbsent(variantKey, () => []).add(well);
      sequences[variantKey] ??= seq;
      concentrations[variantKey] ??= conc;
    }
  }

  String getSequence(String key) {
    return sequences[key] ?? '';
  }

  String getWell(String key) {
    final wellList = wells[key] ?? [];
    return wellList.length > 1 ? '{${wellList.join(';')}}' : (wellList.isNotEmpty ? wellList.first : '');
  }

  dynamic getConcentration(String key) {
    return concentrations[key];
  }

  bool contains(String category, int pos, int side, dynamic id, {String? compatibility}) {
    return sequences.containsKey(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));
  }

  // Overloads using components
  String getSequenceByComponents(String category, int pos, int side, dynamic id, {String? compatibility}) =>
      getSequence(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));

  String getWellByComponents(String category, int pos, int side, dynamic id, {String? compatibility}) =>
      getWell(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));

  dynamic getConcentrationByComponents(String category, int pos, int side, dynamic id, {String? compatibility}) =>
      getConcentration(_makePlateVariantKey(category, pos, side, id, normalizePlateCompatibility(compatibility)));

  /// Returns the set of compatibility tokens available for a given base position on this plate.
  Set<String> availableCompatibilities(String category, int pos, int side, dynamic id) {
    final baseKey = _makePlateBaseKey(category, pos, side, id);
    return Set<String>.from(compatibilitiesByBase[baseKey] ?? const <String>{});
  }

  int countCategory(String category) {
    return sequences.keys.where((k) => k.startsWith('$category|')).length;
  }

  int countID(String id) {
    return sequences.keys.where((key) => _parsePlateVariantKey(key).id == id).length;
  }

  String getCategoryFromID(String id) {
    final key = sequences.keys.firstWhere((entry) => _parsePlateVariantKey(entry).id == id, orElse: () => '');
    if (key.isEmpty) throw Exception('ID not found: $id');
    return _parsePlateVariantKey(key).category;
  }

  int countDisplayEntryPositions(PlateDisplayEntry entry) {
    return sequences.keys.where((key) {
      final parts = _parsePlateVariantKey(key);
      return parts.category == entry.category && parts.id == entry.id && parts.compatibility == entry.compatibility;
    }).length;
  }

  List<PlateDisplayEntry> get displayEntries {
    final displayMap = <String, PlateDisplayEntry>{};

    for (final key in sequences.keys) {
      final parts = _parsePlateVariantKey(key);
      final displayKey = '${parts.category}|${parts.id}|${parts.compatibility}';
      displayMap.putIfAbsent(displayKey, () => PlateDisplayEntry(category: parts.category, id: parts.id, compatibility: parts.compatibility));
    }

    final entries = displayMap.values.toList();
    entries.sort((a, b) {
      final categoryComparison = (_plateCategoryOrder[a.category] ?? 99).compareTo(_plateCategoryOrder[b.category] ?? 99);
      if (categoryComparison != 0) return categoryComparison;

      final aIdNumeric = int.tryParse(a.id);
      final bIdNumeric = int.tryParse(b.id);
      if (aIdNumeric != null && bIdNumeric != null && aIdNumeric != bIdNumeric) {
        return aIdNumeric.compareTo(bIdNumeric);
      }

      final idComparison = a.id.compareTo(b.id);
      if (idComparison != 0) return idComparison;

      if (a.isDefaultCompatibility != b.isDefaultCompatibility) {
        return a.isDefaultCompatibility ? -1 : 1;
      }

      return a.compatibility.compareTo(b.compatibility);
    });
    return entries;
  }

  List<String> get uniqueIds => sequences.keys.map((key) => _parsePlateVariantKey(key).id).toSet().toList();
}
