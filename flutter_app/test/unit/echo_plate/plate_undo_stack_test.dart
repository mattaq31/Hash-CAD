import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_undo_stack.dart';

import '../../helpers/design_state_test_factory.dart';

/// Helper: creates a layout with [slatCount] slats auto-assigned to plates.
PlateLayoutState _autoAssignedLayout(int slatCount) {
  final state = DesignStateTestFactory.createWithSlats(slatCount: slatCount);
  final layout = PlateLayoutState.fromSlats(state.slats, state.layerMap);
  layout.autoAssign(state.slats, state.layerMap);
  return layout;
}

void main() {
  group('PlateUndoStack', () {
    late PlateUndoStack stack;

    setUp(() {
      stack = PlateUndoStack();
    });

    test('saveState + undo returns the first state', () {
      final state1 = _autoAssignedLayout(3);
      final state2 = _autoAssignedLayout(5);

      stack.saveState(state1);
      stack.saveState(state2);

      final restored = stack.undo();
      expect(restored, isNotNull);
      expect(restored!.unassignedSlats.length, state1.unassignedSlats.length);
    });

    test('redo after undo restores the second state', () {
      final state1 = _autoAssignedLayout(3);
      final state2 = _autoAssignedLayout(5);

      stack.saveState(state1);
      stack.saveState(state2);

      stack.undo();
      final restored = stack.redo();
      expect(restored, isNotNull);
      expect(restored!.unassignedSlats.length, state2.unassignedSlats.length);
    });

    test('canUndo / canRedo flags are correct', () {
      expect(stack.canUndo, isFalse);
      expect(stack.canRedo, isFalse);

      final state1 = _autoAssignedLayout(3);
      stack.saveState(state1);
      expect(stack.canUndo, isFalse); // only one state, nothing to undo to
      expect(stack.canRedo, isFalse);

      final state2 = _autoAssignedLayout(5);
      stack.saveState(state2);
      expect(stack.canUndo, isTrue);
      expect(stack.canRedo, isFalse);

      stack.undo();
      expect(stack.canUndo, isFalse);
      expect(stack.canRedo, isTrue);
    });

    test('undo at beginning returns null', () {
      final state1 = _autoAssignedLayout(3);
      stack.saveState(state1);

      expect(stack.undo(), isNull);
    });

    test('redo at end returns null', () {
      final state1 = _autoAssignedLayout(3);
      stack.saveState(state1);

      expect(stack.redo(), isNull);
    });

    test('new save discards redo history', () {
      final state1 = _autoAssignedLayout(3);
      final state2 = _autoAssignedLayout(5);
      final state3 = _autoAssignedLayout(7);

      stack.saveState(state1);
      stack.saveState(state2);
      stack.undo(); // back to state1

      stack.saveState(state3); // should discard state2 from redo history
      expect(stack.canRedo, isFalse);
      expect(stack.redo(), isNull);
    });

    test('max history trimming', () {
      // Save maxHistory + 1 states — the oldest should be trimmed
      for (int i = 0; i <= PlateUndoStack.maxHistory; i++) {
        final state = _autoAssignedLayout(3);
        stack.saveState(state);
      }

      // Should still be able to undo
      expect(stack.canUndo, isTrue);
      // Should NOT be able to redo (we're at the latest state)
      expect(stack.canRedo, isFalse);

      // Count how many undos are possible — history is capped at maxHistory
      int undoCount = 0;
      while (stack.undo() != null) {
        undoCount++;
      }
      // 51 saves, capped to 50 entries, index at 49 → 49 undos
      expect(undoCount, PlateUndoStack.maxHistory - 1);
    });

    test('clear resets stack', () {
      final state1 = _autoAssignedLayout(3);
      final state2 = _autoAssignedLayout(5);

      stack.saveState(state1);
      stack.saveState(state2);
      expect(stack.canUndo, isTrue);

      stack.clear();
      expect(stack.canUndo, isFalse);
      expect(stack.canRedo, isFalse);
    });

    test('returned states are independent copies', () {
      final state1 = _autoAssignedLayout(3);
      stack.saveState(state1);

      final state2 = _autoAssignedLayout(5);
      stack.saveState(state2);

      final restored = stack.undo()!;
      // Modify the restored state
      restored.unassignedSlats.add('fake-slat');

      // Redo should return original state2, unaffected by the modification
      final redone = stack.redo()!;
      expect(redone.unassignedSlats, isNot(contains('fake-slat')));
    });
  });
}
