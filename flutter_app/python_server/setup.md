Setting up the Integrated Python Server
====
Step 1: gRPC Protocol
---
* The .proto file is what controls how the server/client are setup to communicate.  It has its own form of syntax, the details of which can be found here: https://grpc.io (or use ChatGPT).

Step 2: Python Server
---
* When the proto file is defined, the next step is to generate the Python server code that utilizes the defined protocol.  First install the required python packages (ideally in a unique environment):
```bash
cd ../.. 
pip install -e .
cd ./flutter_app/python_server
pip install -r requirements.txt
```
* Next, use the below command to generate the server code (from the base flutter app directory):
```bash
python -m grpc_tools.protoc -I./python_dart_grpc_protocols --python_out=./python_server/server_architecture --pyi_out=./python_server/server_architecture --grpc_python_out=./python_server/server_architecture ./python_dart_grpc_protocols/hamming_evolve_communication.proto
```
* The above generates the Python server class code.  The server then requires your own custom logic to implement the various protocol functions.  The current implementation can be found in `main_server.py` and `HandleEvolveManager.py`.
* A client can be simulated through the `client_tester.py` file.
* Note: there's some issue with relative imports in hamming_evolve_communication_pb2_grpc.py, where the top import needs to start with a `from .`  Not sure if this can be permanently resolved some other way.

Step 3: Flutter Client
---
* Generate the corresponding functions for the Flutter client using the below CLI command (from the flutter app directory):
```bash
protoc -I ./python_dart_grpc_protocols/ ./python_dart_grpc_protocols/hamming_evolve_communication.proto --dart_out=grpc:lib/grpc_client_architecture
```
* You also need to generate the corresponding functions for the server health checker as below:

```bash
protoc -I ./python_dart_grpc_protocols/ ./python_dart_grpc_protocols/health.proto --dart_out=grpc:lib/grpc_client_architecture
```

Step 4: Bundling Python server with Nuitka
---

* The python server can be bundled up into a single executable using Nuitka.  Should use a minimal python environment (`bcc_packaging`) for this to prevent bloat.  Command for Mac/Linux is as follows:
```bash
python -m nuitka main_server.py --standalone --onefile --output-dir=./nuitka_package --output-filename=hamming_server --include-module=matplotlib.backends.backend_pdf --onefile-tempdir-spec={HOME}/.nuitka_cache --nofollow-import-to=matplotlib.backends.backend_macosx
```
For Windows use the following:
```bash
python -m nuitka main_server.py --standalone --onefile --output-dir=./nuitka_package --output-filename=hamming_server --include-module=matplotlib.backends.backend_pdf --onefile-tempdir-spec="{HOME}\\.nuitka_cache" --enable-plugin=no-qt
```

* Still unsure on whether the cache filepath is the same on every OS - will need to check.
* The above bundle will be slow to run for the first time (since it needs to unload its files into a temp directory) but should then be super fast after that.
