// Slat grouping data model and state management.
//
// Groups exist independently of slat properties — they're a separate organizational
// layer used for visualization (color-by-group mode) and lab workflow (PEG precipitation).
// Multiple "configurations" allow the same set of slats to be grouped differently
// for different purposes (e.g. one config for PEG, another for functional comparison).
import 'package:flutter/material.dart';

import 'design_state_contract.dart';

/// A named set of slats with a display color, belonging to a single [GroupConfiguration].
class SlatGroup {
  final String id;
  String name;
  Color color;
  Set<String> slatIds;

  SlatGroup({required this.id, required this.name, required this.color, Set<String>? slatIds}) : slatIds = slatIds ?? {};
}

/// A complete grouping scheme — like a tab of independent group assignments.
/// Each configuration maps every slat to at most one group.
class GroupConfiguration {
  final String id;
  String name;
  Map<String, SlatGroup> groups;
  // Reverse lookup: slatId -> groupId (for O(1) group resolution)
  Map<String, String> slatToGroup;
  int nextGroupNumber;

  GroupConfiguration({required this.id, required this.name, Map<String, SlatGroup>? groups, Map<String, String>? slatToGroup, this.nextGroupNumber = 1})
      : groups = groups ?? {},
        slatToGroup = slatToGroup ?? {};
}

/// State management mixin for the slat grouping system.
///
/// Handles configuration CRUD, group CRUD, and the bridge between selection state
/// and group membership. Color resolution for the 2D/3D painters is also provided here.
mixin DesignStateGroupingMixin on ChangeNotifier, DesignStateContract {
  @override
  Map<String, GroupConfiguration> groupConfigurations = {};
  @override
  String? activeGroupConfigId;
  int _nextConfigNumber = 1;
  @override
  bool preserveSelectionOnLayerChange = false;
  // Incremented on every group mutation so painters can detect changes via shouldRepaint
  @override
  int groupVersion = 0;

  /// The currently active configuration (null if none exists or none selected).
  @override
  GroupConfiguration? get activeGroupConfig => activeGroupConfigId != null ? groupConfigurations[activeGroupConfigId] : null;

  /// Returns the group ID that contains all currently selected slats (if they all
  /// belong to the same group), or null otherwise. Used to detect when a group's
  /// slats are actively selected for the "Update Group" workflow.
  @override
  String? get selectedGroupId {
    if (activeGroupConfig == null || selectedSlats.isEmpty) return null;
    var config = activeGroupConfig!;
    String? commonGroupId;
    for (var slatId in selectedSlats) {
      var groupId = config.slatToGroup[slatId];
      if (groupId == null) return null;
      if (commonGroupId == null) {
        commonGroupId = groupId;
      } else if (commonGroupId != groupId) {
        return null;
      }
    }
    // Only match if the selection exactly equals the group's membership
    if (commonGroupId != null && activeGroupConfig!.groups[commonGroupId]?.slatIds.length == selectedSlats.length) {
      return commonGroupId;
    }
    return null;
  }

  @override
  void createGroupConfiguration({String? name}) {
    String id = 'C$_nextConfigNumber';
    String configName = name ?? 'Config $_nextConfigNumber';
    _nextConfigNumber++;
    groupConfigurations[id] = GroupConfiguration(id: id, name: configName);
    activeGroupConfigId = id;
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  @override
  void deleteGroupConfiguration(String configId) {
    groupConfigurations.remove(configId);
    if (activeGroupConfigId == configId) {
      activeGroupConfigId = groupConfigurations.isNotEmpty ? groupConfigurations.keys.first : null;
    }
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  @override
  void renameGroupConfiguration(String configId, String newName) {
    groupConfigurations[configId]?.name = newName;
    saveUndoState();
    notifyListeners();
  }

  @override
  void setActiveGroupConfiguration(String? configId) {
    activeGroupConfigId = configId;
    groupVersion++;
    notifyListeners();
  }

  /// Creates a new group from the current selection, removing slats from any
  /// existing group they belong to (a slat can only be in one group per config).
  @override
  void createGroupFromSelection() {
    if (activeGroupConfig == null || selectedSlats.isEmpty) return;
    var config = activeGroupConfig!;
    String groupId = 'G${config.nextGroupNumber}';
    String groupName = 'Group ${config.nextGroupNumber}';
    int colorIndex = config.groups.length % colorPalette.length;
    Color groupColor = Color(int.parse('0xFF${colorPalette[colorIndex].replaceFirst('#', '')}'));
    config.nextGroupNumber++;

    var group = SlatGroup(id: groupId, name: groupName, color: groupColor);
    for (var slatId in selectedSlats) {
      if (!slats.containsKey(slatId)) continue;
      if (slats[slatId]!.phantomParent != null) continue;
      // Remove from previous group if reassigning
      if (config.slatToGroup.containsKey(slatId)) {
        config.groups[config.slatToGroup[slatId]]?.slatIds.remove(slatId);
      }
      group.slatIds.add(slatId);
      config.slatToGroup[slatId] = groupId;
    }
    config.groups[groupId] = group;
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  @override
  void deleteGroup(String groupId) {
    if (activeGroupConfig == null) return;
    var config = activeGroupConfig!;
    var group = config.groups[groupId];
    if (group == null) return;
    for (var slatId in group.slatIds) {
      config.slatToGroup.remove(slatId);
    }
    config.groups.remove(groupId);
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  @override
  void renameGroup(String groupId, String newName) {
    activeGroupConfig?.groups[groupId]?.name = newName;
    saveUndoState();
    notifyListeners();
  }

  @override
  void recolorGroup(String groupId, Color color) {
    activeGroupConfig?.groups[groupId]?.color = color;
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  @override
  void addSlatsToGroup(String groupId, List<String> slatIds) {
    if (activeGroupConfig == null) return;
    var config = activeGroupConfig!;
    var group = config.groups[groupId];
    if (group == null) return;
    for (var slatId in slatIds) {
      if (!slats.containsKey(slatId)) continue;
      if (slats[slatId]!.phantomParent != null) continue;
      if (config.slatToGroup.containsKey(slatId)) {
        config.groups[config.slatToGroup[slatId]]?.slatIds.remove(slatId);
      }
      group.slatIds.add(slatId);
      config.slatToGroup[slatId] = groupId;
    }
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  @override
  void removeSlatsFromGroup(String groupId, List<String> slatIds) {
    if (activeGroupConfig == null) return;
    var config = activeGroupConfig!;
    var group = config.groups[groupId];
    if (group == null) return;
    for (var slatId in slatIds) {
      group.slatIds.remove(slatId);
      config.slatToGroup.remove(slatId);
    }
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  /// Selects all slats belonging to a group (sets selectedSlats to match group membership).
  @override
  void selectGroupSlats(String groupId) {
    if (activeGroupConfig == null) return;
    var group = activeGroupConfig!.groups[groupId];
    if (group == null) return;
    selectedSlats = group.slatIds.where((id) => slats.containsKey(id)).toList();
    notifyListeners();
  }

  /// Replaces the membership of an existing group with the current selection.
  /// Slats moving from other groups are reassigned automatically.
  @override
  void updateGroupToSelection(String groupId) {
    if (activeGroupConfig == null || selectedSlats.isEmpty) return;
    var config = activeGroupConfig!;
    var group = config.groups[groupId];
    if (group == null) return;

    // Remove old members from the reverse lookup
    for (var slatId in group.slatIds) {
      config.slatToGroup.remove(slatId);
    }
    group.slatIds.clear();

    // Assign current selection to this group
    for (var slatId in selectedSlats) {
      if (!slats.containsKey(slatId)) continue;
      if (slats[slatId]!.phantomParent != null) continue;
      // Steal from other groups if needed
      if (config.slatToGroup.containsKey(slatId)) {
        config.groups[config.slatToGroup[slatId]]?.slatIds.remove(slatId);
      }
      group.slatIds.add(slatId);
      config.slatToGroup[slatId] = groupId;
    }
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  /// Partitions all non-phantom slats into groups of [groupSize], chunking
  /// within each layer independently (never mixing slats from different layers).
  @override
  void autoGroupSlats(int groupSize) {
    if (activeGroupConfig == null || groupSize <= 0) return;
    var config = activeGroupConfig!;

    config.groups.clear();
    config.slatToGroup.clear();
    config.nextGroupNumber = 1;

    // Bucket slats by layer, sorted by layer order
    Map<String, List<String>> slatsByLayer = {};
    for (var entry in slats.entries) {
      if (entry.value.phantomParent != null) continue;
      slatsByLayer.putIfAbsent(entry.value.layer, () => []).add(entry.key);
    }
    List<String> sortedLayerKeys = slatsByLayer.keys.toList()
      ..sort((a, b) => (layerMap[a]?['order'] ?? 0).compareTo(layerMap[b]?['order'] ?? 0));

    // Chunk within each layer independently
    for (var layerKey in sortedLayerKeys) {
      var layerSlats = slatsByLayer[layerKey]!
        ..sort((a, b) => slats[a]!.numericID.compareTo(slats[b]!.numericID));

      for (int i = 0; i < layerSlats.length; i += groupSize) {
        int end = (i + groupSize < layerSlats.length) ? i + groupSize : layerSlats.length;
        List<String> chunk = layerSlats.sublist(i, end);

        String groupId = 'G${config.nextGroupNumber}';
        String groupName = 'Group ${config.nextGroupNumber}';
        int colorIndex = config.groups.length % colorPalette.length;
        Color groupColor = Color(int.parse('0xFF${colorPalette[colorIndex].replaceFirst('#', '')}'));
        config.nextGroupNumber++;

        var group = SlatGroup(id: groupId, name: groupName, color: groupColor, slatIds: chunk.toSet());
        config.groups[groupId] = group;
        for (var slatId in chunk) {
          config.slatToGroup[slatId] = groupId;
        }
      }
    }
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  @override
  void clearAllGroups() {
    if (activeGroupConfig == null) return;
    activeGroupConfig!.groups.clear();
    activeGroupConfig!.slatToGroup.clear();
    activeGroupConfig!.nextGroupNumber = 1;
    groupVersion++;
    saveUndoState();
    notifyListeners();
  }

  /// Resets all group state including the configuration counter.
  @override
  void resetGroupState() {
    groupConfigurations = {};
    activeGroupConfigId = null;
    _nextConfigNumber = 1;
    groupVersion++;
  }

  /// Removes a deleted slat from ALL configurations (not just the active one).
  @override
  void cleanupDeletedSlat(String slatId) {
    for (var config in groupConfigurations.values) {
      var groupId = config.slatToGroup[slatId];
      if (groupId != null) {
        config.groups[groupId]?.slatIds.remove(slatId);
        config.slatToGroup.remove(slatId);
      }
    }
  }

  /// Returns the group color for a slat in the active configuration, or null if
  /// the slat is ungrouped. Phantom slats inherit their parent's group color.
  @override
  Color? resolveGroupColor(String slatId) {
    if (activeGroupConfig == null) return null;
    var groupId = activeGroupConfig!.slatToGroup[slatId];
    // If the slat isn't directly grouped, check if it's a phantom with a grouped parent
    if (groupId == null) {
      var parentId = slats[slatId]?.phantomParent;
      if (parentId != null) {
        groupId = activeGroupConfig!.slatToGroup[parentId];
      }
    }
    if (groupId == null) return null;
    return activeGroupConfig!.groups[groupId]?.color;
  }
}
