import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'split_screen.dart';
import 'shared_app_state.dart';
import 'window_manager.dart' if (dart.library.html) 'web_window_manager.dart';

Future<void> main() async{
  WidgetsFlutterBinding.ensureInitialized();

  await initializeWindow();

  runApp(ChangeNotifierProvider(
    create: (context) => MyAppState(),
    child: MaterialApp(
      home: SplitScreen(),
      title: 'Crisscross Designer',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
      ),
    ),
  ));
}
