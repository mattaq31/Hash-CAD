import 'package:flutter/material.dart';
import 'dart:math';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/parasitic_valency.dart';
import '../../crisscross_core/sparse_to_array_conversion.dart';
import '../../crisscross_core/common_utilities.dart';
import '../main_design_io.dart';
import 'design_state_handle_link_mixin.dart';

/// Mixin containing handle assignment and assembly handle operations for DesignState
mixin DesignStateHandleMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;

  Map<String, Map<String, dynamic>> get layerMap;

  Map<String, Map<Offset, String>> get occupiedGridPoints;

  Map<String, Map<int, String>> get phantomMap;

  String get selectedLayerKey;

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

  // Access to link manager from other mixin
  HandleLinkManager get assemblyLinkManager;

  // Selection state for assembly handles
  List<Offset> get selectedAssemblyPositions;
  set selectedAssemblyPositions(List<Offset> value);

  // Methods from other mixins
  void saveUndoState();

  String? getLayerByOrder(int order);

  void undo2DAction({bool redo = false});

  bool handleWithinBounds(Slat slat, int position, int side){

    int topSide = getSlatSideFromLayer(layerMap, selectedLayerKey, 'top');

    if(layerMap[selectedLayerKey]!['order'] == 0 && topSide != side) {
      return false;
    }
    if(layerMap[selectedLayerKey]!['order'] == layerMap.length - 1 && topSide == side) {
      return false;
    }
    return true;
  }


  Set<HandleKey> smartSetHandle(Slat slat, int position, int side, String handlePayload, String category, {bool requestStateUpdate = false}) {

    Set<HandleKey> slatsUpdated = {};
    // For assembly handles, use recursive propagation with link manager integration
    if (category.contains('ASSEMBLY')) {
      /// Recursive function that propagates handle through:
      /// 1) Phantom network (parent/siblings)
      /// 2) Explicit link manager groups
      /// 3) Physical layer attachments
      void recursivePropagateHandle(Slat querySlat, int queryPosition, int querySide, String queryCategory) {
        HandleKey accessKey = (querySlat.id, queryPosition, querySide);

        // Prevent infinite loops
        if (slatsUpdated.contains(accessKey)) return;
        slatsUpdated.add(accessKey);

        // Set handle on this slat (only if it's within the bounds)
        if (handleWithinBounds(querySlat, queryPosition, querySide)) {
          querySlat.setPlaceholderHandle(queryPosition, querySide, handlePayload, queryCategory);
        }

        // 1) Propagate through phantom network
        if (phantomMap.containsKey(querySlat.id) || querySlat.phantomParent != null) {
          String refID = querySlat.phantomParent ?? querySlat.id;

          // Propagate to phantom siblings
          for (var siblingPhantomID in phantomMap[refID]?.values ?? []) {
            recursivePropagateHandle(slats[siblingPhantomID]!, queryPosition, querySide, queryCategory);
          }

          // Propagate to parent if this is a phantom
          if (querySlat.phantomParent != null) {
            recursivePropagateHandle(slats[querySlat.phantomParent]!, queryPosition, querySide, queryCategory);
          }
        }

        // 2) Propagate through link manager groups (only for non-phantom slats)
        if (querySlat.phantomParent == null) {
          for (var linkedKey in assemblyLinkManager.getLinkedHandles(accessKey)) {
            if (linkedKey != accessKey && slats.containsKey(linkedKey.$1)) {
              Slat linkedSlat = slats[linkedKey.$1]!;
              // Determine the category for the linked handle based on its current value
              var linkedHandleDict = getHandleDict(linkedSlat, linkedKey.$3);
              String linkedCategory = linkedHandleDict[linkedKey.$2]?['category'] ?? queryCategory;
              recursivePropagateHandle(linkedSlat, linkedKey.$2, linkedKey.$3, linkedCategory);
            }
          }
        }

        // 3) Propagate to physical layer attachments
        String layer = querySlat.layer;
        int topOrBottom = getLayerOffsetForSide(layerMap, layer, querySide);
        String? adjacentLayerToCheck = getLayerByOrder(layerMap[layer]!['order'] + topOrBottom);

        if (adjacentLayerToCheck != null) {
          Offset coordinate = querySlat.slatPositionToCoordinate[queryPosition]!;
          if (occupiedGridPoints[adjacentLayerToCheck]?.containsKey(coordinate) ?? false) {
            Slat attachedSlat = slats[occupiedGridPoints[adjacentLayerToCheck]![coordinate]]!;
            int opposingPosition = attachedSlat.slatCoordinateToPosition[coordinate]!;
            int opposingSide = getOpposingSide(layerMap, adjacentLayerToCheck, topOrBottom);
            String opposingCategory = queryCategory == 'ASSEMBLY_HANDLE' ? 'ASSEMBLY_ANTIHANDLE' : 'ASSEMBLY_HANDLE';
            recursivePropagateHandle(attachedSlat, opposingPosition, opposingSide, opposingCategory);
          }
        }
      }

      // Start propagation
      recursivePropagateHandle(slat, position, side, category);

      // Enforcement phase: check if any visited handle has an enforced value
      Set<int> enforcedValues = {};
      for (var key in slatsUpdated) {
        int? enforced = assemblyLinkManager.getEnforceValue(key);
        if (enforced != null && enforced != 0) {
          enforcedValues.add(enforced);
        }
      }

      // If there's a single enforced value that differs from what we set, apply it
      if (enforcedValues.length == 1) {
        int enforced = enforcedValues.first;
        if (enforced.toString() != handlePayload) {
          for (var key in slatsUpdated) {
            Slat targetSlat = slats[key.$1]!;
            var handleDict = getHandleDict(targetSlat, key.$3);
            String currentCategory = handleDict[key.$2]?['category'] ?? category;
            if (handleWithinBounds(targetSlat, key.$2, key.$3)) {
              targetSlat.setPlaceholderHandle(key.$2, key.$3, enforced.toString(), currentCategory);
            }
          }
        }
      } else if (enforcedValues.length > 1) {
        // Multiple conflicting enforced values - this should have been prevented by UI
        throw StateError('Conflicting enforced values detected: ${enforcedValues.join(", ")}');
      }
    } else {
      // For cargo or seed handles: simple phantom propagation (no link manager)
      if (phantomMap.containsKey(slat.id) || slat.phantomParent != null) {
        String refID = slat.phantomParent ?? slat.id;

        // Apply to all phantom siblings
        for (String siblingPhantomID in phantomMap[refID]?.values ?? []) {
          slats[siblingPhantomID]!.setPlaceholderHandle(position, side, handlePayload, category);
          slatsUpdated.add((siblingPhantomID, position, side));
        }

        // Apply to reference slat
        slats[refID]!.setPlaceholderHandle(position, side, handlePayload, category);
        slatsUpdated.add((refID, position, side));

      } else {
        slat.setPlaceholderHandle(position, side, handlePayload, category);
        slatsUpdated.add((slat.id, position, side));
      }
    }

    if (requestStateUpdate) {
      saveUndoState();
      notifyListeners();
    }
    return slatsUpdated;
  }

  /// Deletes an assembly handle with smart propagation through phantoms and layer attachments.
  ///
  /// Default behavior: Removes the handle and breaks its link, but leaves other linked handles intact.
  /// Cascade mode: Also deletes all linked handles and their layer attachments.
  ///
  /// Returns a set of all coordinates that were affected (for batch updating occupancy maps).
  Set<(String, Offset)> smartDeleteHandle(Slat slat, int position, int side, {bool cascadeDelete = false, bool requestStateUpdate = false}) {
    if (slat.phantomParent != null) {
      // For phantom slats, redirect to parent
      return smartDeleteHandle(slats[slat.phantomParent]!, position, side, cascadeDelete: cascadeDelete);
    }

    var handleDict = getHandleDict(slat, side);
    if (handleDict[position] == null) return {};

    String category = handleDict[position]!['category'];
    Set<(String, Offset)> affectedCoordinates = {};
    Set<HandleKey> visited = {};

    if (cascadeDelete && category.contains('ASSEMBLY')) {
      // Cascade: Delete through full propagation (phantoms + links + attachments)
      _propagateDelete(slat.id, position, side, category, visited, affectedCoordinates);

      // Remove all visited keys from link manager
      for (var key in visited) {
        assemblyLinkManager.removeLink(key);
      }
    } else {
      // Default: Delete this handle + phantom siblings + layer attachment only
      _deleteWithPhantomAndLayerPropagation(slat, position, side, category, visited, affectedCoordinates);

      // Break link only for the original handle (if ASSEMBLY)
      if (category.contains('ASSEMBLY')) {
        assemblyLinkManager.removeLink((slat.id, position, side));
      }
    }

    if (requestStateUpdate) {
      saveUndoState();
      notifyListeners();
    }

    return affectedCoordinates;
  }

  /// Recursively deletes handles through all propagation paths (phantom + links + layer attachments).
  void _propagateDelete(String slatId, int position, int side, String category, Set<HandleKey> visited, Set<(String, Offset)> affectedCoordinates) {
    HandleKey accessKey = (slatId, position, side);
    if (visited.contains(accessKey)) return;
    visited.add(accessKey);

    Slat slat = slats[slatId]!;
    Offset coordinate = slat.slatPositionToCoordinate[position]!;
    affectedCoordinates.add((slat.layer, coordinate));

    // 1) Propagate through phantom network BEFORE deleting
    if (phantomMap.containsKey(slat.id) || slat.phantomParent != null) {
      String refID = slat.phantomParent ?? slat.id;

      for (String siblingPhantomID in phantomMap[refID]?.values ?? <String>[]) {
        _propagateDelete(siblingPhantomID, position, side, category, visited, affectedCoordinates);
      }

      if (slat.phantomParent != null) {
        _propagateDelete(refID, position, side, category, visited, affectedCoordinates);
      }
    }

    // 2) Propagate through link manager groups (only for non-phantom slats)
    if (slat.phantomParent == null) {
      for (var linkedKey in assemblyLinkManager.getLinkedHandles(accessKey)) {
        if (linkedKey != accessKey && slats.containsKey(linkedKey.$1)) {
          var linkedSlat = slats[linkedKey.$1]!;
          var linkedHandleDict = getHandleDict(linkedSlat, linkedKey.$3);
          String linkedCategory = linkedHandleDict[linkedKey.$2]?['category'] ?? category;
          _propagateDelete(linkedKey.$1, linkedKey.$2, linkedKey.$3, linkedCategory, visited, affectedCoordinates);
        }
      }
    }

    // 3) Propagate to physical layer attachment
    String layer = slat.layer;
    int topOrBottom = getLayerOffsetForSide(layerMap, layer, side);
    String? adjacentLayerToCheck = getLayerByOrder(layerMap[layer]!['order'] + topOrBottom);

    if (adjacentLayerToCheck != null) {
      if (occupiedGridPoints[adjacentLayerToCheck]?.containsKey(coordinate) ?? false) {
        Slat attachedSlat = slats[occupiedGridPoints[adjacentLayerToCheck]![coordinate]]!;
        int opposingPosition = attachedSlat.slatCoordinateToPosition[coordinate]!;
        int opposingSide = getOpposingSide(layerMap, adjacentLayerToCheck, topOrBottom);
        String opposingCategory = category == 'ASSEMBLY_HANDLE' ? 'ASSEMBLY_ANTIHANDLE' : 'ASSEMBLY_HANDLE';
        _propagateDelete(attachedSlat.id, opposingPosition, opposingSide, opposingCategory, visited, affectedCoordinates);
      }
    }

    // Delete the handle from this slat
    _removeHandleFromSlat(slat, position, side);
  }

  /// Deletes handle through phantom network and layer attachment only (not through link groups).
  void _deleteWithPhantomAndLayerPropagation(Slat slat, int position, int side, String category, Set<HandleKey> visited, Set<(String, Offset)> affectedCoordinates) {
    HandleKey accessKey = (slat.id, position, side);
    if (visited.contains(accessKey)) return;
    visited.add(accessKey);

    Offset coordinate = slat.slatPositionToCoordinate[position]!;
    affectedCoordinates.add((slat.layer, coordinate));

    // Propagate to phantom network
    if (phantomMap.containsKey(slat.id) || slat.phantomParent != null) {
      String refID = slat.phantomParent ?? slat.id;

      for (var siblingPhantomID in phantomMap[refID]?.values ?? []) {
        Slat siblingSlat = slats[siblingPhantomID]!;
        _deleteWithPhantomAndLayerPropagation(siblingSlat, position, side, category, visited, affectedCoordinates);
      }

      if (slat.phantomParent != null) {
        _deleteWithPhantomAndLayerPropagation(slats[refID]!, position, side, category, visited, affectedCoordinates);
      }
    }

    // Propagate to layer attachment
    String layer = slat.layer;
    int topOrBottom = getLayerOffsetForSide(layerMap, layer, side);
    String? adjacentLayerToCheck = getLayerByOrder(layerMap[layer]!['order'] + topOrBottom);

    if (adjacentLayerToCheck != null) {
      if (occupiedGridPoints[adjacentLayerToCheck]?.containsKey(coordinate) ?? false) {
        Slat attachedSlat = slats[occupiedGridPoints[adjacentLayerToCheck]![coordinate]]!;
        int opposingPosition = attachedSlat.slatCoordinateToPosition[coordinate]!;
        int opposingSide = getOpposingSide(layerMap, adjacentLayerToCheck, topOrBottom);
        String opposingCategory = category == 'ASSEMBLY_HANDLE' ? 'ASSEMBLY_ANTIHANDLE' : 'ASSEMBLY_HANDLE';
        _deleteWithPhantomAndLayerPropagation(
            attachedSlat, opposingPosition, opposingSide, opposingCategory, visited, affectedCoordinates);
      }
    }

    // Delete the handle
    _removeHandleFromSlat(slat, position, side);
  }

  /// Removes a handle from a slat without any propagation.
  void _removeHandleFromSlat(Slat slat, int position, int side) {
    var handleDict = getHandleDict(slat, side);
    handleDict.remove(position);
    slat.placeholderList.remove('handle-$position-h$side');
  }

  /// Selects or deselects an assembly handle at the given coordinate.
  void selectAssemblyHandle(Offset coordinate, {bool addOnly = false}) {
    if (selectedAssemblyPositions.contains(coordinate) && !addOnly) {
      selectedAssemblyPositions.remove(coordinate);
    } else if (!selectedAssemblyPositions.contains(coordinate)) {
      selectedAssemblyPositions.add(coordinate);
    }
    notifyListeners();
  }

  /// Clears all selected assembly handle positions.
  void clearAssemblySelection() {
    selectedAssemblyPositions.clear();
    notifyListeners();
  }

  void deleteSelectedHandles(String slatSide){
    int integerSlatSide = getSlatSideFromLayer(layerMap, selectedLayerKey, slatSide);
    for (var coord in selectedAssemblyPositions) {
      var slat = slats[occupiedGridPoints[selectedLayerKey]?[coord]]!;
      int position = slat.slatCoordinateToPosition[coord]!;
      smartDeleteHandle(slat, position, integerSlatSide, cascadeDelete: false);
    }
    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  /// Moves assembly handles from source to destination coordinates, preserving links.
  void moveAssemblyHandle(Map<Offset, Offset> coordinateTransferMap, String layerID, String slatSide) {
    int integerSlatSide = getSlatSideFromLayer(layerMap, layerID, slatSide);

    // PHASE 1: Collect handle data and link keys before changes
    List<({Offset fromCoord, Offset toCoord, Slat slatDonor, int donorPosition,
           Slat slatReceiver, int receiverPosition, String handleValue, String handleCategory,
           HandleKey oldKey, HandleKey newKey})> moveOperations = [];

    for (var fromCoord in coordinateTransferMap.keys) {
      var slatID = occupiedGridPoints[layerID]?[fromCoord];
      if (slatID == null) continue;

      var slatDonor = slats[slatID]!;
      int donorPosition = slatDonor.slatCoordinateToPosition[fromCoord]!;
      var handleDict = getHandleDict(slatDonor, integerSlatSide);

      if (handleDict[donorPosition] == null) continue; // No handle to move
      if (!handleDict[donorPosition]!['category'].toString().contains('ASSEMBLY')) continue; // Not an assembly handle

      String handleValue = handleDict[donorPosition]!['value'].toString();
      String handleCategory = handleDict[donorPosition]!['category'];
      Offset toCoord = coordinateTransferMap[fromCoord]!;

      if (!occupiedGridPoints[layerID]!.containsKey(toCoord)) continue; // No receiver slat present

      var receiverSlatID = occupiedGridPoints[layerID]![toCoord]!;

      var slatReceiver = slats[receiverSlatID]!;
      int receiverPosition = slatReceiver.slatCoordinateToPosition[toCoord]!;

      // Track old and new keys for link manager update
      HandleKey oldKey = (slatDonor.id, donorPosition, integerSlatSide);
      HandleKey newKey = (slatReceiver.id, receiverPosition, integerSlatSide);

      moveOperations.add((
        fromCoord: fromCoord, toCoord: toCoord,
        slatDonor: slatDonor, donorPosition: donorPosition,
        slatReceiver: slatReceiver, receiverPosition: receiverPosition,
        handleValue: handleValue, handleCategory: handleCategory,
        oldKey: oldKey, newKey: newKey,
      ));
    }

    // PHASE 2: Update link manager keys BEFORE deleting (so links are preserved)
    for (var op in moveOperations) {
      assemblyLinkManager.updateKey(op.oldKey, op.newKey);
    }

    // PHASE 3: Delete from source (cascade=false, links already moved)
    for (var op in moveOperations) {
      // Delete directly without touching link manager (already updated)
      smartDeleteHandle(op.slatDonor, op.donorPosition, integerSlatSide);
    }

    // PHASE 4: Add to destination
    for (var op in moveOperations) {
      smartSetHandle(op.slatReceiver, op.receiverPosition, integerSlatSide, op.handleValue, op.handleCategory);
    }

    hammingValueValid = false;
    saveUndoState();
    notifyListeners();
  }

  /// Deletes a handle through phantom network only (no link manager, no layer attachments).
  /// Used for cargo and seed handles which don't use the link manager.
  /// Returns a set of all affected (layerID, coordinate) pairs for batch occupancy map updates.
  Set<(String, Offset)> deleteHandleWithPhantomPropagation(Slat slat, int position, int side) {
    Set<(String, Offset)> affectedCoordinates = {};
    Set<String> visited = {};

    void propagate(Slat currentSlat) {
      if (visited.contains(currentSlat.id)) return;
      visited.add(currentSlat.id);

      // Track this coordinate
      Offset coordinate = currentSlat.slatPositionToCoordinate[position]!;
      affectedCoordinates.add((currentSlat.layer, coordinate));

      // Remove handle from this slat
      _removeHandleFromSlat(currentSlat, position, side);

      // Propagate through phantom network
      if (phantomMap.containsKey(currentSlat.id) || currentSlat.phantomParent != null) {
        String refID = currentSlat.phantomParent ?? currentSlat.id;

        // Propagate to phantom siblings
        for (String siblingPhantomID in phantomMap[refID]?.values ?? <String>[]) {
          propagate(slats[siblingPhantomID]!);
        }

        // Propagate to parent if this is a phantom
        if (currentSlat.phantomParent != null) {
          propagate(slats[refID]!);
        }
      }
    }

    propagate(slat);
    return affectedCoordinates;
  }

  // assigns a full handle array to the design slats - assumes that handles -> antihandles -> handles -> etc. is the correct mapping
  void assignAssemblyHandleArray(List<List<List<int>>> handleArray, Offset? minPos, Offset? maxPos) {

    if (minPos == null || maxPos == null) {
      (minPos, maxPos) = extractGridBoundary(slats);
    }

    Set<HandleKey> assignedHandles = {};

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
            // Interface aLayer is between layers aLayer and aLayer+1
            // Layer's TOP faces interface (order), BOTTOM also faces interface (order - 1)
            if (aLayer == layerMap[slat.layer]!['order']) {
              // This layer's TOP faces interface aLayer
              slatSide = getSlatSideFromLayer(layerMap, slat.layer, 'top');
              category = 'ASSEMBLY_HANDLE';
            } else {
              // This layer's BOTTOM faces interface aLayer
              slatSide = getSlatSideFromLayer(layerMap, slat.layer, 'bottom');
              category = 'ASSEMBLY_ANTIHANDLE';
            }

            if (assignedHandles.contains((slat.id, i + 1, slatSide))) { // prevents double assignment due to overlapping assembly layers
              continue;
            }

            var localAssignedHandles = smartSetHandle(slat, i + 1, slatSide, '${handleArray[x][y][aLayer]}', category);
            assignedHandles.addAll(localAssignedHandles);
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

  void generateRandomAssemblyHandles(int uniqueHandleCount, bool splitLayerHandles, {bool allAvailableHandles = false}) {
    Offset minPos;
    Offset maxPos;
    (minPos, maxPos) = extractGridBoundary(slats);

    if (minPos == Offset.infinite || maxPos == Offset.zero) {
      return; // i.e. no slats present
    }

    // Collect existing assembly handle positions when in "all available" mode
    Set<(int, int, int)>? additionalPositions;
    Set<(String, int, int)>? outOfBoundsPositions;
    if (allAvailableHandles) {
      additionalPositions = {};
      outOfBoundsPositions = {};
      int numInterfaces = layerMap.length - 1;
      for (var slat in slats.values) {
        for (int side in [2, 5]) {
          var handleDict = getHandleDict(slat, side);
          for (var entry in handleDict.entries) {
            if (entry.value['category']?.contains('ASSEMBLY') ?? false) {
              Offset coord = slat.slatPositionToCoordinate[entry.key]!;
              int x = (coord.dx - minPos.dx).toInt();
              int y = (coord.dy - minPos.dy).toInt();
              // TOP side faces interface above (order - 1), BOTTOM side faces interface below (order)
              int arrayLayer = (side == getSlatSideFromLayer(layerMap, slat.layer, 'top'))
                  ? layerMap[slat.layer]!['order']
                  : layerMap[slat.layer]!['order'] -1;
              if (arrayLayer >= 0 && arrayLayer < numInterfaces) {
                additionalPositions.add((x, y, arrayLayer));
              }
              else{
                outOfBoundsPositions.add((slat.id, side, entry.key));
              }
            }
          }
        }
      }
    }

    // Clear existing assembly handles
    for (var slat in slats.values) {
      slat.clearAssemblyHandles();
    }

    List<List<List<int>>> slatArray = convertSparseSlatBundletoArray(slats, layerMap, minPos, maxPos, gridSize, allTypes: true);
    List<List<List<int>>> handleArray;
    int seed = DateTime.now().millisecondsSinceEpoch % 1000;

    if (splitLayerHandles && layerMap.length > 2) {
      handleArray = generateLayerSplitHandles(slatArray, uniqueHandleCount, seed: seed, additionalPositions: additionalPositions);
    } else {
      handleArray = generateRandomSlatHandles(slatArray, uniqueHandleCount, seed: seed, additionalPositions: additionalPositions);
    }
    assignAssemblyHandleArray(handleArray, minPos, maxPos);

    // assigns all remaining handles that were out of bounds of the handle array
    if (allAvailableHandles && outOfBoundsPositions != null && outOfBoundsPositions.isNotEmpty) {
      Random rand = Random(DateTime.now().millisecondsSinceEpoch % 1000);
      for (var (slatID, side, position) in outOfBoundsPositions) {
        String category = (side == getSlatSideFromLayer(layerMap, slats[slatID]!.layer, 'top'))
            ? 'ASSEMBLY_HANDLE'
            : 'ASSEMBLY_ANTIHANDLE';
        String handlePayload =  (rand.nextInt(uniqueHandleCount) + 1).toString(); // generate a pseudo-random handle value
        smartSetHandle(slats[slatID]!, position, side, handlePayload, category);
      }
    }

    saveUndoState();
    notifyListeners();
  }

  Future<bool> updateAssemblyHandlesFromFile(BuildContext context) async {
    /// Reads assembly handles from a file and applies them to the slats (e.g. generated after evolution)
    bool readStatus = await importAssemblyHandlesFromFileIntoSlatArray(slats, layerMap, gridSize);
    if (!readStatus) {
      undo2DAction();
      return false;
    }

    // Check for issues after import
    if (context.mounted) {
      fullHandleValidationWithWarning(context);
    }

    saveUndoState();
    notifyListeners();
    return true;
  }

  void fullHandleValidationWithWarning(BuildContext context){
    List<String> warnings = [];

    // Check for link manager constraint violations
    String? linkWarning = checkLinkManagerConstraints();
    if (linkWarning != null) warnings.add(linkWarning);

    // Check for phantom slat inconsistencies
    String? phantomWarning = checkPhantomSlatConsistency();
    if (phantomWarning != null) warnings.add(phantomWarning);

    // Show warnings if any
    if (warnings.isNotEmpty && context.mounted) {
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Import Warnings'),
          content: SingleChildScrollView(
            child: Text(warnings.join('\n\n')),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('OK'),
            ),
          ],
        ),
      );
    }
  }

  /// Checks if imported handles violate link manager constraints.
  /// Returns a warning message if violations exist, null otherwise.
  String? checkLinkManagerConstraints() {
    List<String> violations = [];

    // Check each linked group for consistent values
    for (var groupEntry in assemblyLinkManager.handleGroupToLink.entries) {
      var groupId = groupEntry.key;
      var handles = groupEntry.value;

      Set<String> valuesInGroup = {};
      for (var key in handles) {
        if (!slats.containsKey(key.$1)) continue;
        var slat = slats[key.$1]!;
        var handleDict = getHandleDict(slat, key.$3);
        if (handleDict[key.$2] != null) {
          var handleVal = handleDict[key.$2]!;
          if (!handleVal['category'].contains('ASSEMBLY')) continue;
          valuesInGroup.add(handleVal['value'].toString());
        }
      }

      if (valuesInGroup.length > 1) {
        violations.add('Link group $groupId has inconsistent values: ${valuesInGroup.join(", ")}');
      }

      // Check enforced value
      if (assemblyLinkManager.handleGroupToValue.containsKey(groupId)) {
        var enforcedValue = assemblyLinkManager.handleGroupToValue[groupId].toString();
        if (valuesInGroup.isNotEmpty && !valuesInGroup.contains(enforcedValue)) {
          violations.add('Link group $groupId has enforced value $enforcedValue but handles have: ${valuesInGroup.join(", ")}');
        }
      }
    }

    // Check blocked handles
    for (var key in assemblyLinkManager.handleBlocks) {
      if (!slats.containsKey(key.$1)) continue;
      var slat = slats[key.$1]!;
      var handleDict = getHandleDict(slat, key.$3);
      if (handleDict[key.$2] != null) {
        var value = handleDict[key.$2]!['value'];
        if (value != '0' && value != 0) {
          violations.add('Blocked handle at ${key.$1} pos ${key.$2} H${key.$3} has value $value (should be empty)');
        }
      }
    }

    if (violations.isEmpty) return null;
    return 'Link constraint violations detected:\n• ${violations.take(5).join('\n• ')}${violations.length > 5 ? '\n• ...and ${violations.length - 5} more' : ''}';
  }

  /// Checks if phantom slats have handles that don't match their parents.
  /// Returns a warning message if inconsistencies exist, null otherwise.
  String? checkPhantomSlatConsistency() {
    List<String> inconsistencies = [];

    for (var entry in phantomMap.entries) {
      String parentId = entry.key;
      if (!slats.containsKey(parentId)) continue;
      var parentSlat = slats[parentId]!;

      for (var phantomId in entry.value.values) {
        if (!slats.containsKey(phantomId)) continue;
        var phantomSlat = slats[phantomId]!;

        // Check H5 handles
        for (var pos in parentSlat.h5Handles.keys) {
          var parentValue = parentSlat.h5Handles[pos]?['value'];
          var phantomValue = phantomSlat.h5Handles[pos]?['value'];
          if (parentValue != phantomValue) {
            inconsistencies.add('$phantomId H5 pos $pos: parent=$parentValue, phantom=$phantomValue');
          }
        }

        // Check H2 handles
        for (var pos in parentSlat.h2Handles.keys) {
          var parentValue = parentSlat.h2Handles[pos]?['value'];
          var phantomValue = phantomSlat.h2Handles[pos]?['value'];
          if (parentValue != phantomValue) {
            inconsistencies.add('$phantomId H2 pos $pos: parent=$parentValue, phantom=$phantomValue');
          }
        }
      }
    }

    if (inconsistencies.isEmpty) return null;
    return 'Phantom slat inconsistencies detected (handles may need syncing):\n• ${inconsistencies.take(5).join('\n• ')}${inconsistencies.length > 5 ? '\n• ...and ${inconsistencies.length - 5} more' : ''}';
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
