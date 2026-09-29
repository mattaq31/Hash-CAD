/// Tests for phantom-family slat operations: selecting a slat with all its phantoms (selectPhantomFamily) and
/// recolouring from either the parent or a phantom (assignColorToSelectedSlats).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/app_management/shared_app_state.dart';

import '../../helpers/design_state_test_factory.dart';

/// Adds a phantom copy of [parentID] on [layer], running horizontally at row [y]; returns the new phantom's ID.
String addPhantom(DesignState state, String parentID, double y, {String layer = 'A'}) {
  final parent = state.slats[parentID]!;
  final before = state.slats.keys.toSet();
  state.addPhantomSlats(layer, {0: {for (var pos in parent.slatPositionToCoordinate.keys) pos: Offset(pos - 1.0, y)}}, {0: parent});
  return state.slats.keys.toSet().difference(before).single;
}

void main() {
  // Layer A: S (A-I1) at y=0 and an unrelated slat U (A-I2) at y=10; phantoms of S at y=5 and y=15 (layer A) and
  // y=40 (layer B).
  late DesignState state;
  late String p1, p2, pB;
  const s = 'A-I1', u = 'A-I2';

  setUp(() {
    state = DesignStateTestFactory.createWithSlats(slatCount: 2, spacing: 10);
    p1 = addPhantom(state, s, 5);
    p2 = addPhantom(state, s, 15);
    pB = addPhantom(state, s, 40, layer: 'B');
    state.selectedLayerKey = 'A';
    state.clearSelection();
  });

  group('selectPhantomFamily', () {
    test('from the parent selects parent and same-layer phantoms only', () {
      state.selectPhantomFamily(s);
      expect(state.selectedSlats.toSet(), {s, p1, p2});
    });

    test('from a phantom selects the same family', () {
      state.selectPhantomFamily(p2);
      expect(state.selectedSlats.toSet(), {s, p1, p2});
    });

    test('replaces the selection by default and extends it when adding', () {
      state.selectSlat(u);
      state.selectPhantomFamily(p1);
      expect(state.selectedSlats.toSet(), {s, p1, p2});

      state.clearSelection();
      state.selectSlat(u);
      state.selectPhantomFamily(p1, addToSelection: true);
      expect(state.selectedSlats.toSet(), {u, s, p1, p2});
    });

    test('a slat without phantoms selects just itself', () {
      state.selectPhantomFamily(u);
      expect(state.selectedSlats, [u]);
    });

    test('on another layer only that layer\'s members are selected', () {
      state.selectedLayerKey = 'B';
      state.selectPhantomFamily(pB);
      expect(state.selectedSlats, [pB]);
    });
  });

  group('assignColorToSelectedSlats with phantoms', () {
    test('recolouring a phantom recolours its parent and all siblings (including other layers)', () {
      state.selectSlat(p1);
      state.assignColorToSelectedSlats(Colors.green);

      for (var id in [s, p1, p2, pB]) {
        expect(state.slats[id]!.uniqueColor, Colors.green, reason: '$id should share the family colour');
      }
      expect(state.slats[u]!.uniqueColor, isNot(Colors.green));
    });

    test('recolouring the parent still recolours all phantoms', () {
      state.selectSlat(s);
      state.assignColorToSelectedSlats(Colors.purple);

      for (var id in [s, p1, p2, pB]) {
        expect(state.slats[id]!.uniqueColor, Colors.purple);
      }
    });

    test('the colour is registered on every layer the family touches', () {
      state.selectSlat(p1);
      state.assignColorToSelectedSlats(Colors.orange);

      expect(state.uniqueSlatColorsByLayer['A'], contains(Colors.orange));
      expect(state.uniqueSlatColorsByLayer['B'], contains(Colors.orange));
    });
  });
}
