import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'shared_app_state.dart';
import 'line_chart.dart';
import 'rating_indicator.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:async';


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

  List<FlSpot> hammingDistanceData = [FlSpot(0, 5)]; // Starts with one point
  List<FlSpot> physicsScoreData = [FlSpot(0, 3)];

  void addHammingDataPoint(double x, double y) {
    setState(() {
      hammingDistanceData.add(FlSpot(x, y));
    });
  }

  // Method to add a new data point to the Physics Score chart
  void addPhysicsDataPoint(double x, double y) {
    setState(() {
      physicsScoreData.add(FlSpot(x, y));
    });
  }

  @override
  Widget build(BuildContext context) {
    final double screenWidth = MediaQuery.of(context).size.width;
    final double fullHeight = 500;
    final double minimizedHeight = 40;
    Timer? simulationTimer;

    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();

    return Opacity(
      opacity: actionState.evolveMode ? 1.0 : 0.0,
      child: Stack(
        children: [
          AnimatedPositioned(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
            top: actionState.evolveMode ? 0 : -fullHeight,
            // Slide in from the top
            left: (screenWidth - 650) / 2,
            // Centered horizontally
            width: 650,
            // Fixed width
            height: isCollapsed ? minimizedHeight : fullHeight,
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
                  if (!isCollapsed) ...[
                    // Line Graph
                    const SizedBox(height: 20),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Row(
                          children: [
                            Expanded(child: StandardLineChart('Evo. Iteration', 'Hamming Distance', hammingDistanceData)),
                            const SizedBox(width: 16),
                            Expanded(child: StandardLineChart('Evo. Iteration', 'Physics Score', physicsScoreData)),
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
                          Text("Current Score",
                              style: TextStyle(
                                  fontSize: 16)),
                          SizedBox(width: 20),
                          RatingIndicator(rating: 60.0),
                          SizedBox(width: 20),
                          Text("Target Score",
                              style: TextStyle(
                                  fontSize: 16)),
                          SizedBox(width: 20),
                          RatingIndicator(rating: 90.0),
                        ],
                      ),
                    ),
                    const SizedBox(height: 30),
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: Center(
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            FilledButton.icon(
                              onPressed: () {

                                // this can simulate the addition of data into the charts
                                // simulationTimer = Timer.periodic(Duration(seconds: 1), (timer) {
                                //   final nextIndex = hammingDistanceData.length.toDouble();
                                //
                                //   // Add random or calculated points
                                //   addHammingDataPoint(
                                //     nextIndex,
                                //     5.0 - (0.5 * nextIndex).clamp(0, 5), // Example formula
                                //   );
                                //
                                //   addPhysicsDataPoint(
                                //     nextIndex,
                                //     3.0 + (nextIndex * 0.3).clamp(0, 3), // Different formula
                                //   );
                                //
                                //   // Optional: stop after certain number of points
                                //   if (hammingDistanceData.length > 20) {
                                //     timer.cancel();
                                //   }
                                // });
                              },
                              icon: const Icon(Icons.play_arrow, size: 18),
                              label: const Text("Start"),
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 12),
                                textStyle: const TextStyle(fontSize: 16),
                              ),
                            ),
                            const SizedBox(width: 12),
                            FilledButton.icon(
                              onPressed: () {
                                // Handle button action here
                              },
                              icon: const Icon(Icons.stop_circle, size: 18),
                              label: const Text("Stop & Save"),
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 12),
                                textStyle: const TextStyle(fontSize: 16),
                              ),
                            ),
                            const SizedBox(width: 12),
                            FilledButton.icon(
                              onPressed: () {
                                // Handle button action here
                              },
                              icon: const Icon(Icons.share, size: 18),
                              label: const Text("Export Run Info"),
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
