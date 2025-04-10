import 'dart:math';

import 'package:flutter/material.dart';
import 'package:benchmark_harness/benchmark_harness.dart';

// Mock DesignState class
class DesignState {
  final Map<String, Map<Offset, String>> occupiedGridPoints;
  final Map<String, Slat> slats;
  final String selectedLayerKey;

  DesignState(this.occupiedGridPoints, this.slats, this.selectedLayerKey);
}

// Mock Slat class
class Slat {
  final Map<String, Offset> slatPositionToCoordinate;
  Slat(this.slatPositionToCoordinate);
}

// Sample Data Generator
DesignState generateMockDesignState(int numOccupied, int numSlats) {
  final rng = Random();
  final Map<String, Map<Offset, String>> occupiedGridPoints = {
    'layer1': {}
  };
  final Map<String, Slat> slats = {};

  for (int i = 0; i < numOccupied; i++) {
    occupiedGridPoints['layer1']![Offset(rng.nextInt(100).toDouble(), rng.nextInt(100).toDouble())] = 'slat$i';
  }

  for (int i = 0; i < numSlats; i++) {
    slats['slat$i'] = Slat({
      'pos1': Offset(rng.nextInt(100).toDouble(), rng.nextInt(100).toDouble())
    });
  }

  return DesignState(occupiedGridPoints, slats, 'layer1');
}

// Original function
bool checkCoordinateOccupancy(DesignState appState, List<Offset> coordinates, Set<String> hiddenSlats) {
  Set<Offset> occupiedPositions = appState.occupiedGridPoints[appState.selectedLayerKey]?.keys.toSet() ?? {};
  Set<Offset> hiddenPositions = {};

  for (var slat in hiddenSlats) {
    hiddenPositions.addAll(appState.slats[slat]?.slatPositionToCoordinate.values ?? {});
  }

  for (var coord in coordinates) {
    if (occupiedPositions.contains(coord) && !hiddenPositions.contains(coord)) {
      return true;
    }
  }
  return false;
}

// Optimized function
bool optimizedCheckCoordinateOccupancy(DesignState appState, List<Offset> coordinates, Set<String> hiddenSlats) {
  final occupiedPositions = appState.occupiedGridPoints[appState.selectedLayerKey]?.keys;
  if (occupiedPositions == null) return false;

  final hiddenPositions = <Offset>{};
  for (var slat in hiddenSlats) {
    hiddenPositions.addAll(appState.slats[slat]?.slatPositionToCoordinate.values ?? {});
  }

  for (var coord in coordinates) {
    if (occupiedPositions.contains(coord) && !hiddenPositions.contains(coord)) {
      return true;
    }
  }
  return false;
}

// Optimized function
bool optimizedCheckCoordinateOccupancyv2(DesignState appState, List<Offset> coordinates, Set<String> hiddenSlats) {
  final selectedLayerKey = appState.selectedLayerKey;
  final occupiedPositions = appState.occupiedGridPoints[selectedLayerKey]?.keys.toSet() ?? {};

  // Early exit if no occupied positions exist
  if (occupiedPositions.isEmpty) return false;

  // Collect hidden positions
  final hiddenPositions = hiddenSlats.expand((slat) => appState.slats[slat]!.slatPositionToCoordinate.values).toSet();

  // Compute effective occupied positions
  occupiedPositions.removeAll(hiddenPositions);

  // Check for intersection between occupied positions and coordinates
  return occupiedPositions.intersection(coordinates.toSet()).isNotEmpty;
}

// Benchmark Base Class
class CheckOccupancyBenchmark extends BenchmarkBase {
  final DesignState appState;
  final List<Offset> coordinates;
  final Set<String> hiddenSlats;
  final bool Function(DesignState, List<Offset>, Set<String>) functionToTest;

  CheckOccupancyBenchmark(String name, this.appState, this.coordinates, this.hiddenSlats, this.functionToTest) : super(name);

  @override
  void run() {
    functionToTest(appState, coordinates, hiddenSlats);
  }
}

void main() {
  final appState = generateMockDesignState(5000, 1000);
  final coordinates = List.generate(100, (index) => Offset(index.toDouble(), index.toDouble()));
  final hiddenSlats = {'slat1', 'slat2'};

  // sleep for 5 s
  CheckOccupancyBenchmark('Optimized', appState, coordinates, hiddenSlats, optimizedCheckCoordinateOccupancy).report();
  CheckOccupancyBenchmark('Optimizedv2', appState, coordinates, hiddenSlats, optimizedCheckCoordinateOccupancyv2).report();
  CheckOccupancyBenchmark('Original', appState, coordinates, hiddenSlats, checkCoordinateOccupancy).report();
  CheckOccupancyBenchmark('Optimized', appState, coordinates, hiddenSlats, optimizedCheckCoordinateOccupancy).report();

}