import 'package:flutter/material.dart';
import 'dart:math';

import '../crisscross_core/slats.dart';
import '../crisscross_core/cargo.dart';
import '../crisscross_core/seed.dart';
import '../crisscross_core/handle_plates.dart';

import 'slat_undo_stack.dart';

// Mixin imports
import 'design_state_mixins/design_state_core_mixin.dart';
import 'design_state_mixins/design_state_file_io_mixin.dart';
import 'design_state_mixins/design_state_layer_mixin.dart';
import 'design_state_mixins/design_state_slat_mixin.dart';
import 'design_state_mixins/design_state_handle_mixin.dart';
import 'design_state_mixins/design_state_slat_color_mixin.dart';
import 'design_state_mixins/design_state_phantom_mixin.dart';
import 'design_state_mixins/design_state_cargo_mixin.dart';
import 'design_state_mixins/design_state_seed_mixin.dart';
import 'design_state_mixins/design_state_plate_mixin.dart';
import 'design_state_mixins/design_state_handle_link_mixin.dart';

/// Finds the first free integer key in a map
int firstFreeKey(Map<int, String> map, {int start = 1}) {
  if (map.isEmpty) return start;
  final keys = map.keys.toSet();
  var k = start;
  while (keys.contains(k)) {
    k++;
  }
  return k;
}

/// Useful function to generate the next capital letter in the alphabet for slat identifier keys
String nextCapitalLetter(String current) {
  int len = current.length;
  List<int> chars = current
      .split('')
      .map((c) => c.codeUnitAt(0) - 'A'.codeUnitAt(0))
      .toList();

  for (int i = len - 1; i >= 0; i--) {
    if (chars[i] < 25) {
      chars[i]++;
      return String.fromCharCodes(chars.map((e) => 'A'.codeUnitAt(0) + e));
    } else {
      chars[i] = 0;
    }
  }
  // If all characters are 'Z', add 'A' to the beginning.
  return 'A${String.fromCharCodes(chars.map((e) => 'A'.codeUnitAt(0) + e))}';
}

// encapsulates all info necessary to describe a transient set of moving slats or cargo
// TODO: should also add ability to visualize moving slats and cargo too...
class HoverPreview {
  final String kind; // 'Slat-Add' | 'Slat-Move' | 'Cargo-Add' | 'Cargo-Move'
  final bool isValid;

  // For slats: a list of 32-pt paths (one per slat in multi-add), in REAL space
  final List<List<Offset>> slatPaths;

  // For cargo/seed: points in REAL space (e.g., handle locations)
  final List<Offset> cargoOrSeedPoints;

  const HoverPreview({
    required this.kind,
    required this.isValid,
    this.slatPaths = const [],
    this.cargoOrSeedPoints = const [],
  });
}

/// State management for the design of the current megastructure
/// Go to the individual mixin files for the bulk of the code
class DesignState extends ChangeNotifier
    with
        DesignStateCoreMixin,
        DesignStateFileIOMixin,
        DesignStateLayerMixin,
        DesignStateSlatMixin,
        DesignStateHandleMixin,
        DesignStateSlatColorMixin,
        DesignStatePhantomMixin,
        DesignStateCargoMixin,
        DesignStateSeedMixin,
        DesignStatePlateMixin,
        DesignStateHandleLinkMixin {
  // Grid and coordinate system constants
  @override
  final double gridSize = 10.0; // do not change
  @override
  late final double y60Jump = gridSize / 2;
  @override
  late final double x60Jump = sqrt(pow(gridSize, 2) - pow(y60Jump, 2));
  @override
  String gridMode = '60';
  @override
  bool standardTilt = true; // just a toggle between the two different tilt types

  @override
  HoverPreview? hoverPreview; // current transient set of slats

  Map<(String, int), Offset> slatDirectionGenerators = {
    ('90', 90): Offset(1, 0),
    ('90', 180): Offset(0, 1),
    ('60', 180): Offset(0, 2),
    ('60', 120): Offset(1, 1),
    ('60', 240): Offset(-1, 1),
  };

  @override
  Map<(String, int), Offset> multiSlatGenerators = {
    ('90', 90): Offset(0, 1),
    ('90', 180): Offset(1, 0),
    ('60', 180): Offset(1, 1),
    ('60', 120): Offset(0, 2),
    ('60', 240): Offset(0, 2),
  };
  @override
  Map<(String, int), Offset> multiSlatGeneratorsAlternate = {
    ('90', 90): Offset(0, -1),
    ('90', 180): Offset(-1, 0),
    ('60', 180): Offset(-1, 1),
    ('60', 120): Offset(1, -1),
    ('60', 240): Offset(-1, -1),
  };

  // trialling a new system for slat addition using a full 360deg rotation and no flips
  Map<(String, int), Offset> multiSlatGeneratorsDB = {
    ('90', 90): Offset(0, 1),
    ('90', 180): Offset(-1, 0),
    ('90', 270): Offset(0, -1),
    ('90', 0): Offset(1, 0),
    ('60', 180): Offset(-1, -1),
    ('60', 120): Offset(-1, 1),
    ('60', 240): Offset(0, -2),
    ('60', 300): Offset(1, -1),
    ('60', 0): Offset(1, 1),
    ('60', 60): Offset(0, 2),
  };

  Map<(String, int), Offset> slatDirectionGeneratorsDB = {
    ('90', 90): Offset(1, 0),
    ('90', 180): Offset(0, 1),
    ('90', 270): Offset(-1, 0),
    ('90', 0): Offset(0, -1),
    ('60', 180): Offset(0, 2),
    ('60', 120): Offset(1, 1),
    ('60', 240): Offset(-1, 1),
    ('60', 300): Offset(-1, -1),
    ('60', 0): Offset(0, -2),
    ('60', 60): Offset(1, -1),
  };

  // when checking seed occupancy, use these values to extend beyond the standard hover position
  Map<String, int> seedOccupancyDimensions = {'width': 5, 'height': 16};

  // good starter colours for distinguishing layers quickly, but user can adjust
  @override
  List<String> colorPalette = [
    '#ebac23',
    '#b80058',
    '#008cf9',
    '#006e00',
    '#00bbad',
    '#d163e6',
    '#b24602',
    '#ff9287',
    '#5954d6',
    '#00c6f8',
    '#878500',
    '#00a76c',
    '#bdbdbd'
  ];

  // main properties for each design layer
  @override
  Map<String, Map<String, dynamic>> layerMap = {
    'A': {
      "direction": 120, // slat default direction
      "DBDirection": 120, // temporary alternative drawing system
      'order': 0, // draw order - has to be updated when layers are moved
      'top_helix': 'H5',
      'bottom_helix': 'H2',
      'next_slat_id': 1,
      'slat_count': 0,
      "color": Color(int.parse('0xFFebac23')), // default slat color
      "hidden": false
    },
    'B': {
      "direction": 240,
      "DBDirection": 240, // temporary alternative drawing system
      'next_slat_id': 1,
      'slat_count': 0,
      'top_helix': 'H5',
      'bottom_helix': 'H2',
      'order': 1,
      "color": Color(int.parse('0xFFb80058')),
      "hidden": false
    },
  };

  @override
  SlatUndoStack undoStack = SlatUndoStack();

  // main slat container
  @override
  Map<String, Slat> slats = {};

  // default values for new layers and slats
  @override
  String selectedLayerKey = 'A';
  @override
  List<String> selectedSlats = []; // to highlight on grid painter
  @override
  String nextLayerKey = 'C';
  @override
  String nextSeedID = 'A';
  @override
  int nextColorIndex = 2;
  @override
  int slatAddCount = 1;
  @override
  String slatAddDirection = 'down';
  @override
  Color uniqueSlatColor = Colors.blue;
  @override
  int currentMaxValency = 0;
  @override
  double currentEffValency = 0.0;
  @override
  bool hammingValueValid = true;
  @override
  int cargoAddCount = 1;
  @override
  String? cargoAdditionType;
  @override
  String slatAdditionType = 'tube';
  @override
  List<Offset> selectedHandlePositions = [];
  @override
  String designName = 'New Megastructure';

  @override
  Map<String, Map<Offset, String>> occupiedCargoPoints = {};
  @override
  Map<(String, String, Offset), Seed> seedRoster = {};
  @override
  Map<String, List<Color>> uniqueSlatColorsByLayer = {};

  @override
  bool currentlyLoadingDesign = false;
  @override
  bool currentlyComputingHamming = false;

  // useful to keep track of occupancy and speed up grid checks
  @override
  Map<String, Map<Offset, String>> occupiedGridPoints = {};
  // used to keep track of phantom slats
  @override
  Map<String, Map<int, String>> phantomMap = {};

  // used to keep track of assembly handle links
  @override
  HandleLinkManager assemblyLinkManager = HandleLinkManager();

  @override
  Map<String, Cargo> cargoPalette = {
    'SEED': Cargo(name: 'SEED', shortName: 'S', color: Color.fromARGB(255, 255, 0, 0)),
  };

  @override
  PlateLibrary plateStack = PlateLibrary();

  /// updates the grid type (60 or 90) - this method stays in the main class
  /// because it needs to call clearAll which is in FileIOMixin
  @override
  void setGridMode(String value) {
    gridMode = value;
    clearAll();
    undoStack = SlatUndoStack();
    notifyListeners();
  }
}
