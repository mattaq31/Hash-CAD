import 'dart:async';

import 'package:grpc/grpc.dart';
import 'hamming_evolve_communication.pbgrpc.dart';
import 'package:flutter/foundation.dart';

import '../app_management/design_state_mixins/design_state_handle_link_mixin.dart';
import '../crisscross_core/slats.dart';


/// Converts handle link manager, phantom coordinates, and phantom parents to proto format.
HandleLinkData convertHandleLinkData(HandleLinkManager linkManager, Map<String, List<(int, int)>> phantomCoords,
    Map<String, String> phantomParents, Map<String, Slat> slats, Map<String, Map<String, dynamic>> layerMap) {
  final result = HandleLinkData();

  // Convert link groups
  linkManager.handleGroupToLink.forEach((groupId, handleKeys) {
    final group = HandleLinkGroup()..groupId = groupId.toString();

    for (var key in handleKeys) {
      var slat = slats[key.$1];
      if (slat == null) continue;
      String pythonId = dartToPythonSlatNameConvert(key.$1, layerMap);
      group.handles.add(HandleKey()
        ..slatId = pythonId
        ..position = key.$2
        ..side = key.$3);
    }

    if (linkManager.handleGroupToValue.containsKey(groupId)) {
      group.hasEnforcedValue = true;
      group.enforcedValue_4 = linkManager.handleGroupToValue[groupId]!;
    }
    result.linkGroups.add(group);
  });

  // Convert blocked handles
  for (var key in linkManager.handleBlocks) {
    var slat = slats[key.$1];
    if (slat == null) continue;
    String pythonId = dartToPythonSlatNameConvert(key.$1, layerMap);
    result.blockedHandles.add(HandleKey()
      ..slatId = pythonId
      ..position = key.$2
      ..side = key.$3);
  }

  // Convert phantom slats
  phantomCoords.forEach((phantomId, coords) {
    final entry = PhantomSlatEntry()
      ..phantomSlatId = phantomId
      ..parentSlatId = phantomParents[phantomId]!;

    final coordList = CoordinateList();
    for (var (x, y) in coords) {
      coordList.coords.add(Coordinate()
        ..x = x
        ..y = y);
    }
    entry.coordinates = coordList;
    result.phantomSlats.add(entry);
  });

  return result;
}

class CrisscrossClient {
  late HandleEvolveClient stub;
  late ClientChannel channel;

  final _controller = StreamController<ProgressUpdate>.broadcast();
  Stream<ProgressUpdate> get updates => _controller.stream;

  // Constructor that immediately runs setup
  CrisscrossClient(int serverPort) {
    if (!kIsWeb) {
      _initialize(serverPort);
    }
  }

  Future<void> shutdown() async {
    if (!kIsWeb) {
      await channel.shutdown();
    }
  }

  Future<void> _initialize(int serverPort) async {
    channel = ClientChannel('127.0.0.1',
        port: serverPort,
        options:
            const ChannelOptions(credentials: ChannelCredentials.insecure()));
    stub = HandleEvolveClient(channel,
        options: CallOptions(timeout: Duration(seconds: 30)));
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


// Convert to Layer3D format
  List<Layer3D> convertToLayer3D(List<List<List<int>>> array3D) {
    List<Layer3D> result = [];

    for (var outerLayer in array3D) {
      Layer3D layer3D = Layer3D();

      // For each 2D layer in the 3D array
      for (var middleLayer in outerLayer) {
        Layer2D layer2D = Layer2D();
        // For each 1D row in the 2D layer
        Layer1D layer1D = Layer1D();
        for (var innerLayer in middleLayer) {
          layer1D.values.add(innerLayer);
        }
        layer2D.rows.add(layer1D);
        layer3D.layers.add(layer2D);
      }
      result.add(layer3D);
    }

    return result;
  }

// Helper to convert Dart record coords into proto CoordinateList
  Map<String, CoordinateList> convertSlatCoords(Map<String, List<(int, int)>> slatCoords) {
    final result = <String, CoordinateList>{};
    slatCoords.forEach((key, list) {
      final coordList = CoordinateList();
      for (final rec in list) {
        final x = rec.$1;
        final y = rec.$2;
        coordList.coords.add(Coordinate()..x = x..y = y);
      }
      result[key] = coordList;
    });
    return result;
  }


  Future<void> pauseEvolve(){
    return stub.pauseProcessing(PauseRequest());
  }

  Future<void> requestExport(String folderPath){
    return stub.requestExport(ExportRequest(folderPath: folderPath));
  }

  Future<List<List<List<int>>>> stopEvolve() async{
    final response = await stub.stopProcessing(StopRequest());
    return protoToList(response.handleArray);
  }


  Future<void> initiateEvolve(
      List<List<List<int>>> slatArray,
      Map<String, List<(int, int)>> slatCoords,
      List<List<List<int>>> handleArray,
      Map<String, String> evoParams,
      Map<String, String> slatTypes,
      String connectionAngle,
      HandleLinkManager linkManager,
      Map<String, List<(int, int)>> phantomCoords,
      Map<String, String> phantomParents,
      Map<String, Slat> slats,
      Map<String, Map<String, dynamic>> layerMap) async {

    List<Layer3D> grpcSlatArray = convertToLayer3D(slatArray);
    List<Layer3D> grpcHandleArray = convertToLayer3D(handleArray);

    // Convert handle link data (link groups, blocked handles, phantom slats)
    HandleLinkData linkData = convertHandleLinkData(linkManager, phantomCoords, phantomParents, slats, layerMap);

    final deadline = Duration(days: 365);  // Set deadline to 365 days (effectively infinite)

    final callOptions = CallOptions(timeout: deadline);

    // Define request parameters
    var request = EvolveRequest(
        slatArray: grpcSlatArray,
        handleArray: grpcHandleArray,
        parameters: evoParams,
        coordinateMap: convertSlatCoords(slatCoords),
        slatTypes: slatTypes,
        connectionAngle: connectionAngle,
        handleLinks: linkData);

    stub.evolveQuery(request, options: callOptions).listen((update) {
      if (kDebugMode) {
        print("Received: Max Valency=${update.hamming}, Eff. Valency=${update.physics}");
      }
      _controller.add(update);
    }, onError: (error) {
      if (kDebugMode) {
        print("Stream error: $error");
      }
    }, onDone: () {
      if (kDebugMode) {
        print("Stream closed");
      }
    });
  }
}
