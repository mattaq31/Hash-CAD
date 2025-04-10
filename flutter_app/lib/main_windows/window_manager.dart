import 'package:flutter/material.dart';
import 'dart:io';
import 'package:window_size/window_size.dart' as window_size;


Future<void> initializeWindow() async {
  if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
    window_size.setWindowMinSize(const Size(800, 600));
    window_size.setWindowMaxSize(Size.infinite);

    final window = await window_size.getWindowInfo();
    final screens = await window_size.getScreenList();

    if (screens.isNotEmpty) {
      final primaryScreen = screens.first;
      final frame = primaryScreen.visibleFrame;
      window_size.setWindowFrame(frame);

      // Add a small delay to ensure the window size is applied
      await Future.delayed(const Duration(milliseconds: 100));
    }
  }
}
