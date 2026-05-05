/// Immutable result of parsing a #-CAD design Excel file.
import 'package:flutter/material.dart';

import '../../crisscross_core/cargo.dart';
import '../../crisscross_core/seed.dart';
import '../../crisscross_core/slats.dart';
import '../design_state_mixins/design_state_handle_link_mixin.dart';
import '../design_state_mixins/design_state_grouping_mixin.dart';

/// Contains all data extracted from a design file by [parseDesignInIsolate].
///
/// If parsing fails, [errorCode] is non-empty and the remaining fields may be
/// partially populated (up to the point of failure).
class ParsedDesignResult {
  final Map<String, Slat> slats;
  final Map<String, Map<String, dynamic>> layerMap;
  final String gridMode;
  final Map<String, Cargo> cargoPalette;
  final Map<(String, String, Offset), Seed> seedRoster;
  final Map<String, Map<int, String>> phantomMap;
  final HandleLinkManager linkManager;
  final String errorCode;
  final Map<String, List<List<dynamic>>>? echoPlateData;
  final Map<String, List<List<dynamic>>>? inputPlateData;
  final Map<String, String>? labMetadata;
  final Map<String, GroupConfiguration> groupConfigurations;

  const ParsedDesignResult({
    required this.slats,
    required this.layerMap,
    required this.gridMode,
    required this.cargoPalette,
    required this.seedRoster,
    required this.phantomMap,
    required this.linkManager,
    required this.errorCode,
    this.echoPlateData,
    this.inputPlateData,
    this.labMetadata,
    this.groupConfigurations = const {},
  });
}
