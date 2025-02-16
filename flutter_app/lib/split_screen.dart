import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '3d_painter.dart';
import 'crosshatch_shader.dart';
import 'grid_painter.dart';
import 'sidebar_tools.dart';
import 'shared_app_state.dart';

class SplitScreen extends StatefulWidget {
  const SplitScreen({super.key});

  @override
  State<SplitScreen> createState() => _SplitScreenState();
}

class _SplitScreenState extends State<SplitScreen> {
  // Initial divider position as a fraction of screen width
  double _dividerPosition = 0.5;

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
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
                    width: leftPaneWidth,
                    child: GridAndCanvas(),
                  ),
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
                    child: ThreeDisplay(),
                  ),
                ],
              );
            },
          ),
          SideBarTools(),
        ],
      ),
    );
  }
}
