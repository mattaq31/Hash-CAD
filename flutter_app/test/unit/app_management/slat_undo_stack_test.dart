import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/app_management/slat_undo_stack.dart';
import 'package:hash_cad/app_management/design_state_mixins/design_state_handle_link_mixin.dart';

import '../../helpers/design_state_test_factory.dart';

/// Creates a minimal DesignSaveState snapshot from a DesignState with [slatCount] slats.
DesignSaveState _snapshotFromSlats(int slatCount) {
  final ds = DesignStateTestFactory.createWithSlats(slatCount: slatCount);
  return DesignSaveState(
    slats: ds.slats,
    occupiedGridPoints: ds.occupiedGridPoints,
    layerMap: ds.layerMap,
    layerMetaData: {'selectedLayerKey': 'A', 'nextLayerKey': 'C', 'nextColorIndex': 2},
    cargoPalette: ds.cargoPalette,
    occupiedCargoPoints: ds.occupiedCargoPoints,
    seedRoster: {},
    phantomMap: {},
    assemblyLinkManager: HandleLinkManager(),
    gridMode: 'crisscross',
    groupConfigurations: {},
    activeGroupConfigId: null,
  );
}

/// Creates a trivially distinguishable snapshot with a custom gridMode tag.
DesignSaveState _taggedSnapshot(String tag) {
  return DesignSaveState(
    slats: {},
    occupiedGridPoints: {},
    layerMap: {},
    layerMetaData: {},
    cargoPalette: {},
    occupiedCargoPoints: {},
    seedRoster: {},
    phantomMap: {},
    assemblyLinkManager: HandleLinkManager(),
    gridMode: tag,
    groupConfigurations: {},
    activeGroupConfigId: null,
  );
}

void main() {
  group('DesignSaveState.copy()', () {
    test('copy produces identical content', () {
      final original = _snapshotFromSlats(3);
      final copy = original.copy();

      expect(copy.slats.length, original.slats.length);
      expect(copy.gridMode, original.gridMode);
      expect(copy.layerMetaData, original.layerMetaData);
      for (var key in original.slats.keys) {
        expect(copy.slats.containsKey(key), isTrue);
      }
      for (var layerKey in original.occupiedGridPoints.keys) {
        expect(copy.occupiedGridPoints[layerKey]?.length, original.occupiedGridPoints[layerKey]?.length);
      }
    });

    test('copy is independent — modifying copy does not affect original', () {
      final original = _snapshotFromSlats(3);
      final copy = original.copy();

      final slatCount = original.slats.length;
      copy.slats.clear();
      expect(original.slats.length, slatCount);
    });

    test('copy is independent — modifying original does not affect copy', () {
      final original = _snapshotFromSlats(3);
      final copy = original.copy();

      final slatKeys = copy.slats.keys.toSet();
      original.slats.clear();
      expect(copy.slats.keys.toSet(), slatKeys);
    });
  });

  group('SlatUndoStack', () {
    late SlatUndoStack stack;

    setUp(() {
      stack = SlatUndoStack();
    });

    test('initially cannot undo or redo', () {
      expect(stack.canUndo, isFalse);
      expect(stack.canRedo, isFalse);
    });

    test('single save — cannot undo or redo', () {
      stack.saveState(_taggedSnapshot('s1'));
      expect(stack.canUndo, isFalse);
      expect(stack.canRedo, isFalse);
    });

    test('two saves — can undo, cannot redo', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));
      expect(stack.canUndo, isTrue);
      expect(stack.canRedo, isFalse);
    });

    test('saveState + undo returns the first state', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));

      final restored = stack.undo();
      expect(restored, isNotNull);
      expect(restored!.gridMode, 's1');
    });

    test('redo after undo restores the second state', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));

      stack.undo();
      final restored = stack.redo();
      expect(restored, isNotNull);
      expect(restored!.gridMode, 's2');
    });

    test('undo at beginning returns null', () {
      stack.saveState(_taggedSnapshot('s1'));
      expect(stack.undo(), isNull);
    });

    test('redo at end returns null', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));
      expect(stack.redo(), isNull);
    });

    test('multiple undos walk backward through history', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));
      stack.saveState(_taggedSnapshot('s3'));

      expect(stack.undo()!.gridMode, 's2');
      expect(stack.undo()!.gridMode, 's1');
      expect(stack.undo(), isNull);
    });

    test('multiple redos walk forward through history', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));
      stack.saveState(_taggedSnapshot('s3'));

      stack.undo();
      stack.undo();

      expect(stack.redo()!.gridMode, 's2');
      expect(stack.redo()!.gridMode, 's3');
      expect(stack.redo(), isNull);
    });

    test('new save discards redo history', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));
      stack.saveState(_taggedSnapshot('s3'));

      stack.undo(); // back to s2
      stack.saveState(_taggedSnapshot('s4')); // should discard s3

      expect(stack.canRedo, isFalse);
      expect(stack.redo(), isNull);
      expect(stack.undo()!.gridMode, 's2');
    });

    test('undo-save-undo chain works correctly', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));

      stack.undo(); // at s1
      stack.saveState(_taggedSnapshot('s3')); // discard s2, now [s1, s3]

      expect(stack.undo()!.gridMode, 's1');
      expect(stack.undo(), isNull);

      expect(stack.redo()!.gridMode, 's3');
      expect(stack.redo(), isNull);
    });

    test('canUndo and canRedo update correctly through undo-redo cycle', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));
      stack.saveState(_taggedSnapshot('s3'));

      // At end: can undo, can't redo
      expect(stack.canUndo, isTrue);
      expect(stack.canRedo, isFalse);

      stack.undo(); // at s2
      expect(stack.canUndo, isTrue);
      expect(stack.canRedo, isTrue);

      stack.undo(); // at s1
      expect(stack.canUndo, isFalse);
      expect(stack.canRedo, isTrue);

      stack.redo(); // at s2
      expect(stack.canUndo, isTrue);
      expect(stack.canRedo, isTrue);

      stack.redo(); // at s3
      expect(stack.canUndo, isTrue);
      expect(stack.canRedo, isFalse);
    });

    test('max history trimming preserves full undo depth', () {
      // Save 51 states (one more than the max of 50)
      for (int i = 0; i < 51; i++) {
        stack.saveState(_taggedSnapshot('s$i'));
      }

      // Should be at the latest state, no redo available
      expect(stack.canRedo, isFalse);
      expect(stack.canUndo, isTrue);

      // Count available undos
      int undoCount = 0;
      while (stack.undo() != null) {
        undoCount++;
      }
      // 50 entries in history, current at index 49 → 49 undos
      expect(undoCount, 49);
    });

    test('max history trimming discards oldest state', () {
      // Save 51 tagged states
      for (int i = 0; i < 51; i++) {
        stack.saveState(_taggedSnapshot('s$i'));
      }

      // Undo all the way back — the oldest reachable should be s1 (s0 was trimmed)
      DesignSaveState? oldest;
      while (true) {
        final prev = stack.undo();
        if (prev == null) break;
        oldest = prev;
      }
      expect(oldest, isNotNull);
      expect(oldest!.gridMode, 's1');
    });

    test('returned states are independent copies — modifying undo result does not affect stack', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));

      final restored = stack.undo()!;
      expect(restored.gridMode, 's1');

      // Mutate the returned object
      restored.slats['fake'] = DesignStateTestFactory.createWithSlats(slatCount: 1).slats.values.first;

      // Redo and come back — should still be clean
      stack.redo();
      final restoredAgain = stack.undo()!;
      expect(restoredAgain.slats.containsKey('fake'), isFalse);
    });

    test('returned states are independent copies — modifying redo result does not affect stack', () {
      stack.saveState(_taggedSnapshot('s1'));
      stack.saveState(_taggedSnapshot('s2'));

      stack.undo();
      final redone = stack.redo()!;
      redone.slats['fake'] = DesignStateTestFactory.createWithSlats(slatCount: 1).slats.values.first;

      // Undo and redo again — should still be clean
      stack.undo();
      final redoneAgain = stack.redo()!;
      expect(redoneAgain.slats.containsKey('fake'), isFalse);
    });

    test('works with realistic DesignSaveState snapshots', () {
      final snap1 = _snapshotFromSlats(3);
      final snap2 = _snapshotFromSlats(5);
      final snap3 = _snapshotFromSlats(7);

      stack.saveState(snap1);
      stack.saveState(snap2);
      stack.saveState(snap3);

      final undone = stack.undo()!;
      expect(undone.slats.length, snap2.slats.length);

      final redone = stack.redo()!;
      expect(redone.slats.length, snap3.slats.length);
    });

    test('saving same state twice creates two undo points', () {
      final snap = _taggedSnapshot('same');
      stack.saveState(snap);
      stack.saveState(snap);

      expect(stack.canUndo, isTrue);
      final restored = stack.undo()!;
      expect(restored.gridMode, 'same');
      expect(stack.canUndo, isFalse);
    });
  });
}
