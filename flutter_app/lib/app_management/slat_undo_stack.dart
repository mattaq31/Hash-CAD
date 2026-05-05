import '../crisscross_core/slats.dart';
import 'package:flutter/material.dart';
import '../crisscross_core/cargo.dart';
import '../crisscross_core/seed.dart';
import 'design_state_mixins/design_state_handle_link_mixin.dart';
import 'design_state_mixins/design_state_grouping_mixin.dart';

class DesignSaveState {
  final Map<String, Slat> slats;
  final Map<String, Map<Offset, String>> occupiedGridPoints;
  final Map<String, Map<String, dynamic>> layerMap;
  final Map<String, dynamic> layerMetaData;
  final Map<String, Cargo> cargoPalette;
  final Map<String, Map<Offset, String>> occupiedCargoPoints;
  final Map<(String, String, Offset), Seed> seedRoster;
  final Map<String, Map<int, String>> phantomMap;
  final HandleLinkManager assemblyLinkManager;
  final String gridMode;
  final Map<String, GroupConfiguration> groupConfigurations;
  final String? activeGroupConfigId;

  DesignSaveState({
    required this.slats,
    required this.occupiedGridPoints,
    required this.layerMap,
    required this.layerMetaData,
    required this.cargoPalette,
    required this.occupiedCargoPoints,
    required this.seedRoster,
    required this.phantomMap,
    required this.assemblyLinkManager,
    required this.gridMode,
    required this.groupConfigurations,
    required this.activeGroupConfigId,
  });

  /// Deep copy constructor
  DesignSaveState copy() {
    return DesignSaveState(
      slats: {
        for (var e in slats.entries) e.key: e.value.copy()
      },
      occupiedGridPoints: {
        for (var e in occupiedGridPoints.entries) e.key: Map.from(e.value)
      },
      layerMap: {
        for (var e in layerMap.entries) e.key: Map.from(e.value)
      },
      layerMetaData: Map.from(layerMetaData),
      cargoPalette: {
        for (var e in cargoPalette.entries) e.key: e.value // copy() if needed
      },
      occupiedCargoPoints: {
        for (var e in occupiedCargoPoints.entries) e.key: Map.from(e.value)
      },
      seedRoster: {
        for (var e in seedRoster.entries) e.key: e.value.copy()
      },
      phantomMap: {
        for (var e in phantomMap.entries) e.key: Map.from(e.value)
      },
      assemblyLinkManager: assemblyLinkManager.copy(),
      gridMode: gridMode,
      groupConfigurations: _copyGroupConfigurations(groupConfigurations),
      activeGroupConfigId: activeGroupConfigId,
    );
  }

  /// Deep copies the full group configuration hierarchy.
  static Map<String, GroupConfiguration> _copyGroupConfigurations(Map<String, GroupConfiguration> configs) {
    return {
      for (var e in configs.entries)
        e.key: GroupConfiguration(
          id: e.value.id,
          name: e.value.name,
          nextGroupNumber: e.value.nextGroupNumber,
          groups: {
            for (var g in e.value.groups.entries)
              g.key: SlatGroup(
                id: g.value.id,
                name: g.value.name,
                color: g.value.color,
                slatIds: Set.from(g.value.slatIds),
              )
          },
          slatToGroup: Map.from(e.value.slatToGroup),
        )
    };
  }
}

class SlatUndoStack {
  final List<DesignSaveState> _history = [];
  int _currentIndex = -1;
  static const int _maxHistory = 50;

  void saveState(DesignSaveState state) {
    // Remove future states if in the middle
    if (_currentIndex < _history.length - 1) {
      _history.removeRange(_currentIndex + 1, _history.length);
    }

    // Add a deep copy of the new state
    _history.add(state.copy());
    _currentIndex++;

    // Trim oldest entry if over capacity
    if (_history.length > _maxHistory) {
      _history.removeAt(0);
      _currentIndex--;
    }
  }

  DesignSaveState? undo() {
    if (_currentIndex > 0) {
      _currentIndex--;
      return _history[_currentIndex].copy();
    }
    return null;
  }

  DesignSaveState? redo() {
    if (_currentIndex < _history.length - 1) {
      _currentIndex++;
      return _history[_currentIndex].copy();
    }
    return null;
  }

  bool get canUndo => _currentIndex > 0;
  bool get canRedo => _currentIndex < _history.length - 1;
}
