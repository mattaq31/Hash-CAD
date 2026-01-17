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

- **DesignState**: Core design data (slats, handles, cargo, seeds)
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

### Data Models

Core data classes in `lib/crisscross_core`:

- **Slat**: DNA origami slat with handle positions
- **Cargo**: Payload molecules attached to slats
- **Seed**: DNA origami seed structures that nucleate assembly
- **HashCadPlate**: DNA plate configuration for assigning sequences to handles

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
│   ├── main_design_io.dart         # Design file I/O
│   ├── slat_undo_stack.dart        # Undo/redo functionality
│   ├── version_tracker.dart        # Version tracking
│   ├── update_service.dart         # Update checking service
│   ├── git_version_updater.dart    # Git version utilities
│   └── design_state_mixins/        # Modular state functionality
├── app_management.dart             # Barrel file
│
├── main_windows/                   # Main UI components
│   ├── split_screen.dart           # Layout container
│   ├── grid_control.dart           # 2D canvas
│   └── grid_control_mixins/        # Event handling
├── main_windows.dart               # Barrel file
│
├── sidebars/                       # Editing panels
├── sidebars.dart                   # Barrel file
│
├── crisscross_core/                # Data models
├── crisscross_core.dart            # Barrel file
│
├── 2d_painters/                    # Canvas rendering
├── painters_2d.dart                # Barrel file
│
├── graphics/                       # 3D visualization
├── graphics.dart                   # Barrel file
│
├── dialogs/                        # Popup windows
├── dialogs.dart                    # Barrel file
│
├── drag_and_drop/                  # Platform-specific file drop targets
├── drag_and_drop.dart              # Barrel file
│
├── echo_and_experimental_helpers/  # Echo export and CSV utilities
├── experimental.dart               # Barrel file
│
└── grpc_client_architecture/       # gRPC client
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



