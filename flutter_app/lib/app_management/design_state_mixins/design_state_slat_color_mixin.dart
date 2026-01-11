import 'package:flutter/material.dart';

import 'design_state_contract.dart';

/// Mixin containing slat color management operations for DesignState
mixin DesignStateSlatColorMixin on ChangeNotifier, DesignStateContract {

  @override
  void assignColorToSelectedSlats(Color color) {
    /// Assigns a color to all selected slats (only non-phantom slats can be edited directly)
    for (var slatID in selectedSlats) {
      if (slats.containsKey(slatID) && slats[slatID]!.phantomParent == null) {
        slats[slatID]!.uniqueColor = color;
        if (phantomMap.containsKey(slatID)) {
          for (var phantomID in phantomMap[slatID]!.values) {
            slats[phantomID]?.uniqueColor = color;
          }
        }
      }
    }

    // add to sidebar viewer system
    uniqueSlatColorsByLayer.putIfAbsent(selectedLayerKey, () => []);
    // check if the color already exists in the list
    if (!uniqueSlatColorsByLayer[selectedLayerKey]!.contains(color)) {
      uniqueSlatColorsByLayer[selectedLayerKey]?.add(color);
    }
    saveUndoState();
    notifyListeners();
  }

  @override
  void editSlatColorSearch(String layerKey, int oldColorIndex, Color newColor) {
    /// Edits the color of all slats of a specific color
    Color oldColor = uniqueSlatColorsByLayer[layerKey]![oldColorIndex];
    for (var slat in slats.values) {
      if (slat.layer == layerKey && slat.uniqueColor == oldColor) {
        slat.uniqueColor = newColor;
      }
    }
    // update the uniqueSlatColorsByLayer map
    uniqueSlatColorsByLayer[layerKey]![oldColorIndex] = newColor;
    notifyListeners();
  }

  @override
  void removeSlatColorFromLayer(String layerKey, int colorIndex) {
    /// Removes a specific color from the list of unique slat colors in a layer
    Color colorToRemove = uniqueSlatColorsByLayer[layerKey]![colorIndex];
    for (var slat in slats.values) {
      if (slat.layer == layerKey && slat.uniqueColor == colorToRemove) {
        slat.clearColor();
      }
    }
    uniqueSlatColorsByLayer[layerKey]?.removeAt(colorIndex);
    saveUndoState();
    notifyListeners();
  }

  @override
  void clearAllSlatColors() {
    /// Clears the color of all slats
    for (var slat in slats.values) {
      slat.clearColor();
    }
    uniqueSlatColorsByLayer.clear();

    saveUndoState();
    notifyListeners();
  }

  @override
  void clearSlatColorsFromLayer(String layer) {
    /// Clears the color of all slats in a specific layer
    for (var slat in slats.values) {
      if (slat.layer == layer) {
        slat.clearColor();
      }
    }
    uniqueSlatColorsByLayer.remove(layer);
    saveUndoState();
    notifyListeners();
  }
}
