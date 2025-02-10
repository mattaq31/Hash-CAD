import 'dart:math' as math;
import 'crisscross_core/slats.dart';
import 'shared_app_state.dart';

import 'package:flutter/material.dart';
import 'package:three_js_controls/three_js_controls.dart';
import 'package:three_js_core/three_js_core.dart' as three;
import 'package:three_js_geometry/three_js_geometry.dart';
import 'package:three_js_math/three_js_math.dart' as tmath;
import 'package:provider/provider.dart';

class ThreeDisplay extends StatefulWidget {
  const ThreeDisplay({super.key});

  @override
  State<ThreeDisplay> createState() => _ThreeDisplay();
}

class _ThreeDisplay extends State<ThreeDisplay> {
  late three.ThreeJS threeJs;
  bool isSetupComplete = false;

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

  late three.Mesh mesh;
  late OrbitControls controls;

  void setup(){
    threeJs.scene = three.Scene();
    threeJs.scene.background = tmath.Color.fromHex32(0xffffff);

    threeJs.camera = three.PerspectiveCamera(70, threeJs.width / threeJs.height, 1, 10000);

    threeJs.camera.position.setValues(749, 186, 1043);
    controls = OrbitControls(threeJs.camera, threeJs.globalKey);
    controls.target.setValues(791, -8, 690);

    controls.enableDamping = true; // an animation loop is required when either damping or auto-rotation are enabled
    controls.dampingFactor = 0.05;

    controls.screenSpacePanning = false;

    controls.minDistance = 100;
    // controls.maxDistance = 1000;

    controls.maxPolarAngle = math.pi / 2;

    // TODO: set better lighting
    final dirLight1 = three.DirectionalLight(0xffffff, 0.5);
    dirLight1.position.setValues(1, 1, 1);
    threeJs.scene.add(dirLight1);

    final dirLight2 = three.DirectionalLight(0x002288, 0.3);
    dirLight2.position.setValues(-1, -1, -1);
    threeJs.scene.add(dirLight2);

    final ambientLight = three.AmbientLight(0x222222);
    threeJs.scene.add(ambientLight);

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

  void addSlats(List<Slat> slats, List<Map<String, dynamic>> layerList){

    for (var slat in slats) {
      if (threeJs.scene.getObjectByName(slat.id) == null) {
        final geometry = CylinderGeometry(2.5, 2.5, 320, 60); // actual size should be 310, but adding an extra 10 to improve visuals
        final material = three.MeshPhongMaterial.fromMap({"color": layerList[slat.layer]['color'].value & 0x00FFFFFF, "flatShading": true});
        final mesh = three.Mesh(geometry, material);
        mesh.name = slat.id;

        mesh.position.y = slat.layer.toDouble() * 6.5;
        mesh.rotation.z = math.pi / 2;

        if (layerList[slat.layer]['direction'] == 'vertical') {
          mesh.rotation.y = -math.pi/2;
          mesh.position.z = slat.slatPositionToCoordinate[1]!.dy + 320/2 - 5;
          mesh.position.x = slat.slatPositionToCoordinate[1]!.dx;
        }
        else{
          mesh.rotation.y = 0;
          mesh.position.x = slat.slatPositionToCoordinate[1]!.dx + 320/2 - 5;
          mesh.position.z = slat.slatPositionToCoordinate[1]!.dy;
        }

          mesh.updateMatrix();
        mesh.matrixAutoUpdate = false;
        threeJs.scene.add(mesh);
      }
    }
    // TODO: add centering system to zoom in on all slats if user desires
  }

  void onResize(double width, double height) {

    if (!mounted || width <= 0 || height <= 0 || !isSetupComplete) return; // Ensure widget is still available

    if (threeJs.camera != null && threeJs.renderer != null) {
      threeJs.camera.aspect = width / height;
      threeJs.camera.updateProjectionMatrix();
      threeJs.renderer?.setSize(width, height, true);
    }
  }

  @override
  Widget build(BuildContext context) {
    
    return Consumer<MyAppState>(
      builder: (context, appState, child) {
        addSlats(appState.slats, appState.layerList);
        return LayoutBuilder(
          builder: (context, constraints) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              onResize(constraints.maxWidth, constraints.maxHeight);
            });
            return threeJs.build();
          },
        );
      }
    );
  }

}

