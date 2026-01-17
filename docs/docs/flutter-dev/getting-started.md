# Getting Started

This guide covers setting up your development environment for contributing to #-CAD.

## Prerequisites

### Flutter SDK

Install Flutter 3.19 following the instructions for your OS from the official Flutter documentation [site](https://docs.flutter.dev/install).

Verify installation:

```bash
flutter --version
flutter doctor
```

### IDE Setup

**IntelliJ**:

1. Install [IntelliJ IDEA](https://www.jetbrains.com/idea/)
2. Install the Flutter and Dart plugins

Other IDEs can be used such as VS Code (but #-CAD was originally developed in IntelliJ).

## Clone and Setup

### Clone the Repository

```bash
git clone https://github.com/mattaq31/Hash-CAD.git
cd Hash-CAD/flutter_app
```

### Install Dependencies

```bash
flutter pub get
```

Dependencies can be edited in `pubspec.yaml`.

### Run App

You can run the app directly in IntelliJ or another IDE from the main.dart file.  You can select the build configuration to build for desktop or web.

After running the app, you can make quick changes to the code and hot reload the app to see the changes.

In debug mode, you can apply breakpoints and step through the code.

## Building for Release

Building for release (with the `--release` flag) creates an executable that can be directly shared with others. Since we don't have a developer certificate, other users will need to accept the security warning when running the app.

## Python Server Setup

The Flutter app communicates with a Python server using gRPC to run handle evolution.  In debug mode, you will need to start the server manually using Python.  In release mode, the server is bundled with the app and runs automatically.

### Install Python Dependencies

```bash
cd flutter_app/python_server
pip install -r requirements.txt
```

### Re-Build auto-generated gRPC files (Optional)

Python-side server code:
```bash
python -m grpc_tools.protoc -I./python_dart_grpc_protocols --python_out=./python_server/server_architecture --pyi_out=./python_server/server_architecture --grpc_python_out=./python_server/server_architecture ./python_dart_grpc_protocols/hamming_evolve_communication.proto
```

Dart-side client code:
```bash
protoc -I ./python_dart_grpc_protocols/ ./python_dart_grpc_protocols/hamming_evolve_communication.proto --dart_out=grpc:lib/grpc_client_architecture

protoc -I ./python_dart_grpc_protocols/ ./python_dart_grpc_protocols/health.proto --dart_out=grpc:lib/grpc_client_architecture
```

### Run Server Manually

```bash
python main_server.py
```

The server runs on `localhost:50055` by default.

### Bundled Server

The desktop app includes a bundled Python server that starts automatically with #-CAD.  You will need to build the server manually if planning to build the app locally:

The build command for Mac/Linux is as follows:
```bash
python -m nuitka main_server.py --standalone --onefile --output-dir=./nuitka_package --output-filename=hamming_server --include-module=matplotlib.backends.backend_pdf --onefile-tempdir-spec={HOME}/.nuitka_cache --nofollow-import-to=matplotlib.backends.backend_macosx
```
For Windows use the following:
```bash
python -m nuitka main_server.py --standalone --onefile --output-dir=./nuitka_package --output-filename=hamming_server --include-module=matplotlib.backends.backend_pdf --onefile-tempdir-spec="{HOME}\\.nuitka_cache" --enable-plugin=no-qt
```
Note: there's some issue with relative imports in hamming_evolve_communication_pb2_grpc.py, where the top import needs to start with a `from .`  Not sure if this can be permanently resolved some other way.

## Running Tests

Automated tests are included which can test some basic functionality within the app (but of course cannot replicate full real-world scenarios).  You can run them with the below commands:

```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/slat_test.dart

# Run with coverage
flutter test --coverage
```

## GitHub Actions

All of the above actions are automated using various GitHub actions workflows:

- `flutter-web-deploy.yml`: Builds and deploys the Flutter web app to GitHub Pages.  This runs automatically when a new commit is pushed to the web-deploy branch.
- `python-server-and-desktop-app-deploy.yml`: Builds the python server and desktop app for Mac, Windows and Linux, then creates a release on GitHub.  The workflow is triggered automatically when a new tag with format 'vx.y.z' is pushed to the repository on the main branch.
- `flutter-test.yml`: Runs automated tests on the Flutter app.  Runs for every push on the main branch.

