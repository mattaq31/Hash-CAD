# gRPC Integration

\#-CAD communicates with a Python backend server via gRPC for computationally intensive operations, primarily the evolutionary handle optimization algorithm.

## Architecture

```
┌─────────────────┐      gRPC (random port)    ┌─────────────────┐
│   Flutter App   │  ◄──────────────────────►  │  Python Server  │
│   (Dart Client) │                            │  (gRPC Server)  │
└─────────────────┘                            └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │  crisscross_kit │
                                               │  (Python lib)   │
                                               └─────────────────┘
```

## Protocol Definitions

**Location**: `flutter_app/python_dart_grpc_protocols/`

### Main Protocol

**File**: `hamming_evolve_communication.proto`

```protobuf
syntax = "proto3";
package evoService;

service HandleEvolve {
  rpc evolveQuery (EvolveRequest) returns (stream ProgressUpdate);
  rpc PauseProcessing (PauseRequest) returns (PauseRequest);
  rpc StopProcessing (StopRequest) returns (FinalResponse);
  rpc requestExport (ExportRequest) returns (ExportResponse);
}

message EvolveRequest {
  repeated Layer3D slatArray = 1;
  repeated Layer3D handleArray = 2;
  map<string, string> parameters = 3;
  map<string, string> slatTypes = 4;
  string connectionAngle = 5;
  map<string, CoordinateList> coordinateMap = 6;
  HandleLinkData handleLinks = 7;
}

message ProgressUpdate {
  double hamming = 1;
  double physics = 2;
  bool isComplete = 3;
}

message FinalResponse {
  repeated Layer3D handleArray = 1;
}
```

### Health Check

**File**: `health.proto`

```protobuf
syntax = "proto3";
package grpc.health.v1;

service Health {
  rpc Check(HealthCheckRequest) returns (HealthCheckResponse);
}

message HealthCheckRequest {
  string service = 1;
}

message HealthCheckResponse {
  enum ServingStatus {
    UNKNOWN = 0;
    SERVING = 1;
    NOT_SERVING = 2;
  }
  ServingStatus status = 1;
}
```

## Generating Code

### Dart Client

```bash
# From flutter_app/
protoc -I ./python_dart_grpc_protocols/ \
  ./python_dart_grpc_protocols/hamming_evolve_communication.proto \
  --dart_out=grpc:lib/grpc_client_architecture

protoc -I ./python_dart_grpc_protocols/ \
  ./python_dart_grpc_protocols/health.proto \
  --dart_out=grpc:lib/grpc_client_architecture
```

### Python Server

```bash
# From flutter_app/
python -m grpc_tools.protoc -I./python_dart_grpc_protocols \
  --python_out=./python_server/server_architecture \
  --pyi_out=./python_server/server_architecture \
  --grpc_python_out=./python_server/server_architecture \
  ./python_dart_grpc_protocols/hamming_evolve_communication.proto
```

**Note**: After generating Python code, fix the import in `hamming_evolve_communication_pb2_grpc.py`:

```python
# Change this:
import hamming_evolve_communication_pb2 as ...

# To this:
from . import hamming_evolve_communication_pb2 as ...
```

## Client Implementation

**File**: `lib/grpc_client_architecture/client_entry.dart`

```dart
import 'package:grpc/grpc.dart';
import 'hamming_evolve_communication.pbgrpc.dart';

class CrisscrossClient {
  late HandleEvolveClient stub;
  late ClientChannel channel;

  final _controller = StreamController<ProgressUpdate>.broadcast();
  Stream<ProgressUpdate> get updates => _controller.stream;

  CrisscrossClient(int serverPort) {
    channel = ClientChannel('127.0.0.1',
        port: serverPort,
        options: const ChannelOptions(credentials: ChannelCredentials.insecure()));
    stub = HandleEvolveClient(channel,
        options: CallOptions(timeout: Duration(seconds: 30)));
  }

  Future<void> initiateEvolve(
      List<List<List<int>>> slatArray,
      Map<String, List<(int, int)>> slatCoords,
      // ... more parameters
  ) async {
    var request = EvolveRequest(
        slatArray: convertToLayer3D(slatArray),
        // ...
    );
    stub.evolveQuery(request).listen((update) {
      _controller.add(update);
    });
  }

  Future<void> pauseEvolve() => stub.pauseProcessing(PauseRequest());

  Future<List<List<List<int>>>> stopEvolve() async {
    final response = await stub.stopProcessing(StopRequest());
    return protoToList(response.handleArray);
  }

  Future<void> shutdown() async => await channel.shutdown();
}
```

## ServerState Integration

**File**: `lib/app_management/server_state.dart`

ServerState manages the gRPC clients and evolution state:

```dart
class ServerState extends ChangeNotifier {
  CrisscrossClient? hammingClient;
  HealthClient? healthClient;

  bool serverActive = false;
  bool evoActive = false;
  String statusIndicator = 'BACKEND INACTIVE';

  List<double> hammingMetrics = [];
  List<double> physicsMetrics = [];

  void launchClients(int port) {
    hammingClient = CrisscrossClient(port);
    healthClient = HealthClient(ClientChannel('127.0.0.1', port: port, ...));

    // Listen for evolution updates
    hammingClient?.updates.listen((update) {
      hammingMetrics.add(update.hamming);
      physicsMetrics.add(update.physics);
      if (update.isComplete) {
        statusIndicator = 'EVOLUTION COMPLETE';
        evoActive = false;
      }
      notifyListeners();
    });
  }

  void evolveAssemblyHandles(...) {
    hammingClient?.initiateEvolve(...);
    evoActive = true;
    statusIndicator = 'RUNNING';
    notifyListeners();
  }

  Future<List<List<List<int>>>> stopEvolve() async {
    evoActive = false;
    return await hammingClient!.stopEvolve();
  }
}
```

## Python Server

**File**: `flutter_app/python_server/main_server.py`

```python
import grpc
from concurrent import futures
from grpc_health.v1 import health_pb2_grpc, health
from server_architecture import hamming_evolve_communication_pb2_grpc
from HandleEvolveManager import HandleEvolveService

def serve():
    DEFAULT_PORT = 50055
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add evolution service
    hamming_evolve_communication_pb2_grpc.add_HandleEvolveServicer_to_server(
        HandleEvolveService(), server
    )

    # Add health check service
    health_pb2_grpc.add_HealthServicer_to_server(health.HealthServicer(), server)

    server.add_insecure_port(f'localhost:{port}')
    print(f"gRPC server started and listening on localhost:{port}")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
```

## Bundled Server

**File**: `lib/grpc_client_architecture/server_startup.dart`

The desktop app bundles a compiled Python server executable (via Nuitka):

```dart
Future<int> launchServer() async {
  var dir = await getApplicationSupportDirectory();
  var filePath = File(p.join(dir.path, _getAssetName())).path;

  // Copy bundled asset to support directory if needed
  ByteData data = await PlatformAssetBundle().load('assets/${_getAssetName()}');
  // ... hash check and write ...

  // Find free port (in release mode)
  int port = 50055;
  if (!kDebugMode) {
    var serverSocket = await ServerSocket.bind(InternetAddress.loopbackIPv4, 0);
    port = serverSocket.port;
    serverSocket.close();
  }

  // Launch server process
  var process = await Process.start(filePath, [port.toString()]);
  return port;
}

String _getAssetName() {
  if (defaultTargetPlatform == TargetPlatform.windows) return 'hamming_server_win.exe';
  if (defaultTargetPlatform == TargetPlatform.macOS) return 'hamming_server_osx';
  if (defaultTargetPlatform == TargetPlatform.linux) return 'hamming_server_lnx';
  return '';
}
```

## Health Checking

The client performs health checks before evolution:

```dart
Future<void> startupServerHealthCheck() async {
  var request = HealthCheckRequest();
  while (true) {
    try {
      var r = await healthClient?.check(request);
      if (r?.status == HealthCheckResponse_ServingStatus.SERVING) {
        statusIndicator = 'IDLE';
        serverActive = true;
        break;
      }
    } catch (_) {
      await Future.delayed(const Duration(milliseconds: 500));
    }
  }
}
```

## Server Shutdown

Proper cleanup when the app closes:

```dart
Future<void> shutdownServerIfAny() async {
  switch (defaultTargetPlatform) {
    case TargetPlatform.linux:
    case TargetPlatform.macOS:
      await Process.run('pkill', [assetName]);
      break;
    case TargetPlatform.windows:
      await Process.run('taskkill', ['/F', '/IM', assetName]);
      break;
  }
}
```
