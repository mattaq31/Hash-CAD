/// Tests for moving cargo onto, off and between phantom slats (DesignStateCargoMixin.moveCargo), including
/// same-family destination collisions and phantoms on layers with flipped helix orientation.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/app_management/shared_app_state.dart';
import 'package:hash_cad/crisscross_core/cargo.dart';
import 'package:hash_cad/crisscross_core/common_utilities.dart';

import '../../helpers/design_state_test_factory.dart';

/// Grid coordinate of [position] (1-indexed) on a horizontal test slat whose origin sits at (0, [y]).
Offset coordAt(int position, double y) => Offset(position - 1.0, y);

/// Adds a phantom copy of [parentID] on [layer], running horizontally at row [y]; returns the new phantom's ID.
String addPhantom(DesignState state, String parentID, double y, {String layer = 'A'}) {
  final parent = state.slats[parentID]!;
  final before = state.slats.keys.toSet();
  state.addPhantomSlats(layer, {0: {for (var pos in parent.slatPositionToCoordinate.keys) pos: coordAt(pos, y)}}, {0: parent});
  return state.slats.keys.toSet().difference(before).single;
}

/// Cargo value on the H5 helix (the 'top' face of layers with default helix settings) of [slatID] at [position].
String? h5Cargo(DesignState state, String slatID, int position) => state.slats[slatID]!.h5Handles[position]?['value'];

/// Asserts occupiedCargoPoints exactly mirrors the non-assembly handles on every slat, keyed the same way the design
/// import rebuilds it (each slat's own layer and that layer's helix orientation).
void expectCargoOccupancyMatchesHandles(DesignState state) {
  final expected = <String, Map<Offset, String>>{};
  for (var slat in state.slats.values) {
    for (var helix in [2, 5]) {
      getHandleDict(slat, helix).forEach((position, handle) {
        if (handle['category'].toString().contains('ASSEMBLY')) return;
        final key = generateLayerSideKey(slat.layer, getOccupancySideFromHelix(state.layerMap, slat.layer, helix));
        expected.putIfAbsent(key, () => {})[slat.slatPositionToCoordinate[position]!] = handle['value'];
      });
    }
  }
  final actual = {for (var e in state.occupiedCargoPoints.entries) if (e.value.isNotEmpty) e.key: e.value};
  expect(actual, equals(expected));
}

void main() {
  final cargoX = Cargo(name: 'X', shortName: 'X', color: Colors.red);
  final cargoY = Cargo(name: 'Y', shortName: 'Y', color: Colors.blue);

  // Layer A layout: S (A-I1) at y=0, U (A-I2) at y=10, V (A-I3) at y=20, with phantoms of S added per test.
  late DesignState state;
  const s = 'A-I1', u = 'A-I2', v = 'A-I3';

  setUp(() {
    state = DesignStateTestFactory.createWithSlats(slatCount: 3, spacing: 10);
  });

  group('getOccupancySideFromHelix', () {
    test('maps helices to faces for default and flipped layers', () {
      expect(getOccupancySideFromHelix(state.layerMap, 'A', 5), 'top');
      expect(getOccupancySideFromHelix(state.layerMap, 'A', 2), 'bottom');
      state.layerMap['B']!['top_helix'] = 'H2';
      state.layerMap['B']!['bottom_helix'] = 'H5';
      expect(getOccupancySideFromHelix(state.layerMap, 'B', 5), 'bottom');
      expect(getOccupancySideFromHelix(state.layerMap, 'B', 2), 'top');
    });
  });

  group('moveCargo with phantom slats', () {
    test('real slat -> phantom propagates cargo to the phantom and its parent', () {
      final p = addPhantom(state, s, 5);
      state.attachCargo(cargoX, 'A', 'top', {1: coordAt(3, 10)});

      state.moveCargo({coordAt(3, 10): coordAt(3, 5)}, 'A', 'top');

      expect(h5Cargo(state, u, 3), isNull);
      expect(h5Cargo(state, p, 3), 'X');
      expect(h5Cargo(state, s, 3), 'X');
      expectCargoOccupancyMatchesHandles(state);
    });

    test('phantom -> phantom moves the handle across the whole phantom family', () {
      final p1 = addPhantom(state, s, 5);
      final p2 = addPhantom(state, s, 15);
      state.attachCargo(cargoX, 'A', 'top', {1: coordAt(4, 5)});
      for (var id in [s, p1, p2]) {
        expect(h5Cargo(state, id, 4), 'X');
      }

      state.moveCargo({coordAt(4, 5): coordAt(7, 15)}, 'A', 'top');

      for (var id in [s, p1, p2]) {
        expect(h5Cargo(state, id, 4), isNull, reason: '$id should have lost the old handle');
        expect(h5Cargo(state, id, 7), 'X', reason: '$id should carry the moved handle');
      }
      expectCargoOccupancyMatchesHandles(state);
    });

    test('phantom -> unrelated real slat clears the whole family', () {
      final p = addPhantom(state, s, 5);
      state.attachCargo(cargoX, 'A', 'top', {1: coordAt(4, 5)});

      state.moveCargo({coordAt(4, 5): coordAt(4, 20)}, 'A', 'top');

      expect(h5Cargo(state, s, 4), isNull);
      expect(h5Cargo(state, p, 4), isNull);
      expect(h5Cargo(state, v, 4), 'X');
      expectCargoOccupancyMatchesHandles(state);
    });

    test('moving both copies of one handle together is not treated as a collision', () {
      final p = addPhantom(state, s, 5);
      state.attachCargo(cargoX, 'A', 'top', {1: coordAt(5, 0)});

      state.moveCargo({coordAt(5, 0): coordAt(6, 0), coordAt(5, 5): coordAt(6, 5)}, 'A', 'top');

      for (var id in [s, p]) {
        expect(h5Cargo(state, id, 5), isNull);
        expect(h5Cargo(state, id, 6), 'X');
      }
      expectCargoOccupancyMatchesHandles(state);
    });

    test('two different cargos landing on the same family handle: first wins, second stays put', () {
      final p = addPhantom(state, s, 5);
      state.attachCargo(cargoX, 'A', 'top', {1: coordAt(3, 10)});
      state.attachCargo(cargoY, 'A', 'top', {1: coordAt(3, 20)});

      // X targets S pos 6 and Y targets P pos 6 - the same shared handle
      state.moveCargo({coordAt(3, 10): coordAt(6, 0), coordAt(3, 20): coordAt(6, 5)}, 'A', 'top');

      expect(h5Cargo(state, s, 6), 'X');
      expect(h5Cargo(state, p, 6), 'X');
      expect(h5Cargo(state, u, 3), isNull);
      expect(h5Cargo(state, v, 3), 'Y', reason: 'the colliding cargo must not be deleted');
      expectCargoOccupancyMatchesHandles(state);
    });

    test('chained moves through a phantom family (A->B while B->C) keep both cargos', () {
      final p = addPhantom(state, s, 5);
      state.attachCargo(cargoX, 'A', 'top', {1: coordAt(2, 0)});
      state.attachCargo(cargoY, 'A', 'top', {1: coordAt(3, 0)});

      // X: S pos 2 -> P pos 3 (where Y currently is), Y: P pos 3 -> S pos 4
      state.moveCargo({coordAt(2, 0): coordAt(3, 5), coordAt(3, 5): coordAt(4, 0)}, 'A', 'top');

      for (var id in [s, p]) {
        expect(h5Cargo(state, id, 2), isNull);
        expect(h5Cargo(state, id, 3), 'X');
        expect(h5Cargo(state, id, 4), 'Y');
      }
      expectCargoOccupancyMatchesHandles(state);
    });
  });

  group('phantoms on a layer with flipped helices', () {
    late String p;

    setUp(() {
      // on layer B the H5 helix faces down, so S's top-face (H5) cargo shows on the phantom's bottom face
      state.layerMap['B']!['top_helix'] = 'H2';
      state.layerMap['B']!['bottom_helix'] = 'H5';
      p = addPhantom(state, s, 40, layer: 'B');
      state.attachCargo(cargoX, 'A', 'top', {1: coordAt(3, 0)});
    });

    test('attachCargo records the phantom copy under its own layer face', () {
      expect(state.occupiedCargoPoints['B-bottom']?[coordAt(3, 40)], 'X');
      expect(state.occupiedCargoPoints['B-top']?[coordAt(3, 40)], isNull);
      expectCargoOccupancyMatchesHandles(state);
    });

    test('moveCargo updates the cross-layer phantom copy on the correct face', () {
      state.moveCargo({coordAt(3, 0): coordAt(8, 0)}, 'A', 'top');

      expect(h5Cargo(state, p, 8), 'X');
      expect(state.occupiedCargoPoints['B-bottom']?[coordAt(3, 40)], isNull);
      expect(state.occupiedCargoPoints['B-bottom']?[coordAt(8, 40)], 'X');
      expectCargoOccupancyMatchesHandles(state);
    });

    test('removeCargo clears the cross-layer phantom copy', () {
      state.removeCargo(s, 'top', coordAt(3, 0));

      expect(h5Cargo(state, p, 3), isNull);
      expectCargoOccupancyMatchesHandles(state);
    });
  });
}
