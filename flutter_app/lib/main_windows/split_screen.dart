import 'dart:ui';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../graphics/3d_painter.dart';
import '../graphics/crosshatch_shader.dart';
import 'grid_control.dart';
import '../sidebars/sidebar_tools.dart';
import '../app_management/shared_app_state.dart';
import '../grpc_client_architecture/hamming_evolve_window.dart';
import '../grpc_client_architecture/server_startup.dart';
import '../app_management/version_tracker.dart';
import 'floating_main_title.dart';


class SplitScreen extends StatefulWidget {
  const SplitScreen({super.key});

  @override
  State<SplitScreen> createState() => _SplitScreenState();
}

class _SplitScreenState extends State<SplitScreen> with WidgetsBindingObserver {
  // Initial divider position as a fraction of screen width
  double _dividerPosition = 0.5;
  bool threeViewerActive = defaultTargetPlatform != TargetPlatform.linux;

  static const WidgetStateProperty<Icon> displayThumbIcon = WidgetStateProperty<Icon>.fromMap(
      <WidgetStatesConstraint, Icon>{
        WidgetState.selected: Icon(Icons.check),
        WidgetState.any: Icon(Icons.close),
      });

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      final serverNotifier = Provider.of<ServerState>(context, listen: false);
      // Launches python server
      if (!kIsWeb && !kDebugMode) {
        launchServer().then((port) {
          serverNotifier.launchClients(port);
        });
      }
      else if (kDebugMode){
        serverNotifier.launchClients(50055);
      }
    });
  }

  @override
  void dispose() {
    // Dispose of the focus nodes when done
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.detached) {
      shutdownServerIfAny();
    }
  }

  @override
  Future<AppExitResponse> didRequestAppExit() {
    shutdownServerIfAny();
    return super.didRequestAppExit();
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    CrossHatchShader.initialize(20.0);
    return Scaffold(
      body: Stack(
        children: [
          LayoutBuilder(
            builder: (context, constraints) {
              final width = constraints.maxWidth;

              // Calculate the width of each half
              final leftPaneWidth = _dividerPosition * width;
              final rightPaneWidth = (1 - _dividerPosition) * width - 10;

              return Row(
                children: [
                  // Left half: the grid
                  SizedBox(
                    width: threeViewerActive ? leftPaneWidth: width,
                    child: GridAndCanvas(),
                  ),
                  if (threeViewerActive) ... [
                    // Divider: draggable center line
                    MouseRegion(
                      cursor: SystemMouseCursors.click, // Change cursor to hand
                      child: GestureDetector(
                        behavior: HitTestBehavior.translucent,
                        onHorizontalDragUpdate: (details) {
                          setState(() {
                            _dividerPosition += details.delta.dx / width;
                            // Clamp the divider position to be between 0.2 and 0.8
                            _dividerPosition = _dividerPosition.clamp(0.2, 0.8);
                          });
                        },
                        child: Container(
                          width: 10.0,
                          color: Color(0x2C070D51),
                          child: Center(
                            child: Container(
                              width: 2.0,
                              color: Color(0x2C00D6F1),
                            ),
                          ),
                        ),
                      ),
                    ),
                    // Right half: 3D viewer
                    SizedBox(
                      width: rightPaneWidth,
                      child: FocusScope(
                        canRequestFocus: true,
                          child: ThreeDisplay()),
                    ),
                  ]
                ],
              );
            },
          ),
          SideBarTools(),
          Positioned(
            top: 0,
            left: 0,
            bottom: 0,
            child: Row(
              children: [
                NavigationRail(
                  labelType: NavigationRailLabelType.all,
                  backgroundColor: Colors.white, // Set the background color to white
                  selectedIndex: actionState.panelMode,
                  onDestinationSelected: (int index) {
                    actionState.setPanelMode(index);
                    if (actionState.isSideBarCollapsed) {
                      actionState.setSideBarStatus(false); // Ensure sidebar is open
                    }
                  },
                  leading: IconButton(
                    // Custom button above the destinations
                    icon: actionState.isSideBarCollapsed ? Icon(Icons.menu) : Icon(Icons.close),
                    onPressed: () {
                      actionState.setSideBarStatus(!actionState.isSideBarCollapsed);
                      },
                  ),
                  destinations: const [
                    NavigationRailDestination(icon: Icon(Icons.brush), label: Text('Slat\nDesign', textAlign: TextAlign.center)),
                    NavigationRailDestination(icon: Icon(Icons.developer_board), label: Text('Assembly\nHandles', textAlign: TextAlign.center)),
                    NavigationRailDestination(icon: Icon(Icons.add_box), label: Text('Cargo\n& Seed', textAlign: TextAlign.center)),
                    NavigationRailDestination(icon: Icon(Icons.precision_manufacturing), label: Text('Echo\nConfig', textAlign: TextAlign.center)),
                  ],
                  trailing: Expanded(
                    child: Column(
                      mainAxisSize: MainAxisSize.max,
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        // Add your image here
                        Image.asset(
                          'assets/main_icon.png',
                          height: 80, // Adjust the height as needed
                        ),
                        Text(
                          VersionInfo.version,
                          style: TextStyle(
                            fontSize: 10,
                            color: Colors.grey[600],
                          ),
                        ),
                        Text(
                          VersionInfo.buildCommit,
                          style: TextStyle(
                            fontSize: 8,
                            color: Colors.grey[400],
                          ),
                        ),
                        const SizedBox(height: 8),
                      ],
                    ),
                  ),
                ),
                const VerticalDivider(thickness: 1, width: 1),
              ],
            ),
          ),
          if(defaultTargetPlatform != TargetPlatform.linux) ... [
          Positioned(
            top: 16.0,
            right: 16.0,
            child: Row(
              children: [
                Text("Activate 3D Display"),
                Switch(
                  thumbIcon: displayThumbIcon,
                  value: threeViewerActive,
                  onChanged: (bool value) {
                    setState(() {
                      threeViewerActive = value;
                    });
                  },
                ),

              ],
            ),
          )],
          // Floating Title Box
          Positioned(
            top: 20,
            left: 0,
            right: 0,
            child: Center(
              child: FloatingEditableTitle(),
            ),
          ),

          HammingEvolveWindow(),


          // Overlay spinner when loading
          if (appState.currentlyLoadingDesign)
            Container(
              color: Colors.black.withValues(alpha:0.4),
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (!kIsWeb) ...[
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                    ],
                    Text(
                      'Importing design...',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
