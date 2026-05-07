// Tests for master mix Excel export warnings: overflow, variable volume, and manual handle underestimate.
import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/slats.dart';
import 'package:hash_cad/echo_and_experimental_helpers/master_mix_config.dart';
import 'package:hash_cad/echo_and_experimental_helpers/master_mix_export.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';
import '../../helpers/test_helpers.dart';

void main() {
  group('generateMasterMixExcel warnings', () {
    test('all three warnings stack: overflow, variable volume, and manual placeholder', () {
      // Both slats share the same WellConfig (ratio=15, volume=500, scaffoldConc=50)
      // so they land in the same group. materialPerHandle = 50*15*500/1000 = 375 pmol.
      //
      // Slat 1: 32 h2 handles at concentration=25
      //   Per handle: ceil(375/25*1000 / 25)*25 = ceil(15000/25)*25 = 15000 nL
      //   Total: 32 × 15000 = 480000 nL → exceeds 25000 nL threshold.
      //   Also has a manual placeholder on h5 position 1 (no plate/concentration).
      final slat1 = Slat(1, 'slat-1', 'layerA', createTestSlatCoordinates(const Offset(0, 0)));
      for (int i = 1; i <= 32; i++) {
        slat1.setHandle(i, 2, 'ATCG', 'A$i', 'Plate_1', 'val', 'ASSEMBLY', 25);
      }
      slat1.setPlaceholderHandle(1, 5, 'manual_val', 'ASSEMBLY');

      // Slat 2: 32 h2 handles at concentration=200
      //   Per handle: ceil(375/200*1000 / 25)*25 = ceil(1875/25)*25 = 1875 nL
      //   Total: 32 × 1875 = 60000 nL → also exceeds, but different total from slat 1
      //   (480000 vs 60000 → variable volume warning triggers within group).
      final slat2 = Slat(2, 'slat-2', 'layerA', createTestSlatCoordinates(const Offset(0, 1)));
      for (int i = 1; i <= 32; i++) {
        slat2.setHandle(i, 2, 'ATCG', 'B$i', 'Plate_1', 'val', 'ASSEMBLY', 200);
      }

      final slats = {'slat-1': slat1, 'slat-2': slat2};
      final layerMap = {
        'layerA': {'order': 0, 'color': null},
      };

      // Same WellConfig for both → same group (variable volume comes from different concentrations).
      final plateAssignments = <int, Map<String, String?>>{
        0: {'A1': 'slat-1', 'A2': 'slat-2'},
      };
      final wellConfigs = <int, Map<String, WellConfig>>{
        0: {
          'A1': const WellConfig(ratio: 15, volume: 500, scaffoldConc: 50),
          'A2': const WellConfig(ratio: 15, volume: 500, scaffoldConc: 50),
        },
      };
      final plateNames = {0: 'TestPlate'};

      // Mark h5 position 1 on slat-1 as manual
      final manualHandles = <String, Set<(int, int)>>{
        'slat-1': {(5, 1)},
      };

      final result = generateMasterMixExcel(
        plateAssignments: plateAssignments,
        wellConfigs: wellConfigs,
        plateNames: plateNames,
        slats: slats,
        layerMap: layerMap,
        mixConfig: const MasterMixConfig(),
        normalizeVolumes: false,
        maxWellVolumeNl: 25000,
        manualHandles: manualHandles,
      );

      // Dialog warnings: manual placeholder + overflow (variable volume is sheet-only)
      expect(result.warnings.length, 2);

      // Manual placeholder warning
      expect(
        result.warnings.any((w) => w.contains('manual') && w.contains('underestimated')),
        isTrue,
        reason: 'Should warn about manual handles without plate assignments',
      );

      // Overflow warning (both slats exceed)
      expect(
        result.warnings.any((w) => w.contains('exceed')),
        isTrue,
        reason: 'Should warn about slats exceeding max well volume',
      );

      // The variable volume warning is rendered in-sheet (not in result.warnings).
      expect(result.bytes.isNotEmpty, isTrue);
    });

    test('no warnings when all handles have plates and volumes are uniform', () {
      final slat1 = Slat(1, 'slat-1', 'layerA', createTestSlatCoordinates(const Offset(0, 0)));
      for (int i = 1; i <= 4; i++) {
        slat1.setHandle(i, 2, 'ATCG', 'A$i', 'Plate_1', 'val', 'ASSEMBLY', 200);
      }

      final slats = {'slat-1': slat1};
      final layerMap = {
        'layerA': {'order': 0, 'color': null},
      };
      final plateAssignments = <int, Map<String, String?>>{
        0: {'A1': 'slat-1'},
      };
      final wellConfigs = <int, Map<String, WellConfig>>{
        0: {'A1': const WellConfig()},
      };

      final result = generateMasterMixExcel(
        plateAssignments: plateAssignments,
        wellConfigs: wellConfigs,
        plateNames: {0: 'P1'},
        slats: slats,
        layerMap: layerMap,
        mixConfig: const MasterMixConfig(),
        normalizeVolumes: false,
        manualHandles: null,
      );

      expect(result.warnings, isEmpty);
    });

    test('manual placeholder warning only when manual handle lacks plate', () {
      final slat1 = Slat(1, 'slat-1', 'layerA', createTestSlatCoordinates(const Offset(0, 0)));
      slat1.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      // Placeholder at h5 pos 1 — manual
      slat1.setPlaceholderHandle(1, 5, 'manual_val', 'ASSEMBLY');
      // Full handle at h5 pos 2 — also manual but HAS plate
      slat1.setHandle(2, 5, 'ATCG', 'B2', 'Plate_2', 'val', 'ASSEMBLY', 200);

      final slats = {'slat-1': slat1};
      final layerMap = {
        'layerA': {'order': 0, 'color': null},
      };
      final plateAssignments = <int, Map<String, String?>>{
        0: {'A1': 'slat-1'},
      };
      final wellConfigs = <int, Map<String, WellConfig>>{
        0: {'A1': const WellConfig()},
      };
      // Both h5 positions marked manual, but only pos 1 is a placeholder
      final manualHandles = <String, Set<(int, int)>>{
        'slat-1': {(5, 1), (5, 2)},
      };

      final result = generateMasterMixExcel(
        plateAssignments: plateAssignments,
        wellConfigs: wellConfigs,
        plateNames: {0: 'P1'},
        slats: slats,
        layerMap: layerMap,
        mixConfig: const MasterMixConfig(),
        normalizeVolumes: false,
        manualHandles: manualHandles,
      );

      // Only 1 handle is a placeholder without plate
      expect(result.warnings.length, 1);
      expect(result.warnings.first, contains('1 handle(s) across 1 slat(s)'));
      expect(result.warnings.first, contains('underestimated'));
    });
  });
}
