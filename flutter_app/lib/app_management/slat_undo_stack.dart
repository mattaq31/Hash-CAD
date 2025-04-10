import '../crisscross_core/slats.dart';
import 'package:flutter/material.dart';

class SlatUndoStack {
  final List<Map<String, Slat>> _history = [];
  final List<Map<String, Map<Offset, String>>> _gridHistory = [];

  int _currentIndex = -1;
  static const int _maxHistory = 10;

  void saveState(Map<String, Slat> slats, Map<String, Map<Offset, String>> occupiedGridPoints) {

    // If we are in the middle of history, remove future states
    if (_currentIndex < _history.length - 1) {
      _history.removeRange(_currentIndex + 1, _history.length);
      _gridHistory.removeRange(_currentIndex + 1, _gridHistory.length);
    }

    // Add new state
    _history.add(Map.fromEntries(slats.entries.map((e) => MapEntry(e.key, e.value.copy()))));
    _gridHistory.add({
      for (var entry in occupiedGridPoints.entries)
        entry.key: Map.from(entry.value)
    });

    // Trim history if it exceeds the max limit
    if (_history.length > _maxHistory) {
      _history.removeAt(0);
      _gridHistory.removeAt(0);
    } else {
      _currentIndex++;
    }
  }

  Map<String, dynamic>? undo() {
    if (_currentIndex > -1) {
      _currentIndex--;

      Map<String, Map<Offset, String>> gridState = {
        for (var entry in _gridHistory[_currentIndex+1].entries)
          entry.key: Map.from(entry.value)
      };
      return {
        'slats': Map.fromEntries(_history[_currentIndex+1].entries.map((e) => MapEntry(e.key, e.value.copy()))),
        'occupiedGridPoints': gridState,
      };
    }
    return null; // No more undo steps
  }
}