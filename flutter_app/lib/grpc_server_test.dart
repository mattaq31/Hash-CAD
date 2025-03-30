import 'dart:math' show Random;

import 'package:grpc/grpc.dart';
import 'grpc_client_architecture/hamming_evolve_communication.pbgrpc.dart';

class Client {
  late HandleEvolveClient stub;

  Future<void> main(List<String> args) async {
    final channel = ClientChannel('127.0.0.1',
        port: 50055,
        options:
        const ChannelOptions(credentials: ChannelCredentials.insecure()));
    stub = HandleEvolveClient(channel,
        options: CallOptions(timeout: Duration(seconds: 30)));
    // Run all of the demos in order.
    try {
      await runStopProcessing();
    } catch (e) {
      print('Caught error: $e');
    }
    await channel.shutdown();
  }

  Future<void> runStopProcessing() async {

    final stopRequest = StopRequest();
    // Call the server-side stopProcessing method
    try {
      final response = await stub.stopProcessing(stopRequest);
      List<List<List<int>>> handleArray3D = protoToList(response.handleArray);
      print('Received response: $response');
    } catch (e) {
      print('Error during gRPC call: $e');
    }

    try {
      await testStream();
    } catch (e) {
      print('Caught error: $e');
    }

  }

  // Helper method to convert the response handleArray to List<List<List<int>>>
  List<List<List<int>>> protoToList(List<Layer3D> protoLayers) {
    List<List<List<int>>> array3D = [];

    for (var layer3D in protoLayers) {
      List<List<int>> array2D = [];
      for (var layer2D in layer3D.layers) {
        for (var layer1D in layer2D.rows) {
          array2D.add(layer1D.values.toList());  // Extract 1D array and add to 2D
        }
      }
      array3D.add(array2D);  // Add 2D layer to 3D array
    }
    return array3D;  // Return the nested List<List<List<int>>>
  }

  Future<void> testStream() async {
    // Create a 12x10x3 zero array
    List<Layer3D> slatArray = List.generate(12, (i) {
      return Layer3D(
          layers: [
            Layer2D(
                rows: List.generate(10, (j) => Layer1D(values: List.filled(3, 2)))
            )
          ]
      );
    });

    // Define request parameters
    var request = EvolveRequest(
        slatArray: slatArray,
        parameters: {
          "mutation_rate": "0.05",
          "crossover": "single_point"
        }
    );

    // Call the evolveQuery method and listen to streamed responses
    try {
      await for (var update in stub.evolveQuery(request)) {
        print("Metrics: ${update.hamming}, ${update.physics}");
      }
    } catch (e) {
      print("Error in evolveQuery: $e");
    }
  }

}

void main(List<String> args) {
  final client = Client();
  client.main(args); // Call the main function of the Client class
}