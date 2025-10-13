import '../app_management/shared_app_state.dart';
import '../graphics/line_chart.dart';
import '../sidebars/assembly_handles_sidebar.dart';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:file_picker/file_picker.dart';
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

  bool _progressHovering = false;
  double _progressHoverX = 0.0;

  final Map<int, String> defaultParams = {
    2: 'mutation_rate',
    6: 'mutation_type_probabilities',
    1: 'evolution_generations',
    3: 'evolution_population',
    4: 'process_count',
    5: 'generational_survivors',
    7: 'random_seed',
    8: 'early_max_valency_stop'
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
      case "EVOLUTION COMPLETE - SAVE RESULTS!":
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
      controllers[key] =
          TextEditingController(text: serverState.evoParams[key] ?? "");
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

    final double fullHeight = 600;
    final double minimizedHeight = 40;
    final double advancedHeight = 750; // Adjust based on extra content

    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    var serverState = context.watch<ServerState>();

    // progress bar metrics
    final int current = serverState.hammingMetrics.length;
    final int total =
        int.tryParse(serverState.evoParams['evolution_generations'] ?? '1') ??
            1;
    final double progress = current / total;

    // initiates server healthcheck
    if (!serverState.serverActive &&
        !serverState.serverCheckInProgress &&
        !kIsWeb) {
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
            height: isCollapsed
                ? minimizedHeight
                : (advancedExpanded ? advancedHeight : fullHeight),
            onEnd: () {
              setState(() {
                if (!isCollapsed) {
                  animationComplete = false;
                }
                if (isCollapsed) {
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
                                      if (serverState.evoActive ||
                                          serverState
                                              .hammingMetrics.isNotEmpty) {
                                        serverState.stopEvolve();
                                      }
                                      actionState.deactivateEvolveMode();
                                    });
                                  },
                                ),
                              ),
                              // Title (click to minimize/maximize)
                              const Text(
                                'Assembly Handle Evolution',
                                style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold),
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
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text.rich(
                          TextSpan(
                            text: "Algorithm Status: ",
                            style: const TextStyle(
                                fontSize: 20, fontWeight: FontWeight.bold),
                            children: [
                              TextSpan(
                                text: serverState.statusIndicator,
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: _getStatusColor(
                                      serverState.statusIndicator),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 5),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const SizedBox(height: 4),
                        Center(
                          child: SizedBox(
                            width: 600,
                            child: Column(
                              crossAxisAlignment:
                              CrossAxisAlignment.stretch,
                              children: [

                                LayoutBuilder(
                                  builder: (context, constraints) {
                                    final width = constraints.maxWidth;
                                    return MouseRegion(
                                      onEnter: (_) => setState(() => _progressHovering = true),
                                      onExit: (_) => setState(() => _progressHovering = false),
                                      onHover: (event) =>
                                          setState(() => _progressHoverX = event.localPosition.dx.clamp(0.0, width)),
                                      child: Stack(
                                        clipBehavior: Clip.none,
                                        children: [
                                          ClipRRect(
                                            borderRadius: BorderRadius.circular(10),
                                            child: LinearProgressIndicator(
                                              value: progress,
                                              minHeight: 12,
                                              backgroundColor: Colors.grey.shade300,
                                              valueColor: AlwaysStoppedAnimation<Color>(
                                                serverState.hammingMetrics.isNotEmpty
                                                    ? getValencyColor(serverState.hammingMetrics.last.toInt())
                                                    : Colors.redAccent,
                                              ),
                                            ),
                                          ),
                                          if (_progressHovering)
                                            Positioned(
                                              left: (_progressHoverX - 36).clamp(0.0, width - 72),
                                              top: -38,
                                              child: Material(
                                                color: Colors.transparent,
                                                elevation: 2,
                                                child: Container(
                                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                                                  decoration: BoxDecoration(
                                                    color: Colors.black87,
                                                    borderRadius: BorderRadius.circular(6),
                                                  ),
                                                  child: Text(
                                                    // compute generation from hover fraction and total (uses `total` from surrounding scope)
                                                    'Currently at Generation $current',
                                                    style: const TextStyle(color: Colors.white, fontSize: 12),
                                                  ),
                                                ),
                                              ),
                                            ),
                                        ],
                                      ),
                                    );
                                  },
                                ),
                                Row(
                                  mainAxisAlignment:
                                  MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text('0'),
                                    Text('$total'),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Center(
                          child: Transform.translate(
                            offset: const Offset(-18, 0), // shift both charts left slightly
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                SizedBox(
                                  width: 330,
                                  child: StandardLineChart(
                                    'Generation',
                                    'Max. Valency',
                                    List.generate(
                                      serverState.hammingMetrics.length,
                                          (index) => FlSpot(index.toDouble(), serverState.hammingMetrics[index]),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 16),
                                SizedBox(
                                  width: 330,
                                  child: StandardLineChart(
                                    'Generation',
                                    'Eff. Valency',
                                    List.generate(
                                      serverState.physicsMetrics.length,
                                          (index) => FlSpot(index.toDouble(), double.parse(serverState.physicsMetrics[index].toStringAsFixed(3))),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 5),
                    Center(
                      child: Column(
                        children: [
                          const SizedBox(height: 5),
                          const Text(
                            "Minimized Parasitic Interaction Scores",
                            style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 10),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Container(
                                width: 240,
                                padding: const EdgeInsets.all(20),
                                margin: const EdgeInsets.only(bottom: 2),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: serverState.hammingMetrics.isNotEmpty ? getValencyColor(serverState.hammingMetrics.last.toInt()) : Colors.redAccent, width: 1),
                                  boxShadow: [
                                    BoxShadow(
                                      color:
                                      serverState.hammingMetrics.isNotEmpty ? getValencyColor(serverState.hammingMetrics.last.toInt()) : Colors.redAccent,
                                      blurRadius: 6,
                                      spreadRadius: 2,
                                    ),
                                  ],
                                ),
                                child: Row(
                                  mainAxisAlignment:
                                      MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text(
                                      "Maximum Valency",
                                      style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold),
                                    ),
                                    Text(
                                      serverState.hammingMetrics.isNotEmpty
                                          ? serverState.hammingMetrics.last
                                              .toString()
                                          : '0',
                                      style: const TextStyle(
                                          fontSize: 20,
                                          fontWeight: FontWeight.w600),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 30),
                              Container(
                                width: 240,
                                padding: const EdgeInsets.all(20),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                      color: Colors.grey.shade400, width: 1),
                                  boxShadow: [
                                    BoxShadow(
                                      color:
                                          Colors.black.withValues(alpha: 0.05),
                                      blurRadius: 6,
                                      offset: const Offset(0, 3),
                                    ),
                                  ],
                                ),
                                child: Row(
                                  mainAxisAlignment:
                                      MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text(
                                      "Effective Valency",
                                      style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold),
                                    ),
                                    Text(
                                      serverState.physicsMetrics.isNotEmpty
                                          ? serverState.physicsMetrics.last
                                              .toStringAsFixed(2)
                                          : '0',
                                      style: const TextStyle(
                                          fontSize: 20,
                                          fontWeight: FontWeight.w600),
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
                          Text("Advanced Settings",
                              style: TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.bold)),
                          Icon(advancedExpanded
                              ? Icons.arrow_drop_up
                              : Icons.arrow_drop_down),
                        ],
                      ),
                    ),
                    // Expandable Text Fields
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      curve: Curves.easeInOut,
                      height: advancedExpanded
                          ? advancedHeight - fullHeight
                          : 0, // Expand smoothly
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
                                      if (!defaultParams.containsKey(index))
                                        return SizedBox();

                                      String paramKey = defaultParams[index]!;
                                      String label =
                                          serverState.paramLabels[paramKey]!;
                                      return Expanded(
                                        child: Padding(
                                          padding: const EdgeInsets.all(8.0),
                                          child: TextField(
                                            enabled:
                                                serverState.statusIndicator ==
                                                    'IDLE',
                                            readOnly:
                                                serverState.statusIndicator !=
                                                    'IDLE',
                                            controller: controllers[paramKey],
                                            decoration: InputDecoration(
                                              border: OutlineInputBorder(),
                                              labelText:
                                                  label, // Now using human-readable label
                                            ),
                                            onChanged: (value) {
                                              serverState.updateEvoParam(
                                                  paramKey, value);
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
                              onPressed: serverState.evoActive ||
                                      !serverState.serverActive ||
                                      appState.slats.isEmpty ||
                                      serverState.statusIndicator ==
                                          'EVOLUTION COMPLETE - SAVE RESULTS!'
                                  ? null
                                  : () {
                                      serverState.evolveAssemblyHandles(
                                          appState.getSlatArray(),
                                          appState.getHandleArray(),
                                          appState.getSlatTypes(),
                                          appState.gridMode);
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
                              onPressed: !serverState.evoActive ||
                                      !serverState.serverActive
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
                              onPressed: serverState.hammingMetrics.isEmpty ||
                                      !serverState.serverActive
                                  ? null
                                  : () {
                                      serverState.stopEvolve().then((result) {
                                        appState.assignAssemblyHandleArray(
                                            result, null, null);
                                        appState.updateDesignHammingValue();
                                        actionState
                                            .setAssemblyHandleDisplay(true);
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
                              onPressed: serverState.hammingMetrics.isEmpty ||
                                      !serverState.serverActive
                                  ? null
                                  : () async {
                                      // main user dialog box for file selection
                                      String? selectedDirectory =
                                          await FilePicker.platform
                                              .getDirectoryPath();
                                      if (selectedDirectory != null) {
                                        serverState.exportRequest(
                                            selectedDirectory); // Send folder path instead of file path
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
                              onPressed: serverState.exportParameters,
                              icon: const Icon(Icons.code, size: 18),
                              label: const Text("Export Parameters"),
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
