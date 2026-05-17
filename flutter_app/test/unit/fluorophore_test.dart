import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/app_management/shared_app_state.dart';
import 'package:hash_cad/crisscross_core/fluorophore.dart';
import 'package:hash_cad/echo_and_experimental_helpers/echo_barcode_painter.dart';
import 'package:hash_cad/echo_and_experimental_helpers/echo_category_colors.dart';

import '../helpers/design_state_test_factory.dart';

void main() {
  group('Fluorophore library CRUD', () {
    late DesignState state;

    setUp(() {
      state = DesignStateTestFactory.createWithSlats(slatCount: 2);
    });

    test('addFluorophore adds to palette', () {
      state.addFluorophore(Fluorophore(name: 'Cy3', shape: FluorophoreShape.diamond));
      expect(state.fluorophorePalette.containsKey('Cy3'), isTrue);
      expect(state.fluorophorePalette['Cy3']!.shape, FluorophoreShape.diamond);
    });

    test('renameFluorophore updates palette key and tagged handles', () {
      state.addFluorophore(Fluorophore(name: 'Cy3', shape: FluorophoreShape.dot));
      // Place an assembly handle and tag it
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(1, 2, '1', 'ASSEMBLY_HANDLE');
      state.assignFluorophoreToHandle((slat.id, 1, 2), 'Cy3');
      expect(slat.h2Handles[1]!['fluorophore'], 'Cy3');

      state.renameFluorophore('Cy3', 'Cy3-mod');
      expect(state.fluorophorePalette.containsKey('Cy3'), isFalse);
      expect(state.fluorophorePalette.containsKey('Cy3-mod'), isTrue);
      expect(slat.h2Handles[1]!['fluorophore'], 'Cy3-mod');
    });

    test('deleteFluorophore removes from palette and clears tagged handles', () {
      state.addFluorophore(Fluorophore(name: 'Cy5', shape: FluorophoreShape.star));
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(1, 2, '1', 'ASSEMBLY_HANDLE');
      state.assignFluorophoreToHandle((slat.id, 1, 2), 'Cy5');
      expect(slat.h2Handles[1]!['fluorophore'], 'Cy5');

      state.deleteFluorophore('Cy5');
      expect(state.fluorophorePalette.containsKey('Cy5'), isFalse);
      expect(slat.h2Handles[1]!.containsKey('fluorophore'), isFalse);
    });

    test('updateFluorophoreShape changes shape', () {
      state.addFluorophore(Fluorophore(name: 'Cy3', shape: FluorophoreShape.dot));
      state.updateFluorophoreShape('Cy3', FluorophoreShape.square);
      expect(state.fluorophorePalette['Cy3']!.shape, FluorophoreShape.square);
    });

    test('duplicate name rejected on rename', () {
      state.addFluorophore(Fluorophore(name: 'Cy3', shape: FluorophoreShape.dot));
      state.addFluorophore(Fluorophore(name: 'Cy5', shape: FluorophoreShape.star));
      state.renameFluorophore('Cy3', 'Cy5');
      // Should not rename since target already exists
      expect(state.fluorophorePalette.containsKey('Cy3'), isTrue);
      expect(state.fluorophorePalette.containsKey('Cy5'), isTrue);
    });
  });

  group('Fluorophore handle assignment', () {
    late DesignState state;

    setUp(() {
      state = DesignStateTestFactory.createWithSlats(slatCount: 2);
      state.addFluorophore(Fluorophore(name: 'Cy3', shape: FluorophoreShape.diamond));
    });

    test('assignFluorophoreToHandle sets field on handle', () {
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(5, 2, '3', 'ASSEMBLY_HANDLE');
      state.assignFluorophoreToHandle((slat.id, 5, 2), 'Cy3');
      expect(slat.h2Handles[5]!['fluorophore'], 'Cy3');
    });

    test('assignment rejected for blocked handles', () {
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(5, 2, '0', 'ASSEMBLY_HANDLE');
      state.assignFluorophoreToHandle((slat.id, 5, 2), 'Cy3');
      expect(slat.h2Handles[5]!.containsKey('fluorophore'), isFalse);
    });

    test('assignment rejected for non-assembly handles', () {
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(5, 2, 'cargo1', 'CARGO');
      state.assignFluorophoreToHandle((slat.id, 5, 2), 'Cy3');
      expect(slat.h2Handles[5]!.containsKey('fluorophore'), isFalse);
    });

    test('clearFluorophoreFromHandle removes field', () {
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(5, 2, '3', 'ASSEMBLY_HANDLE');
      state.assignFluorophoreToHandle((slat.id, 5, 2), 'Cy3');
      state.clearFluorophoreFromHandle((slat.id, 5, 2));
      expect(slat.h2Handles[5]!.containsKey('fluorophore'), isFalse);
    });

    test('assignFluorophoreToHandle invalidates existing plate assignment', () {
      final slat = state.slats.values.first;
      slat.setHandle(5, 2, 'ACGT', 'A1', 'plate1', '3', 'ASSEMBLY_HANDLE', 100);

      state.assignFluorophoreToHandle((slat.id, 5, 2), 'Cy3');

      expect(slat.checkPlaceholder(5, 2), isTrue);
      expect(slat.h2Handles[5]!['value'], '3');
      expect(slat.h2Handles[5]!['category'], 'ASSEMBLY_HANDLE');
      expect(slat.h2Handles[5]!['fluorophore'], 'Cy3');
      expect(slat.h2Handles[5]!.containsKey('sequence'), isFalse);
      expect(slat.h2Handles[5]!.containsKey('plate'), isFalse);
      expect(slat.h2Handles[5]!.containsKey('well'), isFalse);
    });

    test('clearFluorophoreFromHandle invalidates existing plate assignment', () {
      final slat = state.slats.values.first;
      slat.setHandle(5, 2, 'ACGT', 'A1', 'plate1', '3', 'ASSEMBLY_HANDLE', 100);
      slat.h2Handles[5]!['fluorophore'] = 'Cy3';

      state.clearFluorophoreFromHandle((slat.id, 5, 2));

      expect(slat.checkPlaceholder(5, 2), isTrue);
      expect(slat.h2Handles[5]!['value'], '3');
      expect(slat.h2Handles[5]!['category'], 'ASSEMBLY_HANDLE');
      expect(slat.h2Handles[5]!.containsKey('fluorophore'), isFalse);
      expect(slat.h2Handles[5]!.containsKey('sequence'), isFalse);
      expect(slat.h2Handles[5]!.containsKey('plate'), isFalse);
      expect(slat.h2Handles[5]!.containsKey('well'), isFalse);
    });

    test('massAssignFluorophore invalidates existing plate assignments', () {
      final slat = state.slats.values.first;
      slat.setHandle(5, 2, 'ACGT', 'A1', 'plate1', '3', 'ASSEMBLY_HANDLE', 100);

      state.massAssignFluorophore({slat.id: {(2, 5)}}, 'Cy3');

      expect(slat.checkPlaceholder(5, 2), isTrue);
      expect(slat.h2Handles[5]!['fluorophore'], 'Cy3');
      expect(slat.h2Handles[5]!.containsKey('sequence'), isFalse);
      expect(slat.h2Handles[5]!.containsKey('plate'), isFalse);
    });

    test('assignment mirrors to phantom copies', () {
      final baseSlat = state.slats.values.first;
      baseSlat.setPlaceholderHandle(5, 5, '3', 'ASSEMBLY_HANDLE');

      final phantomCoordinates = <int, Map<int, Offset>>{
        1: {
          for (var entry in baseSlat.slatPositionToCoordinate.entries) entry.key: entry.value + const Offset(0, 40),
        }
      };
      state.addPhantomSlats(baseSlat.layer, phantomCoordinates, {1: baseSlat});
      final phantomSlat = state.slats.values.firstWhere((slat) => slat.phantomParent == baseSlat.id);

      state.assignFluorophoreToHandle((baseSlat.id, 5, 5), 'Cy3');

      expect(baseSlat.h5Handles[5]!['fluorophore'], 'Cy3');
      expect(phantomSlat.h5Handles[5]!['fluorophore'], 'Cy3');
    });
  });

  group('Compatibility override', () {
    late DesignState state;

    setUp(() {
      state = DesignStateTestFactory.createWithSlats(slatCount: 1);
      state.addFluorophore(Fluorophore(name: 'Cy3', shape: FluorophoreShape.diamond));
    });

    test('getEffectiveCompatibility returns fluorophore name when tagged', () {
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(3, 2, '1', 'ASSEMBLY_HANDLE');
      slat.h2Handles[3]!['fluorophore'] = 'Cy3';

      final compat = state.getEffectiveCompatibility(slat.slatType, 3, 2, slat.id);
      expect(compat, 'Cy3');
    });

    test('getEffectiveCompatibility falls back to slat rule when no fluorophore', () {
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(3, 2, '1', 'ASSEMBLY_HANDLE');

      final compat = state.getEffectiveCompatibility(slat.slatType, 3, 2, slat.id);
      // Tube slat at position 3 should have no special compatibility
      expect(compat, isNull);
    });
  });

  group('Fluorophore preservation through handle operations', () {
    late DesignState state;

    setUp(() {
      state = DesignStateTestFactory.createWithSlats(slatCount: 2);
      state.addFluorophore(Fluorophore(name: 'Cy3', shape: FluorophoreShape.diamond));
    });

    test('setHandle preserves fluorophore field', () {
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(5, 2, '3', 'ASSEMBLY_HANDLE');
      slat.h2Handles[5]!['fluorophore'] = 'Cy3';

      // Simulate plate assignment updating the handle
      slat.setHandle(5, 2, 'ACGT', 'A1', 'plate1', '3', 'ASSEMBLY_HANDLE', 100);
      expect(slat.h2Handles[5]!['fluorophore'], 'Cy3');
      expect(slat.h2Handles[5]!['sequence'], 'ACGT');
    });

    test('updatePlaceholderHandle preserves fluorophore field', () {
      final slat = state.slats.values.first;
      slat.setPlaceholderHandle(5, 2, '3', 'ASSEMBLY_HANDLE');
      slat.h2Handles[5]!['fluorophore'] = 'Cy3';

      slat.updatePlaceholderHandle(5, 2, 'ACGT', 'A1', 'plate1', '3', 'ASSEMBLY_HANDLE', 100);
      expect(slat.h2Handles[5]!['fluorophore'], 'Cy3');
    });

    test('moveAssemblyHandle transfers source fluorophore to destination', () {
      final slats = state.slats.values.toList()..sort((a, b) => a.numericID.compareTo(b.numericID));
      final donor = slats[0];
      final receiver = slats[1];
      state.addFluorophore(Fluorophore(name: 'Cy5', shape: FluorophoreShape.star));

      donor.setPlaceholderHandle(5, 5, '1', 'ASSEMBLY_HANDLE');
      receiver.setPlaceholderHandle(5, 5, '2', 'ASSEMBLY_HANDLE');
      state.assignFluorophoreToHandle((donor.id, 5, 5), 'Cy3');
      state.assignFluorophoreToHandle((receiver.id, 5, 5), 'Cy5');

      state.moveAssemblyHandle({donor.slatPositionToCoordinate[5]!: receiver.slatPositionToCoordinate[5]!}, 'A', 'top');

      expect(donor.h5Handles.containsKey(5), isFalse);
      expect(receiver.h5Handles[5]!['value'], '1');
      expect(receiver.h5Handles[5]!['fluorophore'], 'Cy3');
    });

    test('moveAssemblyHandle clears stale destination fluorophore when source has none', () {
      final slats = state.slats.values.toList()..sort((a, b) => a.numericID.compareTo(b.numericID));
      final donor = slats[0];
      final receiver = slats[1];
      state.addFluorophore(Fluorophore(name: 'Cy5', shape: FluorophoreShape.star));

      donor.setPlaceholderHandle(5, 5, '1', 'ASSEMBLY_HANDLE');
      receiver.setPlaceholderHandle(5, 5, '2', 'ASSEMBLY_HANDLE');
      state.assignFluorophoreToHandle((receiver.id, 5, 5), 'Cy5');

      state.moveAssemblyHandle({donor.slatPositionToCoordinate[5]!: receiver.slatPositionToCoordinate[5]!}, 'A', 'top');

      expect(receiver.h5Handles[5]!['value'], '1');
      expect(receiver.h5Handles[5]!.containsKey('fluorophore'), isFalse);
    });
  });

  group('Fluorophore model', () {
    test('shape serialization roundtrip', () {
      for (var shape in FluorophoreShape.values) {
        final str = fluorophoreShapeToString(shape);
        final parsed = fluorophoreShapeFromString(str);
        expect(parsed, shape);
      }
    });

    test('fluorophoreShapeFromString defaults to dot for unknown value', () {
      expect(fluorophoreShapeFromString('unknown'), FluorophoreShape.dot);
    });

    test('copyWith creates modified copy', () {
      final f = Fluorophore(name: 'Cy3', shape: FluorophoreShape.dot);
      final f2 = f.copyWith(shape: FluorophoreShape.star);
      expect(f2.name, 'Cy3');
      expect(f2.shape, FluorophoreShape.star);
    });
  });

  group('clearAll resets fluorophore state', () {
    test('fluorophorePalette is empty after reset', () {
      final state = DesignStateTestFactory.createWithSlats(slatCount: 1);
      state.addFluorophore(Fluorophore(name: 'Cy3', shape: FluorophoreShape.dot));
      expect(state.fluorophorePalette.isNotEmpty, isTrue);

      state.resetDefaults();
      expect(state.fluorophorePalette.isEmpty, isTrue);
    });
  });

  group('Echo barcode painter fluorophore behavior', () {
    test('effectiveCategoryForHandle prioritizes fluorophore marker', () {
      final handle = <String, dynamic>{'value': '3', 'category': 'ASSEMBLY_HANDLE', 'fluorophore': 'Cy3'};
      expect(HandleBarcodePainter.effectiveCategoryForHandle(handle), 'FLUOROPHORE');
    });

    test('effectiveEchoHandleCategory is shared by PDF export and painter logic', () {
      final handle = <String, dynamic>{'value': '3', 'category': 'ASSEMBLY_HANDLE', 'fluorophore': 'Cy3'};
      expect(effectiveEchoHandleCategory(handle), 'FLUOROPHORE');
      expect(HandleBarcodePainter.effectiveCategoryForHandle(handle), effectiveEchoHandleCategory(handle));
    });

    test('shouldRepaint detects fluorophore-only mutation on shared handle maps', () {
      final h2Handles = <int, Map<String, dynamic>>{
        1: {'value': '3', 'category': 'ASSEMBLY_HANDLE'}
      };
      final empty = <int, Map<String, dynamic>>{};

      final before = HandleBarcodePainter(h2Handles: h2Handles, h5Handles: empty, maxLength: 1);
      h2Handles[1]!['fluorophore'] = 'Cy3';
      final after = HandleBarcodePainter(h2Handles: h2Handles, h5Handles: empty, maxLength: 1);

      expect(after.shouldRepaint(before), isTrue);
    });
  });
}
