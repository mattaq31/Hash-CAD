import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'split_screen.dart';
import 'shared_app_state.dart';

void main() {
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
