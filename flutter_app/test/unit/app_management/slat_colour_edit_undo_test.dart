/// Tests that editing an existing slat colour from the colour swatches (editSlatColorSearch) can be undone as one step.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/app_management/shared_app_state.dart';

import '../../helpers/design_state_test_factory.dart';

void main() {
  const s = 'A-I1';
  const red = Color(0xFFFF0000);
  const blue = Color(0xFF0000FF);
  late DesignState state;

  setUp(() {
    state = DesignStateTestFactory.createWithSlats(slatCount: 2, spacing: 10);
    state.selectedLayerKey = 'A';
    state.clearSelection();
    state.selectSlat(s);
    state.assignColorToSelectedSlats(red);
  });

  test('a finished colour edit is undone in one step', () {
    // The picker reports every intermediate colour while it is dragged.
    state.editSlatColorSearch('A', 0, const Color(0xFF800080));
    state.editSlatColorSearch('A', 0, blue);
    state.finishSlatColorEdit();
    expect(state.slats[s]!.uniqueColor, blue);

    state.undo2DAction();
    expect(state.slats[s]!.uniqueColor, red);
    expect(state.uniqueSlatColorsByLayer['A'], [red]);

    state.undo2DAction(redo: true);
    expect(state.slats[s]!.uniqueColor, blue);
    expect(state.uniqueSlatColorsByLayer['A'], [blue]);
  });

  test('closing the picker without an edit adds no undo step', () {
    state.finishSlatColorEdit();
    state.undo2DAction();
    // The only step left to undo is the original colour assignment.
    expect(state.slats[s]!.uniqueColor, isNull);
  });
}
