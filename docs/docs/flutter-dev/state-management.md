# State Management

\#-CAD uses the Provider package for state management, with state split across four main classes that handle different concerns.

## Architecture Overview

```dart
// In main.dart
MultiProvider(
  providers: [
      ChangeNotifierProvider(
        create: (context) {
          final designState = DesignState();
          designState.initializeUndoStack(); // Ensures undo stack starts with the initial state
          designState.loadAssemblyHandleColors(); // Load persisted handle colors
          return designState;
        },
      ),
      ChangeNotifierProvider(create: (context) => ActionState()),
      ChangeNotifierProvider(create: (context) => ServerState()),
      ChangeNotifierProvider(create: (context) => UpdateState()),
  ],
)
```

## DesignState

**File**: `lib/app_management/shared_app_state.dart`

The central state container for all design data. Uses mixin composition for modularity.

### Mixin Architecture

```dart
class DesignState extends ChangeNotifier
    with DesignStateContract,
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
  // ...
}
```

### Key Mixins

| Mixin | File | Responsibility                            |
|-------|------|-------------------------------------------|
| `DesignStateContract` | `design_state_contract.dart` | Interface for inter-mixin communication   |
| `DesignStateCoreMixin` | `design_state_core_mixin.dart` | Basic state initialization                |
| `DesignStateFileIOMixin` | `design_state_file_io_mixin.dart` | Excel import/export                       |
| `DesignStateLayerMixin` | `design_state_layer_mixin.dart` | Multi-layer management                    |
| `DesignStateSlatMixin` | `design_state_slat_mixin.dart` | Slat create/read/update/delete operations |
| `DesignStateHandleMixin` | `design_state_handle_mixin.dart` | Handle assignment                         |
| `DesignStateSlatColorMixin` | `design_state_slat_color_mixin.dart` | Slat color customization                  |
| `DesignStatePhantomMixin` | `design_state_phantom_mixin.dart` | Phantom slat management                   |
| `DesignStateCargoMixin` | `design_state_cargo_mixin.dart` | Cargo placement                           |
| `DesignStateSeedMixin` | `design_state_seed_mixin.dart` | Seed geometry                             |
| `DesignStatePlateMixin` | `design_state_plate_mixin.dart` | DNA plate management                      |
| `DesignStateHandleLinkMixin` | `design_state_handle_link_mixin.dart` | Handle linking                            |

### Example Core Data Structures

```dart
// Slat dictionary - keyed by unique slat ID
Map<String, Slat> slats;

// Layer information
String selectedLayerKey;  // Current layer key (e.g., 'A', 'B')
String nextLayerKey;      // Next available layer key

// Undo/redo via SlatUndoStack
SlatUndoStack undoStack;  // Manages DesignSaveState snapshots
```
The full documentation for this class is available in the dart API [here](../flutter-api/index.html).

## ActionState

**File**: `lib/app_management/action_state.dart`

Manages UI state, display preferences, and user action modes.

### Key Properties

```dart
class ActionState extends ChangeNotifier {
  // Panel/mode selection (0=slats, 1=assembly, 2=cargo, 3=settings)
  int panelMode;

  // Mode strings for each panel
  String slatMode;       // 'Add', 'Delete', etc.
  String cargoMode;
  String assemblyMode;

  // Display toggles
  bool displayGrid;
  bool displayAssemblyHandles;
  bool displayCargoHandles;
  bool displaySlatIDs;
  bool displaySeeds;
  bool displayBorder;
  bool viewPhantoms;

  // UI state
  double splitScreenDividerWidth;
  bool evolveMode;
  bool threeJSViewerActive;
  bool isSideBarCollapsed;

  // Echo export settings
  Map<String, dynamic> echoExportSettings;
  //....
}
```

### Usage

```dart
// Switch panels
actionState.setPanelMode(1);  // Switch to assembly panel

// Toggle display options
actionState.setGridDisplay(true);
actionState.setAssemblyHandleDisplay(true);

// Update mode within a panel
actionState.updateSlatMode('Delete');

// Check current panel
if (actionState.panelMode == 0) {
  // Handle slat panel interactions
}
```
The full documentation for this class is available in the dart API [here](../flutter-api/index.html).

## ServerState

**File**: `lib/app_management/server_state.dart`

Handles gRPC communication with the Python evolution server.

### Key Properties

```dart
class ServerState extends ChangeNotifier {
  // gRPC clients
  CrisscrossClient? hammingClient;
  HealthClient? healthClient;

  // Connection state
  bool serverActive;
  String statusIndicator;  // 'BACKEND INACTIVE', 'IDLE', 'RUNNING', 'PAUSED'

  // Evolution parameters (stored as strings)
  Map<String, String> evoParams;  // mutation_rate, evolution_generations, etc.

  // Evolution progress
  bool evoActive;
  List<double> hammingMetrics;
  List<double> physicsMetrics;
}
```

### Server Communication

```dart
// Launch gRPC clients
serverState.launchClients(50055);

// Start evolution
serverState.evolveAssemblyHandles(slatArray, slatCoords, handleArray, ...);

// Pause/stop evolution
serverState.pauseEvolve();
List<List<List<int>>> result = await serverState.stopEvolve();

// Health check
await serverState.startupServerHealthCheck();
```

## UpdateState

**File**: `lib/app_management/update_state.dart`

Manages app update checking and notification.

### Key Properties

```dart
class UpdateState extends ChangeNotifier {
  // Update status
  UpdateStatus _status;  // idle, checking, available, error
  ReleaseInfo? _latestRelease;
  String? _errorMessage;

  // Computed properties
  bool get updateAvailable;
  bool get isChecking;
  String get installPath;
}

enum UpdateStatus {
  idle,
  checking,
  available,
  error,
}
// ...
```

### Usage

```dart
// Check for updates (silent respects hourly interval)
bool hasUpdate = await updateState.checkForUpdates(silent: true);

// Manual check (ignores interval)
bool hasUpdate = await updateState.checkForUpdates(silent: false);

// Skip current version
await updateState.skipCurrentVersion();

// Dismiss update dialog
updateState.dismiss();

// ...
```

## Inter-State Communication

States can reference each other when needed:

```dart
// In a widget
final designState = context.read<DesignState>();
final serverState = context.read<ServerState>();
final actionState = context.read<ActionState>();

// Example: check if evolution mode is active
if (actionState.evolveMode && serverState.evoActive) {
  // Evolution is running
}

// Access design data for server operations
final slats = designState.slats;
```

## Best Practices

### Updating State
```dart
// Always call notifyListeners() after changes
// the below functions are fictitious examples:
void addSlat(Slat slat) {
  slats[slat.id] = slat;
  notifyListeners();  // Triggers UI rebuild
}

// Batch updates for performance
void batchUpdate(List<Slat> newSlats) {
  for (final slat in newSlats) {
    slats[slat.id] = slat;
  }
  notifyListeners();  // Single notification
}
```

### Undo/Redo

The app uses `SlatUndoStack` which manages `DesignSaveState` snapshots:

```dart
// SlatUndoStack manages history internally
class SlatUndoStack {
  final List<DesignSaveState> _history = [];
  int _currentIndex = -1;
  static const int _maxHistory = 50;

  void saveState(DesignSaveState state);
  DesignSaveState? undo();
  DesignSaveState? redo();
  bool get canUndo;
  bool get canRedo;
}
```

You should save the state after any operation that modifies the design:

```dart
  void saveUndoState() {
    undoStack.saveState(DesignSaveState(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: layerMap,
        layerMetaData: {
          'selectedLayerKey': selectedLayerKey,
          'nextLayerKey': nextLayerKey,
          'nextColorIndex': nextColorIndex,
        },
        cargoPalette: cargoPalette,
        occupiedCargoPoints: occupiedCargoPoints,
        seedRoster: seedRoster,
        phantomMap: phantomMap,
        assemblyLinkManager: assemblyLinkManager,
        gridMode: gridMode));
  }
```
