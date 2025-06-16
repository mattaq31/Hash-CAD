import 'dart:typed_data';
import 'package:excel/excel.dart';


String sanitizePlateMap(String name) {
  final parts = name.split('_');
  return parts.length >= 2 ? '${parts[0]}_${parts[1]}' : name;
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

      if (cell == null){
        rowData[key ?? ''] =  null;
      }
      else{
        final value = cell.value;
        if (value is TextCellValue) {
          rowData[key ?? ''] = value.value.text ?? '';
        } else if (value is IntCellValue) {
          rowData[key ?? ''] = value.value;
        }
        else if (value is DoubleCellValue) {
          rowData[key ?? ''] = value.value;
        }
        else {
          throw Exception('Unsupported cell type: ${value.runtimeType}');
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

  void readPlates(List<Uint8List> plateFiles, List<String> plateNames) {
    for (int i = 0; i < plateFiles.length; i++) {
      final name = plateNames[i];
      final plate = HashCadPlate(plateFiles[i], name);
      plates[name] = plate;

      for (final key in plate.sequences.keys) {
        globalSequences[key] = plate.getSequence(key);
        globalConcentrations[key] = plate.getConcentration(key);
        globalWells[key] = plate.getWell(key);
      }
    }
  }

  String _makeKey(String category, int pos, int side, dynamic id) {
    return '$category|$pos|$side|$id';
  }

  // Public methods using full key
  String getSequence(String key) => globalSequences[key] ?? '';
  String getWell(String key) => globalWells[key] ?? '';
  dynamic getConcentration(String key) => globalConcentrations[key];

  bool contains(String category, int pos, int side, dynamic id) {
    return globalSequences.containsKey(_makeKey(category, pos, side, id));
  }
  List<String> listPlateNames() => plates.keys.toList();

  // Overloads using components
  String getSequenceByComponents(String category, int pos, int side, dynamic id) =>
      getSequence(_makeKey(category, pos, side, id));

  String getWellByComponents(String category, int pos, int side, dynamic id) =>
      getWell(_makeKey(category, pos, side, id));

  dynamic getConcentrationByComponents(String category, int pos, int side, dynamic id) =>
      getConcentration(_makeKey(category, pos, side, id));

  Map<String, dynamic> getOligoData(String category, int pos, int side, dynamic id) {
    final key = _makeKey(category, pos, side, id);
    return {
      'well': globalWells[key] ?? '',
      'sequence': globalSequences[key] ?? '',
      'concentration': globalConcentrations[key],
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
    }
  }

  void clear(){
    plates.clear();
    globalSequences.clear();
    globalWells.clear();
    globalConcentrations.clear();
  }

}

class HashCadPlate {
  final Map<String, List<String>> wells = {};
  final Map<String, String> sequences = {};
  final Map<String, dynamic> concentrations = {};
  String plateName;

  HashCadPlate(Uint8List plateData, this.plateName, {int plateSize = 384})  {

    List<Map<String, dynamic>> rawPlateData = readDnaPlateMapping(plateData);
    identifyWellsAndSequences(rawPlateData);
  }

  void identifyWellsAndSequences(List<Map<String, dynamic>> rawPlateData) {
    String? assemblyHandleStatementMade;

    for (final row in rawPlateData) {
      final pattern = row['name'];
      if (pattern == 'NON-SLAT OLIGO' || pattern is! String) {
        continue;
      }

      final well = row['well'] ?? '';
      final seq = row['sequence'] ?? '';
      final conc = row['concentration'] ?? 0;

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
      final key = _makeKey(category, position, orientation, id);
      wells.putIfAbsent(key, () => []).add(well);
      sequences[key] ??= seq;
      concentrations[key] ??= conc;
    }
  }

  String _makeKey(String category, int pos, int side, dynamic id) {
    return '$category|$pos|$side|$id';
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

  bool contains(String category, int pos, int side, dynamic id) {
    return sequences.containsKey(_makeKey(category, pos, side, id));
  }

  // Overloads using components
  String getSequenceByComponents(String category, int pos, int side, dynamic id) =>
      getSequence(_makeKey(category, pos, side, id));

  String getWellByComponents(String category, int pos, int side, dynamic id) =>
      getWell(_makeKey(category, pos, side, id));

  dynamic getConcentrationByComponents(String category, int pos, int side, dynamic id) =>
      getConcentration(_makeKey(category, pos, side, id));

  int countCategory(String category) {
    return sequences.keys.where((k) => k.startsWith('$category|')).length;
  }
  int countID(String id) {
    return sequences.keys.where((k) => k.endsWith('|$id')).length;
  }

  String getCategoryFromID(String id) {
    final key = sequences.keys.firstWhere((k) => k.endsWith('|$id'), orElse: () => '');
    if (key.isEmpty) throw Exception('ID not found: $id');
    return key.split('|')[0];
  }

  List<String> get uniqueIds => sequences.keys.map((w) => w.split('|').last).toSet().toList();
}

