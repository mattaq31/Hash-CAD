import 'package:flutter/material.dart';

import 'design_state_contract.dart';

/// Mixin containing slat color management operations for DesignState
mixin DesignStateSlatColorMixin on ChangeNotifier, DesignStateContract {

  /// Assigns a color to all selected slats.  Phantoms always share their parent's colour, so selecting either a
  /// parent or one of its phantoms recolours the whole family.
  @override
  void assignColorToSelectedSlats(Color color) {
    Set<String> recolouredLayers = {selectedLayerKey};
    for (var slatID in selectedSlats) {
      if (!slats.containsKey(slatID)) continue;
      String rootID = slats[slatID]!.phantomParent ?? slatID;
      for (var memberID in [rootID, ...?phantomMap[rootID]?.values]) {
        var member = slats[memberID];
        if (member == null) continue;
        member.uniqueColor = color;
        recolouredLayers.add(member.layer);
      }
    }

    // add to sidebar viewer system (family members can sit on other layers, so each touched layer gets the colour)
    for (var layer in recolouredLayers) {
      uniqueSlatColorsByLayer.putIfAbsent(layer, () => []);
      if (!uniqueSlatColorsByLayer[layer]!.contains(color)) {
        uniqueSlatColorsByLayer[layer]!.add(color);
      }
    }
    saveUndoState();
    notifyListeners();
  }

  /// Edits the color of all slats of a specific color
  @override
  void editSlatColorSearch(String layerKey, int oldColorIndex, Color newColor) {
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

  /// Removes a specific color from the list of unique slat colors in a layer
  @override
  void removeSlatColorFromLayer(String layerKey, int colorIndex) {
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

  /// Clears the color of all slats
  @override
  void clearAllSlatColors() {
    for (var slat in slats.values) {
      slat.clearColor();
    }
    uniqueSlatColorsByLayer.clear();

    saveUndoState();
    notifyListeners();
  }

  /// Clears the color of all slats in a specific layer
  @override
  void clearSlatColorsFromLayer(String layer) {
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
