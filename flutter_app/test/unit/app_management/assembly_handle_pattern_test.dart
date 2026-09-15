// Unit tests for recording, naming and placing assembly handle patterns (DesignStateAssemblyPatternMixin).

import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/app_management/shared_app_state.dart';
import 'package:hash_cad/crisscross_core/assembly_handle_pattern.dart';
import 'package:hash_cad/crisscross_core/common_utilities.dart';
import 'package:hash_cad/crisscross_core/slats.dart';

import '../../helpers/design_state_test_factory.dart';

/// Returns the slat occupying [coord] on [layer].
Slat _slatAt(DesignState state, String layer, Offset coord) =>
    state.slats[state.occupiedGridPoints[layer]![coord]!]!;

/// Returns the handle dict entry at [coord] on [layer]/[attachMode].
Map<String, dynamic>? _handleAt(DesignState state, String layer, String attachMode, Offset coord) {
  final slat = _slatAt(state, layer, coord);
  final side = getSlatSideFromLayer(state.layerMap, layer, attachMode);
  return getHandleDict(slat, side)[slat.slatCoordinateToPosition[coord]!];
}

/// Returns the handle key for [coord] on [layer]/[attachMode].
HandleKey _keyAt(DesignState state, String layer, String attachMode, Offset coord) {
  final slat = _slatAt(state, layer, coord);
  final side = getSlatSideFromLayer(state.layerMap, layer, attachMode);
  return (slat.id, slat.slatCoordinateToPosition[coord]!, side);
}

void main() {
  late DesignState state;
  late List<Offset> slatCoords; // coordinates of the first slat on layer A, ordered by position

  setUp(() {
    // Layer A (bottom) holds slats; top-side handles on A are allowed as B sits above it
    state = DesignStateTestFactory.createWithSlats(slatCount: 3);
    final firstSlat = state.slats.values.first;
    slatCoords = [for (int p = 1; p <= firstSlat.maxLength; p++) firstSlat.slatPositionToCoordinate[p]!];
  });

  /// Places a handle with [value] at [coord] on the top side of layer A.
  void placeTop(Offset coord, String value) {
    final slat = _slatAt(state, 'A', coord);
    final side = getSlatSideFromLayer(state.layerMap, 'A', 'top');
    state.smartSetHandle(slat, slat.slatCoordinateToPosition[coord]!, side, value, 'ASSEMBLY_HANDLE');
  }

  group('recordAssemblyHandlePattern', () {
    test('records values and offsets relative to the top-left handle', () {
      placeTop(slatCoords[2], '7');
      placeTop(slatCoords[4], '9');
      state.selectedAssemblyPositions = [slatCoords[4], slatCoords[2]];

      final id = state.recordAssemblyHandlePattern('A', 'top');

      expect(id, isNotNull);
      final pattern = state.assemblyHandlePatterns[id]!;
      expect(pattern.name, 'Pattern 1');
      expect(pattern.entries.length, 2);

      final anchor = findPatternAnchor([slatCoords[2], slatCoords[4]]);
      final byOffset = {for (var e in pattern.entries) e.offset: e};
      expect(byOffset.keys, contains(Offset.zero));
      expect(byOffset[slatCoords[2] - anchor]!.value, '7');
      expect(byOffset[slatCoords[4] - anchor]!.value, '9');
    });

    test('records blocked handles as blocked entries', () {
      placeTop(slatCoords[1], '5');
      state.toggleHandleBlockAndApply(_keyAt(state, 'A', 'top', slatCoords[3]));
      state.selectedAssemblyPositions = [slatCoords[1], slatCoords[3]];

      final pattern = state.assemblyHandlePatterns[state.recordAssemblyHandlePattern('A', 'top')]!;

      final blocked = pattern.entries.where((e) => e.blocked).toList();
      expect(blocked.length, 1);
      expect(blocked.single.value, '0');
      expect(pattern.entries.where((e) => !e.blocked).single.value, '5');
    });

    test('can record only valued handles or only blocks', () {
      placeTop(slatCoords[1], '5');
      state.toggleHandleBlockAndApply(_keyAt(state, 'A', 'top', slatCoords[3]));
      state.selectedAssemblyPositions = [slatCoords[1], slatCoords[3]];

      final handlesOnly = state.assemblyHandlePatterns[
          state.recordAssemblyHandlePattern('A', 'top', includeBlocks: false)]!;
      expect(handlesOnly.entries.single.value, '5');
      expect(handlesOnly.entries.single.blocked, isFalse);
      expect(handlesOnly.entries.single.offset, Offset.zero); // anchor computed from recorded entries only

      final blocksOnly = state.assemblyHandlePatterns[
          state.recordAssemblyHandlePattern('A', 'top', includeHandles: false)]!;
      expect(blocksOnly.entries.single.blocked, isTrue);
      expect(blocksOnly.entries.single.offset, Offset.zero);

      // no blocks in the selection -> nothing to record
      state.selectedAssemblyPositions = [slatCoords[1]];
      expect(state.recordAssemblyHandlePattern('A', 'top', includeHandles: false), isNull);
    });

    test('treats an unregistered value-0 handle as a block when filtering', () {
      // value '0' without a registered block is still drawn as a block by the slat painter
      placeTop(slatCoords[2], '0');
      state.selectedAssemblyPositions = [slatCoords[2]];

      expect(state.recordAssemblyHandlePattern('A', 'top', includeBlocks: false), isNull);
      final blocksOnly = state.assemblyHandlePatterns[
          state.recordAssemblyHandlePattern('A', 'top', includeHandles: false)]!;
      expect(blocksOnly.entries.single.blocked, isTrue);
    });

    test('skips selected positions without an assembly handle and returns null when nothing is recordable', () {
      state.selectedAssemblyPositions = [slatCoords[0]];
      expect(state.recordAssemblyHandlePattern('A', 'top'), isNull);
      expect(state.assemblyHandlePatterns, isEmpty);
    });

    test('default names reuse the first free number', () {
      placeTop(slatCoords[0], '1');
      state.selectedAssemblyPositions = [slatCoords[0]];
      final first = state.recordAssemblyHandlePattern('A', 'top')!;
      final second = state.recordAssemblyHandlePattern('A', 'top')!;
      expect(state.assemblyHandlePatterns[second]!.name, 'Pattern 2');

      state.deleteAssemblyHandlePattern(first);
      final third = state.recordAssemblyHandlePattern('A', 'top')!;
      expect(state.assemblyHandlePatterns[third]!.name, 'Pattern 1');
    });
  });

  group('renameAssemblyHandlePattern', () {
    test('rejects empty and duplicate names', () {
      placeTop(slatCoords[0], '1');
      state.selectedAssemblyPositions = [slatCoords[0]];
      final a = state.recordAssemblyHandlePattern('A', 'top')!;
      state.recordAssemblyHandlePattern('A', 'top');

      expect(state.renameAssemblyHandlePattern(a, '   '), isFalse);
      expect(state.renameAssemblyHandlePattern(a, 'Pattern 2'), isFalse);
      expect(state.renameAssemblyHandlePattern(a, 'Motif'), isTrue);
      expect(state.assemblyHandlePatterns[a]!.name, 'Motif');
    });
  });

  group('placeAssemblyHandlePattern', () {
    /// Records a pattern with values 3 and 4 on adjacent positions, plus a blocked position two further along.
    String recordSamplePattern() {
      placeTop(slatCoords[0], '3');
      placeTop(slatCoords[1], '4');
      state.toggleHandleBlockAndApply(_keyAt(state, 'A', 'top', slatCoords[3]));
      state.selectedAssemblyPositions = [slatCoords[0], slatCoords[1], slatCoords[3]];
      final id = state.recordAssemblyHandlePattern('A', 'top')!;
      // wipe the source handles so placement results are unambiguous
      state.clearAssemblyHandles();
      return id;
    }

    test('places values and blocks on the top side', () {
      final id = recordSamplePattern();
      final anchor = findPatternAnchor([slatCoords[0], slatCoords[1], slatCoords[3]]);
      final shift = slatCoords[10] - slatCoords[0];

      state.placeAssemblyHandlePattern(id, 'A', 'top', anchor + shift);

      expect(_handleAt(state, 'A', 'top', slatCoords[10])!['value'], '3');
      expect(_handleAt(state, 'A', 'top', slatCoords[10])!['category'], 'ASSEMBLY_HANDLE');
      expect(_handleAt(state, 'A', 'top', slatCoords[11])!['value'], '4');
      expect(_handleAt(state, 'A', 'top', slatCoords[13])!['value'], '0');
      expect(state.assemblyLinkManager.handleBlocks, contains(_keyAt(state, 'A', 'top', slatCoords[13])));
      expect(state.hammingValueValid, isFalse);
    });

    test('places on the bottom side with antihandle category', () {
      // layer B sits above A, so bottom-side handles are only valid on B
      state = DesignStateTestFactory.createWithMultiLayerSlats(slatsPerLayer: {'A': 1, 'B': 1});
      final bSlat = state.slats.values.firstWhere((s) => s.layer == 'B');
      final bCoords = [for (int p = 1; p <= bSlat.maxLength; p++) bSlat.slatPositionToCoordinate[p]!];
      final pattern = AssemblyHandlePattern(id: 'X', name: 'Manual', entries: const [
        AssemblyHandlePatternEntry(offset: Offset.zero, value: '12'),
      ]);
      state.assemblyHandlePatterns['X'] = pattern;

      state.placeAssemblyHandlePattern('X', 'B', 'bottom', bCoords[5]);

      final handle = _handleAt(state, 'B', 'bottom', bCoords[5])!;
      expect(handle['value'], '12');
      expect(handle['category'], 'ASSEMBLY_ANTIHANDLE');
    });

    test('enforce flag enforces placed values but not blocks', () {
      final id = recordSamplePattern();
      final anchor = findPatternAnchor([slatCoords[0], slatCoords[1], slatCoords[3]]);

      state.placeAssemblyHandlePattern(id, 'A', 'top', anchor, enforce: true);

      expect(state.assemblyLinkManager.getEnforceValue(_keyAt(state, 'A', 'top', slatCoords[0])), 3);
      expect(state.assemblyLinkManager.getEnforceValue(_keyAt(state, 'A', 'top', slatCoords[1])), 4);
      // blocked handles report 0 through the block list, not an enforced value group
      expect(state.assemblyLinkManager.getEnforceValue(_keyAt(state, 'A', 'top', slatCoords[3])), 0);
    });

    test('overrides an existing block and enforced value at a target position', () {
      final pattern = AssemblyHandlePattern(id: 'X', name: 'Single', entries: const [
        AssemblyHandlePatternEntry(offset: Offset.zero, value: '8'),
      ]);
      state.assemblyHandlePatterns['X'] = pattern;
      final blockedKey = _keyAt(state, 'A', 'top', slatCoords[6]);
      state.toggleHandleBlockAndApply(blockedKey);
      placeTop(slatCoords[7], '2');
      state.setHandleEnforcedValue(_keyAt(state, 'A', 'top', slatCoords[7]), 2);

      state.placeAssemblyHandlePattern('X', 'A', 'top', slatCoords[6]);
      state.placeAssemblyHandlePattern('X', 'A', 'top', slatCoords[7]);

      expect(state.assemblyLinkManager.handleBlocks, isNot(contains(blockedKey)));
      expect(_handleAt(state, 'A', 'top', slatCoords[6])!['value'], '8');
      expect(_handleAt(state, 'A', 'top', slatCoords[7])!['value'], '8');
      // the single-member group created by enforcing must be gone, otherwise the handle is drawn as linked
      final enforcedKey = _keyAt(state, 'A', 'top', slatCoords[7]);
      expect(state.assemblyLinkManager.handleLinkToGroup.containsKey(enforcedKey), isFalse);
      expect(state.assemblyLinkManager.getEnforceValue(enforcedKey), isNull);
    });

    test('a single undo reverts a whole stamp', () {
      final id = recordSamplePattern();
      state.saveUndoState(); // baseline after clearing the source handles
      final anchor = findPatternAnchor([slatCoords[0], slatCoords[1], slatCoords[3]]);

      state.placeAssemblyHandlePattern(id, 'A', 'top', anchor);
      state.undo2DAction();

      expect(_handleAt(state, 'A', 'top', slatCoords[0]), isNull);
      expect(_handleAt(state, 'A', 'top', slatCoords[1]), isNull);
      expect(state.assemblyHandlePatterns.containsKey(id), isTrue);
    });
  });

  test('resetDefaults clears patterns', () {
    placeTop(slatCoords[0], '1');
    state.selectedAssemblyPositions = [slatCoords[0]];
    state.recordAssemblyHandlePattern('A', 'top');

    state.resetDefaults();

    expect(state.assemblyHandlePatterns, isEmpty);
  });
}
