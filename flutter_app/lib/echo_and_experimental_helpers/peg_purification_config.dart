/// Configuration for PEG purification helper sheet generation.
class PegPurificationConfig {
  /// PEG concentration multiplier (2 or 3). Affects target Mg and PEG volume calculations.
  final int pegConcentration;

  const PegPurificationConfig({this.pegConcentration = 3});

  /// Serializes to key-value pairs for lab_metadata sheet storage.
  Map<String, String> toMap() => {
        'peg_concentration': pegConcentration.toString(),
      };

  /// Reconstructs from lab_metadata key-value pairs, falling back to defaults for missing keys.
  static PegPurificationConfig fromMap(Map<String, String> m) => PegPurificationConfig(
        pegConcentration: int.tryParse(m['peg_concentration'] ?? '') ?? 3,
      );

  PegPurificationConfig copyWith({int? pegConcentration}) {
    return PegPurificationConfig(pegConcentration: pegConcentration ?? this.pegConcentration);
  }
}
