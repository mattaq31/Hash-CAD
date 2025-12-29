import '../grpc_client_architecture/client_entry.dart';
import '../grpc_client_architecture/health.pbgrpc.dart';
import 'main_design_io.dart';

import 'package:flutter/foundation.dart';
import 'package:grpc/grpc.dart';

/// State management for communicating with python server
class ServerState extends ChangeNotifier {

  CrisscrossClient? hammingClient;
  HealthClient? healthClient;

  int serverPort = 50055;

  bool serverActive = false;
  bool serverCheckInProgress = false;

  List<double> hammingMetrics = [];
  List<double> physicsMetrics = [];

  Map<String, String> evoParams = {
    'mutation_rate': '5',
    'mutation_type_probabilities': '0.425, 0.425, 0.15',
    'evolution_generations': '2000',
    'evolution_population': '50',
    'process_count': 'DEFAULT',
    'generational_survivors': '3',
    'random_seed': '8',
    'unique_handle_sequences': '64',
    'early_max_valency_stop': '1',
    'split_sequence_handles': 'false'
  };

  // Human-readable labels for UI display
  final Map<String, String> paramLabels = {
    'mutation_rate': 'Mutation Rate',
    'mutation_type_probabilities': 'Mutation Probabilities',
    'evolution_generations': 'Max Generations',
    'evolution_population': 'Evolution Population',
    'process_count': 'Number of Threads',
    'generational_survivors': 'Generational Survivors',
    'random_seed': 'Random Seed',
    'number_unique_handles': 'Unique Handle Count',
    'split_sequence_handles': 'Split Sequence Handles',
    'early_max_valency_stop': 'Early Stop Target'
  };

  bool evoActive = false;
  String statusIndicator = 'BACKEND INACTIVE';

  ServerState();

  void evolveAssemblyHandles(List<List<List<int>>> slatArray, Map<String, List<(int, int)>> slatCoords, List<List<List<int>>> handleArray, Map<String, String> slatTypes, String connectionAngle) {
    hammingClient?.initiateEvolve(slatArray, slatCoords, handleArray, evoParams, slatTypes, connectionAngle);
    evoActive = true;
    statusIndicator = 'RUNNING';
    notifyListeners();
  }

  void exportParameters(){
    exportEvolutionParameters(evoParams);
  }

  void pauseEvolve(){
    hammingClient?.pauseEvolve();
    evoActive = false;
    statusIndicator = 'PAUSED';
    notifyListeners();
  }

  void exportRequest(String folderPath){
    hammingClient?.requestExport(folderPath);
  }

  Future<List<List<List<int>>>> stopEvolve(){
    evoActive = false;
    Future<List<List<List<int>>>> finalArray = hammingClient!.stopEvolve();
    hammingMetrics = [];
    physicsMetrics = [];
    statusIndicator = 'IDLE';
    notifyListeners();
    return finalArray;
  }

  void updateEvoParam(String parameter, String value){
    evoParams[parameter] = value;
    notifyListeners();
  }

  void launchClients(int port){
    serverPort = port;
    if (!kIsWeb) {
      hammingClient = CrisscrossClient(serverPort);
      healthClient = HealthClient(ClientChannel('127.0.0.1',
          port: serverPort,
          options:
          const ChannelOptions(credentials: ChannelCredentials.insecure())));

      hammingClient?.updates.listen((update) {
        hammingMetrics.add(update.hamming);
        physicsMetrics.add(update.physics);
        if(update.isComplete){
          statusIndicator = 'EVOLUTION COMPLETE - SAVE RESULTS!';
          evoActive = false;
        }
        notifyListeners(); // Notify UI elements
      });
    }
    notifyListeners();
  }

  @override
  void dispose() {
    if (!kIsWeb) {
      hammingClient?.shutdown();
    }// Clean up resources
    super.dispose();
  }

  // TODO: also implement health checks before sending a direct request to the server...
  Future<void> startupServerHealthCheck() async {

    if (serverCheckInProgress) return; // Prevent starting the check again
    serverCheckInProgress = true;

    while (healthClient == null){
      await Future.delayed(const Duration(seconds: 1));
    }

    var request = HealthCheckRequest();
    while (true) {
      try {
        var r = await healthClient?.check(request);
        if (r?.status == HealthCheckResponse_ServingStatus.SERVING) {
          statusIndicator = 'IDLE';
          serverActive = true;
          break;
        } else {
          serverActive = false;
        }
      } catch (_) {
        serverActive = false;
        await Future.delayed(const Duration(milliseconds: 500));
      }
    }
  }
}