import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'shared_app_state.dart';
import 'line_chart.dart';
import 'rating_indicator.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:file_picker/file_picker.dart';


class HammingEvolveWindow extends StatefulWidget {
  const HammingEvolveWindow({
    super.key,
  });

  @override
  State<HammingEvolveWindow> createState() => _HammingEvolveWindowState();
}

class _HammingEvolveWindowState extends State<HammingEvolveWindow> {
  bool isCollapsed = false;
  bool isHovered = false;
  bool animationComplete = true; // only enables item visibility when the animation is complete i.e. box is fully extended
  bool advancedExpanded = false;

  final Map<int, String> defaultParams = {
    2: 'mutation_rate',
    6: 'mutation_type_probabilities',
    1: 'evolution_generations',
    3: 'evolution_population',
    4: 'process_count',
    5: 'generational_survivors',
    7: 'seed'
  };

  final Map<String, TextEditingController> controllers = {};

  @override
  void initState() {
    super.initState();
    var serverState = context.read<ServerState>(); // Read once in initState
    for (var key in defaultParams.values) {
      controllers[key] = TextEditingController(text: serverState.evoParams[key] ?? "");
    }
  }

  @override
  void dispose() {
    for (var controller in controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final double screenWidth = MediaQuery.of(context).size.width;

    final double fullHeight = 500;
    final double minimizedHeight = 40;
    final double advancedHeight = 650; // Adjust based on extra content

    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    var serverState = context.watch<ServerState>();

    return Opacity(
      opacity: actionState.evolveMode ? 1.0 : 0.0,
      child: Stack(
        children: [
          AnimatedPositioned(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
            top: actionState.evolveMode ? 0 : -fullHeight,
            // Slide in from the top
            left: (screenWidth - 750) / 2,
            // Centered horizontally
            width: 750,
            // Fixed width
            height: isCollapsed ? minimizedHeight : (advancedExpanded ? advancedHeight : fullHeight),
            onEnd: () {
              setState(() {
                if (!isCollapsed){
                  animationComplete = false;
                }
                if (isCollapsed){
                  animationComplete = true;
                }
              });
            },
            child: Material(
              elevation: 10,
              borderRadius: BorderRadius.circular(12),
              color: Colors.white,
              child: Column(
                children: [
                  // Header (minimize/maximize + close button)
                  MouseRegion(
                    onEnter: (_) => setState(() => isHovered = true),
                    onExit: (_) => setState(() => isHovered = false),
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          isCollapsed = !isCollapsed;
                          advancedExpanded = false;
                        });
                      },
                      child: Container(
                        height: minimizedHeight,
                        decoration: BoxDecoration(
                          color: isHovered
                              ? Colors.blueGrey.shade600
                              : Colors.blueGrey,
                          borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(12)),
                        ),
                        child: SizedBox(
                          width: double.infinity,
                          // Make sure it takes the full width
                          child: Stack(
                            alignment: Alignment.center,
                            children: [
                              Positioned(
                                left: 0,
                                child: IconButton(
                                  icon: const Icon(Icons.close,
                                      color: Colors.white, size: 18),
                                  onPressed: () {
                                    setState(() {
                                      if (serverState.evoActive || serverState.hammingMetrics.isNotEmpty){
                                        serverState.stopEvolve();
                                      }
                                      actionState.deactivateEvolveMode();
                                    });
                                  },
                                ),
                              ),
                              // Title (click to minimize/maximize)
                              const Text(
                                'Hamming Evolution Tracker',
                                style: TextStyle(
                                    color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                              // Close button (positioned on the left)
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                  if (!isCollapsed && !animationComplete) ...[
                    // Line Graph
                    const SizedBox(height: 20),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Row(
                          children: [
                            Expanded(
                                child: StandardLineChart(
                                    'Evo. Iteration',
                                    'Worst Slat Mismatch Score',
                                    List.generate(
                                        serverState.hammingMetrics.length,
                                        (index) => FlSpot(
                                            index.toDouble(),
                                            32-serverState
                                                .hammingMetrics[index])))),
                            const SizedBox(width: 16),
                            Expanded(child: StandardLineChart('Evo. Iteration', 'Physics Score', List.generate(
                                serverState.physicsMetrics.length,
                                    (index) => FlSpot(
                                    index.toDouble(),
                                    serverState
                                        .physicsMetrics[index])))),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 30),
                    Center(
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text("Current Mismatch Score", style: TextStyle(fontSize: 20)),
                          SizedBox(width: 20),
                          HammingIndicator(value: serverState.hammingMetrics.isNotEmpty
                              ? serverState.hammingMetrics.last
                              : 0.0,),
                          SizedBox(width: 50),
                          Text("Target Mismatch Score", style: TextStyle(fontSize: 20)),
                          SizedBox(width: 20),
                          HammingIndicator(value: 30.0),
                        ],
                      ),
                    ),
                    SizedBox(height: 20),
                    // Expandable Text Button
                    GestureDetector(
                      onTap: () {
                        setState(() {
                          advancedExpanded = !advancedExpanded;
                        });
                      },
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text("Advanced Settings", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          Icon(advancedExpanded ? Icons.arrow_drop_up : Icons.arrow_drop_down),
                        ],
                      ),
                    ),
                    // Expandable Text Fields
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      curve: Curves.easeInOut,
                      height: advancedExpanded ? advancedHeight - fullHeight : 0, // Expand smoothly
                      child: SingleChildScrollView(
                        child: Padding(
                          padding: const EdgeInsets.all(12.0),
                          child: Column(
                            children: [
                              ...List.generate(2, (row) {
                                return Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: List.generate(
                                    4,
                                        (col) {
                                      int index = row * 4 + col + 1;
                                      if (!defaultParams.containsKey(index)) return SizedBox();

                                      String paramKey = defaultParams[index]!;
                                      String label = serverState.paramLabels[paramKey]!;
                                      return Expanded(
                                        child: Padding(
                                          padding: const EdgeInsets.all(8.0),
                                          child: TextField(
                                            controller: controllers[paramKey],
                                            decoration: InputDecoration(
                                              border: OutlineInputBorder(),
                                              labelText: label, // Now using human-readable label
                                            ),
                                            onChanged: (value) {
                                              serverState.updateEvoParam(paramKey, value);
                                            },
                                          ),
                                        ),
                                      );
                                    },
                                  ),
                                );
                              }),
                            ],
                          ),
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Center(
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            FilledButton.icon(
                              onPressed: serverState.evoActive
                                  ? null
                                  : () {
                                serverState.evolveAssemblyHandles(appState.getSlatArray());
                              },
                              icon: const Icon(Icons.play_arrow, size: 18),
                              label: const Text("Start"),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green, // Red background
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 12),
                                textStyle: const TextStyle(fontSize: 16),
                              ),
                            ),
                            const SizedBox(width: 12),
                            FilledButton.icon(
                              onPressed: !serverState.evoActive
                                  ? null
                                  : () {
                                serverState.pauseEvolve();
                              },
                              icon: const Icon(Icons.pause, size: 18),
                              label: const Text("Pause"),
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 12),
                                textStyle: const TextStyle(fontSize: 16),
                              ),
                            ),
                            const SizedBox(width: 12),
                            FilledButton.icon(
                              onPressed: serverState.hammingMetrics.isEmpty ? null :  () {
                                serverState.stopEvolve().then((result) {
                                appState.assignAssemblyHandleArray(result, null, null);
                              });
                              },
                              icon: const Icon(Icons.stop_circle, size: 18),
                              label: const Text("Stop & Save"),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.red, // Red background
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 12),
                                textStyle: const TextStyle(fontSize: 16),
                              ),
                            ),
                            const SizedBox(width: 12),
                            FilledButton.icon(
                              onPressed: () async {
                                // main user dialog box for file selection
                                String? selectedDirectory = await FilePicker.platform.getDirectoryPath();
                                if (selectedDirectory != null) {
                                  serverState.exportRequest(selectedDirectory); // Send folder path instead of file path
                                }
                              },
                              icon: const Icon(Icons.share, size: 18),
                              label: const Text("Export Run"),
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 12),
                                textStyle: const TextStyle(fontSize: 16),
                              ),
                            ),
                            const SizedBox(width: 12),
                            FilledButton.icon(
                              onPressed: null,
                              icon: const Icon(Icons.code, size: 18),
                              label: const Text("Export Script"),
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 12),
                                textStyle: const TextStyle(fontSize: 16),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
