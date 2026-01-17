# Grid Control

The `GridAndCanvas` widget is the core 2D visualization component, handling rendering and user interactions on the design canvas.

## Architecture

**File**: `lib/main_windows/grid_control.dart`

```dart
class _GridAndCanvasState extends State<GridAndCanvas>
    with
        GridControlContract<GridAndCanvas>,
        GridControlHelpersMixin<GridAndCanvas>,
        GridControlPositionGeneratorsMixin<GridAndCanvas>,
        GridControlHoverEventsMixin<GridAndCanvas>,
        GridControlMouseEventsMixin<GridAndCanvas>,
        GridControlGestureEventsMixin<GridAndCanvas>,
        GridControlKeyboardEventsMixin<GridAndCanvas>,
        GridControlPaintersMixin<GridAndCanvas>  {
  // Main 2D canvas widget
}
```
## Coordinate System

### Grid Coordinates

All designs are enforced to exist on a 2D rectangular grid, with 14 nm (represented as 10 units) between each handle position.  Hexagonal designs are also supported on this grid (with some transformations to the grid system).

The design uses `Offset` for grid positions:

```dart
// Current scale and offset (zoom and pan)
double scale = 0.8;
Offset offset = Offset(800, 700);

// Scale bounds
double minScale = 0.1;
double maxScale = 6.0;

// Hover position in real space
Offset? hoverPosition;
```

### Grid Snapping

The `gridSnap` function converts screen coordinates to snapped grid positions:

```dart
Offset gridSnap(Offset inputPosition, DesignState designState) {
  if (designState.gridMode == '90') {
    // Standard rectangular grid
    return Offset(
      (((inputPosition.dx - offset.dx) / scale) / designState.gridSize).round() * designState.gridSize,
      (((inputPosition.dy - offset.dy) / scale) / designState.gridSize).round() * designState.gridSize,
    );
  } else if (designState.gridMode == '60') {
    // Hexagonal grid - finds nearest of two candidate points
    // ...
  }
}
```

## Event Handling Mixins

### Mouse Events

**File**: `grid_control_mouse_events_mixin.dart`

Handles pointer events via Flutter's `Listener` widget:

```dart
mixin GridControlMouseEventsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  void handlePointerDown(PointerDownEvent event, DesignState appState, ActionState actionState);
  void handlePointerMove(PointerMoveEvent event, DesignState appState, ActionState actionState);
  void handlePointerUp(PointerUpEvent event, DesignState appState, ActionState actionState, BuildContext context);
  void handlePointerSignal(PointerSignalEvent event);  // Scroll wheel zoom
}
```

### Keyboard Events

**File**: `grid_control_keyboard_events_mixin.dart`

Uses `CallbackShortcuts` for keyboard bindings:

```dart
mixin GridControlKeyboardEventsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  // Keyboard state tracking
  bool isShiftPressed = false;
  bool isCtrlPressed = false;
  bool isMetaPressed = false;
  final FocusNode keyFocusNode = FocusNode();

  Map<ShortcutActivator, VoidCallback> getKeyboardBindings(
    DesignState appState, ActionState actionState, BuildContext context);
  KeyEventResult handleKeyEvent(FocusNode node, KeyEvent event);
}
```

### Gesture Events

**File**: `grid_control_gesture_events_mixin.dart`

Handles touch and trackpad gestures:

```dart
mixin GridControlGestureEventsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  Offset initialPanOffset = Offset.zero;
  Offset initialGestureFocalPoint = Offset.zero;

  void handleScaleStart(ScaleStartDetails details);
  void handleScaleUpdate(ScaleUpdateDetails details);
  void handleTapDown(TapDownDetails details, DesignState appState, ActionState actionState, BuildContext context);
  void handleTapUp(TapUpDetails details, DesignState appState, ActionState actionState, BuildContext context);
}
```

### Hover Events

**File**: `grid_control_hover_events_mixin.dart`

Provides visual feedback for cursor position:

```dart
mixin GridControlHoverEventsMixin<T extends StatefulWidget> on State<T>, GridControlContract<T> {
  Offset? hoverPosition;
  bool hoverValid = true;
  Map<int, Map<int, Offset>> hoverSlatMap = {};

  void handleHover(PointerHoverEvent event, DesignState appState, ActionState actionState);
  void handleHoverExit(PointerExitEvent event);
  void setHoverCoordinates(DesignState appState);
}
```

## Rendering

### Custom Painters

The canvas uses Flutter's `CustomPainter` via the `GridControlPaintersMixin`. Painters are stacked using `buildPainterStack()`:

```dart
// Painters are combined in buildPainterStack method
CustomPaint(
  painter: GridPainter(...),  // Background grid
  child: CustomPaint(
    painter: SlatPainter(...),  // Slats
    child: CustomPaint(
      painter: SeedPainter(...),  // Seeds
      // ... more painters
    ),
  ),
)
```

### Painter Classes

| Painter | File | Purpose |
|---------|------|---------|
| `GridPainter` | `grid_painter.dart` | Background grid lines |
| `SlatPainter` | `slat_painter.dart` | Slat visualization |
| `HandleHoverPainter` | `handle_hover_painter.dart` | Handle placement preview |
| `SlatHoverPainter` | `slat_hover_painter.dart` | Slat placement preview |
| `SeedPainter` | `seed_painter.dart` | Seed structures |
| `DeletePainter` | `delete_painter.dart` | Delete mode cursor |
| `DragBoxPainter` | `drag_box_painter.dart` | Selection box |

## Zoom and Pan

### State Variables

```dart
// Scale bounds
double minScale = 0.1;
double maxScale = 6.0;

// Current transform state
double scale = 0.8;
Offset offset = Offset(800, 700);
```

### Scroll Wheel Zoom

The `scrollZoomCalculator` function handles zoom while keeping the cursor position fixed:

```dart
(double, Offset) scrollZoomCalculator(PointerScrollEvent event, {double zoomFactor = 0.2}) {
  double newScale = scale;

  if (event.scrollDelta.dy > 0) {
    newScale = (scale * (1 - zoomFactor)).clamp(minScale, maxScale);
  } else if (event.scrollDelta.dy < 0) {
    newScale = (scale * (1 + zoomFactor)).clamp(minScale, maxScale);
  }

  // Keep cursor position fixed during zoom
  final Offset focus = (event.localPosition - offset);
  var calcOffset = event.localPosition - focus * (newScale / scale);

  return (newScale, calcOffset);
}
```

## Selection

### Drag Selection Box

The grid control tracks drag box state for multi-select:

```dart
// Drag box state
bool dragBoxActive = false;
Offset? dragBoxStart;
Offset? dragBoxEnd;
```

Selection state is managed in `DesignState`, not the grid control:

```dart
// In DesignState
Set<String> selectedSlats = {};
List<Offset> selectedHandlePositions = [];
List<Offset> selectedAssemblyPositions = [];
```

### Move State

For moving selected items:

```dart
bool dragActive = false;
Offset slatMoveAnchor = Offset.zero;
List<String> hiddenSlats = [];      // Slats being moved
List<Offset> hiddenCargo = [];      // Cargo being moved
List<Offset> hiddenAssembly = [];   // Assembly handles being moved
```

## Action Modes

The `getActionMode` helper returns a string describing the current user action:

```dart
String getActionMode(ActionState actionState) {
  if (actionState.panelMode == 0) {
    // Slat panel: "Slat-Add", "Slat-Delete", "Slat-Move"
  } else if (actionState.panelMode == 1) {
    // Assembly panel: "Assembly-Add", "Assembly-Delete", "Assembly-Move"
  } else if (actionState.panelMode == 2) {
    // Cargo panel: "Cargo-Add", "Cargo-Delete", "Cargo-Move"
  }
  return "Neutral";
}
```

## SVG Export

**File**: `lib/2d_painters/2d_view_svg_exporter.dart`

Export slat designs to SVG via a dialog:

```dart
void exportSlatsToSvg({
  required List<Slat> slats,
  required Map<String, Map<String, dynamic>> layerMap,
  required DesignState appState,
  required ActionState actionState,
  required SvgExportOptions exportOptions,
});
```
