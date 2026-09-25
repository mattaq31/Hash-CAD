// Shared text rendering for DNA handle sequences, used by every view that inspects a handle's oligo
// (input plate pictograph/layout views, manual handle dialog, ...). Keeps the category coloring,
// core/linker/unique sequence split and click-to-copy behaviour consistent across the app.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../echo_and_experimental_helpers/echo_category_colors.dart';

/// Returns the display color for a handle [category] when used as text/highlight color.
///
/// [categoryColor] maps FLAT to a very light grey that is almost invisible as
/// text or against empty wells, so FLAT is darkened here for legibility.
Color plateCategoryDisplayColor(String category) {
  if (category.toUpperCase() == 'FLAT') return Colors.grey.shade700;
  return categoryColor(category);
}

/// Splits a stored handle sequence (`core + tt + unique`) into colored spans:
/// the core in black, the `tt` / ` TT ` linker in grey, and the unique tail in
/// [highlight]. If no linker is present the whole sequence is shown in black.
List<TextSpan> buildSequenceSpans(String fullSequence, Color highlight) {
  // Prefer the last linker occurrence: lowercase 'tt' or an uppercase ' TT '
  // flanked by spaces.
  final ttIndex = fullSequence.lastIndexOf('tt');
  final upperTtIndex = fullSequence.lastIndexOf(' TT ');
  final int linkerIndex;
  final int linkerLen;
  if (upperTtIndex > ttIndex) {
    linkerIndex = upperTtIndex;
    linkerLen = 4; // ' TT ' including the flanking spaces
  } else {
    linkerIndex = ttIndex;
    linkerLen = 2; // 'tt'
  }
  if (linkerIndex < 0) {
    // No linker present: show the whole sequence in plain black.
    return [TextSpan(text: fullSequence, style: const TextStyle(color: Colors.black))];
  }
  final core = fullSequence.substring(0, linkerIndex);
  final linker = fullSequence.substring(linkerIndex, linkerIndex + linkerLen); // preserves 'tt' vs ' TT '
  final unique = fullSequence.substring(linkerIndex + linkerLen);
  return [
    TextSpan(text: core, style: const TextStyle(color: Colors.black)),
    TextSpan(text: linker, style: TextStyle(color: Colors.grey.shade500)),
    TextSpan(text: unique, style: TextStyle(color: highlight, fontWeight: FontWeight.bold)),
  ];
}

/// Copies [sequence] to the clipboard and confirms with a short SnackBar.
void copySequenceToClipboard(BuildContext context, String sequence) {
  Clipboard.setData(ClipboardData(text: sequence));
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content: Text('Sequence copied to clipboard'), duration: Duration(seconds: 1)),
  );
}

/// Monospace, click-to-copy line describing a handle: caller-supplied [prefix] spans (position, name,
/// concentration, etc.) followed by the colored [sequence] from [buildSequenceSpans].
class CopyableHandleSequenceText extends StatelessWidget {
  final String sequence;

  /// Color for the unique (post-linker) part of the sequence, usually from [plateCategoryDisplayColor].
  final Color highlight;

  /// Descriptive spans shown before the sequence; they inherit black monospace text at [fontSize].
  final List<InlineSpan> prefix;
  final double fontSize;

  const CopyableHandleSequenceText({
    super.key,
    required this.sequence,
    required this.highlight,
    this.prefix = const [],
    this.fontSize = 12,
  });

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: 'Click to copy',
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: GestureDetector(
          onTap: () => copySequenceToClipboard(context, sequence),
          child: Text.rich(
            TextSpan(
              style: TextStyle(fontSize: fontSize, fontFamily: 'monospace', color: Colors.black),
              children: [...prefix, ...buildSequenceSpans(sequence, highlight)],
            ),
            textAlign: TextAlign.center,
            softWrap: true,
          ),
        ),
      ),
    );
  }
}
