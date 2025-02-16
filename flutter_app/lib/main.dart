import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'split_screen.dart';
import 'shared_app_state.dart';
import 'window_manager.dart' if (dart.library.html) 'web_window_manager.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeWindow();
  runApp(MultiProvider(
    providers: [ChangeNotifierProvider(create: (context) => DesignState()),
      ChangeNotifierProvider(create: (context) => ActionState())],
    child: MaterialApp(
      home: SplitScreen(),
      title: 'Crisscross Designer',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
      ),
    ),
  ));
}
