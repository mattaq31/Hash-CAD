import 'package:flutter/material.dart';

import '../../crisscross_core/cargo.dart';
import '../../2d_painters/helper_functions.dart' as utils;
import '../shared_app_state.dart';
import '../slat_undo_stack.dart';
import 'design_state_contract.dart';


/// Mixin containing core utility operations for DesignState
mixin DesignStateCoreMixin on ChangeNotifier, DesignStateContract {

  @override
  void setHoverPreview(HoverPreview? preview) {
    hoverPreview = preview;
    notifyListeners();
  }

  @override
  void initializeUndoStack() {
    saveUndoState();
  }

  @override
  Offset convertRealSpacetoCoordinateSpace(Offset inputPosition) {
    return utils.convertRealSpacetoCoordinateSpace(inputPosition, gridMode, gridSize, x60Jump, y60Jump);
  }

  @override
  Offset convertCoordinateSpacetoRealSpace(Offset inputPosition) {
    return utils.convertCoordinateSpacetoRealSpace(inputPosition, gridMode, gridSize, x60Jump, y60Jump);
  }

  @override
  String? getLayerByOrder(int order) {
    for (final entry in layerMap.entries) {
      if (entry.value['order'] == order) {
        return entry.key;
      }
    }
    return null;
  }

  @override
  String flipSlatSide(String side) => side == 'top' ? 'bottom' : 'top';

  @override
  bool layerNumberValid(int layerOrder) {
    return layerOrder != -1 && layerOrder < layerMap.length ? true : false;
  }

  @override
  void resetDefaults() {
    selectedLayerKey = 'A';
    selectedSlats = [];
    nextLayerKey = 'C';
    nextSeedID = 'A';
    nextColorIndex = 2;
    slatAddCount = 1;
    currentMaxValency = 0;
    currentEffValency = 0.0;
    hammingValueValid = true;
    cargoAddCount = 1;
    cargoAdditionType = null;
    occupiedGridPoints = {};
    phantomMap = {};
    seedRoster = {};
    uniqueSlatColor = Colors.blue;
    uniqueSlatColorsByLayer = {};
    slatAdditionType = 'tube';
    cargoPalette = {
        'SEED': Cargo(name: 'SEED', shortName: 'S1', color: Color.fromARGB(255, 255, 0, 0)),
      };
    occupiedCargoPoints = {};
    selectedHandlePositions = [];
  }

  @override
  void setDesignName(String newName) {
    if (newName == '') {
      designName = 'New Megastructure';
    } else {
      designName = newName;
    }
    if (designName.contains(',')) {
      designName = designName.replaceAll(',', '_');
    }
    notifyListeners();
  }

  @override
  void setUniqueSlatColor(Color color) {
    uniqueSlatColor = color;
    notifyListeners();
  }

  @override
  void saveUndoState() {
    undoStack.saveState(DesignSaveState(
        slats: slats,
        occupiedGridPoints: occupiedGridPoints,
        layerMap: layerMap,
        layerMetaData: {
          'selectedLayerKey': selectedLayerKey,
          'nextLayerKey': nextLayerKey,
          'nextColorIndex': nextColorIndex,
        },
        cargoPalette: cargoPalette,
        occupiedCargoPoints: occupiedCargoPoints,
        seedRoster: seedRoster,
        phantomMap: phantomMap,
        assemblyLinkManager: assemblyLinkManager,
        gridMode: gridMode));
  }

  @override
  void undo2DAction({bool redo = false}) {
    // reverses actions taken on the 2D portion of the design
    clearSelection();
    hammingValueValid = false;
    DesignSaveState? newState;
    if (redo) {
      newState = undoStack.redo();
    } else {
      newState = undoStack.undo();
    }

    if (newState != null) {
      slats = newState.slats;
      occupiedGridPoints = newState.occupiedGridPoints;
      occupiedCargoPoints = newState.occupiedCargoPoints;
      cargoPalette = newState.cargoPalette;
      layerMap = newState.layerMap;
      selectedLayerKey = newState.layerMetaData['selectedLayerKey'];
      nextLayerKey = newState.layerMetaData['nextLayerKey'];
      nextColorIndex = newState.layerMetaData['nextColorIndex'];
      seedRoster = newState.seedRoster;
      assemblyLinkManager = newState.assemblyLinkManager;
      gridMode = newState.gridMode;
      phantomMap = newState.phantomMap;
      if (!cargoPalette.containsKey(cargoAdditionType)) {
        cargoAdditionType = null;
      }
    }
    notifyListeners();
  }

}
