import 'dart:math' as math;
import '../crisscross_core/slats.dart';
import '../app_management/shared_app_state.dart';

import 'package:flutter/material.dart';
import 'package:three_js_controls/three_js_controls.dart';
import 'package:three_js_core/three_js_core.dart' as three;
import 'package:three_js_geometry/three_js_geometry.dart';
import 'package:three_js_math/three_js_math.dart' as tmath;
import 'package:provider/provider.dart';
import 'package:three_js_helpers/three_js_helpers.dart';
import '../2d_painters/helper_functions.dart';
import '../crisscross_core/cargo.dart';

class ThreeDisplay extends StatefulWidget {
  const ThreeDisplay({super.key});

  @override
  State<ThreeDisplay> createState() => _ThreeDisplay();
}

class _ThreeDisplay extends State<ThreeDisplay> {
  late three.ThreeJS threeJs;
  bool isSetupComplete = false;
  double VFOV = 70;
  late double HFOV;
  Set<String> slatIDs = {};
  Map<String, Map<String, three.Mesh>> slatAccessories = {};
  Map<String, three.MeshPhongMaterial> layerMaterials = {};
  Map<String, three.MeshPhongMaterial> cargoMaterials = {};

  double gridSize = 10;
  late double y60Jump = gridSize / 2;
  late double x60Jump = math.sqrt(math.pow(gridSize, 2) - math.pow(y60Jump, 2));
  String gridMode = '60';

  bool assemblyHandleView = false;
  bool cargoHandleView = true;

  // parameters for six-helix bundle view
  bool helixBundleView = true;
  final double helixBundleSize = 5/(1 + math.sqrt(3));
  late double helixBundledX = (math.sqrt(3)/2) * helixBundleSize;
  late List<List<double>> helixBundlePositions = [
    [-helixBundledX, -helixBundleSize/2],
    [helixBundledX, -helixBundleSize/2],
    [-helixBundledX, helixBundleSize/2],
    [helixBundledX, helixBundleSize/2],
    [0, helixBundleSize],
    [0, -helixBundleSize],
  ];

  static const WidgetStateProperty<Icon> switchThumbIcon = WidgetStateProperty<Icon>.fromMap(
    <WidgetStatesConstraint, Icon>{
      WidgetState.selected: Icon(Icons.check),
      WidgetState.any: Icon(Icons.close),
    },
  );

  late List<three.Object3D> importantObjects = [];

  @override
  void initState() {
    threeJs = three.ThreeJS(
        onSetupComplete: () {
          setState(() {
            isSetupComplete = true;
          });
        },
        setup: setup,
        settings: three.Settings(renderOptions: {
          "minFilter": tmath.LinearFilter,
          "magFilter": tmath.LinearFilter,
          "format": tmath.RGBAFormat,
          "samples": 4
        }));
    super.initState();
  }

  @override
  void dispose() {
    threeJs.dispose();
    controls.dispose();
    super.dispose();
  }

  late OrbitControls controls;

  void setup(){
    threeJs.scene = three.Scene();
    threeJs.scene.background = tmath.Color.fromHex32(0xffffff);

    threeJs.camera = three.PerspectiveCamera(VFOV, threeJs.width / threeJs.height, 1, 10000);
    HFOV = 2 * math.atan(math.tan(VFOV * math.pi / 180 / 2) * threeJs.width / threeJs.height) * 180 / math.pi;

    threeJs.camera.position.setValues(-63.18, 154.58, 328.46);
    controls = OrbitControls(threeJs.camera, threeJs.globalKey);
    controls.target.setValues(-21.87, -8, 3.73);

    controls.enableDamping = true; // an animation loop is required when either damping or auto-rotation are enabled
    controls.dampingFactor = 0.05;

    controls.screenSpacePanning = false;

    controls.minDistance = 100;
    // controls.maxDistance = 1000;

    final gridHelper = GridHelper(1000, 50); // Grid size: 1000, 50 divisions
    threeJs.scene.add(gridHelper);

    final axesHelper = AxesHelper(1000);
    threeJs.scene.add(axesHelper);

    // TODO: set better lighting
    final dirLight1 = three.DirectionalLight(0xffffff, 0.5);
    dirLight1.position.setValues(1, 1, 1);
    threeJs.scene.add(dirLight1);

    final dirLight2 = three.DirectionalLight(0x002288, 0.3);
    dirLight2.position.setValues(-1, -1, -1);
    threeJs.scene.add(dirLight2);

    final ambientLight = three.AmbientLight(0x222222);
    threeJs.scene.add(ambientLight);

    importantObjects = [gridHelper, axesHelper, dirLight1, dirLight2, ambientLight];

    threeJs.addAnimationEvent((dt){
      controls.update();
      // logCameraDetails();
    });

  }

  void logCameraDetails() {
    final pos = threeJs.camera.position;
    final target = controls.target; // OrbitControls has a 'target' property

    print("Camera Position: (${pos.x}, ${pos.y}, ${pos.z})");
    print("LookAt Target: (${target.x}, ${target.y}, ${target.z})");
  }

  /// Calculates a slat's directionality angle based on the first and last points
  double calculateSlatAngle(Offset p1, Offset p2) {
    double dx = p2.dx - p1.dx;
    double dy = p2.dy - p1.dy;
    double angle = math.atan2(dy, dx); // Angle in radians
    return angle;
  }

  /// Calculates the extension from the slat's center point to the edge of the slat, based on the slat's angle and the grid size.
  Offset calculateSlatExtend(Offset p1, Offset p2, double gridSize){
    double slatAngle = calculateSlatAngle(p1, p2);
    double extX = (gridSize/2) * math.cos(slatAngle);
    double extY = (gridSize/2) * math.sin(slatAngle);
    return Offset(extX, extY);
  }

  three.Group createSlatBundle(String name, three.MeshPhongMaterial material, double slatAngle, double height, double centerX, double centerZ){

    final group = three.Group();
    group.name = name;

    if (helixBundleView){
      // full representation of a slat six-helix bundle
      for (var pos in helixBundlePositions) {
        final geometry = CylinderGeometry(helixBundleSize/2, helixBundleSize/2, gridSize * 32, 60);
        final mesh = three.Mesh(geometry, material);
        mesh.position.setX(pos[1]);
        mesh.position.setY(0);
        mesh.position.setZ(pos[0]);
        group.add(mesh);
      }
    }
    else {
      // single rod only (in the center)
      final geometry = CylinderGeometry(2.5, 2.5, gridSize * 32, 60); // actual size should be 310, but adding an extra 10 to improve visuals
      final mesh = three.Mesh(geometry, material);
      mesh.position.setX(0);
      mesh.position.setY(0);
      mesh.position.setZ(0);
      group.add(mesh);
    }

    // a value of 6.5 used for each layer (enough for one slat + a small gap for cargo later on)
    group.position.y = height;
    group.position.z = centerZ;
    group.position.x = centerX;

    group.rotation.z = math.pi / 2;  // default
    group.rotation.y = -slatAngle;

    return group;

  }

  void createHandle(String slatID, String name, Offset position, three.MeshPhongMaterial material, double zOrder, String topSide, String handleSide, String handleType){
    /// Creates a new handle graphic in the 3D scene.

    three.BufferGeometry geometry;

    if (handleType == 'Assembly') {
      geometry = CylinderGeometry(helixBundleView ? 0.8 : 2, helixBundleView ? 0.8 : 2, 1.5, 8);
    }
    else {
      geometry = three.BoxGeometry(4, 6, 4);
    }

    final mesh = three.Mesh(geometry, material);
    mesh.name = name;
    double verticalOffset = (topSide == handleSide) ? 2.5 : -2.5;
    if (handleType == 'Cargo'){
      verticalOffset += (topSide == handleSide) ? 2 : -2;
    }
    mesh.position.setValues(position.dx, (zOrder * 6.5) + verticalOffset, position.dy);
    mesh.rotation.z = math.pi;
    mesh.updateMatrix();
    mesh.matrixAutoUpdate = false;
    threeJs.scene.add(mesh);
    slatAccessories[slatID]?[name] = mesh;
  }

  void updateHandle(three.Object3D handleMesh, Offset newPosition, double newZOrder, String newTopSide, String newHandleSide, String handleType){
    /// Makes updates to the position and color of an existing handle in the 3D scene, if necessary.  Regenerating from scratch is slow so an update is preferred instead.

    // TODO: switching from cargo to assembly handle is not currently catered for properly!
    double verticalOffset = (newTopSide == newHandleSide) ? 2.5 : -2.5;
    if (handleType == 'Cargo'){
      verticalOffset += (newTopSide == newHandleSide) ? 2 : -2;
    }
    bool updateNeeded = false;
    // general position change
    if (handleMesh.position.x != newPosition.dx || handleMesh.position.y != (newZOrder * 6.5) + verticalOffset || handleMesh.position.z != newPosition.dy) {
      handleMesh.position.x = newPosition.dx;
      handleMesh.position.y = (newZOrder * 6.5) + verticalOffset;
      handleMesh.position.z = newPosition.dy;
      updateNeeded = true;
    }

    if (updateNeeded) {
      handleMesh.updateMatrix();
    }
  }

  void handleAssembly(Slat slat, int handlePosition, Offset position, int color, double order, String topSide, String handleSide) {
    final handleName = '${slat.id}-handle-$handlePosition-$handleSide';
    final existingHandleMesh = threeJs.scene.getObjectByName(handleName);

    bool existingHandle = false;
    String handleType = 'Assembly';
    var cargoName = 'Assembly';

    if (handleSide == 'H5'){
      existingHandle = slat.h5Handles.containsKey(handlePosition);
      if (existingHandle) {
        handleType = slat.h5Handles[handlePosition]!['category'];
        cargoName = slat.h5Handles[handlePosition]!['descriptor'];
      }
    }
    else if (handleSide == 'H2'){
      existingHandle = slat.h2Handles.containsKey(handlePosition);
      if (existingHandle) {
        handleType = slat.h2Handles[handlePosition]!['category'];
        cargoName = slat.h2Handles[handlePosition]!['descriptor'];
      }
    }

    if (existingHandle && (assemblyHandleView && handleType == 'Assembly' || cargoHandleView && handleType == 'Cargo')) {
      if (existingHandleMesh == null) {
        // Create new handle if missing
        createHandle(slat.id, handleName, position, handleType == 'Assembly' ? layerMaterials[slat.layer]!: cargoMaterials[cargoName]!, order, topSide, handleSide, handleType);
      } else {
        // Update existing handle
        updateHandle(existingHandleMesh, position, order, topSide, handleSide, handleType);
      }
    } else if (existingHandleMesh != null){
      // Remove handle if it was deleted from the slat but still lingering in the scene (or if the assembly handle view has been turned off)
      threeJs.scene.remove(existingHandleMesh);
      slatAccessories[slat.id]?.remove(handleName);
    }
  }


  void manageHandles(Slat baseSlat, Map<String, Map<String, dynamic>> layerMap) {

    /// Adds, updates or removes assembly handles from the 3D scene based on the current state of the slat.
    if (!slatAccessories.containsKey(baseSlat.id)) {
      slatAccessories[baseSlat.id] = {};
    }

    final topSide = (layerMap[baseSlat.layer]?['top_helix'] == 'H5') ? 'H5' : 'H2';
    final color = layerMap[baseSlat.layer]?['color'].value & 0x00FFFFFF;
    final order = layerMap[baseSlat.layer]?['order'].toDouble();
    for (var i = 1; i <= baseSlat.maxLength; i++) {
      handleAssembly(
        baseSlat,
        i,
        convertCoordinateSpacetoRealSpace(baseSlat.slatPositionToCoordinate[i]!, gridMode, gridSize, x60Jump, y60Jump),
        color,
        order,
        topSide,
        'H2',
      );
      handleAssembly(
        baseSlat,
        i,
        convertCoordinateSpacetoRealSpace(baseSlat.slatPositionToCoordinate[i]!, gridMode, gridSize, x60Jump, y60Jump),
        color,
        order,
        topSide,
        'H5',
      );
    }
  }

  /// Adds all provided slats into the 3D scene, updating existing slats if necessary.
  void manageSlats(List<Slat> slats, Map<String, Map<String, dynamic>> layerMap, Map<String, Cargo> cargoPalette){

    if (!isSetupComplete || threeJs.scene == null) return;

    Set localIDs = slats.map((slat) => slat.id).toSet();
    Set removedIDs = slatIDs.difference(localIDs);


    // prepares the material for each layer in the system
    for (var layer in layerMap.keys) {
      if (!layerMaterials.containsKey(layer)) {
        layerMaterials[layer] = three.MeshPhongMaterial.fromMap({"color": layerMap[layer]?['color'].value & 0x00FFFFFF, "flatShading": true});
      }
      else if (layerMaterials[layer]?.color.getHex() != (layerMap[layer]?['color'].value & 0x00FFFFFF)){
        layerMaterials[layer]?.color.setFromHex32(layerMap[layer]?['color'].value & 0x00FFFFFF);
      }
    }

    // prepares the material for each cargo type in the palette
    for (var cargoKey in cargoPalette.keys) {
      if (!cargoMaterials.containsKey(cargoKey)) {
        cargoMaterials[cargoKey] = three.MeshPhongMaterial.fromMap({"color": cargoPalette[cargoKey]!.color.value & 0x00FFFFFF, "flatShading": true});
      }
      else if (cargoMaterials[cargoKey]?.color.getHex() != (cargoPalette[cargoKey]!.color.value & 0x00FFFFFF)){
        cargoMaterials[cargoKey]?.color.setFromHex32(cargoPalette[cargoKey]!.color.value & 0x00FFFFFF);
      }
    }

    // removes associated material if a layer has been deleted
    final keysToRemove = <String>[];
    for (var layer in layerMaterials.keys) {
      if (!layerMap.containsKey(layer)) {
        keysToRemove.add(layer);
      }
    }
    for (var key in keysToRemove) {
      layerMaterials[key]?.dispose();
      layerMaterials.remove(key);
    }

    // deletes slats that are no longer in the list
    for (var id in removedIDs) {
      removeSlat(id);
      slatIDs.remove(id);
    }

    for (var slat in slats) {
      var p1 = convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[1]!, gridMode, gridSize, x60Jump, y60Jump);
      var p2 = convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[32]!, gridMode, gridSize, x60Jump, y60Jump);
      // same angle/extension system used here as in 2D system

      double slatAngle = calculateSlatAngle(p1, p2);
      Offset slatExtend = calculateSlatExtend(p1, p2, 2*(gridSize * 32/2 - gridSize/2));

      // if slat does not exist, recreate from scratch
      if (threeJs.scene.getObjectByName(slat.id) == null) {
        slatIDs.add(slat.id);
        final meshGroup = createSlatBundle(slat.id, layerMaterials[slat.layer]!,
            slatAngle, layerMap[slat.layer]?['order'].toDouble() * 6.5, p1.dx + slatExtend.dx, p1.dy + slatExtend.dy);
        meshGroup.updateMatrix();
        meshGroup.matrixAutoUpdate = false;
        threeJs.scene.add(meshGroup);

        manageHandles(slat, layerMap); // add assembly handles to the slat
      }
      // slat already exists - should check to see if layer position, color, or direction has changed
      else{
        bool updateNeeded = false;
        final meshSlat = threeJs.scene.getObjectByName(slat.id);

        double incomingSlatAngle = -slatAngle;
        double incomingPositionZ = p1.dy + slatExtend.dy;
        double incomingPositionX = p1.dx + slatExtend.dx;
        double incomingLayer = layerMap[slat.layer]?['order'].toDouble() * 6.5;

        // general position change
        if (meshSlat?.position.x != incomingPositionX || meshSlat?.position.z != incomingPositionZ || meshSlat?.rotation.y != incomingSlatAngle) {
          meshSlat?.position.x = incomingPositionX;
          meshSlat?.position.z = incomingPositionZ;
          meshSlat?.rotation.y = incomingSlatAngle;
          updateNeeded = true;
        }

        // layer change
        if (meshSlat?.position.y != incomingLayer) {
          meshSlat?.position.y = incomingLayer;
          updateNeeded = true;
        }

        manageHandles(slat, layerMap); // add/update/remove assembly handles

        // request update if necessary
        if(updateNeeded) {
          meshSlat?.updateMatrix();
        }
      }
    }
  }

  /// Removes a slat from the 3D scene
  void removeSlat(String id){
    final slat = threeJs.scene.getObjectByName(id);
    if (slat != null) {
      threeJs.scene.remove(slat);

      slatAccessories[id]?.forEach((name, handle) {
        threeJs.scene.remove(handle);
      });
    }
  }

  void clearSceneExcept(List<three.Object3D> keepObjects) {
    for (var object in List.from(threeJs.scene.children)) {
      if (!keepObjects.contains(object)) {
        if (object is three.Mesh) {
          object.geometry?.dispose();
          (object.material)?.dispose();
        }
        threeJs.scene.remove(object);
      }
    }
  }

  void centerOnSlats(){
    if (!isSetupComplete) return;

    // Get all slats in the scene
    List<three.Object3D> slats = threeJs.scene.children
        .where((obj) => obj.name.contains("-"))
        .toList();

    // nothing to focus on
    if (slats.isEmpty) return;

    // Compute bounding box of all slats
    var boundingBox = tmath.BoundingBox();

    for (var slat in slats) {
      var slatBox = tmath.BoundingBox().setFromObject(slat);
      boundingBox.expandByPoint(slatBox.min);
      boundingBox.expandByPoint(slatBox.max);
    }

    // Compute centroid of the bounding box
    tmath.Vector3 center = tmath.Vector3(0, 0, 0);
    boundingBox.getCenter(center);

    // Can use this to indicate centre position (for debugging purposes)
    // final geometry = three.SphereGeometry(2.5); // actual size should be 310, but adding an extra 10 to improve visuals
    // final material = three.MeshPhongMaterial.fromMap({"color": 0xFF00FF, "flatShading": true});
    // final mesh = three.Mesh(geometry, material);
    // mesh.position.setValues(center.x, center.y, center.z);
    // threeJs.scene.add(mesh);

    // computes boundary sphere i.e. container that encapsulates all slats
    // Attempts to find the best camera distance based on the horizontal/vertical aspect ratio
    var boundSphere = tmath.BoundingSphere();
    boundingBox.getBoundingSphere(boundSphere);
    double hDistance = boundSphere.radius / (math.tan(HFOV * math.pi / 180 / 2));
    double vDistance = boundSphere.radius / (math.tan(VFOV * math.pi / 180 / 2));
    double cameraDistance = 1.1 * math.max(hDistance, vDistance); // adds a little buffer, just in case

    // Desired fixed camera angles TODO: should these be tunable?
    double elevationAngle = 30 * (math.pi / 180); // Convert to radians
    double azimuthAngle = 45 * (math.pi / 180);

    // Convert spherical coordinates to Cartesian (x, y, z)
    double radius = cameraDistance;  // Distance from the scene center
    double x = radius * math.cos(elevationAngle) * math.cos(azimuthAngle);
    double y = radius * math.sin(elevationAngle); // Height due to elevation
    double z = radius * math.cos(elevationAngle) * math.sin(azimuthAngle);

    // Compute new camera position relative to the bounding box center
    tmath.Vector3 newCameraPosition = tmath.Vector3(x, y, z).add(center);

    // Applies the new camera position
    threeJs.camera.position.setValues(newCameraPosition.x, newCameraPosition.y, newCameraPosition.z);

    // updates camera target to the center of all slats
    controls.target.setValues(center.x, center.y, center.z);
    controls.update();
  }


  /// Attempts to adjust viewer size when window is adjusted, although this is still not 100% effective
  void onResize(double width, double height) {
    if (!mounted || width <= 0 || height <= 0 || !isSetupComplete) return; // Ensure widget is still available

    if (threeJs.camera != null && threeJs.renderer != null) {
      threeJs.camera.aspect = width / height;
      HFOV = 2 * math.atan(math.tan(VFOV * math.pi / 180 / 2) * width / height) * 180 / math.pi;
      threeJs.camera.updateProjectionMatrix();
      threeJs.renderer?.setSize(width, height, true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<DesignState>(builder: (context, appState, child) {
      // TODO: at some point, it would be better if the appState could be directly accessed...
      gridSize = appState.gridSize;
      gridMode = appState.gridMode;
      y60Jump = appState.y60Jump;
      x60Jump = appState.x60Jump;

      manageSlats(appState.slats.values.toList(), appState.layerMap, appState.cargoPalette);
      return Stack(
        children: [
          LayoutBuilder(
            builder: (context, constraints) {
              WidgetsBinding.instance.addPostFrameCallback((_) {
                onResize(constraints.maxWidth, constraints.maxHeight);
              });
              return threeJs.build();
            },
          ),
          Positioned(
            bottom: 16.0,
            right: 16.0,
            child: Row(
              children: [
                Text("Display Slats as 6HBs"),
                Switch(
                  thumbIcon: switchThumbIcon,
                  value: helixBundleView,
                  onChanged: (bool value) {
                    setState(() {
                      helixBundleView = value;
                      clearSceneExcept(importantObjects);
                      manageSlats(appState.slats.values.toList(), appState.layerMap, appState.cargoPalette);
                    });
                  },
                ),
                Text("Display Assembly Handles"),
                Switch(
                  thumbIcon: switchThumbIcon,
                  value: assemblyHandleView,
                  onChanged: (bool value) {
                    setState(() {
                      assemblyHandleView = value;
                    });
                  },
                ),
                Text("Display Cargo Handles"),
                Switch(
                  thumbIcon: switchThumbIcon,
                  value: cargoHandleView,
                  onChanged: (bool value) {
                    setState(() {
                      cargoHandleView = value;
                    });
                  },
                ),
                ElevatedButton(
                  onPressed: centerOnSlats,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white.withValues(alpha: 0.3),
                    // Semi-transparent
                    foregroundColor: Colors.black, // Text/icon color
                  ),
                  child: const Icon(Icons.filter_center_focus),
                ),
              ],
            ),
          ),
        ],
      );
    });
  }
}

