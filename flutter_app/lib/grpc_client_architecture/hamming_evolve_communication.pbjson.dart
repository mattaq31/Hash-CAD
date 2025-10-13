//
//  Generated code. Do not modify.
//  source: hamming_evolve_communication.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:convert' as $convert;
import 'dart:core' as $core;
import 'dart:typed_data' as $typed_data;

@$core.Deprecated('Use evolveRequestDescriptor instead')
const EvolveRequest$json = {
  '1': 'EvolveRequest',
  '2': [
    {'1': 'slatArray', '3': 1, '4': 3, '5': 11, '6': '.evoService.Layer3D', '10': 'slatArray'},
    {'1': 'handleArray', '3': 2, '4': 3, '5': 11, '6': '.evoService.Layer3D', '10': 'handleArray'},
    {'1': 'parameters', '3': 3, '4': 3, '5': 11, '6': '.evoService.EvolveRequest.ParametersEntry', '10': 'parameters'},
    {'1': 'slatTypes', '3': 4, '4': 3, '5': 11, '6': '.evoService.EvolveRequest.SlatTypesEntry', '10': 'slatTypes'},
    {'1': 'connectionAngle', '3': 5, '4': 1, '5': 9, '10': 'connectionAngle'},
    {'1': 'coordinateMap', '3': 6, '4': 3, '5': 11, '6': '.evoService.EvolveRequest.CoordinateMapEntry', '10': 'coordinateMap'},
  ],
  '3': [EvolveRequest_ParametersEntry$json, EvolveRequest_SlatTypesEntry$json, EvolveRequest_CoordinateMapEntry$json],
};

@$core.Deprecated('Use evolveRequestDescriptor instead')
const EvolveRequest_ParametersEntry$json = {
  '1': 'ParametersEntry',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'value', '3': 2, '4': 1, '5': 9, '10': 'value'},
  ],
  '7': {'7': true},
};

@$core.Deprecated('Use evolveRequestDescriptor instead')
const EvolveRequest_SlatTypesEntry$json = {
  '1': 'SlatTypesEntry',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'value', '3': 2, '4': 1, '5': 9, '10': 'value'},
  ],
  '7': {'7': true},
};

@$core.Deprecated('Use evolveRequestDescriptor instead')
const EvolveRequest_CoordinateMapEntry$json = {
  '1': 'CoordinateMapEntry',
  '2': [
    {'1': 'key', '3': 1, '4': 1, '5': 9, '10': 'key'},
    {'1': 'value', '3': 2, '4': 1, '5': 11, '6': '.evoService.CoordinateList', '10': 'value'},
  ],
  '7': {'7': true},
};

/// Descriptor for `EvolveRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List evolveRequestDescriptor = $convert.base64Decode(
    'Cg1Fdm9sdmVSZXF1ZXN0EjEKCXNsYXRBcnJheRgBIAMoCzITLmV2b1NlcnZpY2UuTGF5ZXIzRF'
    'IJc2xhdEFycmF5EjUKC2hhbmRsZUFycmF5GAIgAygLMhMuZXZvU2VydmljZS5MYXllcjNEUgto'
    'YW5kbGVBcnJheRJJCgpwYXJhbWV0ZXJzGAMgAygLMikuZXZvU2VydmljZS5Fdm9sdmVSZXF1ZX'
    'N0LlBhcmFtZXRlcnNFbnRyeVIKcGFyYW1ldGVycxJGCglzbGF0VHlwZXMYBCADKAsyKC5ldm9T'
    'ZXJ2aWNlLkV2b2x2ZVJlcXVlc3QuU2xhdFR5cGVzRW50cnlSCXNsYXRUeXBlcxIoCg9jb25uZW'
    'N0aW9uQW5nbGUYBSABKAlSD2Nvbm5lY3Rpb25BbmdsZRJSCg1jb29yZGluYXRlTWFwGAYgAygL'
    'MiwuZXZvU2VydmljZS5Fdm9sdmVSZXF1ZXN0LkNvb3JkaW5hdGVNYXBFbnRyeVINY29vcmRpbm'
    'F0ZU1hcBo9Cg9QYXJhbWV0ZXJzRW50cnkSEAoDa2V5GAEgASgJUgNrZXkSFAoFdmFsdWUYAiAB'
    'KAlSBXZhbHVlOgI4ARo8Cg5TbGF0VHlwZXNFbnRyeRIQCgNrZXkYASABKAlSA2tleRIUCgV2YW'
    'x1ZRgCIAEoCVIFdmFsdWU6AjgBGlwKEkNvb3JkaW5hdGVNYXBFbnRyeRIQCgNrZXkYASABKAlS'
    'A2tleRIwCgV2YWx1ZRgCIAEoCzIaLmV2b1NlcnZpY2UuQ29vcmRpbmF0ZUxpc3RSBXZhbHVlOg'
    'I4AQ==');

@$core.Deprecated('Use layer3DDescriptor instead')
const Layer3D$json = {
  '1': 'Layer3D',
  '2': [
    {'1': 'layers', '3': 1, '4': 3, '5': 11, '6': '.evoService.Layer2D', '10': 'layers'},
  ],
};

/// Descriptor for `Layer3D`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List layer3DDescriptor = $convert.base64Decode(
    'CgdMYXllcjNEEisKBmxheWVycxgBIAMoCzITLmV2b1NlcnZpY2UuTGF5ZXIyRFIGbGF5ZXJz');

@$core.Deprecated('Use layer2DDescriptor instead')
const Layer2D$json = {
  '1': 'Layer2D',
  '2': [
    {'1': 'rows', '3': 1, '4': 3, '5': 11, '6': '.evoService.Layer1D', '10': 'rows'},
  ],
};

/// Descriptor for `Layer2D`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List layer2DDescriptor = $convert.base64Decode(
    'CgdMYXllcjJEEicKBHJvd3MYASADKAsyEy5ldm9TZXJ2aWNlLkxheWVyMURSBHJvd3M=');

@$core.Deprecated('Use layer1DDescriptor instead')
const Layer1D$json = {
  '1': 'Layer1D',
  '2': [
    {'1': 'values', '3': 1, '4': 3, '5': 5, '10': 'values'},
  ],
};

/// Descriptor for `Layer1D`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List layer1DDescriptor = $convert.base64Decode(
    'CgdMYXllcjFEEhYKBnZhbHVlcxgBIAMoBVIGdmFsdWVz');

@$core.Deprecated('Use progressUpdateDescriptor instead')
const ProgressUpdate$json = {
  '1': 'ProgressUpdate',
  '2': [
    {'1': 'hamming', '3': 1, '4': 1, '5': 1, '10': 'hamming'},
    {'1': 'physics', '3': 2, '4': 1, '5': 1, '10': 'physics'},
    {'1': 'isComplete', '3': 3, '4': 1, '5': 8, '10': 'isComplete'},
  ],
};

/// Descriptor for `ProgressUpdate`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List progressUpdateDescriptor = $convert.base64Decode(
    'Cg5Qcm9ncmVzc1VwZGF0ZRIYCgdoYW1taW5nGAEgASgBUgdoYW1taW5nEhgKB3BoeXNpY3MYAi'
    'ABKAFSB3BoeXNpY3MSHgoKaXNDb21wbGV0ZRgDIAEoCFIKaXNDb21wbGV0ZQ==');

@$core.Deprecated('Use stopRequestDescriptor instead')
const StopRequest$json = {
  '1': 'StopRequest',
};

/// Descriptor for `StopRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List stopRequestDescriptor = $convert.base64Decode(
    'CgtTdG9wUmVxdWVzdA==');

@$core.Deprecated('Use pauseRequestDescriptor instead')
const PauseRequest$json = {
  '1': 'PauseRequest',
};

/// Descriptor for `PauseRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List pauseRequestDescriptor = $convert.base64Decode(
    'CgxQYXVzZVJlcXVlc3Q=');

@$core.Deprecated('Use exportResponseDescriptor instead')
const ExportResponse$json = {
  '1': 'ExportResponse',
};

/// Descriptor for `ExportResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List exportResponseDescriptor = $convert.base64Decode(
    'Cg5FeHBvcnRSZXNwb25zZQ==');

@$core.Deprecated('Use exportRequestDescriptor instead')
const ExportRequest$json = {
  '1': 'ExportRequest',
  '2': [
    {'1': 'folderPath', '3': 1, '4': 1, '5': 9, '10': 'folderPath'},
  ],
};

/// Descriptor for `ExportRequest`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List exportRequestDescriptor = $convert.base64Decode(
    'Cg1FeHBvcnRSZXF1ZXN0Eh4KCmZvbGRlclBhdGgYASABKAlSCmZvbGRlclBhdGg=');

@$core.Deprecated('Use finalResponseDescriptor instead')
const FinalResponse$json = {
  '1': 'FinalResponse',
  '2': [
    {'1': 'handleArray', '3': 1, '4': 3, '5': 11, '6': '.evoService.Layer3D', '10': 'handleArray'},
  ],
};

/// Descriptor for `FinalResponse`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List finalResponseDescriptor = $convert.base64Decode(
    'Cg1GaW5hbFJlc3BvbnNlEjUKC2hhbmRsZUFycmF5GAEgAygLMhMuZXZvU2VydmljZS5MYXllcj'
    'NEUgtoYW5kbGVBcnJheQ==');

@$core.Deprecated('Use coordinateListDescriptor instead')
const CoordinateList$json = {
  '1': 'CoordinateList',
  '2': [
    {'1': 'coords', '3': 1, '4': 3, '5': 11, '6': '.evoService.Coordinate', '10': 'coords'},
  ],
};

/// Descriptor for `CoordinateList`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List coordinateListDescriptor = $convert.base64Decode(
    'Cg5Db29yZGluYXRlTGlzdBIuCgZjb29yZHMYASADKAsyFi5ldm9TZXJ2aWNlLkNvb3JkaW5hdG'
    'VSBmNvb3Jkcw==');

@$core.Deprecated('Use coordinateDescriptor instead')
const Coordinate$json = {
  '1': 'Coordinate',
  '2': [
    {'1': 'x', '3': 1, '4': 1, '5': 5, '10': 'x'},
    {'1': 'y', '3': 2, '4': 1, '5': 5, '10': 'y'},
  ],
};

/// Descriptor for `Coordinate`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List coordinateDescriptor = $convert.base64Decode(
    'CgpDb29yZGluYXRlEgwKAXgYASABKAVSAXgSDAoBeRgCIAEoBVIBeQ==');

