import 'package:flutter/material.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/common_utilities.dart';
import '../shared_app_state.dart';


String dartToPythonSlatNameConvert(String name, Map<String, Map<String, dynamic>> layerMap){
  String layerID = name.split('-').first.replaceAll('-I', '');
  int layerOrder = layerMap[layerID]!['order'] + 1;
  int slat = int.parse(name.split('-').last.replaceAll('I', ''));

  return 'layer$layerOrder-slat$slat';
}

String pythonToDartSlatNameConvert(String name, Map<String, Map<String, dynamic>> layerMap){
  int layer = int.parse(name.split('-').first.replaceAll('layer', '')) - 1;
  int slat = int.parse(name.split('-').last.replaceAll('slat', ''));
  String? layerID = getLayerByOrder(layerMap, layer);
  return '$layerID-I$slat';
}

/// Manages handle linking constraints for assembly handles.
///
/// This class tracks three types of constraints on handle values:
///
/// 1. **Linked Groups**: Handles that must share the same value. When one handle
///    in a group changes, all others must change to match.
///    - Stored in: handleLinkToGroup (key → groupId) and
///      handleGroupToLink (groupId → list of keys)
///
/// 2. **Enforced Values**: Groups that must have a specific handle value.
///    - Stored in: handleGroupToValue (groupId → value)
///
/// 3. **Blocked Handles**: Individual handles that must be zero (deleted).
///    - Stored in: handleBlocks (list of keys)
///
/// Handle keys use the convention: (slatID, position, helixSide)
/// Example: ('A-I5', 3, 2) means position 3 on H2 side of A-I5.
///
/// Group IDs use two separate namespaces to avoid collisions:
/// - Numeric (1, 2, 3...): User-defined groups from spreadsheet
/// - Alphabetic ('A', 'B', 'C'...): Auto-generated groups for enforced values
/// Alphabetic groups are never saved to file.
class HandleLinkManager {
  /// Maps handle key → group ID
  Map<HandleKey, dynamic> handleLinkToGroup = {};

  /// Maps group ID → list of handle keys
  Map<dynamic, List<HandleKey>> handleGroupToLink = {};

  /// Maps group ID → enforced value
  Map<dynamic, int> handleGroupToValue = {};

  /// List of blocked handle positions
  List<HandleKey> handleBlocks = [];

  /// Next alphabetic group ID for auto-generated groups (never saved to file)
  String nextGroupAssignment = 'A';

  /// Tracks highest numeric group ID from spreadsheet
  int maxGroupId = 0;

  HandleLinkManager();

  /// Returns the enforced value for a handle key, or null if not enforced.
  /// Returns 0 if the handle is blocked.
  int? getEnforceValue(HandleKey accessKey) {
    if (handleBlocks.contains(accessKey)) {
      return 0;
    }
    if (handleLinkToGroup.containsKey(accessKey)) {
      var group = handleLinkToGroup[accessKey];
      if (handleGroupToValue.containsKey(group)) {
        return handleGroupToValue[group];
      }
    }
    return null;
  }

  /// Adds a block to a handle.
  void addBlock(HandleKey key) {
    if (!handleBlocks.contains(key)) {
      handleBlocks.add(key);
    }
  }

  /// Removes a block from a handle.
  void removeBlock(HandleKey key) {
    handleBlocks.remove(key);
  }

  /// Removes a link from a handle.
  void removeLink(HandleKey key) {
    var group = handleLinkToGroup[key];
    if (group != null) {
      handleGroupToLink[group]?.remove(key);
      handleLinkToGroup.remove(key);
      if (handleGroupToLink[group]?.isEmpty ?? true) {
        handleGroupToLink.remove(group);
        handleGroupToValue.remove(group);
      }
    }
  }

  /// Updates a handle key to a new key, preserving all links and blocks.
  /// Used when moving assembly handles to transfer their link relationships.
  void updateKey(HandleKey oldKey, HandleKey newKey) {
    // Update blocks
    int blockIndex = handleBlocks.indexOf(oldKey);
    if (blockIndex != -1) {
      handleBlocks[blockIndex] = newKey;
    }

    // Update links
    var group = handleLinkToGroup[oldKey];
    if (group != null) {
      // Remove old key from group
      handleGroupToLink[group]?.remove(oldKey);
      handleLinkToGroup.remove(oldKey);

      // Add new key to group
      handleLinkToGroup[newKey] = group;
      handleGroupToLink[group]?.add(newKey);
    }
  }

  /// Removes an entire handle link group.
  void removeGroup(dynamic groupId) {
    if (handleGroupToLink.containsKey(groupId)) {
      for (var key in handleGroupToLink[groupId]!) {
        handleLinkToGroup.remove(key);
      }
      handleGroupToLink.remove(groupId);
      handleGroupToValue.remove(groupId);
    }
  }

  /// Merge sourceGroup into targetGroup, moving all keys and enforced values.
  /// Throws if groups have conflicting enforced values.
  void _mergeGroups(dynamic targetGroup, dynamic sourceGroup) {
    for (var key in handleGroupToLink[sourceGroup]!) {
      handleLinkToGroup[key] = targetGroup;
      handleGroupToLink[targetGroup]!.add(key);
    }
    handleGroupToLink.remove(sourceGroup);

    if (handleGroupToValue.containsKey(sourceGroup)) {
      if (handleGroupToValue.containsKey(targetGroup) && handleGroupToValue[targetGroup] != handleGroupToValue[sourceGroup]) {
        throw StateError('Cannot merge two handle link groups with different enforced values.');
      }
      handleGroupToValue[targetGroup] = handleGroupToValue[sourceGroup]!;
      handleGroupToValue.remove(sourceGroup);
    }
  }

  /// Adds a link between two handles. Creates a new group if needed, or merges existing groups.
  void addLink(HandleKey key1, HandleKey key2) {
    var group1 = handleLinkToGroup[key1];
    var group2 = handleLinkToGroup[key2];

    if (group1 == null && group2 == null) {
      // Create new group using alphabetic ID (never saved to file)
      var newGroup = nextCapitalLetter(nextGroupAssignment);
      nextGroupAssignment = newGroup;
      handleLinkToGroup[key1] = newGroup;
      handleLinkToGroup[key2] = newGroup;
      handleGroupToLink[newGroup] = [key1, key2];
    } else if (group1 != null && group2 == null) {
      // Add key2 to group1
      handleLinkToGroup[key2] = group1;
      handleGroupToLink[group1]!.add(key2);
    } else if (group1 == null && group2 != null) {
      // Add key1 to group2
      handleLinkToGroup[key1] = group2;
      handleGroupToLink[group2]!.add(key1);
    } else if (group1 != group2) {
      // Merge group2 into group1
      _mergeGroups(group1, group2);
    }
  }

  /// Links multiple handles together. First handle becomes the anchor group.
  void linkMultiple(List<HandleKey> keys) {
    if (keys.length < 2) return;
    for (int i = 1; i < keys.length; i++) {
      addLink(keys[0], keys[i]);
    }
  }

  /// Sets an enforced value for a group containing the given handle key.
  /// Creates a new group if the handle is not already in one.
  void setEnforcedValue(HandleKey key, int value) {
    var group = handleLinkToGroup[key];
    if (group == null) {
      // Create a single-handle group with the enforced value
      var newGroup = nextCapitalLetter(nextGroupAssignment);
      nextGroupAssignment = newGroup;
      handleLinkToGroup[key] = newGroup;
      handleGroupToLink[newGroup] = [key];
      handleGroupToValue[newGroup] = value;
    } else {
      handleGroupToValue[group] = value;
    }
  }

  /// Gets all handles linked to the given handle (including itself).
  List<HandleKey> getLinkedHandles(HandleKey key) {
    var group = handleLinkToGroup[key];
    if (group == null) return [key];
    return List.from(handleGroupToLink[group] ?? [key]);
  }

  /// Returns the group ID for a handle, or null if not in a group.
  dynamic getGroup(HandleKey key) {
    return handleLinkToGroup[key];
  }

  /// Clears all link and block data.
  void clearAll() {
    handleLinkToGroup.clear();
    handleGroupToLink.clear();
    handleGroupToValue.clear();
    handleBlocks.clear();
    nextGroupAssignment = 'A';
    maxGroupId = 0;
  }

  /// Creates a deep copy of the link manager.
  HandleLinkManager copy() {
    var newManager = HandleLinkManager();
    newManager.handleLinkToGroup = Map.from(handleLinkToGroup);
    newManager.handleGroupToLink = {for (var entry in handleGroupToLink.entries) entry.key: List.from(entry.value)};
    newManager.handleGroupToValue = Map.from(handleGroupToValue);
    newManager.handleBlocks = List.from(handleBlocks);
    newManager.nextGroupAssignment = nextGroupAssignment;
    newManager.maxGroupId = maxGroupId;
    return newManager;
  }

  /// Imports link data from Excel sheet format.
  /// Each slat has 6 rows: [slat_name, Position, h5-val, h5-link-group, h2-val, h2-link-group]
  void importFromExcelData(List<List<dynamic>> data, Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap) {
    clearAll();

    for (int i = 0; i < data.length; i += 6) {
      if (i >= data.length) break;

      var slatName = pythonToDartSlatNameConvert(data[i][0]!.toString(), layerMap);

      if (slatName.isEmpty) continue;

      // Get slat to determine max length
      var slat = slats[slatName];
      if (slat == null) continue;

      // Process H5 (rows i+2 and i+3) and H2 (rows i+4 and i+5)
      for (var (side, valRowOffset, groupRowOffset) in [(5, 2, 3), (2, 4, 5)]) {
        if (i + valRowOffset >= data.length || i + groupRowOffset >= data.length) continue;

        var valRow = data[i + valRowOffset];
        var groupRow = data[i + groupRowOffset];

        for (int pos = 1; pos <= slat.maxLength; pos++) {
          if (pos >= valRow.length || pos >= groupRow.length) continue;

          var enforceVal = _parseNumeric(valRow[pos]);
          var group = _parseNumeric(groupRow[pos]);
          HandleKey key = (slatName, pos, side);

          if (enforceVal == null && group == null) continue;

          if (enforceVal == 0) {
            // Blocked handle
            handleBlocks.add(key);
          } else if (enforceVal != null && group == null) {
            // Enforce value without explicit group - create auto group
            var newGroup = nextCapitalLetter(nextGroupAssignment);
            nextGroupAssignment = newGroup;
            handleGroupToValue[newGroup] = enforceVal.toInt();
            handleGroupToLink[newGroup] = [key];
            handleLinkToGroup[key] = newGroup;
          } else if (group != null) {
            // Explicit group
            int groupInt = group.toInt();
            handleLinkToGroup[key] = groupInt;
            handleGroupToLink.putIfAbsent(groupInt, () => []);
            handleGroupToLink[groupInt]!.add(key);

            if (enforceVal != null) {
              if (handleGroupToValue.containsKey(groupInt) && handleGroupToValue[groupInt] != enforceVal.toInt()) {
                throw StateError('Cannot enforce multiple values to the same slat handle group. Check the slat_handle_links sheet.');
              }
              handleGroupToValue[groupInt] = enforceVal.toInt();
            }
            maxGroupId = maxGroupId > groupInt ? maxGroupId : groupInt;
          }
        }
      }
    }
  }

  /// Parses a value that might be null, empty string, or numeric
  num? _parseNumeric(dynamic value) {
    if (value == null) return null;
    if (value is num) return value;
    if (value is String) {
      if (value.isEmpty) return null;
      return num.tryParse(value);
    }
    return null;
  }

  /// Exports link data to Excel sheet format.
  /// Returns list of rows, where each slat has 6 rows.
  List<List<dynamic>> exportToExcelData(Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap) {
    List<List<dynamic>> output = [];

    // Determine max slat length
    int maxSlatLen = 0;
    for (var slat in slats.values) {
      if (slat.phantomParent == null) {
        maxSlatLen = maxSlatLen > slat.maxLength ? maxSlatLen : slat.maxLength;
      }
    }

    for (var entry in slats.entries) {
      if (entry.value.phantomParent != null) continue; // no phantom slats
      var slatId = entry.key;
      var slat = entry.value;

      if (slat.phantomParent != null) continue;

      // Layer-Slat Name row
      output.add([dartToPythonSlatNameConvert(slatId, layerMap), ...List.filled(maxSlatLen, null)]);

      // Position row
      output.add(['Position', ...List.generate(slat.maxLength, (i) => i + 1), ...List.filled(maxSlatLen - slat.maxLength, null)]);

      // Handle rows (h5-val, h5-link-group, h2-val, h2-link-group)
      for (var side in [5, 2]) {
        List<dynamic> valRow = ['h$side-val'];
        List<dynamic> groupRow = ['h$side-link-group'];

        for (int pos = 1; pos <= slat.maxLength; pos++) {
          HandleKey key = (slatId, pos, side);
          dynamic val;
          dynamic group;

          // Check if blocked
          if (handleBlocks.contains(key)) {
            val = 0;
          }
          // Check if in a group
          else if (handleLinkToGroup.containsKey(key)) {
            var g = handleLinkToGroup[key];
            val = handleGroupToValue[g];
            // Only export numeric group IDs (not alphabetic auto-generated ones)
            if (g is int) {
              group = g;
            }
          }

          valRow.add(val ?? '');
          groupRow.add(group ?? '');
        }

        valRow.addAll(List.filled(maxSlatLen - slat.maxLength, null));
        groupRow.addAll(List.filled(maxSlatLen - slat.maxLength, null));
        output.add(valRow);
        output.add(groupRow);
      }
    }

    return output;
  }

  /// Checks if any links or blocks exist
  bool get hasData => handleLinkToGroup.isNotEmpty || handleBlocks.isNotEmpty;

  /// Removes all link manager entries for a given slat ID.
  /// Called when a slat is deleted to clean up stale references.
  void removeAllEntriesForSlat(String slatId) {
    // Remove from blocks
    handleBlocks.removeWhere((key) => key.$1 == slatId);

    // Find all keys for this slat
    List<HandleKey> keysToRemove = handleLinkToGroup.keys.where((key) => key.$1 == slatId).toList();

    // Remove each key from its group
    for (var key in keysToRemove) {
      removeLink(key);
    }
  }

  /// Validates import data for conflicts before applying.
  /// Returns null if valid, or an error message if conflicts exist.
  String? validateImport(List<List<dynamic>> data, Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap) {
    // Create a temporary manager to parse the data
    var tempManager = HandleLinkManager();
    try {
      tempManager.importFromExcelData(data, slats, layerMap);
    } on StateError catch (e) {
      // importFromExcelData throws StateError for conflicting enforced values in same group
      return e.message;
    } catch (e) {
      return 'Import error: ${e.toString()}';
    }

    // Check for conflicts with existing handle values in slats
    for (var groupEntry in tempManager.handleGroupToValue.entries) {
      var groupId = groupEntry.key;
      var enforcedValue = groupEntry.value;

      for (var handleKey in tempManager.handleGroupToLink[groupId] ?? []) {
        var slat = slats[handleKey.$1];
        if (slat == null) continue;

        var handleDict = handleKey.$3 == 5 ? slat.h5Handles : slat.h2Handles;
        var currentHandle = handleDict[handleKey.$2];

        if (currentHandle != null && currentHandle['category']?.contains('ASSEMBLY') == true) {
          var currentValue = int.tryParse(currentHandle['value']?.toString() ?? '');
          if (currentValue != null && currentValue != 0 && currentValue != enforcedValue) {
            String slatName = dartToPythonSlatNameConvert(handleKey.$1, layerMap);
            return 'Conflict: Handle at $slatName position ${handleKey.$2} H${handleKey.$3} has value '
                '$currentValue but import requires $enforcedValue';
          }
        }
      }
    }

    // Check for blocks that conflict with existing non-zero handles
    for (var blockedKey in tempManager.handleBlocks) {
      var slat = slats[blockedKey.$1];
      if (slat == null) continue;

      var handleDict = blockedKey.$3 == 5 ? slat.h5Handles : slat.h2Handles;
      var currentHandle = handleDict[blockedKey.$2];

      if (currentHandle != null && currentHandle['category']?.contains('ASSEMBLY') == true) {
        var currentValue = int.tryParse(currentHandle['value']?.toString() ?? '');
        if (currentValue != null && currentValue != 0) {
          String slatName = dartToPythonSlatNameConvert(blockedKey.$1, layerMap);
          return 'Conflict: Handle at $slatName position ${blockedKey.$2} H${blockedKey.$3} has value '
              '$currentValue but import blocks this position (requires 0)';
        }
      }
    }

    return null; // No conflicts
  }
}

/// Mixin providing HandleLinkManager access in DesignState
mixin DesignStateHandleLinkMixin on ChangeNotifier {
  // Required state
  Map<String, Slat> get slats;
  Map<String, Map<String, dynamic>> get layerMap;

  // The link manager instance
  HandleLinkManager get assemblyLinkManager;
  set assemblyLinkManager(HandleLinkManager value);

  /// Clears all handle links and blocks
  void clearAllHandleLinks() {
    assemblyLinkManager.clearAll();
    notifyListeners();
  }

  /// Imports handle link data from Excel format
  void importHandleLinks(List<List<dynamic>> data) {
    assemblyLinkManager.importFromExcelData(data, slats, layerMap);
    notifyListeners();
  }

  /// Exports handle link data to Excel format
  List<List<dynamic>> exportHandleLinks() {
    return assemblyLinkManager.exportToExcelData(slats, layerMap);
  }
}
