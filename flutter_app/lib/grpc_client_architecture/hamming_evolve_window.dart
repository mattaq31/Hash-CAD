import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';
import '../graphics/line_chart.dart';
import '../graphics/rating_indicator.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:file_picker/file_picker.dart';
import 'package:dotted_border/dotted_border.dart';
import 'package:flutter/foundation.dart';

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
  double hammingTargetValue = 30.0;

  final Map<int, String> defaultParams = {
    2: 'mutation_rate',
    6: 'mutation_type_probabilities',
    1: 'evolution_generations',
    3: 'evolution_population',
    4: 'process_count',
    5: 'generational_survivors',
    7: 'random_seed'
  };

  final Map<String, TextEditingController> controllers = {};

  // Function to determine the color
  Color _getStatusColor(String status) {
    switch (status) {
      case "RUNNING":
        return Colors.green;
      case "PAUSED":
        return Colors.orange;
      case "IDLE":
        return Colors.red;
      case "BACKEND INACTIVE":
        return Colors.deepPurple;
      case "EVOLUTION COMPLETE - MAKE SURE TO SAVE RESULT":
        return Colors.blue;
      default:
        return Colors.black;
    }
  }

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

  void increaseValue(ServerState serverState) {
    setState(() {
      hammingTargetValue  = (hammingTargetValue < 32) ? hammingTargetValue + 1.0 : 32.0;
      serverState.updateEvoParam('early_hamming_stop', hammingTargetValue.toString());// Increment by 1
    });
  }

  void decreaseValue(ServerState serverState) {
    setState(() {
      hammingTargetValue = (hammingTargetValue > 0) ? hammingTargetValue - 1.0 : 0.0;  // Ensure non-negative
      serverState.updateEvoParam('early_hamming_stop', hammingTargetValue.toString());// Increment by 1
    });
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

    // initiates server healthcheck
    if (!serverState.serverActive && !serverState.serverCheckInProgress  && !kIsWeb) {
      serverState.startupServerHealthCheck();
    }

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
                                    'Worst Mismatch\n Score',
                                    List.generate(
                                        serverState.hammingMetrics.length,
                                        (index) => FlSpot(
                                            index.toDouble(),
                                            32-serverState
                                                .hammingMetrics[index])))),
                            const SizedBox(width: 16),
                            Expanded(child: StandardLineChart('Evo. Iteration', 'Partition Score', List.generate(
                                serverState.physicsMetrics.length,
                                    (index) => FlSpot(
                                    index.toDouble(),
                                    serverState
                                        .physicsMetrics[index])))),
                          ],
                        ),
                      ),
                    ),
                    // const SizedBox(height: 30),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text.rich(
                          TextSpan(
                            text: "Algorithm Status: ",
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            children: [
                              TextSpan(
                                text: serverState.statusIndicator,
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: _getStatusColor(serverState.statusIndicator),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 15),
                    Center(
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              DottedBorder(
                                  color: Colors.grey.shade400,
                                  strokeWidth: 1,
                                  radius: Radius.circular(12),
                                  padding: EdgeInsets.all(25),
                                  borderType: BorderType.RRect,
                                  child: Row(
                                    children: [
                                      Text("Current Mismatch Score",
                                          style: TextStyle(fontSize: 16)),
                                      SizedBox(width: 20),
                                      HammingIndicator(
                                        value: serverState.hammingMetrics.isNotEmpty
                                            ? serverState.hammingMetrics.last
                                            : 0.0,),
                                    ],
                                  )),
                              SizedBox(width: 50),
                              DottedBorder(
                                color: Colors.grey.shade400,
                                strokeWidth: 1,
                                radius: Radius.circular(12),
                                padding: EdgeInsets.all(15),
                                borderType: BorderType.RRect,
                                child: Row(
                                  children: [
                                    Text("Target Mismatch Score", style: TextStyle(fontSize: 16)),
                                    SizedBox(width: 20),
                                    HammingIndicator(value: hammingTargetValue),
                                    Column(
                                      children: [
                                        IconButton(
                                          icon: Icon(Icons.arrow_circle_up),
                                          onPressed: serverState.statusIndicator != 'IDLE' ? null : (){
                                            increaseValue(serverState);
                                          },
                                        ),
                                        IconButton(
                                          icon: Icon(Icons.arrow_circle_down),
                                          onPressed: serverState.statusIndicator != 'IDLE' ? null : () {
                                            decreaseValue(serverState);
                                            },
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
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
                          Text("Advanced Settings", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
                              onPressed: serverState.evoActive || !serverState.serverActive || appState.slats.isEmpty || serverState.statusIndicator == 'EVOLUTION COMPLETE - MAKE SURE TO SAVE RESULT'
                                  ? null
                                  : () {
                                serverState.evolveAssemblyHandles(appState.getSlatArray(), appState.getHandleArray());
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
                              onPressed: !serverState.evoActive || !serverState.serverActive
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
                              onPressed: serverState.hammingMetrics.isEmpty  || !serverState.serverActive ? null :  () {
                                serverState.stopEvolve().then((result) {
                                appState.assignAssemblyHandleArray(result, null, null);
                                appState.updateDesignHammingValue();
                                actionState.setAssemblyHandleDisplay(true);
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
                              onPressed: serverState.hammingMetrics.isEmpty  || !serverState.serverActive ? null : () async {
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
