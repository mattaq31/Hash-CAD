import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'main_windows/split_screen.dart';
import 'app_management/shared_app_state.dart';
import 'main_windows/window_manager.dart'
    if (dart.library.js_interop) 'main_windows/web_window_manager.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeWindow();
  runApp(MultiProvider(
    providers: [
      ChangeNotifierProvider(
        create: (context) {
          final designState = DesignState();
          designState.initializeUndoStack(); // Ensures undo stack starts with the initial state
          return designState;
        },
      ),
      ChangeNotifierProvider(create: (context) => ActionState()),
      ChangeNotifierProvider(create: (context) => ServerState())
    ],
    child: MaterialApp(
      home: SplitScreen(),
      title: 'Hash-CAD',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
      ),
    ),
  ));
}
