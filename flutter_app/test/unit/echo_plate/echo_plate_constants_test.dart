import 'package:flutter_test/flutter_test.dart';
import 'package:hash_cad/crisscross_core/slats.dart';
import 'package:hash_cad/echo_and_experimental_helpers/echo_plate_constants.dart';
import 'package:hash_cad/echo_and_experimental_helpers/plate_layout_state.dart';
import '../../helpers/test_helpers.dart';

void main() {
  group('echoRoundedVolumeNl', () {
    test('rounds up to nearest 25 nL', () {
      // materialPerHandle=37.5, conc=200 → 37.5/200*1000 = 187.5 → ceil(187.5/25)*25 = 200
      expect(echoRoundedVolumeNl(37.5, 200), 200);
    });

    test('exact multiple of 25 stays unchanged', () {
      // materialPerHandle=50, conc=200 → 50/200*1000 = 250 → exact multiple
      expect(echoRoundedVolumeNl(50, 200), 250);
    });

    test('very small volume rounds up to 25', () {
      // materialPerHandle=1, conc=200 → 1/200*1000 = 5 → ceil(5/25)*25 = 25
      expect(echoRoundedVolumeNl(1, 200), 25);
    });

    test('high concentration yields small volume', () {
      // materialPerHandle=37.5, conc=1000 → 37.5/1000*1000 = 37.5 → ceil(37.5/25)*25 = 50
      expect(echoRoundedVolumeNl(37.5, 1000), 50);
    });
  });

  group('slatTotalVolumeNl', () {
    test('sums volumes across h2 and h5 handles', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat.setHandle(2, 2, 'ATCG', 'A2', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat.setHandle(1, 5, 'ATCG', 'B1', 'Plate_2', 'val', 'ASSEMBLY', 200);

      const config = WellConfig(); // materialPerHandle = 37.5
      final total = slatTotalVolumeNl(slat, config);
      // Each handle: echoRoundedVolumeNl(37.5, 200) = 200 nL, 3 handles = 600
      expect(total, 600);
    });

    test('skips handles with null concentration', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      // Add a placeholder (no concentration key)
      slat.setPlaceholderHandle(2, 2, 'val', 'ASSEMBLY');

      const config = WellConfig();
      final total = slatTotalVolumeNl(slat, config);
      // Only handle at pos 1 counts: 200 nL
      expect(total, 200);
    });

    test('skips handles with zero concentration', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);
      slat.h2Handles[2] = {'sequence': 'ATCG', 'well': 'A2', 'plate': 'P', 'value': 'v', 'category': 'ASSEMBLY', 'concentration': 0};

      const config = WellConfig();
      expect(slatTotalVolumeNl(slat, config), 200);
    });

    test('returns 0 for slat with no handles', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      const config = WellConfig();
      expect(slatTotalVolumeNl(slat, config), 0);
    });

    test('uses custom WellConfig materialPerHandle correctly', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      // ratio=30, volume=50, scaffoldConc=50 → materialPerHandle = 50*30*50/1000 = 75
      final config = WellConfig(ratio: 30, volume: 50, scaffoldConc: 50);
      // echoRoundedVolumeNl(75, 200) = ceil(375/25)*25 = 375
      expect(slatTotalVolumeNl(slat, config), 375);
    });
  });

  group('wellWarningState', () {
    test('incomplete=true when placeholders exist', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setPlaceholderHandle(1, 2, 'val', 'ASSEMBLY');

      final result = wellWarningState(slat, const WellConfig());
      expect(result.incomplete, isTrue);
    });

    test('exceedsVolume=true when total exceeds echoMaxWellVolumeNl', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      // 32 h2 handles at conc=25 → materialPerHandle=37.5 → 37.5/25*1000 = 1500 nL each → 32*1500 = 48000
      for (int i = 1; i <= 32; i++) {
        slat.setHandle(i, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 25);
      }

      final result = wellWarningState(slat, const WellConfig());
      expect(result.incomplete, isFalse);
      expect(result.exceedsVolume, isTrue);
    });

    test('both false for normal slat under limit', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = wellWarningState(slat, const WellConfig());
      expect(result.incomplete, isFalse);
      expect(result.exceedsVolume, isFalse);
    });

    test('both false when config is null', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setHandle(1, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 200);

      final result = wellWarningState(slat, null);
      expect(result.incomplete, isFalse);
      expect(result.exceedsVolume, isFalse);
    });

    test('incomplete takes precedence — exceedsVolume not checked when incomplete', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      // Add placeholder AND many high-volume handles
      slat.setPlaceholderHandle(1, 2, 'val', 'ASSEMBLY');
      for (int i = 2; i <= 32; i++) {
        slat.setHandle(i, 2, 'ATCG', 'A1', 'Plate_1', 'val', 'ASSEMBLY', 25);
      }

      final result = wellWarningState(slat, const WellConfig());
      expect(result.incomplete, isTrue);
      expect(result.exceedsVolume, isFalse);
    });

    test('boundary: exactly echoMaxWellVolumeNl does NOT trigger', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      // We need exactly 25000 nL total. echoRoundedVolumeNl(37.5, conc) per handle.
      // 25 handles at 200 conc → 25 * 200 = 5000. Not enough.
      // We need N * volPerHandle = 25000. With conc=200, volPerHandle=200. So 125 handles? Max is 32+32=64.
      // With conc=37.5, volPerHandle = ceil(37.5/37.5*1000/25)*25 = ceil(1000/25)*25 = 1000. 25 handles = 25000.
      // Use a custom config to make materialPerHandle=37.5 with conc=37.5 → 1000 nL/handle
      // 25 handles * 1000 = 25000 exactly
      for (int i = 1; i <= 25; i++) {
        slat.h2Handles[i] = {'sequence': 'ATCG', 'well': 'A1', 'plate': 'P', 'value': 'v', 'category': 'ASSEMBLY', 'concentration': 37.5};
      }

      const config = WellConfig(); // materialPerHandle = 37.5
      // Verify our assumption
      expect(slatTotalVolumeNl(slat, config), echoMaxWellVolumeNl);

      final result = wellWarningState(slat, config);
      expect(result.exceedsVolume, isFalse);
    });
  });

  group('Slat.setPlaceholderHandle dedup', () {
    test('calling twice with same pos/side → placeholderList.length == 1', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setPlaceholderHandle(1, 2, 'val1', 'ASSEMBLY');
      slat.setPlaceholderHandle(1, 2, 'val2', 'ASSEMBLY');

      expect(slat.placeholderList.where((e) => e == 'handle-1-h2').length, 1);
    });

    test('different positions → both added', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setPlaceholderHandle(1, 2, 'val', 'ASSEMBLY');
      slat.setPlaceholderHandle(2, 2, 'val', 'ASSEMBLY');

      expect(slat.placeholderList.length, 2);
      expect(slat.placeholderList, contains('handle-1-h2'));
      expect(slat.placeholderList, contains('handle-2-h2'));
    });

    test('same position, different sides → both added', () {
      final slat = Slat(1, 'slat-1', 'A', createTestSlatCoordinates(const Offset(0, 0)));
      slat.setPlaceholderHandle(1, 2, 'val', 'ASSEMBLY');
      slat.setPlaceholderHandle(1, 5, 'val', 'ASSEMBLY');

      expect(slat.placeholderList.length, 2);
      expect(slat.placeholderList, contains('handle-1-h2'));
      expect(slat.placeholderList, contains('handle-1-h5'));
    });
  });
}
