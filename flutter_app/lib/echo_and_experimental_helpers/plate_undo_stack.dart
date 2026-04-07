import 'plate_layout_state.dart';

class PlateUndoStack {
  final List<PlateLayoutState> _history = [];
  int _currentIndex = -1;
  static const int maxHistory = 50;

  void saveState(PlateLayoutState state) {
    // Remove future states if in the middle
    if (_currentIndex < _history.length - 1) {
      _history.removeRange(_currentIndex + 1, _history.length);
    }

    // Add a deep copy of the new state
    _history.add(state.copy());
    _currentIndex++;

    // Trim oldest entry if over capacity
    if (_history.length > maxHistory) {
      _history.removeAt(0);
      _currentIndex--;
    }
  }

  PlateLayoutState? undo() {
    if (_currentIndex > 0) {
      _currentIndex--;
      return _history[_currentIndex].copy();
    }
    return null;
  }

  PlateLayoutState? redo() {
    if (_currentIndex < _history.length - 1) {
      _currentIndex++;
      return _history[_currentIndex].copy();
    }
    return null;
  }

  bool get canUndo => _currentIndex > 0;
  bool get canRedo => _currentIndex < _history.length - 1;

  void clear() {
    _history.clear();
    _currentIndex = -1;
  }
}
