import 'dart:typed_data';
import 'package:excel/excel.dart';

// Custom exceptions for better error handling
class PlateParsingException extends Exception {
  final String message;
  PlateParsingException(this.message);
  @override
  String toString() => 'PlateParsingException: $message';
}

class PlateValidationException extends Exception {
  final String message;
  PlateValidationException(this.message);
  @override
  String toString() => 'PlateValidationException: $message';
}

// Configuration constants
class PlateConfig {
  static const String defaultSheetName = 'All Data';
  static const List<String> requiredColumns = ['name', 'well', 'sequence', 'concentration'];
  static const int defaultPlateSize = 384;
  static const Pattern validWellPattern = r'^[A-P]([1-9]|1[0-9]|2[0-4])$';
}

// Data models
class PlateEntry {
  final String name;
  final String well;
  final String sequence;
  final dynamic concentration;

  PlateEntry({
    required this.name,
    required this.well,
    required this.sequence,
    required this.concentration,
  });

  Map<String, dynamic> toJson() => {
    'name': name,
    'well': well,
    'sequence': sequence,
    'concentration': concentration,
  };
}

// Input validation service
class PlateValidator {
  static bool isValidWell(String well) {
    return RegExp(PlateConfig.validWellPattern).hasMatch(well);
  }

  static bool isValidSequence(String sequence) {
    return sequence.isNotEmpty && RegExp(r'^[ATCG]+$').hasMatch(sequence.toUpperCase());
  }

  static bool isValidConcentration(dynamic concentration) {
    if (concentration == null) return false;
    if (concentration is num) return concentration >= 0;
    if (concentration is String) {
      final parsed = double.tryParse(concentration);
      return parsed != null && parsed >= 0;
    }
    return false;
  }

  static void validatePlateEntry(PlateEntry entry) {
    if (entry.name.isEmpty) {
      throw PlateValidationException('Entry name cannot be empty');
    }

    if (!isValidWell(entry.well)) {
      throw PlateValidationException('Invalid well format: ${entry.well}');
    }

    if (!isValidSequence(entry.sequence)) {
      throw PlateValidationException('Invalid sequence: ${entry.sequence}');
    }

    if (!isValidConcentration(entry.concentration)) {
      throw PlateValidationException('Invalid concentration: ${entry.concentration}');
    }
  }
}

// File parsing service
class ExcelFileParser {
  static List<Map<String, dynamic>> parseExcelFile(
      Uint8List fileBytes, {
        String sheetName = PlateConfig.defaultSheetName,
      }) {
    try {
      final excel = Excel.decodeBytes(fileBytes);
      final sheet = excel.tables[sheetName];

      if (sheet == null) {
        throw PlateParsingException('Sheet "$sheetName" not found');
      }

      if (sheet.rows.isEmpty) {
        throw PlateParsingException('Sheet is empty');
      }

      final headers = _extractHeaders(sheet.rows.first);
      _validateHeaders(headers);

      return _parseDataRows(sheet.rows.skip(1), headers);
    } catch (e) {
      if (e is PlateParsingException) rethrow;
      throw PlateParsingException('Failed to parse Excel file: $e');
    }
  }

  static List<String> _extractHeaders(List<Data?> headerRow) {
    return headerRow
        .map((cell) => cell?.value?.toString().trim() ?? '')
        .toList();
  }

  static void _validateHeaders(List<String> headers) {
    for (final required in PlateConfig.requiredColumns) {
      if (!headers.contains(required)) {
        throw PlateParsingException('Missing required column: $required');
      }
    }
  }

  static List<Map<String, dynamic>> _parseDataRows(
      Iterable<List<Data?>> dataRows,
      List<String> headers,
      ) {
    final result = <Map<String, dynamic>>[];

    for (final (index, row) in dataRows.indexed) {
      try {
        final rowData = <String, dynamic>{};

        for (int i = 0; i < headers.length; i++) {
          final header = headers[i];
          final cell = i < row.length ? row[i] : null;
          rowData[header] = _extractCellValue(cell);
        }

        result.add(rowData);
      } catch (e) {
        throw PlateParsingException('Error parsing row ${index + 2}: $e');
      }
    }

    return result;
  }

  static dynamic _extractCellValue(Data? cell) {
    if (cell?.value == null) return null;

    final value = cell!.value!;
    return switch (value) {
      TextCellValue() => value.value.text?.trim() ?? '',
      IntCellValue() => value.value,
      DoubleCellValue() => value.value,
      BoolCellValue() => value.value,
      DateCellValue() => value.value,
      TimeCellValue() => value.value,
      DateTimeCellValue() => value.value,
      _ => throw PlateParsingException('Unsupported cell type: ${value.runtimeType}'),
    };
  }
}

// Improved plate class with single responsibility
class MicroPlate {
  final String name;
  final int plateSize;
  final Map<String, List<String>> _wells = {};
  final Map<String, String> _sequences = {};
  final Map<String, dynamic> _concentrations = {};

  MicroPlate(this.name, {this.plateSize = PlateConfig.defaultPlateSize});

  // Factory constructor for creating from parsed data
  factory MicroPlate.fromParsedData(
      String name,
      List<Map<String, dynamic>> rawData, {
        int plateSize = PlateConfig.defaultPlateSize,
      }) {
    final plate = MicroPlate(name, plateSize: plateSize);
    plate._processEntries(rawData);
    return plate;
  }

  void _processEntries(List<Map<String, dynamic>> rawData) {
    for (final row in rawData) {
      try {
        final entry = _createPlateEntry(row);
        PlateValidator.validatePlateEntry(entry);
        _addEntry(entry);
      } catch (e) {
        // Log error and continue processing other entries
        print('Warning: Skipping invalid entry - $e');
      }
    }
  }

  PlateEntry _createPlateEntry(Map<String, dynamic> row) {
    return PlateEntry(
      name: row['name']?.toString() ?? '',
      well: row['well']?.toString() ?? '',
      sequence: row['sequence']?.toString() ?? '',
      concentration: row['concentration'],
    );
  }

  void _addEntry(PlateEntry entry) {
    final key = _generateKey(entry.name);

    _wells.putIfAbsent(key, () => []).add(entry.well);
    _sequences[key] ??= entry.sequence;
    _concentrations[key] ??= entry.concentration;
  }

  String _generateKey(String name) {
    final parts = name.split('-');
    if (parts.length < 4) return name;

    final category = parts[0];
    final id = parts[1];
    final orientation = int.tryParse(parts[2].replaceAll(RegExp(r'[^0-9]'), '')) ?? 0;
    final position = int.tryParse(parts[3].split('_').lastOrNull ?? '') ?? 0;

    return '$category|$position|$orientation|$id';
  }

  // Public getters with null safety
  List<String> getWells(String key) => List.unmodifiable(_wells[key] ?? []);
  String getSequence(String key) => _sequences[key] ?? '';
  dynamic getConcentration(String key) => _concentrations[key];

  // Statistics
  int get entryCount => _sequences.length;
  int get wellCount => _wells.values.fold(0, (sum, wells) => sum + wells.length);
}

// Repository pattern for data management
class PlateRepository {
  final Map<String, MicroPlate> _plates = {};

  void addPlate(MicroPlate plate) {
    _plates[plate.name] = plate;
  }

  MicroPlate? getPlate(String name) => _plates[name];

  void removePlate(String name) {
    _plates.remove(name);
  }

  List<String> getPlateNames() => List.unmodifiable(_plates.keys);

  // Global search across all plates
  Map<String, dynamic> findEntryAcrossPlates(String key) {
    for (final plate in _plates.values) {
      final wells = plate.getWells(key);
      if (wells.isNotEmpty) {
        return {
          'plateName': plate.name,
          'wells': wells,
          'sequence': plate.getSequence(key),
          'concentration': plate.getConcentration(key),
        };
      }
    }
    return {};
  }

  // Memory cleanup
  void dispose() {
    _plates.clear();
  }
}

// Main service class following single responsibility principle
class MicroPlateService {
  final PlateRepository _repository = PlateRepository();

  Future<void> loadPlateFromFile(
      String plateName,
      Uint8List fileBytes, {
        String sheetName = PlateConfig.defaultSheetName,
      }) async {
    try {
      // Parse in isolate for heavy processing
      final rawData = await _parseFileInIsolate(fileBytes, sheetName);

      // Create and validate plate
      final plate = MicroPlate.fromParsedData(plateName, rawData);

      // Store in repository
      _repository.addPlate(plate);

    } catch (e) {
      throw PlateParsingException('Failed to load plate "$plateName": $e');
    }
  }

  Future<List<Map<String, dynamic>>> _parseFileInIsolate(
      Uint8List fileBytes,
      String sheetName,
      ) async {
    // TODO: Implement isolate-based parsing for large files
    return ExcelFileParser.parseExcelFile(fileBytes, sheetName: sheetName);
  }

  // Public API methods
  MicroPlate? getPlate(String name) => _repository.getPlate(name);
  List<String> getPlateNames() => _repository.getPlateNames();
  void removePlate(String name) => _repository.removePlate(name);

  Map<String, dynamic> findEntry(String key) =>
      _repository.findEntryAcrossPlates(key);

  void dispose() => _repository.dispose();
}