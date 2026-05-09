# UI Components

This page documents the main UI components in the #-CAD Flutter application.

## Main Layout

### SplitScreen

**File**: `lib/main_windows/split_screen.dart`

The root layout widget that divides the screen into left (2D canvas) and right (sidebar/3D) panels.

```dart
class SplitScreen extends StatefulWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          flex: leftPanelFlex,
          child: GridAndCanvas(),  // 2D view
        ),
        GestureDetector(
          // Draggable divider
          child: Container(width: 8, color: Colors.grey),
        ),
        Expanded(
          flex: rightPanelFlex,
          child: _buildRightPanel(),  // Sidebar or 3D
        ),
      ],
    );
  }
}
```

### TogglePanel

**File**: `lib/main_windows/floating_switches.dart`

Floating panel with quick-access toggle buttons for display settings:

```dart
TogglePanel(
  actionState: actionState,
  onCenterPressed: centerOnSlats,  // Callback to center view
)
```

Provides toggles for grid, borders, slat IDs, seeds, and other display options.

## Sidebars

All sidebars are located in `lib/sidebars/`.

| Sidebar | File | Purpose |
|---------|------|---------|
| `SlatDesignTools` | `slat_design_sidebar.dart` | Grid mode, layer management, slat editing |
| `AssemblyHandleDesignTools` | `assembly_handles_sidebar.dart` | Handle assignment, evolution controls |
| `CargoTools` | `cargo_sidebar.dart` | Cargo and seed placement |
| `EchoTools` | `echo_sidebar.dart` | Echo Liquid Handler export settings |
| `GroupingSidebar` | `grouping_sidebar.dart` | Slat grouping configurations and colour assignment |
| `LayerManager` | `layer_manager.dart` | Layer ordering and visibility |

### SlatDesignTools

For slat design mode - grid type selection, layer management, and slat properties:

```dart
class SlatDesignTools extends StatefulWidget {
  // Includes:
  // - Grid mode toggle (90° vs 60°)
  // - Layer manager
  // - Slat add/edit selection panels
}
```

### AssemblyHandleDesignTools

For handle assignment and evolution:

```dart
class AssemblyHandleDesignTools extends StatefulWidget {
  // Includes:
  // - Handle value input
  // - Attachment mode (top/bottom)
  // - Evolution parameters
  // - Server status and controls
}
```

### Supporting Components

| Component | File | Purpose |
|-----------|------|---------|
| `SlatAddSelectionPanel` | `slat_add_selection_panel.dart` | Slat type selection for adding |
| `SlatEditSelectionPanel` | `slat_edit_selection_panel.dart` | Edit selected slats |
| `SlatLinkerWindow` | `slat_linker_window.dart` | Link slats together |

## Dialogs

Located in `lib/dialogs/`.

| Dialog | File | Purpose |
|--------|------|---------|
| `AlertWindow` | `alert_window.dart` | Generic confirmations and warnings |
| `UpdateDialog` | `update_dialog.dart` | App update notifications |

### AlertWindow

**File**: `lib/dialogs/alert_window.dart`

Generic dialog for confirmations and warnings. Used throughout the app for destructive action confirmations.

## Echo Plate Components

Located in `lib/echo_and_experimental_helpers/`.

| Component | File | Purpose |
|-----------|------|---------|
| `EchoPlateWindow` | `echo_plate_window.dart` | Main 96-well plate layout editor (drag-drop, selection, keyboard) |
| `EchoPlateGrid` | `echo_plate_grid.dart` | 96-well grid widget with colour modes |
| `EchoPlateWell` | `echo_plate_well.dart` | Individual well rendering with barcode |
| `EchoPlateSidebar` | `echo_plate_sidebar.dart` | Plate list and sidebar controls |
| `EchoPlatePainters` | `echo_plate_painters.dart` | Plate outline with chamfered corners |
| `EchoPlateBars` | `echo_plate_bars.dart` | Category breakdown bar chart |
| `HandleBarcodePainter` | `echo_barcode_painter.dart` | Per-well handle barcode painter |
| `WellConfigDialog` | `echo_well_config_dialog.dart` | Per-well ratio/volume/concentration editor |
| `ManualHandleDialog` | `manual_handle_dialog.dart` | Mark specific handles as manual (non-Echo) |
| `MassManualHandleDialog` | `mass_manual_handle_dialog.dart` | Bulk manual handle marking across slats |

### PlateLayoutState

**File**: `lib/echo_and_experimental_helpers/plate_layout_state.dart`

The central state container for echo plate assignment. Manages:

- `unassignedSlats` — slats not yet placed on any plate
- `plateAssignments` — map of plate index → well → slat ID
- `wellConfigs` — per-well dispensing parameters (ratio, volume, scaffold concentration)
- `duplicateGroups` — tracking slat duplicates across plates
- `manualHandles` — per-slat positions that are pipetted manually
- `masterMixConfig` / `pegConfig` — lab protocol settings
- Export format flags (PDF, CSV, helper sheets, PEG sheet, volume normalization)

### Export Modules

| Module | File | Output |
|--------|------|--------|
| `generateEchoCsv` | `echo_export.dart` | Echo liquid handler CSV transfer instructions |
| `exportMasterMixWorkbook` | `master_mix_export.dart` | Master mix Excel with per-type sheets |
| `exportPegPurificationWorkbook` | `peg_purification_export.dart` | PEG purification helper Excel sheet |
| `exportPlateLayoutPdf` | `echo_plate_pdf_export.dart` | PDF plate layout report with barcode visuals |

## Graphics Components

Located in `lib/graphics/`.

| Component | File | Purpose |
|-----------|------|---------|
| `StatusIndicator` | `status_indicator.dart` | Display status messages with optional content |
| `AssemblyColorLegend` | `assembly_color_legend.dart` | Handle color coding legend |
| `LineChart` | `line_chart.dart` | Evolution metrics visualization |
| `RatingIndicator` | `rating_indicator.dart` | Visual rating display |
| `HoneycombPictogram` | `honeycomb_pictogram.dart` | Honeycomb pattern visualization |
| `CrosshatchShader` | `crosshatch_shader.dart` | Crosshatch pattern for 2D fills |
| `exportDesignToSTL` | `stl_exporter.dart` | Binary STL export for 3D printing |
| `validateFullConnectivity` | `stl_export_validation.dart` | Assembly connectivity check before STL export |

### StatusIndicator

**File**: `lib/graphics/status_indicator.dart`

A floating indicator that displays status text lines with optional additional content:

```dart
StatusIndicator(
  lines: ['Slats Selected: 5'],
  additionalContent: AssemblyColorLegend(appState: appState),  // Optional
)
```

### AssemblyColorLegend

**File**: `lib/graphics/assembly_color_legend.dart`

Legend showing handle color coding for assembly mode.

## 3D Visualization

**File**: `lib/graphics/3d_painter.dart`

Uses the [three_js](https://github.com/Knightro63/three_js) packages for WebGL rendering with instanced meshes for performance.

### Key Classes

| Class | Purpose |
|-------|---------|
| `InstanceMetrics` | Manages instanced mesh rendering for slats/cargo/seeds |
| `ThreeDisplay` | Main 3D view widget |

### Instanced Rendering

Uses `three.InstancedMesh` for efficient rendering of many similar objects:

```dart
class InstanceMetrics {
  late three.InstancedMesh mesh;
  final three.BufferGeometry geometry;
  final Map<String, int> nameIndex;       // Object name -> instance index
  final Map<String, tmath.Vector3> positionIndex;
  final Map<String, Color> colorIndex;
  // ...
}
```

### Custom 3D Meshes

**File**: `lib/graphics/custom_3d_meshes.dart`

Geometry generation for slat, cargo, and seed visualization.

## Theme colors

```dart
// In theme configuration
ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
      );

// Starter layer colors (from a matplotlib colormap)
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
```
