import 'package:flutter/material.dart';
import 'package:hash_cad/app_management/shared_app_state.dart';

import 'test_helpers.dart';

/// Factory for creating DesignState instances in a testable configuration.
///
/// The main challenge with testing DesignState is that:
/// 1. It uses multiple mixins that have interdependencies
/// 2. Some methods call notifyListeners() and saveUndoState()
/// 3. Certain operations require BuildContext (which we'll skip for unit tests)
///
/// This factory creates a fresh DesignState with isolated state for each test.
class DesignStateTestFactory {
  /// Creates a fresh DesignState for testing.
  ///
  /// The state is initialized with default values:
  /// - Two layers: 'A' and 'B'
  /// - Empty slats map
  /// - Empty occupancy maps
  static DesignState create() {
    return DesignState();
  }

  /// Creates a DesignState with pre-populated slats for testing deletion.
  ///
  /// Adds [slatCount] slats to layer 'A' at specified coordinates.
  /// Each slat is spaced [spacing] units apart vertically.
  static DesignState createWithSlats({
    required int slatCount,
    Offset startOrigin = const Offset(0, 0),
    int spacing = 20,
    String layer = 'A',
  }) {
    final state = DesignState();

    final origins = <Offset>[];
    for (int i = 0; i < slatCount; i++) {
      origins.add(Offset(startOrigin.dx, startOrigin.dy + (i * spacing)));
    }

    final coordinates = buildSlatCoordinatesMap(origins);
    state.addSlats(layer, coordinates);
    return state;
  }

  /// Creates a DesignState with slats on multiple layers.
  static DesignState createWithMultiLayerSlats({
    Map<String, int> slatsPerLayer = const {'A': 1, 'B': 1},
    int spacing = 20,
  }) {
    final state = DesignState();

    for (var entry in slatsPerLayer.entries) {
      final layer = entry.key;
      final count = entry.value;

      final origins = <Offset>[];
      for (int i = 0; i < count; i++) {
        origins.add(Offset(0, i * spacing.toDouble()));
      }

      final coordinates = buildSlatCoordinatesMap(origins);
      state.addSlats(layer, coordinates);
    }

    return state;
  }
}
