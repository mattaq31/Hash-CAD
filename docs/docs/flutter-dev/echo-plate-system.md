# Echo Plate System

The Echo plate system provides a complete workflow for assigning slats to 96-well output plates and generating lab automation files. Located in `lib/echo_and_experimental_helpers/`.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  PlateLayoutState (plate_layout_state.dart)                          │
│  - Slat-to-well assignments, duplicates, well configs                │
│  - Manual handle markings, experiment title, export flags            │
│  - Serialization to/from the output_echo_plates Excel sheet          │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────────┐
        ▼              ▼              ▼                  ▼
  Echo CSV Export  PDF Export   Master Mix Export   PEG Export
  (echo_export)    (pdf_export)  (master_mix)       (peg_purif)
```

## State Management

### PlateLayoutState

**File**: `plate_layout_state.dart`

Central state for echo plate operations. Not a `ChangeNotifier` — it is managed by `DesignState` which calls `notifyListeners()` on changes.

Key data:

```dart
class PlateLayoutState {
  List<String> unassignedSlats;
  Map<int, Map<String, String?>> plateAssignments;  // plateIndex → well → slatId
  Map<String, Set<String>> duplicateGroups;
  Map<String, Set<(int, int)>> manualHandles;       // baseSlatId → (helix, position)
  Map<int, String> plateNames;
  Map<int, Map<String, WellConfig>> wellConfigs;
  String experimentTitle;
  MasterMixConfig masterMixConfig;
  PegPurificationConfig pegConfig;
  // Export format flags
  bool generatePdf, generateCsv, generateHelperSheets, generatePegSheet;
  bool normalizeVolumes;
}
```

### WellConfig

Per-well dispensing parameters:

```dart
class WellConfig {
  final double ratio;          // staple:scaffold molar ratio (default 15)
  final double volume;         // reaction volume in µL (default 50)
  final double scaffoldConc;   // scaffold concentration in nM (default 50)

  double get materialPerHandle => scaffoldConc * ratio * volume / 1000;  // pmol
  double get totalSlatQuantity => scaffoldConc * volume / 1000;          // pmol
}
```

### PlateUndoStack

**File**: `plate_undo_stack.dart`

Separate undo/redo stack for plate operations (max 50 states), independent of the main design undo stack.

## Export Modules

### Echo CSV (echo_export.dart)

`generateEchoCsv()` produces transfer instructions for the Echo liquid handler:

- One row per handle per occupied well
- Transfer volume computed from `materialPerHandle / concentration`, rounded to 25 nL increments
- Optional volume normalization appends water transfers so all wells in the same config group have equal total volume
- Returns `EchoCsvResult` with main CSV bytes, optional manual CSV bytes, warnings, and water stats

### PDF Report (echo_plate_pdf_export.dart)

`exportPlateLayoutPdf()` generates a multi-page landscape PDF:

- One page per plate showing well assignments with handle barcodes
- Colour coding by design layer, slat type, volume warning, or custom groups
- Manual handle positions highlighted

### Master Mix Export (master_mix_export.dart)

`exportMasterMixWorkbook()` generates an Excel workbook with:

- Per-slat-type sheets (tubes vs. double-barrel)
- Horizontal group layout showing volume calculations
- Scaffold, buffer, and MgCl₂ volumes per reaction

### PEG Purification Export (peg_purification_export.dart)

`exportPegPurificationWorkbook()` generates a helper sheet with:

- Per-group columns with PEG purification volume calculations
- Configurable PEG concentration (2× or 3×)

## UI Components

### EchoPlateWindow

**File**: `echo_plate_window.dart`

The main plate layout editor. Features:

- Drag-and-drop slats from sidebar to wells
- Multi-select wells with click/shift-click/drag-box
- Keyboard shortcuts (Delete, Ctrl+A, Ctrl+D for duplicate)
- Auto-assign with split-by-type/layer options
- Batch config application to selected wells

### EchoPlateGrid

**File**: `echo_plate_grid.dart`

Renders a 96-well plate grid with colour modes:

- Design layer colours
- Slat type colours
- Volume warning states
- Group configuration colours

### EchoPlateSidebar

**File**: `echo_plate_sidebar.dart`

Sidebar showing:

- Plate list with add/remove/rename
- Unassigned slat list
- Batch operations (auto-assign, remove all)

## Persistence

Plate state is saved within the design `.xlsx` file:

- **`output_echo_plates` sheet**: Consolidated grid with all plates (title row, slat assignments, well configs, manual handles section)
- **`lab_metadata` sheet**: Key-value pairs for export flags and master mix/PEG config
- **`input_source_plates` sheet**: Source plate definitions

Import uses `PlateLayoutState.fromConsolidatedSheet()` to reconstruct state from the Excel data.

## Configuration Classes

### MasterMixConfig

**File**: `master_mix_config.dart`

Configurable master mix calculation parameters:

- Scaffold stock concentration
- Core staples mode (standard vs. double-barrel)
- TEF stock/final concentrations
- MgCl₂ stock/final concentrations
- Buffer slats mode (percentage or count)

### PegPurificationConfig

**File**: `peg_purification_config.dart`

PEG purification settings (currently just `pegConcentration`: 2× or 3×).

## Constants

**File**: `echo_plate_constants.dart`

Layout constants (well dimensions, grid padding, window sizes), plate row/column helpers (`wellName`, `wellRow`, `wellCol`), colour mode enums, and volume calculation helpers (`echoRoundedVolumeNl`).

**File**: `echo_category_colors.dart`

Maps handle categories (ASSEMBLY_HANDLE, CARGO, SEED, FLAT, etc.) to display colours for both Flutter UI and PDF export.
