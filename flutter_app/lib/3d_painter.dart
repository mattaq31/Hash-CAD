import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:three_js_controls/three_js_controls.dart';
import 'package:three_js_core/three_js_core.dart' as three;
import 'package:three_js_geometry/three_js_geometry.dart';
import 'package:three_js_math/three_js_math.dart' as tmath;

class ThreeDisplay extends StatefulWidget {
  const ThreeDisplay({super.key});

  @override
  State<ThreeDisplay> createState() => _ThreeDisplay();
}

class _ThreeDisplay extends State<ThreeDisplay> {
  late three.ThreeJS threeJs;

  @override
  Widget build(BuildContext context) {
    return threeJs.build();
  }

  @override
  void initState() {
    threeJs = three.ThreeJS(
        onSetupComplete: () {
          setState(() {});
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
    threeJs.scene.background = tmath.Color.fromHex32(0xcccccc);
    threeJs.scene.fog = three.FogExp2(0xcccccc, 0.002);

    threeJs.camera = three.PerspectiveCamera(60, threeJs.width / threeJs.height, 1, 1000);
    threeJs.camera.position.setValues(400, 200, 0);

    controls = OrbitControls(threeJs.camera, threeJs.globalKey);

    controls.enableDamping = true; // an animation loop is required when either damping or auto-rotation are enabled
    controls.dampingFactor = 0.05;

    controls.screenSpacePanning = false;

    controls.minDistance = 100;
    controls.maxDistance = 500;

    controls.maxPolarAngle = math.pi / 2;


    // TO UPDATE
    final geometry = CylinderGeometry(10, 10, 32);
    final material = three.MeshPhongMaterial.fromMap({"color": 0x4B0082, "flatShading": true});

    for (int i = 0; i < 500; i++) {
      final mesh = three.Mesh(geometry, material);
      mesh.position.x = math.Random().nextDouble() * 1600 - 800;
      mesh.position.y = 0;
      mesh.position.z = math.Random().nextDouble() * 1600 - 800;
      mesh.updateMatrix();
      mesh.matrixAutoUpdate = false;
      threeJs.scene.add(mesh);
    }

    final dirLight1 = three.DirectionalLight(0xffffff);
    dirLight1.position.setValues(1, 1, 1);
    threeJs.scene.add(dirLight1);

    final dirLight2 = three.DirectionalLight(0x002288);
    dirLight2.position.setValues(-1, -1, -1);
    threeJs.scene.add(dirLight2);

    final ambientLight = three.AmbientLight(0x222222);
    threeJs.scene.add(ambientLight);

    threeJs.addAnimationEvent((dt){
      controls.update();
    });

  }

}

