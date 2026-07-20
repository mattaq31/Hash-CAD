// Fluorophore model for tagging assembly handles with fluorophore compatibility.

/// Allowed marker shapes for fluorophore indicators in the 2D view.
enum FluorophoreShape { square, dot, diamond, star }

/// Converts a shape enum to its string representation for serialization.
String fluorophoreShapeToString(FluorophoreShape shape) {
  return shape.name;
}

/// Parses a shape string back to the enum value.
FluorophoreShape fluorophoreShapeFromString(String value) {
  return FluorophoreShape.values.firstWhere(
    (s) => s.name == value,
    orElse: () => FluorophoreShape.dot,
  );
}

/// A fluorophore entry in the per-design library.
/// The name is used directly as the compatibility token for source plate lookup.
class Fluorophore {
  /// User-facing fluorophore name, also used as the plate compatibility token.
  final String name;

  /// Marker shape shown in the 2D schematic for handles using this fluorophore.
  final FluorophoreShape shape;

  /// Creates a fluorophore definition for the per-design fluorophore library.
  const Fluorophore({required this.name, required this.shape});

  /// Returns a copy of this fluorophore with updated fields.
  Fluorophore copyWith({String? name, FluorophoreShape? shape}) {
    return Fluorophore(
      name: name ?? this.name,
      shape: shape ?? this.shape,
    );
  }
}
