import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app_management/shared_app_state.dart';
import '../app_management/action_state.dart';
import '../main_windows/floating_switches.dart';
import '../2d_painters/2d_view_svg_exporter.dart';
import '../graphics/status_indicator.dart';
import '../graphics/assembly_color_legend.dart';

import 'grid_control_mixins/grid_control_contract.dart';
import 'grid_control_mixins/grid_control_helpers_mixin.dart';
import 'grid_control_mixins/grid_control_position_generators_mixin.dart';
import 'grid_control_mixins/grid_control_hover_events_mixin.dart';
import 'grid_control_mixins/grid_control_mouse_events_mixin.dart';
import 'grid_control_mixins/grid_control_gesture_events_mixin.dart';
import 'grid_control_mixins/grid_control_keyboard_events_mixin.dart';
import 'grid_control_mixins/grid_control_painters_mixin.dart';

/// Class that takes care of painting all 2D objects on the grid, including the grid itself, slats and slat hover effects.
class GridAndCanvas extends StatefulWidget {

  const GridAndCanvas({super.key});

  @override
  State<GridAndCanvas> createState() => _GridAndCanvasState();
}

class _GridAndCanvasState extends State<GridAndCanvas>
    with
        GridControlContract<GridAndCanvas>,
        GridControlHelpersMixin<GridAndCanvas>,
        GridControlPositionGeneratorsMixin<GridAndCanvas>,
        GridControlHoverEventsMixin<GridAndCanvas>,
        GridControlMouseEventsMixin<GridAndCanvas>,
        GridControlGestureEventsMixin<GridAndCanvas>,
        GridControlKeyboardEventsMixin<GridAndCanvas>,
        GridControlPaintersMixin<GridAndCanvas>,
        TickerProviderStateMixin<GridAndCanvas> {

  // Scale parameters
  @override
  double initialScale = 1.0;
  @override
  double minScale = 0.1;
  @override
  double maxScale = 6.0;

  @override
  bool moveFlipRequested = false;
  @override
  int moveRotationSteps = 0;

  // Current scale and offset (zoom and move)
  @override
  double scale = 0.8;
  @override
  Offset offset = Offset(800, 700);

  // For the gesture detector (touchpad)
  @override
  Offset initialPanOffset = Offset.zero;
  @override
  Offset initialGestureFocalPoint = Offset.zero;

  // Hover (mouse over grid area) state
  @override
  Offset? hoverPosition;
  @override
  bool hoverValid = true;
  @override
  Map<int, Map<int, Offset>> hoverSlatMap = {};

  // Dragging/moving state
  @override
  bool dragActive = false;
  @override
  Offset lastPointerPosition = Offset.zero;
  @override
  Offset slatMoveAnchor = Offset.zero;
  @override
  List<String> hiddenSlats = [];
  @override
  List<Offset> hiddenCargo = [];
  @override
  List<Offset> hiddenAssembly = [];

  // Keyboard state
  @override
  bool isShiftPressed = false;
  @override
  bool isCtrlPressed = false;
  @override
  bool isMetaPressed = false;
  @override
  final FocusNode keyFocusNode = FocusNode();

  // Controls for drag-select box
  @override
  bool dragBoxActive = false;
  @override
  Offset? dragBoxStart;
  @override
  Offset? dragBoxEnd;

  // Zoom bounds flash animation
  late AnimationController _zoomBoundsFlashController;
  @override
  double zoomBoundsFlashOpacity = 0.0;

  @override
  void initState() {
    super.initState();
    _zoomBoundsFlashController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _zoomBoundsFlashController.addListener(() {
      setState(() {
        zoomBoundsFlashOpacity = 1.0 - _zoomBoundsFlashController.value;
      });
    });
  }

  @override
  void dispose() {
    _zoomBoundsFlashController.dispose();
    super.dispose();
  }

  @override
  void triggerZoomBoundsFlash() {
    _zoomBoundsFlashController.forward(from: 0.0);
  }

  /// Updates the coordinates for the hover slat preview
  @override
  void setHoverCoordinates(DesignState appState) {
    if (hoverPosition == null) return;
    hoverSlatMap = generateSlatPositions(hoverPosition!, true, appState); // REAL space
    final paths = hoverSlatMap.values
        .map((inner) => inner.values.toList())
        .toList();
    appState.setHoverPreview(HoverPreview(
      kind: 'Slat-Add',
      isValid: hoverValid,
      slatPaths: paths,
    ));
  }

  @override
  Widget build(BuildContext context) {

    // watches the current slat and layer statuses
    var appState = context.watch<DesignState>();

    // watches the current action mode
    var actionState = context.watch<ActionState>();

    // gets a quick status update for the floating panel
    List<String> statusText = getStatusIndicatorText(actionState, appState);

    // Main app activity defined here
    return Stack(
      children: [
        Scaffold(
          body: Listener(
            // all move events (dragging, zooming) are defined here
            onPointerSignal: handlePointerSignal,
            onPointerDown: (event) => handlePointerDown(event, appState, actionState),
            onPointerMove: (event) => handlePointerMove(event, appState, actionState),
            onPointerUp: (event) => handlePointerUp(event, appState, actionState, context),

            child: CallbackShortcuts(
              bindings: getKeyboardBindings(appState, actionState, context), // defines keyboard shortcuts
              child: Focus(
                autofocus: true,
                focusNode: keyFocusNode,
                onKeyEvent: handleKeyEvent,  // handles key press and release events
                child: MouseRegion(
                  cursor: getCursorForSlatMode(getActionMode(actionState)),  // different cursor for different modes
                  onHover: (event) => handleHover(event, appState, actionState),
                  onExit: handleHoverExit,
                  child: GestureDetector( // this defines touchpad/mouse gestures where one is adding, selecting or removing items (move not handled here)
                    onScaleStart: handleScaleStart,
                    onScaleUpdate: handleScaleUpdate,
                    onTapDown: (details) => handleTapDown(details, appState, actionState, context),
                    onTapUp: (details) => handleTapUp(details, appState, actionState, context),
                    onSecondaryTapUp: (details) => handleSecondaryTapUp(details, appState, actionState),
                    child: buildPainterStack(appState, actionState), // the main painters (slats, hover, grid, etc.) are defined in here
                  ),
                ),
              ),
            ),
          ),
        ),

        // floating buttons and indicators here

        // Top-left floating button that moves with sidebar
        AnimatedPositioned(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
          top: 20,
          left: actionState.isSideBarCollapsed ? 72 + 15 : 72 + 330 + 10,
          child: Tooltip(
            message: 'Export Slat Design to SVG Image',
            waitDuration: Duration(milliseconds: 500),
            child: FloatingActionButton.small(
              foregroundColor: Theme.of(context).colorScheme.onPrimary,
              backgroundColor: Theme.of(context).colorScheme.primary,
              child: Icon(Icons.camera),
              onPressed: () async {
                final options = await showSvgExportDialog(context, actionState);
                if (options != null) {
                  exportSlatsToSvg(
                    slats: appState.slats.values.toList(),
                    layerMap: appState.layerMap,
                    appState: appState,
                    actionState: actionState,
                    exportOptions: options,
                  );
                }
              },
            ),
        ),
      ),
      AnimatedPositioned(
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOut,
        bottom: 90,
        left: actionState.isSideBarCollapsed ? 72 + 25 : 72 + 330 + 20,
        child: AnimatedSwitcher(
          switchInCurve: Curves.easeInOut,
          switchOutCurve: Curves.easeInOut,
          transitionBuilder: (child, animation) {
            return FadeTransition(
              opacity: animation,
              child: ScaleTransition(
                scale: animation,
                alignment: Alignment.topCenter,
                child: child,
              ),
            );
          },
          duration: const Duration(milliseconds: 400),
          child: statusText.isEmpty
              ? const SizedBox.shrink()
              : StatusIndicator(
                  lines: statusText,
                  additionalContent: getActionMode(actionState) == 'Assembly-Move' ? AssemblyColorLegend(appState: appState) : null,
                ),
        ),
      ),

      TogglePanel(actionState: actionState, onCenterPressed: centerOnSlats)
    ]);
  }
}