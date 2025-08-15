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
import '../main_windows/floating_switches.dart';
import './custom_3d_meshes.dart';
import '../crisscross_core/seed.dart';


bool approxEqual(double a, double b, [double epsilon = 1e-4]) {
  return (a - b).abs() < epsilon;
}

String seedKeyToString((String, String, Offset) key) {
  final offset = key.$3;
  // Round coordinates to avoid float precision issues in string
  return '${key.$1}_${key.$2}_${offset.dx.toStringAsFixed(2)}x${offset.dy.toStringAsFixed(2)}';
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
  final Map<String, tmath.Vector3> scaleIndex;
  final Map<String, Color> colorIndex;
  final three.Object3D dummy = three.Object3D();
  final three.ThreeJS threeJs;

  InstanceMetrics({required this.geometry, required this.threeJs, this.nextIndex = 0, this.maxIndex = 1000, this.indexMultiplier = 1000})
      : recycledIndices = Queue<int>(),
        nameIndex = {},
        positionIndex = {},
        rotationIndex = {},
        scaleIndex = {},
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
    mesh.frustumCulled = false;
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
    final oldScaleIndex = Map<String, tmath.Vector3>.from(scaleIndex);
    final oldColorIndex = Map<String, Color>.from(colorIndex);

    maxIndex = newCapacity;
    recycledIndices.clear();
    nameIndex.clear();
    positionIndex.clear();
    rotationIndex.clear();
    colorIndex.clear();
    scaleIndex.clear();

    createMesh(updateOld: true);

    // Reapply old instance data
    for (final entry in oldNameIndex.entries) {
      final name = entry.key;
      // Allocate the old index
      nameIndex[name] = entry.value;

      // Restore position/rotation
      final position = oldPositionIndex[name]!;
      final rotation = oldRotationIndex[name]!;
      final scale = oldScaleIndex[name] ?? tmath.Vector3(1, 1, 1); // Default scale to 1 if not set

      setPositionRotationScale(name, position, rotation, scale);

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

  void setPositionRotationScale(String name, tmath.Vector3 position, tmath.Euler rotation, tmath.Vector3 scale) {
    positionIndex[name] = position;
    rotationIndex[name] = rotation;
    scaleIndex[name] = scale;

    dummy.position = position;
    dummy.rotation.set(rotation.x, rotation.y, rotation.z);
    dummy.scale = scale;
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

  void setScale(String name, tmath.Vector3 scale) {
    scaleIndex[name] = scale;
    dummy.scale = scale;
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
    if (!nameIndex.containsKey(name)) {
      return; // Name not found, nothing to recycle
    }
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
    scaleIndex.remove(name);
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
      scaleIndex.remove(name);
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

  tmath.Vector3? getScale(String name) => scaleIndex[name];

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
  Set<(String, String, Offset)> seedIDs = {};
  Map<String, Map<String, String>> handleIDs = {};

  // instancing preparation
  Map<String, InstanceMetrics> instanceManager = {};

  double gridSize = 10;
  late double y60Jump = gridSize / 2;
  late double x60Jump = math.sqrt(math.pow(gridSize, 2) - math.pow(y60Jump, 2));
  String gridMode = '60';
  String lastGridMode = '60';

  bool assemblyHandleView = false;
  bool cargoHandleView = true;
  bool seedHandleView = true;
  bool slatTipExtendView = true;

  bool gridView = true;
  GridHelper gridHelper = GridHelper(1000, 50); // Grid size: 1000, 50 divisions
  AxesHelper axesHelper = AxesHelper(1000);

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

    if (gridView){
      threeJs.scene.add(gridHelper);
      threeJs.scene.add(axesHelper);
    }

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

    // preparing instancing meshes for slats, seeds and handles
    instanceManager['slat'] = InstanceMetrics(geometry: CylinderGeometry(2.5, 2.5, gridSize * 32, 20), threeJs: threeJs, maxIndex: 1000); // actual size should be 310, but adding an extra 10 to improve visuals
    instanceManager['slatShort'] = InstanceMetrics(geometry: CylinderGeometry(2.5, 2.5, gridSize * 31, 20), threeJs: threeJs, maxIndex: 1000);

    instanceManager['honeyCombSlat'] = InstanceMetrics(geometry: createHoneyCombSlat(helixBundlePositions, helixBundleSize, gridSize, true), threeJs: threeJs, maxIndex: 1000);
    instanceManager['honeyCombSlatShort'] = InstanceMetrics(geometry: createHoneyCombSlat(helixBundlePositions, helixBundleSize, gridSize, false), threeJs: threeJs, maxIndex: 1000);

    instanceManager['honeyCombAssHandle'] = InstanceMetrics(geometry: CylinderGeometry(0.8, 0.8, 1.5, 8), threeJs: threeJs, maxIndex: 10000);
    instanceManager['assHandle'] = InstanceMetrics(geometry: CylinderGeometry(2, 2, 1.5, 8), threeJs: threeJs, maxIndex: 10000);
    instanceManager['cargoHandle'] = InstanceMetrics(geometry: three.BoxGeometry(4, 6, 4), threeJs: threeJs, maxIndex: 1000);

    // prepares mesh instances of the different seed variants (normal, 60deg and 60deg inverted)
    var dummySeed = Seed(ID: 'dummy1', coordinates: generateBasicSeedCoordinates(16, 5, 10, false, false));
    var dummyTiltSeed = Seed(ID: 'dummy2', coordinates: generateBasicSeedCoordinates(16, 5, 10, true, false));
    var dummyTiltSeedInvert = Seed(ID: 'dummy3', coordinates: generateBasicSeedCoordinates(16, 5, 10, true, true));

    var seedGeometry = createSeedTubeGeometry(
      dummySeed.coordinates,
      gridSize,
      dummySeed.rotationAngle!,
      dummySeed.transverseAngle!,
      16,
      5,
      1.5,
    );
    var tiltSeedGeometry = createSeedTubeGeometry(
      dummyTiltSeed.coordinates,
      gridSize,
      dummyTiltSeed.rotationAngle!,
      dummyTiltSeed.transverseAngle!,
      16,
      5,
      1.5,
    );
    var tiltSeedGeometryInvert = createSeedTubeGeometry(
      dummyTiltSeedInvert.coordinates,
      gridSize,
      dummyTiltSeedInvert.rotationAngle!,
      dummyTiltSeedInvert.transverseAngle!,
      16,
      5,
      1.5,
    );

    instanceManager['seed'] = InstanceMetrics(geometry: seedGeometry, threeJs: threeJs, maxIndex: 20);
    instanceManager['tiltSeed'] = InstanceMetrics(geometry: tiltSeedGeometry, threeJs: threeJs, maxIndex: 20);
    instanceManager['tiltSeedInvert'] = InstanceMetrics(geometry: tiltSeedGeometryInvert, threeJs: threeJs, maxIndex: 20);

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

    String instanceType;

    if (helixBundleView){
      if (slatTipExtendView){
        instanceType = 'honeyCombSlat';
      }
      else{
        instanceType = 'honeyCombSlatShort';
      }
    }
    else{
      if (slatTipExtendView){
        instanceType = 'slat';
      }
      else{
        instanceType = 'slatShort';
      }
    }

    instanceManager[instanceType]!.allocateIndex(name);
    instanceManager[instanceType]!.setPositionRotation(name, position, rotation);
    instanceManager[instanceType]!.setColor(name, color);

  }

  void positionSeedInstance(String name, Color color, double seedAngle, double transverseAngle, double height, double centerX, double centerZ, bool flip, bool transposeFlip){


    var position = tmath.Vector3(centerX, height, centerZ);
    var rotation = tmath.Euler(0, gridMode == '60' ?  -seedAngle + math.pi/2 : -seedAngle, 0);

    // annoyingly, rotation in x can rotate the seed on either its long or short edge (seems to be related to the gimbal lock problem).
    // Thus, for certain orientations the flip results in the wrong position.  Below, I manually patched the incorrect orientations using specific offsets.
    // A more elegant solution could potentially be to use quaternions, but this would require further research.
    if (!flip && gridMode == '90'){
      rotation.x = math.pi;
      if (approxEqual(seedAngle, math.pi/2) || approxEqual(seedAngle, -math.pi/2)){
        rotation.y += math.pi;
      }
    }

    // also annoying is the fact that flips in 90 and 60 degree modes need to be handled differently...
    if (((flip && !transposeFlip) || (!flip && transposeFlip)) && gridMode == '60'){
      rotation.x = math.pi;
      rotation.y = seedAngle + math.pi/2;
    }

    String instanceType = gridMode == '60' ? (transposeFlip ? 'tiltSeedInvert':'tiltSeed') : 'seed';

    instanceManager[instanceType]!.allocateIndex(name);
    instanceManager[instanceType]!.setPositionRotation(name, position, rotation);
    instanceManager[instanceType]!.setColor(name, color);

  }

  void positionHandleInstance(String slatName, String name, Offset position, Color color, double zOrder, String topSide, String handleSide, String handleType, bool updateOnly){
    /// Creates or updates a handle graphic in the 3D scene.

    double verticalOffset = (topSide == handleSide) ? 2.5 : -2.5;

    if (handleType == 'CARGO'){
      verticalOffset += (topSide == handleSide) ? 2 : -2;
    }

    var vecPosition = tmath.Vector3(position.dx, (zOrder * 6.5) + verticalOffset, position.dy);
    var euRotation = tmath.Euler(0, 0, math.pi);

    String instanceType;
    if (handleType == 'CARGO') {
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
    String handleType = 'ASSEMBLY_HANDLE';
    var cargoName = 'X';

    if (handleSide == 'H5'){
      existingHandle = slat.h5Handles.containsKey(handlePosition);
      if (existingHandle) {
        handleType = slat.h5Handles[handlePosition]!['category'];
        cargoName = slat.h5Handles[handlePosition]!['value'];
      }
    }
    else if (handleSide == 'H2'){
      existingHandle = slat.h2Handles.containsKey(handlePosition);
      if (existingHandle) {
        handleType = slat.h2Handles[handlePosition]!['category'];
        cargoName = slat.h2Handles[handlePosition]!['value'];
      }
    }

    if (existingHandle && (assemblyHandleView && handleType.contains('ASSEMBLY') || cargoHandleView && handleType == 'CARGO' || seedHandleView && handleType == 'SEED')) {
      Color color = handleType.contains('ASSEMBLY') ? layerMap[slat.layer]!['color']: handleType == 'CARGO' ? cargoPalette[cargoName]!.color: cargoPalette['SEED']!.color;
      positionHandleInstance(slat.id, handleName, position, color, order, topSide, handleSide, handleType, handleInstanceExists);
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

      Color mainColor = slat.uniqueColor ?? layerMap[slat.layer]?['color'];

      var p1 = convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[1]!, gridMode, gridSize, x60Jump, y60Jump);
      var p2 = convertCoordinateSpacetoRealSpace(slat.slatPositionToCoordinate[32]!, gridMode, gridSize, x60Jump, y60Jump);
      // same angle/extension system used here as in 2D system

      double slatAngle = calculateSlatAngle(p1, p2);
      Offset slatExtend = calculateSlatExtend(p1, p2, 2 * (gridSize * 32 / 2 - gridSize / 2));

      double finalX = p1.dx + slatExtend.dx;
      double finalY = p1.dy + slatExtend.dy;

      String slatType = helixBundleView ? 'honeyCombSlat' : 'slat';

      if (instanceManager[slatType]?.getIndex(slat.id) == null) {
        slatIDs.add(slat.id);
        positionSlatInstance(slat.id, mainColor, slatAngle,
            layerMap[slat.layer]?['order'].toDouble() * 6.5,
            finalX, finalY);
      }

      else {
        double incomingSlatAngle = -slatAngle;
        double incomingPositionZ = p1.dy + slatExtend.dy;
        double incomingPositionX = p1.dx + slatExtend.dx;
        double incomingLayer = layerMap[slat.layer]?['order'].toDouble() * 6.5;

        tmath.Vector3 currentPosition = instanceManager[slatType]!.getPosition(slat.id)!;
        tmath.Euler currentRotation = instanceManager[slatType]!.getRotation(slat.id)!;
        Color currentColor = instanceManager[slatType]!.getColor(slat.id)!;

        if (!approxEqual(currentPosition.x, incomingPositionX) ||
            !approxEqual(currentPosition.y, incomingLayer) ||
            !approxEqual(currentPosition.z, incomingPositionZ) ||
            !approxEqual(currentRotation.y, incomingSlatAngle) ||
            currentColor != mainColor) {
          positionSlatInstance(
              slat.id, mainColor, slatAngle, incomingLayer,
              incomingPositionX, incomingPositionZ);
        }
      }
      manageHandles(slat, layerMap, cargoPalette);
    }
  }

  void manageSeeds(Map<(String, String, Offset), Seed> seedRoster, Map<String, Map<String, dynamic>> layerMap, Color color){
    if (!isSetupComplete || threeJs.scene == null) return;

    if (gridMode != lastGridMode){
      instanceManager['seed']!.recycleAllIndices();
      instanceManager['tiltSeed']!.recycleAllIndices();
      instanceManager['tiltSeedInvert']!.recycleAllIndices();
      lastGridMode = gridMode;
      seedIDs.clear();
    }

    Set localIDs = seedRoster.keys.toSet();
    Set removedIDs = seedIDs.difference(localIDs);

    // deletes seeds that are no longer in the design
    for (var id in removedIDs) {
      var removedID = seedKeyToString(id);
      if (gridMode == '60') {
        instanceManager['tiltSeed']!.hideAndRecycle(removedID);
        instanceManager['tiltSeedInvert']!.hideAndRecycle(removedID);
      }
      else{
        instanceManager['seed']!.hideAndRecycle(removedID);
      }
      seedIDs.remove(id);
    }

    // TODO: if this becomes laggy, can consider only updating seeds if they've changed position/color/etc
    for (var seed in seedRoster.entries) {
      positionSeedInstance(
          seedKeyToString(seed.key),
          color,
          seed.value.rotationAngle!.toDouble() * (math.pi / 180),
          seed.value.transverseAngle!.toDouble() * (math.pi / 180),
          (layerMap[seed.key.$1]?['order'].toDouble()) * 6.5 + ((seed.key.$2 == 'top' ? 1 : -1) * 4.3),
          seed.value.coordinates[1]!.dx,
          seed.value.coordinates[1]!.dy,
          seed.value.tiltFlip!,
          seed.value.transposeFlip!);
      seedIDs.add(seed.key);
    }
  }

  /// Removes a slat from the 3D scene
  void removeSlat(String id){

    instanceManager['honeyCombSlat']!.hideAndRecycle(id);
    instanceManager['honeyCombSlatShort']!.hideAndRecycle(id);
    instanceManager['slat']!.hideAndRecycle(id);
    instanceManager['slatShort']!.hideAndRecycle(id);

    if (handleIDs.containsKey(id)) {
      for (var handleInstance in handleIDs[id]!.entries) {
        instanceManager[handleInstance.value]!.hideAndRecycle(handleInstance.key);
      }
      handleIDs.remove(id);
    }
  }

  void clearScene() {
    instanceManager['slat']!.recycleAllIndices();
    instanceManager['slatShort']!.recycleAllIndices();
    instanceManager['seed']!.recycleAllIndices();
    instanceManager['tiltSeed']!.recycleAllIndices();
    instanceManager['tiltSeedInvert']!.recycleAllIndices();
    instanceManager['honeyCombSlat']!.recycleAllIndices();
    instanceManager['honeyCombSlatShort']!.recycleAllIndices();
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

      gridSize = appState.gridSize;
      gridMode = appState.gridMode;
      y60Jump = appState.y60Jump;
      x60Jump = appState.x60Jump;

      manageSlats(appState.slats.values.toList(), appState.layerMap, appState.cargoPalette);
      manageSeeds(appState.seedRoster, appState.layerMap, appState.cargoPalette['SEED']!.color);

      if (!gridView) {
        threeJs.scene.remove(gridHelper);
        threeJs.scene.remove(axesHelper);
      }
      else{
        if (isSetupComplete && threeJs.scene != null && !threeJs.scene.children.contains(gridHelper)) {
          threeJs.scene.add(gridHelper);
          threeJs.scene.add(axesHelper);
        }
      }

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
            bottom: 20.0,
            right: 15.0,
            child: Row(
              children: [
                buildFabIcon(
                  icon: Icons.hive,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: '6HB display',
                  value: helixBundleView,
                  onChanged: (val) => setState(() {
                    helixBundleView = val;
                    clearScene();
                    manageSlats(appState.slats.values.toList(), appState.layerMap, appState.cargoPalette);
                  }),
                ),
                buildFabIcon(
                  icon: Icons.expand,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Draw Slat Tip Extensions',
                  value: slatTipExtendView,
                  onChanged: (val) => setState(() {
                    slatTipExtendView = val;
                    clearScene();
                    manageSlats(appState.slats.values.toList(), appState.layerMap, appState.cargoPalette);
                  }),
                ),
                buildFabIcon(
                  icon: Icons.developer_board,
                  color: Theme.of(context).colorScheme.primary,
                  tooltip: 'Assembly Handles',
                  value: assemblyHandleView,
                  onChanged: (val) => setState(() {
                    assemblyHandleView = val;
                  }),
                ),
                buildFabIcon(
                  color: Theme.of(context).colorScheme.primary,
                  icon: Icons.warehouse,
                  tooltip: 'Cargo Handles',
                  value: cargoHandleView,
                  onChanged: (val) => setState(() {
                    cargoHandleView = val;
                  }),
                ),
                buildFabIcon(
                  color: Theme.of(context).colorScheme.primary,
                  icon: Icons.spa,
                  tooltip: 'Seed Handles',
                  value: seedHandleView,
                  onChanged: (val) => setState(() {
                    seedHandleView = val;
                  }),
                ),
                buildFabIcon(
                  color: Theme.of(context).colorScheme.primary,
                  icon: Icons.grid_on,
                  tooltip: 'Grid',
                  value: gridView,
                  onChanged: (val) => setState(() {
                    gridView = val;
                  }),
                ),
                Tooltip(
                  message: 'Center View',
                  child: ElevatedButton(
                    onPressed: () {
                      centerOnSlats(instanceManager[helixBundleView ? 'honeyCombSlat' : 'slat']!);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primary,
                      foregroundColor: Colors.white,
                      shape: const CircleBorder(),
                      padding: const EdgeInsets.all(25),
                    ),
                    child: const Icon(Icons.filter_center_focus),
                  ),
                ),
              ],
            ),
          ),
        ],
      );
    });
  }
}

