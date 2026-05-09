# Flutter Developer Guide

This section provides documentation for developers working on the #-CAD Flutter application.  For the full API, please refer to the main API page [here](../flutter-api/index.html).


## Architecture Overview

\#-CAD is built with Flutter and follows a layered architecture:

- UI Layer
    - SplitScreen
    - GridControl
    - Sidebars
    - Dialogs
- State Layer
    - DesignState
    - ActionState
    - ServerState
    - UpdateState
- Core Layer
    - Slat
    - Cargo
    - Seed
    - HandlePlates
    - Valency computation
- Communication Layer
    - gRPC Client
    - Python Server

## Key Components

### State Management

The application uses **Provider** for state management with four main state classes:

- **DesignState**: Core design data (slats, handles, cargo, seeds, groups)
- **ActionState**: UI state and user preferences
- **ServerState**: gRPC server connection and evolution status
- **UpdateState**: Keeps track of app version and suggests updates when available

See [State Management](state-management.md) for details.

### Main UI Components

| Component | File | Description |
|-----------|------|-------------|
| SplitScreen | `lib/main_windows/split_screen.dart` | Main layout container |
| GridAndCanvas | `lib/main_windows/grid_control.dart` | 2D canvas with interactions |
| Sidebars | `lib/sidebars/*.dart` | Context-sensitive editing panels |
| ThreeDisplay | `lib/graphics/3d_painter.dart` | Three.js visualization |
| EchoPlateWindow | `lib/echo_and_experimental_helpers/echo_plate_window.dart` | Echo plate layout editor |

### Data Models

Core data classes in `lib/crisscross_core`:

- **Slat**: DNA origami slat with handle positions
- **Cargo**: Payload molecules attached to slats
- **Seed**: DNA origami seed structures that nucleate assembly
- **HashCadPlate**: DNA plate configuration for assigning sequences to handles

### Design I/O

File import/export in `lib/app_management/design_io/`:

- **design_export.dart**: Writes complete designs to Excel workbooks
- **design_import.dart**: Parses Excel workbooks into design state
- **plate_io.dart**: Input source plate handling
- **assembly_handle_io.dart**: Assembly handle array read/write
- **handle_link_io.dart**: Handle link constraint persistence
- **evolution_export.dart**: Export for evolution server parameters
- **excel_utilities.dart**: Shared Excel cell read/write helpers
- **design_io_constants.dart**: Sheet names, cell positions, format constants
- **parsed_design_result.dart**: Import result data container
- **file_picker_helpers.dart**: Cross-platform file picker wrappers

### Echo & Experimental Helpers

Lab automation in `lib/echo_and_experimental_helpers/`:

- **PlateLayoutState**: Manages slat-to-well assignments, duplicates, configs
- **echo_export.dart**: Generates Echo CSV transfer instructions
- **master_mix_export.dart**: Master mix volume calculation sheets
- **peg_purification_export.dart**: PEG purification helper sheets
- **echo_plate_pdf_export.dart**: PDF plate layout reports
- **MasterMixConfig / PegPurificationConfig**: Persisted experiment settings
- **PlateUndoStack**: Undo/redo for plate operations

## Project Structure

```
lib/
├── main.dart                       # App entry point
│
├── app_management/                 # State management
│   ├── shared_app_state.dart       # DesignState (main)
│   ├── action_state.dart           # UI state
│   ├── server_state.dart           # gRPC state
│   ├── update_state.dart           # App update state
│   ├── app_preferences.dart        # User preferences
│   ├── slat_undo_stack.dart        # Undo/redo functionality
│   ├── version_tracker.dart        # Version tracking
│   ├── update_service.dart         # Update checking service
│   ├── git_version_updater.dart    # Git version utilities
│   ├── design_io/                  # Design file import/export module
│   │   ├── design_io.dart          # Barrel export
│   │   ├── design_export.dart      # Excel workbook export
│   │   ├── design_import.dart      # Excel workbook import
│   │   ├── design_io_constants.dart# Sheet names, cell positions
│   │   ├── excel_utilities.dart    # Shared cell read/write helpers
│   │   ├── parsed_design_result.dart # Import result container
│   │   ├── assembly_handle_io.dart # Assembly handle arrays
│   │   ├── plate_io.dart           # Input source plates
│   │   ├── handle_link_io.dart     # Handle link constraints
│   │   ├── evolution_export.dart   # Evolution parameter export
│   │   ├── file_picker_helpers.dart# Cross-platform file pickers
│   │   ├── save_file_desktop.dart  # Desktop save implementation
│   │   └── save_file_web.dart      # Web save implementation
│   └── design_state_mixins/        # Modular state functionality
│       ├── design_state_contract.dart
│       ├── design_state_core_mixin.dart
│       ├── design_state_file_io_mixin.dart
│       ├── design_state_layer_mixin.dart
│       ├── design_state_slat_mixin.dart
│       ├── design_state_handle_mixin.dart
│       ├── design_state_slat_color_mixin.dart
│       ├── design_state_phantom_mixin.dart
│       ├── design_state_cargo_mixin.dart
│       ├── design_state_seed_mixin.dart
│       ├── design_state_plate_mixin.dart
│       ├── design_state_handle_link_mixin.dart
│       └── design_state_grouping_mixin.dart
├── app_management.dart             # Barrel file
│
├── main_windows/                   # Main UI components
│   ├── split_screen.dart           # Layout container
│   ├── grid_control.dart           # 2D canvas
│   ├── floating_switches.dart      # Toggle panel
│   ├── floating_main_title.dart    # Title overlay
│   ├── window_manager.dart         # Desktop window setup
│   ├── web_window_manager.dart     # Web window stub
│   ├── windows_app_kill_listener.dart # Server cleanup on close
│   └── grid_control_mixins/        # Event handling
├── main_windows.dart               # Barrel file
│
├── sidebars/                       # Editing panels
│   ├── slat_design_sidebar.dart
│   ├── assembly_handles_sidebar.dart
│   ├── cargo_sidebar.dart
│   ├── echo_sidebar.dart
│   ├── grouping_sidebar.dart       # Slat grouping UI
│   ├── layer_manager.dart
│   ├── slat_linker_window.dart
│   ├── slat_add_selection_panel.dart
│   ├── slat_edit_selection_panel.dart
│   └── sidebar_tools.dart
├── sidebars.dart                   # Barrel file
│
├── crisscross_core/                # Data models
├── crisscross_core.dart            # Barrel file
│
├── 2d_painters/                    # Canvas rendering
├── painters_2d.dart                # Barrel file
│
├── graphics/                       # 3D visualization + STL export
├── graphics.dart                   # Barrel file
│
├── dialogs/                        # Popup windows
├── dialogs.dart                    # Barrel file
│
├── drag_and_drop/                  # Platform-specific file drop targets
├── drag_and_drop.dart              # Barrel file
│
├── echo_and_experimental_helpers/  # Echo plate UI, CSV/PDF/Excel export
│   ├── plate_layout_state.dart     # Slat-to-well state (PlateLayoutState)
│   ├── echo_plate_constants.dart   # Layout constants + helpers
│   ├── echo_category_colors.dart   # Handle category color map
│   ├── plate_undo_stack.dart       # Undo/redo for plate ops
│   ├── master_mix_config.dart      # Master mix settings
│   ├── peg_purification_config.dart# PEG purification settings
│   ├── echo_export.dart            # Echo CSV generation
│   ├── master_mix_export.dart      # Master mix Excel export
│   ├── peg_purification_export.dart# PEG helper sheet export
│   ├── echo_plate_pdf_export.dart  # PDF plate report
│   ├── echo_plate_window.dart      # Main echo plate editor
│   ├── echo_plate_grid.dart        # 96-well grid widget
│   ├── echo_plate_sidebar.dart     # Plate sidebar controls
│   ├── echo_plate_well.dart        # Single well widget
│   ├── echo_plate_painters.dart    # Plate outline/chamfer painters
│   ├── echo_plate_bars.dart        # Category bar chart widget
│   ├── echo_barcode_painter.dart   # Handle barcode painter
│   ├── echo_well_config_dialog.dart# Well config dialog
│   ├── manual_handle_dialog.dart   # Manual handle marking dialog
│   └── mass_manual_handle_dialog.dart # Bulk manual handle dialog
├── experimental.dart               # Barrel file
│
└── grpc_client_architecture/       # gRPC client (auto-generated)
```

## Development Workflow

### Quick Links

- [Getting Started](getting-started.md) - Set up your development environment
- [State Management](state-management.md) - Understand the Provider architecture
- [Grid Control](grid-control.md) - 2D canvas implementation
- [gRPC Integration](grpc-integration.md) - Python server communication
- [Components](components.md) - UI component reference

## Design Patterns

### Mixin-Based Composition

Complex classes use mixins for modular functionality:

```dart
class DesignState extends ChangeNotifier
    with DesignStateCoreM,
         DesignStateSlatMixin,
         DesignStateHandleMixin,
         DesignStateLayerMixin,
         // ... more mixins
```

### Event Handling

User interactions are handled through specialized mixins:

- `GridControlMouseEventsMixin` - Mouse clicks and drags
- `GridControlKeyboardEventsMixin` - Keyboard shortcuts
- `GridControlGestureEventsMixin` - Touch/gesture events
- `GridControlHoverEventsMixin` - Hover previews

### Coordinate Systems

The application uses a grid-based coordinate system:

- **Grid coordinates**: Logical positions (x, y) on the design grid
- **Pixel coordinates**: Screen positions after zoom/pan transformation
- **Grid size**: 10.0 pixels per grid unit (configurable)
- **Hex offset**: 60° angle for triangular grids 
- **Real world units**: The distance between two handles is always 14 nm.  On the hex grid, the x distance between points is 12.12 nm while the y distance is 7 nm.

## Dependencies

Key packages used:

| Package | Purpose                     |
|---------|-----------------------------|
| `provider` | State management            |
| `grpc` | Python server communication |
| `three_js` | 3D visualization            |
| `excel` | File I/O                    |
| `fl_chart` | Metrics visualization       |
| `window_manager` | Desktop window control      |
| `file_picker` | Desktop file system control |
| `flutter_colorpicker` | Color picker system         |



