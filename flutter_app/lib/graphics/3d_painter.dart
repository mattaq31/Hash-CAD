import 'dart:collection';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:three_js_helpers/three_js_helpers.dart';
import 'package:three_js_controls/three_js_controls.dart';
import 'package:three_js_core/three_js_core.dart' as three;
import 'package:three_js_geometry/three_js_geometry.dart';
import 'package:three_js_math/three_js_math.dart' as tmath;
import 'package:three_js_helpers/camera_helper.dart';

import '../2d_painters/helper_functions.dart';
import '../crisscross_core/cargo.dart';
import '../crisscross_core/slats.dart';
import '../app_management/shared_app_state.dart';

bool approxEqual(double a, double b, [double epsilon = 1e-4]) {
  return (a - b).abs() < epsilon;
}

three.BufferGeometry createHoneyCombSlat(List<List<double>> helixBundlePositions, double helixBundleSize, double gridSize) {

  final mergedGeometry = three.BufferGeometry();
  final mergedPositions = <double>[];
  final mergedNormals = <double>[];
  final mergedIndices = <int>[];

  int indexOffset = 0;

  for (var pos in helixBundlePositions) {

    // Create cylinder geometry
    CylinderGeometry geometry = CylinderGeometry(helixBundleSize/2, helixBundleSize/2, gridSize * 32, 20);

    // Translate the geometry to its position
    geometry.translate(pos[1], 0, pos[0]);

    final posAttr = geometry.attributes['position'] as tmath.BufferAttribute;
    final normAttr = geometry.attributes['normal'] as tmath.BufferAttribute;

    // Copy positions and normals
    for (int i = 0; i < posAttr.count; i++) {
      mergedPositions.add(posAttr.getX(i)!.toDouble());
      mergedPositions.add(posAttr.getY(i)!.toDouble());
      mergedPositions.add(posAttr.getZ(i)!.toDouble());
    }

    for (int i = 0; i < normAttr.count; i++) {
      mergedNormals.add(normAttr.getX(i)!.toDouble());
      mergedNormals.add(normAttr.getY(i)!.toDouble());
      mergedNormals.add(normAttr.getZ(i)!.toDouble());
    }

    if (geometry.index != null) {
      final idx = geometry.index!;
      for (int i = 0; i < idx.count; i++) {
        mergedIndices.add(idx.getX(i)!.toInt() + indexOffset);
      }
    } else {
      for (int i = 0; i < posAttr.count; i++) {
        mergedIndices.add(i + indexOffset);
      }
    }

    indexOffset += posAttr.count;
  }

  // Set attributes and index
  mergedGeometry.setAttributeFromString('position', tmath.Float32BufferAttribute.fromList(mergedPositions, 3));
  mergedGeometry.setAttributeFromString('normal', tmath.Float32BufferAttribute.fromList(mergedNormals, 3));
  mergedGeometry.setIndex(tmath.Uint16BufferAttribute.fromList(mergedIndices, 1));

  return mergedGeometry;
}


class InstanceMetrics {
  int nextIndex;
  int maxIndex;
  int indexMultiplier;
  late three.InstancedMesh mesh;
  final three.Material material = three.MeshStandardMaterial.fromMap({"color": 0x00FFFFFF, "flatShading": false});
  final three.BufferGeometry geometry;
  final Queue<int> recycledIndices;
  final Map<String, int> nameIndex;
  final Map<String, tmath.Vector3> positionIndex;
  final Map<String, tmath.Euler> rotationIndex;
  final Map<String, Color> colorIndex;
  final three.Object3D dummy = three.Object3D();
  final three.ThreeJS threeJs;

  InstanceMetrics({required this.geometry, required this.threeJs, this.nextIndex = 0, this.maxIndex = 1000, this.indexMultiplier = 1000})
      : recycledIndices = Queue<int>(),
        nameIndex = {},
        positionIndex = {},
        rotationIndex = {},
        colorIndex = {}
  {
    createMesh();
  }

  void createMesh({bool updateOld=false}){
    if (updateOld){
      threeJs.scene.remove(mesh);
    }
    mesh = three.InstancedMesh(geometry, material, maxIndex);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    final colors = tmath.Float32Array(maxIndex * 3);
    final colorAttr = tmath.InstancedBufferAttribute(colors, 3);
    mesh.instanceColor = colorAttr;

    final initDummy = three.Object3D();
    initDummy.position.setValues(99999, 99999, 99999); // place out of sight
    initDummy.rotation.set(0, 0, 0);
    initDummy.updateMatrix();
    for (int i = 0; i < maxIndex; i++) {
      mesh.setMatrixAt(i, initDummy.matrix);
    }

    threeJs.scene.add(mesh);
  }

  void _expandCapacity(int newCapacity) {
    if (newCapacity <= maxIndex) return;

    // Backup old state
    final oldNameIndex = Map<String, int>.from(nameIndex);
    final oldPositionIndex = Map<String, tmath.Vector3>.from(positionIndex);
    final oldRotationIndex = Map<String, tmath.Euler>.from(rotationIndex);
    final oldColorIndex = Map<String, Color>.from(colorIndex);

    maxIndex = newCapacity;
    recycledIndices.clear();
    nameIndex.clear();
    positionIndex.clear();
    rotationIndex.clear();
    colorIndex.clear();

    createMesh(updateOld: true);

    // Reapply old instance data
    for (final entry in oldNameIndex.entries) {


      final name = entry.key;

      // Allocate the old index
      nameIndex[name] = entry.value;

      // Restore position/rotation
      final position = oldPositionIndex[name]!;
      final rotation = oldRotationIndex[name]!;

      setPositionRotation(name, position, rotation);

      // Restore color
      final color = oldColorIndex[name];
      if (color != null) {
        setColor(name, color);
      }
    }
  }

  /// Allocates an index, reusing recycled ones if available.
  int allocateIndex(String name) {
    if (nameIndex.containsKey(name)) {
      return nameIndex[name]!;
    }

    int index;
    if (recycledIndices.isNotEmpty) {
      index = recycledIndices.removeFirst();
    } else if (nextIndex < maxIndex) {
      index = nextIndex++;
    } else {
      _expandCapacity(maxIndex + indexMultiplier);
      index = nextIndex++;
    }

    nameIndex[name] = index;
    return index;
  }

  void setPositionRotation(String name, tmath.Vector3 position, tmath.Euler rotation){
    positionIndex[name] = position;
    rotationIndex[name] = rotation;
    dummy.position = position;
    dummy.rotation.set(rotation.x, rotation.y, rotation.z);
    dummy.updateMatrix();

    mesh.setMatrixAt(nameIndex[name]!, dummy.matrix.clone());
    mesh.instanceMatrix?.needsUpdate = true;
  }

  void setPosition(String name, tmath.Vector3 position) {
    positionIndex[name] = position;
    dummy.position = position;
    dummy.updateMatrix();
    mesh.setMatrixAt(nameIndex[name]!, dummy.matrix.clone());
    mesh.instanceMatrix?.needsUpdate = true;
  }

  void setRotation(String name, tmath.Euler rotation) {
    rotationIndex[name] = rotation;
    dummy.rotation.set(rotation.x, rotation.y, rotation.z);
    dummy.updateMatrix();
    mesh.setMatrixAt(nameIndex[name]!, dummy.matrix.clone());
    mesh.instanceMatrix?.needsUpdate = true;
  }

  void setColor(String name, Color color) {
    colorIndex[name] = color;
    mesh.instanceColor?.setXYZ(nameIndex[name]!, color.r, color.g, color.b);
    mesh.instanceColor!.needsUpdate = true;
  }

  void hideAndRecycle(String name){
    dummy.position.setValues(99999, 99999, 99999); // place out of sight
    dummy.updateMatrix();
    mesh.setMatrixAt(nameIndex[name]!, dummy.matrix.clone());
    mesh.instanceMatrix?.needsUpdate = true;
    recycleIndex(name);
  }

  /// Recycles a previously used index and removes its name mapping.
  void recycleIndex(String name) {
    final index = nameIndex.remove(name);
    positionIndex.remove(name);
    rotationIndex.remove(name);
    colorIndex.remove(name);

    if (index != null) {
      recycledIndices.add(index);
    }
  }

  void recycleAllIndices(){
    dummy.position.setValues(99999, 99999, 99999); // place out of sight
    dummy.updateMatrix();
    for (var name in nameIndex.keys.toList()) {
      final index = nameIndex.remove(name);
      positionIndex.remove(name);
      rotationIndex.remove(name);
      colorIndex.remove(name);

      if (index != null) {
        recycledIndices.add(index);
      }

      mesh.setMatrixAt(index!, dummy.matrix.clone());
      mesh.instanceMatrix?.needsUpdate = true;
    }
  }

  /// Gets the index for a given name, or null if not found.
  int? getIndex(String name) => nameIndex[name];

  tmath.Vector3? getPosition(String name) => positionIndex[name];

  tmath.Euler? getRotation(String name) => rotationIndex[name];

  Color? getColor(String name) => colorIndex[name];

  /// Checks if an index is currently available.
  bool hasAvailable() => recycledIndices.isNotEmpty || nextIndex < maxIndex;
}


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
  Map<String, Map<String, String>> handleIDs = {};

  // instancing preparation
  Map<String, InstanceMetrics> instanceManager = {};

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

  @override
  void initState() {
    threeJs = three.ThreeJS(
        onSetupComplete: () {
          setState(() {
            isSetupComplete = true;
          });
        },
        setup: setup,
        settings: three.Settings(
          // useOpenGL: true,
            renderOptions: {
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

    // main shadow-generating camera
    final dirLight1 = three.DirectionalLight(0xffffff, 0.8);
    dirLight1.position.setValues(0, 200, 0);
    dirLight1.castShadow = true;
    final shadowCam = dirLight1.shadow?.camera as three.OrthographicCamera;
    shadowCam.left = -500;
    shadowCam.right = 500;
    shadowCam.top = 500;
    shadowCam.bottom = -500;
    shadowCam.near = 0.5;
    shadowCam.far = 1000;
    shadowCam.updateProjectionMatrix();
    threeJs.scene.add(dirLight1);

    // ambient light (to light up underside of design)
    final ambientLight = three.AmbientLight(0xffffff, 0.3);

    threeJs.scene.add(ambientLight);

    threeJs.renderer?.shadowMap.type = tmath.PCFSoftShadowMap; // to generate soft shadows

    threeJs.renderer?.shadowMap.enabled = true;

    threeJs.addAnimationEvent((dt){
      controls.update();
      // logCameraDetails();
    });

    // preparing instancing meshes for slats and handles
    var baseSlatGeometry = CylinderGeometry(2.5, 2.5, gridSize * 32, 20); // actual size should be 310, but adding an extra 10 to improve visuals

    instanceManager['slat'] = InstanceMetrics(geometry: baseSlatGeometry, threeJs: threeJs, maxIndex: 1000);
    instanceManager['honeyCombSlat'] = InstanceMetrics(geometry: createHoneyCombSlat(helixBundlePositions, helixBundleSize, gridSize), threeJs: threeJs, maxIndex: 1000);

    instanceManager['honeyCombAssHandle'] = InstanceMetrics(geometry: CylinderGeometry(0.8, 0.8, 1.5, 8), threeJs: threeJs, maxIndex: 10000);
    instanceManager['assHandle'] = InstanceMetrics(geometry: CylinderGeometry(2, 2, 1.5, 8), threeJs: threeJs, maxIndex: 10000);
    instanceManager['cargoHandle'] = InstanceMetrics(geometry: three.BoxGeometry(4, 6, 4), threeJs: threeJs, maxIndex: 1000);
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

  void positionSlatInstance(String name, Color color, double slatAngle, double height, double centerX, double centerZ){

    var position = tmath.Vector3(centerX, height, centerZ);
    var rotation = tmath.Euler(0, -slatAngle, math.pi / 2);

    if (helixBundleView){
      instanceManager['honeyCombSlat']!.allocateIndex(name);
      instanceManager['honeyCombSlat']!.setPositionRotation(name, position, rotation);
      instanceManager['honeyCombSlat']!.setColor(name, color);
    }
    else {

      instanceManager['slat']!.allocateIndex(name);
      instanceManager['slat']!.setPositionRotation(name, position, rotation);
      instanceManager['slat']!.setColor(name, color);
    }
  }

  void positionHandleInstance(String slatName, String name, Offset position, Color color, double zOrder, String topSide, String handleSide, String handleType, bool updateOnly){
    /// Creates or updates a handle graphic in the 3D scene.

    double verticalOffset = (topSide == handleSide) ? 2.5 : -2.5;
    if (handleType == 'Cargo'){
      verticalOffset += (topSide == handleSide) ? 2 : -2;
    }

    var vecPosition = tmath.Vector3(position.dx, (zOrder * 6.5) + verticalOffset, position.dy);
    var euRotation = tmath.Euler(0, 0, math.pi);

    String instanceType;
    if (handleType == 'Cargo') {
      instanceType = 'cargoHandle';
    }
    else{
      if (helixBundleView){
        instanceType = 'honeyCombAssHandle';
      }
      else{
        instanceType = 'assHandle';
      }
    }

    if (updateOnly) {
      // in the situation where the handle changes type, delete the old one and prepare for a new handle type
      if (instanceManager[instanceType]!.getIndex(name) == null) {
        instanceManager[handleIDs[slatName]![name]]!.hideAndRecycle(name);
        handleIDs[slatName]![name] = instanceType;
      }
      else {
        // trigger an update if the handle position or color changes (e.g. due to a slat moving)
        tmath.Vector3 currentPosition = instanceManager[instanceType]!.getPosition(name)!;
        Color currentColor = instanceManager[instanceType]!.getColor(name)!;
        if (approxEqual(currentPosition.x, vecPosition.x) &&
            approxEqual(currentPosition.y, vecPosition.y) &&
            approxEqual(currentPosition.z, vecPosition.z) &&
            currentColor == color) {
          return;
        }
      }
    }
    else{
      handleIDs[slatName]![name] = instanceType; // prepare a new handle
    }
    // execute handle positioning and color setup
    instanceManager[instanceType]!.allocateIndex(name);
    instanceManager[instanceType]!.setPositionRotation(name, vecPosition, euRotation);
    instanceManager[instanceType]!.setColor(name, color);
  }

  void handleAssembly(Slat slat, int handlePosition, Offset position, int color, double order, String topSide, String handleSide, Map<String, Map<String, dynamic>> layerMap, Map<String, Cargo> cargoPalette) {
    /// Adds, deletes or updates all handles for a slat (both H2 and H5)
    final handleName = '${slat.id}-handle-$handlePosition-$handleSide';

    if (!handleIDs.containsKey(slat.id)) {
      handleIDs[slat.id] = {};
    }

    bool handleInstanceExists = handleIDs[slat.id]!.containsKey(handleName);

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
      positionHandleInstance(slat.id, handleName, position, handleType == 'Assembly' ? layerMap[slat.layer]!['color']: cargoPalette[cargoName]!.color, order, topSide, handleSide, handleType, handleInstanceExists);
    } else if (handleInstanceExists){
      // Remove handle if it was deleted from the slat but still lingering in the scene (or if the assembly handle view has been turned off)
      instanceManager[handleIDs[slat.id]![handleName]]!.hideAndRecycle(handleName);
      handleIDs[slat.id]!.remove(handleName);
    }
  }


  void manageHandles(Slat baseSlat, Map<String, Map<String, dynamic>> layerMap, Map<String, Cargo> cargoPalette) {
    /// Adds, updates or removes assembly handles from the 3D scene based on the current state of the slat.

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
        layerMap,
        cargoPalette
      );
      handleAssembly(
        baseSlat,
        i,
        convertCoordinateSpacetoRealSpace(baseSlat.slatPositionToCoordinate[i]!, gridMode, gridSize, x60Jump, y60Jump),
        color,
        order,
        topSide,
        'H5',
        layerMap,
        cargoPalette
      );
    }
  }

  /// Adds all provided slats into the 3D scene, updating existing slats if necessary.
  void manageSlats(List<Slat> slats, Map<String, Map<String, dynamic>> layerMap, Map<String, Cargo> cargoPalette){

    if (!isSetupComplete || threeJs.scene == null) return;

    Set localIDs = slats.map((slat) => slat.id).toSet();

    Set removedIDs = slatIDs.difference(localIDs);

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
      Offset slatExtend = calculateSlatExtend(p1, p2, 2 * (gridSize * 32 / 2 - gridSize / 2));

      String slatType = helixBundleView ? 'honeyCombSlat' : 'slat';

      if (instanceManager[slatType]?.getIndex(slat.id) == null) {
        slatIDs.add(slat.id);
        positionSlatInstance(slat.id, layerMap[slat.layer]?['color'], slatAngle,
            layerMap[slat.layer]?['order'].toDouble() * 6.5,
            p1.dx + slatExtend.dx, p1.dy + slatExtend.dy);
      }

      else {
        double incomingSlatAngle = -slatAngle;
        double incomingPositionZ = p1.dy + slatExtend.dy;
        double incomingPositionX = p1.dx + slatExtend.dx;
        double incomingLayer = layerMap[slat.layer]?['order'].toDouble() * 6.5;

        tmath.Vector3 currentPosition = instanceManager[slatType]!.getPosition(
            slat.id)!;
        tmath.Euler currentRotation = instanceManager[slatType]!.getRotation(
            slat.id)!;
        Color currentColor = instanceManager[slatType]!.getColor(slat.id)!;

        if (!approxEqual(currentPosition.x, incomingPositionX) ||
            !approxEqual(currentPosition.y, incomingLayer) ||
            !approxEqual(currentPosition.z, incomingPositionZ) ||
            !approxEqual(currentRotation.y, incomingSlatAngle) ||
            currentColor != layerMap[slat.layer]?['color']) {
          positionSlatInstance(
              slat.id, layerMap[slat.layer]?['color'], slatAngle, incomingLayer,
              incomingPositionX, incomingPositionZ);
        }
      }
      manageHandles(slat, layerMap, cargoPalette);
    }
  }

  /// Removes a slat from the 3D scene
  void removeSlat(String id){
    if (helixBundleView) {
      instanceManager['honeyCombSlat']!.hideAndRecycle(id);
    }
    else{
      instanceManager['slat']!.hideAndRecycle(id);
    }
    if (handleIDs.containsKey(id)) {
      for (var handleInstance in handleIDs[id]!.entries) {
        instanceManager[handleInstance.value]!.hideAndRecycle(handleInstance.key);
      }
      handleIDs.remove(id);
    }
  }

  void clearScene() {
    instanceManager['slat']!.recycleAllIndices();
    instanceManager['honeyCombSlat']!.recycleAllIndices();
    instanceManager['cargoHandle']!.recycleAllIndices();
    instanceManager['honeyCombAssHandle']!.recycleAllIndices();
    instanceManager['assHandle']!.recycleAllIndices();
    slatIDs.clear();
    handleIDs.clear();
  }

  void centerOnSlats(InstanceMetrics slatInstances){
    if (!isSetupComplete) return;

    final positions = slatInstances.positionIndex;
    final rotations = slatInstances.rotationIndex;
    if (positions.isEmpty) return;

    // Get local geometry bounding box
    final localBox = tmath.BoundingBox();
    localBox.setFromBuffer(slatInstances.geometry.attributes["position"]!);

    // Start global bounding box
    final boundingBox = tmath.BoundingBox();

    // Reuse a dummy Object3D to apply transforms
    final dummy = three.Object3D();

    for (final name in positions.keys) {
      final position = positions[name]!;
      final rotation = rotations[name] ?? tmath.Euler(0, 0, 0);

      dummy.position = position;
      dummy.rotation.set(rotation.x, rotation.y, rotation.z);
      dummy.updateMatrix();

      // Transform a clone of the local box
      final transformedBox = localBox.clone();
      transformedBox.applyMatrix4(dummy.matrix);

      // Merge into global bounding box
      boundingBox.expandByPoint(transformedBox.min);
      boundingBox.expandByPoint(transformedBox.max);
    }

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
                      clearScene();
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
                  onPressed: () {
                    centerOnSlats(instanceManager[helixBundleView ? 'honeyCombSlat' : 'slat']!);
                  },
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

