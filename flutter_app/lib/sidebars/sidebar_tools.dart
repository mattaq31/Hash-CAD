import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'echo_sidebar.dart';
import '../app_management/shared_app_state.dart';
import 'slat_design_sidebar.dart';
import 'assembly_handles_sidebar.dart';
import 'cargo_sidebar.dart';

class SideBarTools extends StatefulWidget {
  const SideBarTools({super.key});

  @override
  State<SideBarTools> createState() => _SideBarToolsState();
}

class _SideBarToolsState extends State<SideBarTools> {

  bool collapseAnimation = false;

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();

    return AnimatedPositioned(
      duration: Duration(milliseconds: 300),
      bottom: 0,
      top: 0,
      left: 72,
      onEnd: () {
        setState(() {
          collapseAnimation = !collapseAnimation;
        });
      },
      width: actionState.isSideBarCollapsed ? 0 : 330,
      // Change width based on collapse state
      // Sidebar width
      child: Material(
        elevation: 8,
        child: Container(
          width: actionState.isSideBarCollapsed ? 0 : 330,
          color: Colors.white,
          padding: EdgeInsets.all(16),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Visibility(
                  visible: !actionState.isSideBarCollapsed && !collapseAnimation,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      FilledButton.icon(
                        onPressed: () {
                          appState.importNewDesign();
                        },
                        icon: Icon(Icons.upload, size: 18),
                        label: Text("Import"),
                        style: ElevatedButton.styleFrom(
                          padding:
                          EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          textStyle: TextStyle(fontSize: 16),
                        ),
                      ),
                      SizedBox(width: 10),
                      FilledButton.icon(
                        onPressed: () {
                          appState.exportCurrentDesign();
                        },
                        icon: Icon(Icons.download, size: 18),
                        label: Text("Export"),
                        style: ElevatedButton.styleFrom(
                          padding:
                          EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          textStyle: TextStyle(fontSize: 16),
                        ),
                      ),
                    ],
                  ),
                ),
            
                Visibility(
                  visible: !actionState.isSideBarCollapsed && !collapseAnimation,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Divider(thickness: 2, color: Colors.grey.shade300),

                      if (actionState.panelMode == 0)
                        SlatDesignTools(),
                      if (actionState.panelMode == 1)
                        AssemblyHandleDesignTools(),
                      if (actionState.panelMode == 2)
                        CargoDesignTools(),
                      if (actionState.panelMode == 3)
                        EchoTools(),
                    ],
                  ),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }
}
