import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';
import 'package:flutter/material.dart';

class EchoTools extends StatefulWidget {
  const EchoTools({super.key});

  @override
  State<EchoTools> createState() => _EchoTools();
}

class _EchoTools extends State<EchoTools> with WidgetsBindingObserver {

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    var serverState = context.watch<ServerState>();

    return Column(children: [
      Text("Echo Export Tools",
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 5),
      Divider(thickness: 2, color: Colors.grey.shade600),
      Text("Features Coming Soon!",
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      Divider(thickness: 2, color: Colors.grey.shade600),
    ]);
  }
}
