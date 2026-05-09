# Design I/O

The `design_io` module handles all file import/export for #-CAD designs. Located in `lib/app_management/design_io/`.

## Architecture

The module uses a **single consolidated Excel format** where each concern maps to named sheets:

| Sheet Pattern | Content |
|---------------|---------|
| `slat_layer_N` | Slat placement grids (with phantom slats encoded) |
| `cargo_layer_N_side_helix` | Cargo handle assignments per layer/side |
| `seed_layer_N_side_helix` | Seed position markers |
| `handle_interface_N` | Assembly handle arrays (one per adjacent layer pair) |
| `metadata` | Layer info, cargo palette, unique slat colours, group colours, grid mode |
| `slat_types` | Per-slat tube/db classification + group membership per config |
| `slat_handle_links` | Handle link constraints |
| `output_echo_plates` | Consolidated echo plate layouts with well configs |
| `input_source_plates` | All input DNA source plates in one sheet |
| `lab_metadata` | Export flags and master mix/PEG config |

## Key Files

### design_io_constants.dart

Single source of truth for the Excel file format. All sheet names, cell positions, category strings, and naming conventions are defined here. Changing a format detail in this file updates both export and import.

### design_export.dart

`exportDesign()` serializes the full design state to a `.xlsx` workbook:

```dart
void exportDesign(
  Map<String, Slat> slats,
  Map<String, Map<String, dynamic>> layerMap,
  Map<String, Cargo> cargoPalette,
  Map<String, Map<Offset, String>> occupiedCargoPoints,
  Map<(String, String, Offset), Seed> seedRoster,
  HandleLinkManager linkManager,
  double gridSize,
  String gridMode,
  String suggestedDesignName, {
  PlateLayoutState? echoPlateLayoutState,
  PlateLibrary? plateLibrary,
  Map<String, GroupConfiguration>? groupConfigurations,
}) async { ... }
```

When `echoPlateLayoutState` is provided, the export writes:

- A consolidated `output_echo_plates` sheet containing all plate assignments and per-well configs
- An `input_source_plates` sheet with all loaded source plate definitions
- A `lab_metadata` sheet with export flags and master mix/PEG configuration

### design_import.dart

`parseDesignInIsolate()` runs in a compute isolate to keep the UI responsive. Returns a `ParsedDesignResult` with error codes on failure:

- `ERR_GENERAL` — missing metadata sheet
- `ERR_SLAT_SHEETS` — malformed slat layer sheets
- `ERR_ASSEMBLY_SHEETS` — assembly handle mismatch
- `ERR_CARGO_SHEETS` / `ERR_SEED_SHEETS` — cargo/seed parsing failures
- `ERR_LINK_MANAGER: <detail>` — handle link import error

### parsed_design_result.dart

Data container returned by the import. Holds slats, layerMap, cargo, seeds, handle links, echo plate state, input plates, and lab metadata.

### excel_utilities.dart

Shared helpers for reading typed cell values (`readExcelInt`, `readExcelDouble`, `readExcelString`) and writing cells (`setCellValue`).

### file_picker_helpers.dart

Cross-platform file picker wrappers (`selectSaveLocation`, `pickExcelFile`) that handle web vs. desktop differences.

### plate_io.dart

Handles reading and writing DNA source plate libraries (the input plates that provide handle sequences).

### assembly_handle_io.dart

Reads/writes assembly handle arrays — converting between the sparse slat representation and dense 2D grid arrays for the Excel format.

### handle_link_io.dart

Persists `HandleLinkManager` state (linked groups, enforced values, blocked handles) to/from the `slat_handle_links` sheet.

### evolution_export.dart

Exports evolution parameters and results for the Python server.

## Round-Trip Guarantee

The import/export pair is designed for lossless round-trips: exporting a design and re-importing should produce identical state. The test suite (`test/unit/app_management/design_io_round_trip_test.dart`) verifies this property.
