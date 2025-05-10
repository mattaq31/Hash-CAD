import 'dart:math';
import 'package:flutter/foundation.dart';

import 'slats.dart';

List<List<List<int>>> generateRandomSlatHandles(List<List<List<int>>> baseArray, int uniqueSequences, {int seed=8}) {
  int xSize = baseArray.length;
  int ySize = baseArray[0].length;
  int numLayers = baseArray[0][0].length;

  List<List<List<int>>> handleArray = List.generate(xSize, (_) => List.generate(ySize, (_) => List.filled(numLayers-1, 0)));

  Random rand = Random(seed);
  for (int i = 0; i < xSize; i++) {
    for (int j = 0; j < ySize; j++) {
      for (int k = 0; k < numLayers - 1; k++) {
        // Check if slats exist in the current and next layer
        if (baseArray[i][j][k] != 0 && baseArray[i][j][k + 1] != 0) {
          handleArray[i][j][k] = rand.nextInt(uniqueSequences) + 1; // Random value between 1 and uniqueSequences
        }
      }
    }
  }
  return handleArray;
}

List<List<List<int>>> generateLayerSplitHandles(List<List<List<int>>> baseArray, int uniqueSequences, {int seed = 8}) {
  int xSize = baseArray.length;
  int ySize = baseArray[0].length;
  int numLayers = baseArray[0][0].length;

  // Initialize the handle array with zeros
  List<List<List<int>>> handleArray = List.generate(xSize, (_) => List.generate(ySize, (_) => List.filled(numLayers - 1, 0)));

  Random rand = Random(seed);

  for (int i = 0; i < xSize; i++) {
    for (int j = 0; j < ySize; j++) {
      for (int k = 0; k < numLayers - 1; k++) {

        int h1, h2;
        if (k % 2 == 0) {
          h1 = 1;
          h2 = (uniqueSequences ~/ 2) + 1;
        } else {
          h1 = (uniqueSequences ~/ 2) + 1;
          h2 = uniqueSequences + 1;
        }

        // Check if slats exist in the current and next layer
        if (baseArray[i][j][k] != 0 && baseArray[i][j][k + 1] != 0) {
          handleArray[i][j][k] = rand.nextInt(h2 - h1) + h1; // Random value between 1 and uniqueSequences
        }
      }
    }
  }

  return handleArray;
}

List<int> shiftLeftWithZeros(List<int> lst, int shift) {
  return List.generate(lst.length, (i) => (i + shift < lst.length) ? lst[i + shift] : 0);
}
List<int> shiftRightWithZeros(List<int> lst, int shift) {
  return List.generate(lst.length, (i) => (i - shift >= 0) ? lst[i - shift] : 0);
}

class HammingInnerArgs {
  /// these arguments are combined so they can be transferred to the isolate function
  final Map<String, List<int>> handleDict;
  final Map<String, List<int>> antihandleDict;
  final int slatLength;

  HammingInnerArgs(this.handleDict, this.antihandleDict, this.slatLength);
}

int hammingInnerCompute(HammingInnerArgs args) {
  /// this part of the compute is split off so it can be run inside an isolate
  final handleDict = args.handleDict;
  final antihandleDict = args.antihandleDict;
  final slatLength = args.slatLength;

  // Computes hamming by running through the usual motions - generate 4 * 32 candidates per handle/antihandle slat pair and check all rotations/translations
  // As opposed to the python version, everything is calculated on the fly here since loops are much faster to compute than Python.
  final handleKeys = handleDict.keys.toList();
  final antihandleKeys = antihandleDict.keys.toList();

  int minValue = 50;

  for (int i = 0; i < handleKeys.length; i++) {
    final handle = handleDict[handleKeys[i]]!;
    final reversedHandle = handle.reversed.toList();

    for (int j = 0; j < antihandleKeys.length; j++) {
      final antihandle = antihandleDict[antihandleKeys[j]]!;

      for (int shift = 0; shift < slatLength; shift++) {
        final List<List<int>> candidates = [
          shiftLeftWithZeros(handle, shift),
          shiftRightWithZeros(handle, shift),
          shiftLeftWithZeros(reversedHandle, shift),
          shiftRightWithZeros(reversedHandle, shift),
        ];
        for (final candidate in candidates) {
          int dist = 0;
          for (int k = 0; k < slatLength; k++) {
            final a = candidate[k];
            final b = antihandle[k];
            if (a == 0 || b == 0 || a != b) dist++;
          }
          minValue = min(minValue, dist);
        }
      }
    }
  }
  return minValue;
}


Future<int> hammingCompute(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap, int slatLength) async {
  /// Computes the hamming distance of the current design in view.
  /// Function not optimized but will be infrequently called so slowdown is expected to be minimal.
  ///  Mimics logic in 'precise hamming compute' in the python library.

  Map<String, List<int>> handleDict = {};
  Map<String, List<int>> antihandleDict = {};

  //BE CAREFUL, THIS MAKES THE ASSUMPTION THAT HANDLES ARE ALWAYS ON THE TOP OF A SLAT AND VICE VERSA
  // curates all handles/antihandles into two dicts
  for (final slat in slats.values) {
    final layerInfo = layerMap[slat.layer]!;
    final h5OnTop = layerInfo['top_helix'] == 'H5';
    final topBottomOrder = h5OnTop ? ['H2', 'H5'] : ['H5', 'H2'];

    final order = layerInfo['order'];
    final isFirstLayer = order == 0;
    final isLastLayer = order == layerMap.length - 1;

    final includeHandle = !isLastLayer;
    final includeAntiHandle = !isFirstLayer;

    for (var tb = 0; tb < 2; tb++) {
      final isTop = tb == 1;
      final include = (isTop && includeHandle) || (!isTop && includeAntiHandle);
      if (!include) continue;

      final isHandle = isTop ? true : false; // handles on top of slat, antihandles on the bottom of a slat
      final dict = isHandle ? handleDict : antihandleDict;
      final List<int> descriptorList = List.filled(slat.maxLength, 0);
      final useH5 = topBottomOrder[tb] == 'H5';

      for (var i = 0; i < slat.maxLength; i++) {
        final handleData = useH5 ? slat.h5Handles[i + 1] : slat.h2Handles[i + 1];
        if (handleData != null && handleData['category'] == 'Assembly') {
          descriptorList[i] = int.parse(handleData['descriptor']);
        }
      }

      dict[slat.id] = descriptorList;
    }
  }
  final args = HammingInnerArgs(handleDict, antihandleDict, slatLength);
  return await compute(hammingInnerCompute, args);
}