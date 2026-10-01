/// Shared cache of laid-out [TextPainter]s for the 2D canvas painters.
///
/// Text shaping/layout is by far the most expensive operation the 2D painters perform, and it used to be redone for
/// every visible handle label on every frame (e.g. while panning/zooming). The set of distinct labels is small and
/// highly repetitive (handle values with an up/down arrow, cargo short names, slat numbers, slat IDs) and only ever
/// drawn in a couple of colours at fixed font sizes, so caching the laid-out painters removes almost all of that work.
library;

import 'dart:collection';

import 'package:flutter/material.dart';

/// Bounded least-recently-used cache of laid-out [TextPainter]s keyed by their text and style.
///
/// Entries are created lazily the first time a label is drawn, so the cache only ever holds labels that actually
/// appear on screen.  Since font size is part of the key, painters at stale sizes simply age out of the cache.
class TextPainterCache {
  TextPainterCache._();

  /// Upper bound on cached painters - comfortably above the few hundred distinct handle labels in a typical design, but
  /// keeps memory bounded for very large designs where every slat ID label is unique.
  static int maxEntries = 2000;

  // LinkedHashMap preserves insertion order; re-inserting on access moves an entry to the end, giving LRU ordering.
  static final LinkedHashMap<(String, Color, double, FontWeight), TextPainter> _cache = LinkedHashMap();

  /// Number of painters currently cached (mainly for tests).
  static int get length => _cache.length;

  /// Returns a laid-out, bold Roboto [TextPainter] for [text] at the given [color] and [fontSize].
  static TextPainter get(String text, Color color, double fontSize, {FontWeight fontWeight = FontWeight.bold}) {
    final key = (text, color, fontSize, fontWeight);
    final cached = _cache.remove(key);
    if (cached != null) {
      _cache[key] = cached; // mark as most recently used
      return cached;
    }

    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(color: color, fontFamily: 'Roboto', fontSize: fontSize, fontWeight: fontWeight),
      ),
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    )..layout();

    _cache[key] = painter;
    if (_cache.length > maxEntries) {
      // evict the least recently used painter.  Not disposed explicitly: its paragraph may still be referenced by a
      // picture recorded earlier this frame, so it's left to the garbage collector instead.
      _cache.remove(_cache.keys.first);
    }
    return painter;
  }

  /// Removes all cached painters (left to the garbage collector, as with eviction).
  static void clear() => _cache.clear();
}
