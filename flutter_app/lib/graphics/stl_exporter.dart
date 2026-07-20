// Exports the 3D view's instanced slat meshes to a binary STL file for 3D printing.
//
// The standard three_js STLBinaryExporter does not handle InstancedMesh objects,
// so this module manually iterates instance transforms and applies them to template
// geometry vertices before writing the STL.

import 'dart:typed_data';

import 'package:three_js_exporters/saveFile/saveFile.dart';
import 'package:three_js_math/three_js_math.dart' as tmath;

import '3d_painter.dart';

/// Default scale: 0.47 mm per internal unit.
/// This makes a standard 32-slot slat (320 internal units) ≈ 150mm (15cm).
const double defaultPrintScaleMmPerUnit = 0.47;

const List<String> _assemblyHandleInstanceNames = ['assHandle', 'honeyCombAssHandle'];
const List<String> _seedInstanceNames = ['seed', 'tiltSeed', 'tiltSeedInvert'];
const List<String> _cargoInstanceNames = ['cargoHandle'];

/// Amount to shrink each cylinder toward its centroid. A 0.1% reduction creates
/// a sub-micron gap between adjacent end-caps, eliminating non-manifold edges
/// without any visible effect on the printed model.
const double _shrinkFactor = 0.999;

/// Exports all visible slat instances as a binary STL file.
///
/// Iterates through each instanced mesh type, transforms template vertices
/// by each allocated instance's matrix, applies scale, and writes binary STL.
/// Each cylinder is shrunk by a tiny amount toward its center to prevent
/// coincident cap faces between adjacent instances.
Future<void> exportDesignToSTL({
  required Map<String, InstanceMetrics> instanceManager,
  required List<String> slatInstanceNames,
  required String designName,
  double scaleFactor = defaultPrintScaleMmPerUnit,
}) async {
  final triangles = <_Triangle>[];

  final allInstanceNames = [...slatInstanceNames, ..._assemblyHandleInstanceNames, ..._seedInstanceNames, ..._cargoInstanceNames];

  // Track exported handle names to avoid duplicates — the same logical handle can
  // exist in both assHandle and honeyCombAssHandle instance managers simultaneously.
  final exportedHandleNames = <String>{};

  for (final instanceName in allInstanceNames) {
    final metrics = instanceManager[instanceName];
    if (metrics == null) continue;

    final bool isAssemblyHandle = _assemblyHandleInstanceNames.contains(instanceName);

    final geometry = metrics.geometry;
    final posAttr = geometry.getAttribute(tmath.Attribute.position);
    final indexAttr = geometry.getIndex();
    if (posAttr == null || indexAttr == null) continue;

    // Extract template vertices
    final int vertexCount = posAttr.count;
    final List<tmath.Vector3> templateVertices = List.generate(vertexCount, (i) {
      return tmath.Vector3(
        posAttr.getX(i)!.toDouble(),
        posAttr.getY(i)!.toDouble(),
        posAttr.getZ(i)!.toDouble(),
      );
    });

    // Extract triangle indices
    final int indexCount = indexAttr.count;
    final List<int> indices = List.generate(indexCount, (i) => indexAttr.getX(i)!.toInt());

    // For each allocated instance, apply its transform and emit triangles
    for (final entry in metrics.nameIndex.entries) {
      final String name = entry.key;
      final int idx = entry.value;

      // Skip hidden/recycled instances (placed at 99999)
      final pos = metrics.positionIndex[name];
      if (pos == null) continue;
      if (pos.x > 90000) continue;

      // Skip duplicate assembly handles (same handle registered in both managers)
      if (isAssemblyHandle) {
        if (exportedHandleNames.contains(name)) continue;
        exportedHandleNames.add(name);
      }

      // Build the 4x4 transform matrix from the stored matrixArray
      final tmath.Matrix4 matrix = tmath.Matrix4.identity();
      final int offset = idx * 16;
      for (int i = 0; i < 16; i++) {
        matrix.storage[i] = metrics.matrixArray[offset + i];
      }

      // Transform each vertex and store.
      // Snap near-zero components to exactly 0.0 — the cylinder geometry has
      // duplicate seam vertices whose matrix products land at slightly different
      // floating-point noise values (e.g. 1.6e-14 vs 1.64e-14), which makes
      // PreForm see non-coincident vertices at shared edges.
      final List<tmath.Vector3> transformed = List.generate(vertexCount, (i) {
        final v = templateVertices[i].clone();
        v.applyMatrix4(matrix);
        v.scale(scaleFactor);
        v.x = _snapToZero(v.x);
        v.y = _snapToZero(v.y);
        v.z = _snapToZero(v.z);
        return v;
      });

      // Shrink each instance toward its centroid to create a sub-micron gap
      // between any adjacent cylinders that would otherwise share a cap face.
      double cx = 0, cy = 0, cz = 0;
      for (final v in transformed) {
        cx += v.x;
        cy += v.y;
        cz += v.z;
      }
      cx /= vertexCount;
      cy /= vertexCount;
      cz /= vertexCount;
      for (final v in transformed) {
        v.x = cx + (v.x - cx) * _shrinkFactor;
        v.y = cy + (v.y - cy) * _shrinkFactor;
        v.z = cz + (v.z - cz) * _shrinkFactor;
      }

      // Emit triangles from index buffer
      for (int i = 0; i < indexCount; i += 3) {
        final v0 = transformed[indices[i]];
        final v1 = transformed[indices[i + 1]];
        final v2 = transformed[indices[i + 2]];
        triangles.add(_Triangle(v0, v1, v2));
      }
    }
  }

  if (triangles.isEmpty) return;

  // Write binary STL
  final bytes = _writeBinarySTL(triangles);
  final fileName = '${designName}_model';
  await SaveFile.saveBytes(printName: fileName, fileType: 'stl', bytes: bytes);
}

/// Snaps values smaller than a single-precision ULP near the model's scale to zero.
double _snapToZero(double v) => v.abs() < 1e-6 ? 0.0 : v;

/// Computes the face normal for a triangle.
tmath.Vector3 _computeNormal(tmath.Vector3 a, tmath.Vector3 b, tmath.Vector3 c) {
  final ab = b.clone()..sub(a);
  final ac = c.clone()..sub(a);
  ab.cross(ac);
  if (ab.x != 0 || ab.y != 0 || ab.z != 0) {
    ab.normalize();
  }
  return ab;
}

/// Writes a list of triangles to binary STL format.
Uint8List _writeBinarySTL(List<_Triangle> triangles) {
  // Binary STL: 80 byte header + 4 byte triangle count + 50 bytes per triangle
  final int bufferLength = 80 + 4 + (triangles.length * 50);
  final ByteData output = ByteData(bufferLength);
  int offset = 80; // skip header (zeroed)

  output.setUint32(offset, triangles.length, Endian.little);
  offset += 4;

  for (final tri in triangles) {
    final normal = _computeNormal(tri.v0, tri.v1, tri.v2);

    output.setFloat32(offset, normal.x, Endian.little); offset += 4;
    output.setFloat32(offset, normal.y, Endian.little); offset += 4;
    output.setFloat32(offset, normal.z, Endian.little); offset += 4;

    output.setFloat32(offset, tri.v0.x, Endian.little); offset += 4;
    output.setFloat32(offset, tri.v0.y, Endian.little); offset += 4;
    output.setFloat32(offset, tri.v0.z, Endian.little); offset += 4;

    output.setFloat32(offset, tri.v1.x, Endian.little); offset += 4;
    output.setFloat32(offset, tri.v1.y, Endian.little); offset += 4;
    output.setFloat32(offset, tri.v1.z, Endian.little); offset += 4;

    output.setFloat32(offset, tri.v2.x, Endian.little); offset += 4;
    output.setFloat32(offset, tri.v2.y, Endian.little); offset += 4;
    output.setFloat32(offset, tri.v2.z, Endian.little); offset += 4;

    output.setUint16(offset, 0, Endian.little); offset += 2; // attribute byte count
  }

  return output.buffer.asUint8List();
}

class _Triangle {
  final tmath.Vector3 v0;
  final tmath.Vector3 v1;
  final tmath.Vector3 v2;
  _Triangle(this.v0, this.v1, this.v2);
}
