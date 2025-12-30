import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/assembly_handles.dart';
import '../../crisscross_core/sparse_to_array_conversion.dart';
import '../main_design_io.dart';

/// Mixin containing handle assignment and assembly handle operations for DesignState
mixin DesignStateHandleMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;

  Map<String, Map<String, dynamic>> get layerMap;

  Map<String, Map<Offset, String>> get occupiedGridPoints;

  Map<String, Map<int, String>> get phantomMap;

  double get gridSize;

  String get gridMode;

  int get currentMaxValency;

  set currentMaxValency(int value);

  double get currentEffValency;

  set currentEffValency(double value);

  bool get hammingValueValid;

  set hammingValueValid(bool value);

  bool get currentlyComputingHamming;

  set currentlyComputingHamming(bool value);

  // Methods from other mixins
  void saveUndoState();

  String? getLayerByOrder(int order);

  void undo2DAction({bool redo = false});

  void setSlatHandle(Slat slat, int position, int side, String handlePayload, String category) {
    if (slat.phantomParent != null && !category.contains('ASSEMBLY')) {
      return; // cannot directly apply cargo handle changes to phantom slats
    }

    // for assembly handles, need to check if there are any phantom slats linked to this slat, and apply the handle to them too
    if (category.contains('ASSEMBLY')) {
      List<(String, int, int)> slatsUpdated = [];
      // this recursive function checks for: 1) direct phantom links, 2) other handles attached to phantom slats, 3) further handles attached to those slats, etc.
      void recursivePhantomSearch(Slat querySlat, int queryPosition, int querySide, String queryCategory) {
        querySlat.setPlaceholderHandle(queryPosition, querySide, handlePayload, queryCategory);
        // immediately set handle for the queried slat
        slatsUpdated.add((querySlat.id, queryPosition, querySide));
        // keep track of updated slats to avoid infinite loops

        // TODO: this means that certain handles will be re-set more than once (e.g. a normal slat to another normal slat) if they have a phantom slat.  Not sure if this is worth optimizing further
        if (phantomMap.containsKey(querySlat.id) || querySlat.phantomParent != null) {
          // check for further phantom links
          String refID = querySlat.phantomParent ??
              querySlat.id; // get the reference ID (either the slat's own ID or its phantom reference)
          for (var siblingPhantomID in phantomMap[refID]!.values) {
            if (slatsUpdated.contains((siblingPhantomID, queryPosition, querySide))) {
              continue; // avoid infinite loops by skipping already-updated slats
            }
            recursivePhantomSearch(slats[siblingPhantomID]!, queryPosition, querySide,
                queryCategory); // recursively apply to sibling phantom slats
          }

          // finally also update the reference slat if the query slat is a phantom
          if (querySlat.phantomParent != null) {
            if (!slatsUpdated.contains((querySlat.phantomParent, queryPosition, querySide))) {
              recursivePhantomSearch(slats[querySlat.phantomParent]!, queryPosition, querySide, queryCategory);
            }
          }

          // also check for slats attached to the query slat
          String layer = querySlat.layer;
          String? adjacentLayerToCheck;
          int topOrBottom = (layerMap[layer]!['top_helix'] == 'H5' && querySide == 5 ||
                  layerMap[layer]!['top_helix'] == 'H2' && querySide == 2)
              ? 1
              : -1;

          adjacentLayerToCheck = getLayerByOrder(
              layerMap[layer]!['order'] + topOrBottom); // can be null if layer is at the bottom or top of the stack

          if (adjacentLayerToCheck != null) {
            Offset coordinate =
                querySlat.slatPositionToCoordinate[queryPosition]!; // get the real coordinate of the handle position
            if (occupiedGridPoints[adjacentLayerToCheck]!.containsKey(coordinate)) {
              // check if there's a slat in the adjacent layer at that coordinate

              // extract required information for the attached slat
              Slat attachedSlat = slats[occupiedGridPoints[adjacentLayerToCheck]![coordinate]]!;
              int opposingPosition = attachedSlat.slatCoordinateToPosition[coordinate]!;
              int opposingSide = (topOrBottom == 1)
                  ? int.parse(layerMap[adjacentLayerToCheck]?['bottom_helix'][1])
                  : int.parse(layerMap[adjacentLayerToCheck]?['top_helix'][1]);

              // run attachment for the new slat position too
              if (!slatsUpdated.contains((attachedSlat.id, opposingPosition, opposingSide))) {
                recursivePhantomSearch(attachedSlat, opposingPosition, opposingSide,
                    queryCategory == 'ASSEMBLY_HANDLE' ? 'ASSEMBLY_ANTIHANDLE' : 'ASSEMBLY_HANDLE');
              }
            }
          }
        }
      }

      recursivePhantomSearch(slat, position, side, category);
    } else {
      // for a cargo or seed handle, the handle can be set here and the function is complete (other than checking for phantom slats)
      if (phantomMap.containsKey(slat.id) || slat.phantomParent != null) {
        // check for phantom links
        String refID =
            slat.phantomParent ?? slat.id; // get the reference ID (either the slat's own ID or its phantom reference)

        // apply handle to all linked phantom slats
        for (var siblingPhantomID in phantomMap[refID]!.values) {
          slats[siblingPhantomID]!.setPlaceholderHandle(position, side, handlePayload, category);
        }

        // also apply handle to the reference slat
        slats[refID]!.setPlaceholderHandle(position, side, handlePayload, category);
      } else {
        slat.setPlaceholderHandle(position, side, handlePayload, category);
      }
    }
  }

  // assigns a full handle array to the design slats - assumes that handles -> antihandles -> handles -> etc. is the correct mapping
  // TODO: this probably loops through phantom slats too - can probably just ignore these since the recursive algorithm should take care of it
  void assignAssemblyHandleArray(List<List<List<int>>> handleArray, Offset? minPos, Offset? maxPos) {
    if (minPos == null || maxPos == null) {
      (minPos, maxPos) = extractGridBoundary(slats);
    }

    for (var slat in slats.values) {
      List assemblyLayers = [];
      if (layerMap[slat.layer]!['order'] == 0) {
        assemblyLayers.add(0);
      } else if (layerMap[slat.layer]!['order'] == layerMap.length - 1) {
        assemblyLayers.add(handleArray[0][0].length - 1);
      } else {
        assemblyLayers.add(layerMap[slat.layer]!['order'] - 1);
        assemblyLayers.add(layerMap[slat.layer]!['order']);
      }
      for (int i = 0; i < slat.maxLength; i++) {
        int x = (slat.slatPositionToCoordinate[i + 1]!.dx - minPos.dx).toInt();
        int y = (slat.slatPositionToCoordinate[i + 1]!.dy - minPos.dy).toInt();
        for (var aLayer in assemblyLayers) {
          if (handleArray[x][y][aLayer] != 0) {
            int slatSide;
            String category;
            if (aLayer == layerMap[slat.layer]!['order']) {
              slatSide = int.parse(layerMap[slat.layer]?['top_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
              category = 'ASSEMBLY_HANDLE';
            } else {
              slatSide = int.parse(layerMap[slat.layer]?['bottom_helix'].replaceAll(RegExp(r'[^0-9]'), ''));
              category = 'ASSEMBLY_ANTIHANDLE';
            }
            setSlatHandle(slat, i + 1, slatSide, '${handleArray[x][y][aLayer]}', category);
          }
        }
      }
    }
  }

  void updateDesignHammingValue() async {
    currentlyComputingHamming = true;
    notifyListeners();
    if (slats.isEmpty) {
      currentMaxValency = 0;
      currentEffValency = 0.0;
    } else {
      Offset minPos;
      Offset maxPos;
      (minPos, maxPos) = extractGridBoundary(slats);
      var handleArray = extractAssemblyHandleArray(slats, layerMap, minPos, maxPos, gridSize);
      List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);
      var valencyResults =
          await parasiticInteractionsCompute(slats, slatArray, handleArray, layerMap, minPos, gridMode);

      currentMaxValency = valencyResults['worst_match'];
      currentEffValency = valencyResults['mean_log_score'];
    }
    hammingValueValid = true;
    currentlyComputingHamming = false;
    notifyListeners();
  }

  void generateRandomAssemblyHandles(int uniqueHandleCount, bool splitLayerHandles) {
    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);

    if (minPos == Offset.infinite || maxPos == Offset.zero) {
      return; // i.e. no slats present
    }

    // Before starting, remove all handles from all slats
    for (var slat in slats.values) {
      slat.clearAssemblyHandles();
    }

    List<List<List<int>>> slatArray =
        convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize, allTypes: true);
    List<List<List<int>>> handleArray;

    if (splitLayerHandles && layerMap.length > 2) {
      handleArray =
          generateLayerSplitHandles(slatArray, uniqueHandleCount, seed: DateTime.now().millisecondsSinceEpoch % 1000);
    } else {
      handleArray =
          generateRandomSlatHandles(slatArray, uniqueHandleCount, seed: DateTime.now().millisecondsSinceEpoch % 1000);
    }
    assignAssemblyHandleArray(handleArray, minPos, maxPos);

    saveUndoState();
    notifyListeners();
  }

  Future<bool> updateAssemblyHandlesFromFile(BuildContext context) async {
    /// Reads assembly handles from a file and applies them to the slats (e.g. generated after evolution)
    // TODO: catch errors if links don't make sense

    bool readStatus = await importAssemblyHandlesFromFileIntoSlatArray(slats, layerMap, gridSize);
    if (!readStatus) {
      undo2DAction();
      return false;
    }

    saveUndoState();
    notifyListeners();
    return true;
  }

  List<List<List<int>>> getSlatArray() {
    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);
    List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize);
    return slatArray;
  }

  Map<String, List<(int, int)>> getSlatCoords() {
    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);

    Map<String, List<(int, int)>> slatCoords = {};

    for (var slat in slats.values) {
      var layerNumber = layerMap[slat.layer]!['order'] + 1;
      var pythonSlatId = slat.id.replaceFirst(slat.layer, layerNumber.toString());
      for (var i = 0; i < slat.maxLength; i++) {
        var pos = slat.slatPositionToCoordinate[i + 1]!;
        int x = (pos.dx - minPos.dx).toInt();
        int y = (pos.dy - minPos.dy).toInt();
        slatCoords.putIfAbsent(pythonSlatId, () => []).add((x, y));
      }
    }
    return slatCoords;
  }

  List<List<List<int>>> getHandleArray() {
    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);
    return extractAssemblyHandleArray(slats, layerMap, minPos, maxPos, gridSize);
  }

  Map<String, String> getSlatTypes() {
    Map<String, String> slatTypes = {};
    for (var slat in slats.values) {
      var layerNumber = layerMap[slat.layer]!['order'] + 1;
      // replace the layer ID with the layer number
      slatTypes[slat.id.replaceFirst(slat.layer, layerNumber.toString())] = slat.slatType;
    }
    return slatTypes;
  }

  void clearAssemblyHandles() {
    /// Removes all handles from the slats
    for (var slat in slats.values) {
      slat.clearAssemblyHandles();
    }
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }
}
