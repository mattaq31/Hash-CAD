import 'package:window_manager/window_manager.dart';
import '../grpc_client_architecture/server_startup.dart';


class ServerKillWindowListener extends WindowListener {
  @override
  void onWindowClose() async {
    await shutdownServerIfAny(); // Kill the server

    // Allow the window to close after cleanup
    windowManager.destroy();
  }
}