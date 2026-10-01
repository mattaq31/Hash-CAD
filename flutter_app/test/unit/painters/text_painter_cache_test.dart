// Tests for the shared TextPainterCache used by the 2D canvas painters (reuse, keying and LRU eviction).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:hash_cad/2d_painters/text_painter_cache.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    TextPainterCache.clear();
    TextPainterCache.maxEntries = 2000;
  });

  test('returns the same laid-out painter for repeated requests', () {
    final a = TextPainterCache.get('↑12', Colors.black, 3.4);
    final b = TextPainterCache.get('↑12', Colors.black, 3.4);
    expect(identical(a, b), isTrue);
    expect(a.width, greaterThan(0));
    expect(TextPainterCache.length, 1);
  });

  test('text, colour and font size are all part of the key', () {
    final base = TextPainterCache.get('5', Colors.black, 4);
    expect(identical(base, TextPainterCache.get('6', Colors.black, 4)), isFalse);
    expect(identical(base, TextPainterCache.get('5', Colors.white, 4)), isFalse);
    expect(identical(base, TextPainterCache.get('5', Colors.black, 6)), isFalse);
    expect(TextPainterCache.length, 4);
  });

  test('evicts the least recently used entry when full', () {
    TextPainterCache.maxEntries = 2;
    final first = TextPainterCache.get('a', Colors.black, 4);
    TextPainterCache.get('b', Colors.black, 4);
    TextPainterCache.get('a', Colors.black, 4); // touch 'a' so 'b' becomes the oldest
    TextPainterCache.get('c', Colors.black, 4); // evicts 'b'

    expect(TextPainterCache.length, 2);
    expect(identical(first, TextPainterCache.get('a', Colors.black, 4)), isTrue);
  });

  test('clear empties the cache', () {
    TextPainterCache.get('x', Colors.black, 4);
    TextPainterCache.clear();
    expect(TextPainterCache.length, 0);
  });
}
