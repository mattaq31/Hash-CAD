//
//  Generated code. Do not modify.
//  source: hamming_evolve_communication.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:core' as $core;

import 'package:protobuf/protobuf.dart' as $pb;

class EvolveRequest extends $pb.GeneratedMessage {
  factory EvolveRequest({
    $core.Iterable<Layer3D>? slatArray,
    $core.Iterable<Layer3D>? handleArray,
    $core.Map<$core.String, $core.String>? parameters,
    $core.Map<$core.String, $core.String>? slatTypes,
    $core.String? connectionAngle,
    $core.Map<$core.String, CoordinateList>? coordinateMap,
    HandleLinkData? handleLinks,
  }) {
    final $result = create();
    if (slatArray != null) {
      $result.slatArray.addAll(slatArray);
    }
    if (handleArray != null) {
      $result.handleArray.addAll(handleArray);
    }
    if (parameters != null) {
      $result.parameters.addAll(parameters);
    }
    if (slatTypes != null) {
      $result.slatTypes.addAll(slatTypes);
    }
    if (connectionAngle != null) {
      $result.connectionAngle = connectionAngle;
    }
    if (coordinateMap != null) {
      $result.coordinateMap.addAll(coordinateMap);
    }
    if (handleLinks != null) {
      $result.handleLinks = handleLinks;
    }
    return $result;
  }
  EvolveRequest._() : super();
  factory EvolveRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory EvolveRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'EvolveRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..pc<Layer3D>(1, _omitFieldNames ? '' : 'slatArray', $pb.PbFieldType.PM, protoName: 'slatArray', subBuilder: Layer3D.create)
    ..pc<Layer3D>(2, _omitFieldNames ? '' : 'handleArray', $pb.PbFieldType.PM, protoName: 'handleArray', subBuilder: Layer3D.create)
    ..m<$core.String, $core.String>(3, _omitFieldNames ? '' : 'parameters', entryClassName: 'EvolveRequest.ParametersEntry', keyFieldType: $pb.PbFieldType.OS, valueFieldType: $pb.PbFieldType.OS, packageName: const $pb.PackageName('evoService'))
    ..m<$core.String, $core.String>(4, _omitFieldNames ? '' : 'slatTypes', protoName: 'slatTypes', entryClassName: 'EvolveRequest.SlatTypesEntry', keyFieldType: $pb.PbFieldType.OS, valueFieldType: $pb.PbFieldType.OS, packageName: const $pb.PackageName('evoService'))
    ..aOS(5, _omitFieldNames ? '' : 'connectionAngle', protoName: 'connectionAngle')
    ..m<$core.String, CoordinateList>(6, _omitFieldNames ? '' : 'coordinateMap', protoName: 'coordinateMap', entryClassName: 'EvolveRequest.CoordinateMapEntry', keyFieldType: $pb.PbFieldType.OS, valueFieldType: $pb.PbFieldType.OM, valueCreator: CoordinateList.create, valueDefaultOrMaker: CoordinateList.getDefault, packageName: const $pb.PackageName('evoService'))
    ..aOM<HandleLinkData>(7, _omitFieldNames ? '' : 'handleLinks', protoName: 'handleLinks', subBuilder: HandleLinkData.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  EvolveRequest clone() => EvolveRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  EvolveRequest copyWith(void Function(EvolveRequest) updates) => super.copyWith((message) => updates(message as EvolveRequest)) as EvolveRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static EvolveRequest create() => EvolveRequest._();
  EvolveRequest createEmptyInstance() => create();
  static $pb.PbList<EvolveRequest> createRepeated() => $pb.PbList<EvolveRequest>();
  @$core.pragma('dart2js:noInline')
  static EvolveRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<EvolveRequest>(create);
  static EvolveRequest? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<Layer3D> get slatArray => $_getList(0);

  @$pb.TagNumber(2)
  $core.List<Layer3D> get handleArray => $_getList(1);

  @$pb.TagNumber(3)
  $core.Map<$core.String, $core.String> get parameters => $_getMap(2);

  @$pb.TagNumber(4)
  $core.Map<$core.String, $core.String> get slatTypes => $_getMap(3);

  @$pb.TagNumber(5)
  $core.String get connectionAngle => $_getSZ(4);
  @$pb.TagNumber(5)
  set connectionAngle($core.String v) { $_setString(4, v); }
  @$pb.TagNumber(5)
  $core.bool hasConnectionAngle() => $_has(4);
  @$pb.TagNumber(5)
  void clearConnectionAngle() => clearField(5);

  @$pb.TagNumber(6)
  $core.Map<$core.String, CoordinateList> get coordinateMap => $_getMap(5);

  @$pb.TagNumber(7)
  HandleLinkData get handleLinks => $_getN(6);
  @$pb.TagNumber(7)
  set handleLinks(HandleLinkData v) { setField(7, v); }
  @$pb.TagNumber(7)
  $core.bool hasHandleLinks() => $_has(6);
  @$pb.TagNumber(7)
  void clearHandleLinks() => clearField(7);
  @$pb.TagNumber(7)
  HandleLinkData ensureHandleLinks() => $_ensure(6);
}

class Layer3D extends $pb.GeneratedMessage {
  factory Layer3D({
    $core.Iterable<Layer2D>? layers,
  }) {
    final $result = create();
    if (layers != null) {
      $result.layers.addAll(layers);
    }
    return $result;
  }
  Layer3D._() : super();
  factory Layer3D.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory Layer3D.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'Layer3D', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..pc<Layer2D>(1, _omitFieldNames ? '' : 'layers', $pb.PbFieldType.PM, subBuilder: Layer2D.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  Layer3D clone() => Layer3D()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  Layer3D copyWith(void Function(Layer3D) updates) => super.copyWith((message) => updates(message as Layer3D)) as Layer3D;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static Layer3D create() => Layer3D._();
  Layer3D createEmptyInstance() => create();
  static $pb.PbList<Layer3D> createRepeated() => $pb.PbList<Layer3D>();
  @$core.pragma('dart2js:noInline')
  static Layer3D getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<Layer3D>(create);
  static Layer3D? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<Layer2D> get layers => $_getList(0);
}

class Layer2D extends $pb.GeneratedMessage {
  factory Layer2D({
    $core.Iterable<Layer1D>? rows,
  }) {
    final $result = create();
    if (rows != null) {
      $result.rows.addAll(rows);
    }
    return $result;
  }
  Layer2D._() : super();
  factory Layer2D.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory Layer2D.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'Layer2D', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..pc<Layer1D>(1, _omitFieldNames ? '' : 'rows', $pb.PbFieldType.PM, subBuilder: Layer1D.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  Layer2D clone() => Layer2D()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  Layer2D copyWith(void Function(Layer2D) updates) => super.copyWith((message) => updates(message as Layer2D)) as Layer2D;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static Layer2D create() => Layer2D._();
  Layer2D createEmptyInstance() => create();
  static $pb.PbList<Layer2D> createRepeated() => $pb.PbList<Layer2D>();
  @$core.pragma('dart2js:noInline')
  static Layer2D getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<Layer2D>(create);
  static Layer2D? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<Layer1D> get rows => $_getList(0);
}

class Layer1D extends $pb.GeneratedMessage {
  factory Layer1D({
    $core.Iterable<$core.int>? values,
  }) {
    final $result = create();
    if (values != null) {
      $result.values.addAll(values);
    }
    return $result;
  }
  Layer1D._() : super();
  factory Layer1D.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory Layer1D.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'Layer1D', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..p<$core.int>(1, _omitFieldNames ? '' : 'values', $pb.PbFieldType.K3)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  Layer1D clone() => Layer1D()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  Layer1D copyWith(void Function(Layer1D) updates) => super.copyWith((message) => updates(message as Layer1D)) as Layer1D;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static Layer1D create() => Layer1D._();
  Layer1D createEmptyInstance() => create();
  static $pb.PbList<Layer1D> createRepeated() => $pb.PbList<Layer1D>();
  @$core.pragma('dart2js:noInline')
  static Layer1D getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<Layer1D>(create);
  static Layer1D? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<$core.int> get values => $_getList(0);
}

class ProgressUpdate extends $pb.GeneratedMessage {
  factory ProgressUpdate({
    $core.double? hamming,
    $core.double? physics,
    $core.bool? isComplete,
  }) {
    final $result = create();
    if (hamming != null) {
      $result.hamming = hamming;
    }
    if (physics != null) {
      $result.physics = physics;
    }
    if (isComplete != null) {
      $result.isComplete = isComplete;
    }
    return $result;
  }
  ProgressUpdate._() : super();
  factory ProgressUpdate.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ProgressUpdate.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ProgressUpdate', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..a<$core.double>(1, _omitFieldNames ? '' : 'hamming', $pb.PbFieldType.OD)
    ..a<$core.double>(2, _omitFieldNames ? '' : 'physics', $pb.PbFieldType.OD)
    ..aOB(3, _omitFieldNames ? '' : 'isComplete', protoName: 'isComplete')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ProgressUpdate clone() => ProgressUpdate()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ProgressUpdate copyWith(void Function(ProgressUpdate) updates) => super.copyWith((message) => updates(message as ProgressUpdate)) as ProgressUpdate;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ProgressUpdate create() => ProgressUpdate._();
  ProgressUpdate createEmptyInstance() => create();
  static $pb.PbList<ProgressUpdate> createRepeated() => $pb.PbList<ProgressUpdate>();
  @$core.pragma('dart2js:noInline')
  static ProgressUpdate getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ProgressUpdate>(create);
  static ProgressUpdate? _defaultInstance;

  @$pb.TagNumber(1)
  $core.double get hamming => $_getN(0);
  @$pb.TagNumber(1)
  set hamming($core.double v) { $_setDouble(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasHamming() => $_has(0);
  @$pb.TagNumber(1)
  void clearHamming() => clearField(1);

  @$pb.TagNumber(2)
  $core.double get physics => $_getN(1);
  @$pb.TagNumber(2)
  set physics($core.double v) { $_setDouble(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasPhysics() => $_has(1);
  @$pb.TagNumber(2)
  void clearPhysics() => clearField(2);

  @$pb.TagNumber(3)
  $core.bool get isComplete => $_getBF(2);
  @$pb.TagNumber(3)
  set isComplete($core.bool v) { $_setBool(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasIsComplete() => $_has(2);
  @$pb.TagNumber(3)
  void clearIsComplete() => clearField(3);
}

class StopRequest extends $pb.GeneratedMessage {
  factory StopRequest() => create();
  StopRequest._() : super();
  factory StopRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory StopRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'StopRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  StopRequest clone() => StopRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  StopRequest copyWith(void Function(StopRequest) updates) => super.copyWith((message) => updates(message as StopRequest)) as StopRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static StopRequest create() => StopRequest._();
  StopRequest createEmptyInstance() => create();
  static $pb.PbList<StopRequest> createRepeated() => $pb.PbList<StopRequest>();
  @$core.pragma('dart2js:noInline')
  static StopRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<StopRequest>(create);
  static StopRequest? _defaultInstance;
}

class PauseRequest extends $pb.GeneratedMessage {
  factory PauseRequest() => create();
  PauseRequest._() : super();
  factory PauseRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory PauseRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'PauseRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  PauseRequest clone() => PauseRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  PauseRequest copyWith(void Function(PauseRequest) updates) => super.copyWith((message) => updates(message as PauseRequest)) as PauseRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static PauseRequest create() => PauseRequest._();
  PauseRequest createEmptyInstance() => create();
  static $pb.PbList<PauseRequest> createRepeated() => $pb.PbList<PauseRequest>();
  @$core.pragma('dart2js:noInline')
  static PauseRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<PauseRequest>(create);
  static PauseRequest? _defaultInstance;
}

class ExportResponse extends $pb.GeneratedMessage {
  factory ExportResponse() => create();
  ExportResponse._() : super();
  factory ExportResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ExportResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ExportResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ExportResponse clone() => ExportResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ExportResponse copyWith(void Function(ExportResponse) updates) => super.copyWith((message) => updates(message as ExportResponse)) as ExportResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ExportResponse create() => ExportResponse._();
  ExportResponse createEmptyInstance() => create();
  static $pb.PbList<ExportResponse> createRepeated() => $pb.PbList<ExportResponse>();
  @$core.pragma('dart2js:noInline')
  static ExportResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ExportResponse>(create);
  static ExportResponse? _defaultInstance;
}

class ExportRequest extends $pb.GeneratedMessage {
  factory ExportRequest({
    $core.String? folderPath,
  }) {
    final $result = create();
    if (folderPath != null) {
      $result.folderPath = folderPath;
    }
    return $result;
  }
  ExportRequest._() : super();
  factory ExportRequest.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory ExportRequest.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'ExportRequest', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'folderPath', protoName: 'folderPath')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  ExportRequest clone() => ExportRequest()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  ExportRequest copyWith(void Function(ExportRequest) updates) => super.copyWith((message) => updates(message as ExportRequest)) as ExportRequest;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static ExportRequest create() => ExportRequest._();
  ExportRequest createEmptyInstance() => create();
  static $pb.PbList<ExportRequest> createRepeated() => $pb.PbList<ExportRequest>();
  @$core.pragma('dart2js:noInline')
  static ExportRequest getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<ExportRequest>(create);
  static ExportRequest? _defaultInstance;

  /// folder path for saving results
  @$pb.TagNumber(1)
  $core.String get folderPath => $_getSZ(0);
  @$pb.TagNumber(1)
  set folderPath($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasFolderPath() => $_has(0);
  @$pb.TagNumber(1)
  void clearFolderPath() => clearField(1);
}

class FinalResponse extends $pb.GeneratedMessage {
  factory FinalResponse({
    $core.Iterable<Layer3D>? handleArray,
  }) {
    final $result = create();
    if (handleArray != null) {
      $result.handleArray.addAll(handleArray);
    }
    return $result;
  }
  FinalResponse._() : super();
  factory FinalResponse.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory FinalResponse.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'FinalResponse', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..pc<Layer3D>(1, _omitFieldNames ? '' : 'handleArray', $pb.PbFieldType.PM, protoName: 'handleArray', subBuilder: Layer3D.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  FinalResponse clone() => FinalResponse()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  FinalResponse copyWith(void Function(FinalResponse) updates) => super.copyWith((message) => updates(message as FinalResponse)) as FinalResponse;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static FinalResponse create() => FinalResponse._();
  FinalResponse createEmptyInstance() => create();
  static $pb.PbList<FinalResponse> createRepeated() => $pb.PbList<FinalResponse>();
  @$core.pragma('dart2js:noInline')
  static FinalResponse getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<FinalResponse>(create);
  static FinalResponse? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<Layer3D> get handleArray => $_getList(0);
}

class CoordinateList extends $pb.GeneratedMessage {
  factory CoordinateList({
    $core.Iterable<Coordinate>? coords,
  }) {
    final $result = create();
    if (coords != null) {
      $result.coords.addAll(coords);
    }
    return $result;
  }
  CoordinateList._() : super();
  factory CoordinateList.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory CoordinateList.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'CoordinateList', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..pc<Coordinate>(1, _omitFieldNames ? '' : 'coords', $pb.PbFieldType.PM, subBuilder: Coordinate.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  CoordinateList clone() => CoordinateList()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  CoordinateList copyWith(void Function(CoordinateList) updates) => super.copyWith((message) => updates(message as CoordinateList)) as CoordinateList;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static CoordinateList create() => CoordinateList._();
  CoordinateList createEmptyInstance() => create();
  static $pb.PbList<CoordinateList> createRepeated() => $pb.PbList<CoordinateList>();
  @$core.pragma('dart2js:noInline')
  static CoordinateList getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<CoordinateList>(create);
  static CoordinateList? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<Coordinate> get coords => $_getList(0);
}

class Coordinate extends $pb.GeneratedMessage {
  factory Coordinate({
    $core.int? x,
    $core.int? y,
  }) {
    final $result = create();
    if (x != null) {
      $result.x = x;
    }
    if (y != null) {
      $result.y = y;
    }
    return $result;
  }
  Coordinate._() : super();
  factory Coordinate.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory Coordinate.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'Coordinate', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..a<$core.int>(1, _omitFieldNames ? '' : 'x', $pb.PbFieldType.O3)
    ..a<$core.int>(2, _omitFieldNames ? '' : 'y', $pb.PbFieldType.O3)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  Coordinate clone() => Coordinate()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  Coordinate copyWith(void Function(Coordinate) updates) => super.copyWith((message) => updates(message as Coordinate)) as Coordinate;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static Coordinate create() => Coordinate._();
  Coordinate createEmptyInstance() => create();
  static $pb.PbList<Coordinate> createRepeated() => $pb.PbList<Coordinate>();
  @$core.pragma('dart2js:noInline')
  static Coordinate getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<Coordinate>(create);
  static Coordinate? _defaultInstance;

  @$pb.TagNumber(1)
  $core.int get x => $_getIZ(0);
  @$pb.TagNumber(1)
  set x($core.int v) { $_setSignedInt32(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasX() => $_has(0);
  @$pb.TagNumber(1)
  void clearX() => clearField(1);

  @$pb.TagNumber(2)
  $core.int get y => $_getIZ(1);
  @$pb.TagNumber(2)
  set y($core.int v) { $_setSignedInt32(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasY() => $_has(1);
  @$pb.TagNumber(2)
  void clearY() => clearField(2);
}

/// Handle key: (slatId, position, side)
class HandleKey extends $pb.GeneratedMessage {
  factory HandleKey({
    $core.String? slatId,
    $core.int? position,
    $core.int? side,
  }) {
    final $result = create();
    if (slatId != null) {
      $result.slatId = slatId;
    }
    if (position != null) {
      $result.position = position;
    }
    if (side != null) {
      $result.side = side;
    }
    return $result;
  }
  HandleKey._() : super();
  factory HandleKey.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory HandleKey.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'HandleKey', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'slatId', protoName: 'slatId')
    ..a<$core.int>(2, _omitFieldNames ? '' : 'position', $pb.PbFieldType.O3)
    ..a<$core.int>(3, _omitFieldNames ? '' : 'side', $pb.PbFieldType.O3)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  HandleKey clone() => HandleKey()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  HandleKey copyWith(void Function(HandleKey) updates) => super.copyWith((message) => updates(message as HandleKey)) as HandleKey;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static HandleKey create() => HandleKey._();
  HandleKey createEmptyInstance() => create();
  static $pb.PbList<HandleKey> createRepeated() => $pb.PbList<HandleKey>();
  @$core.pragma('dart2js:noInline')
  static HandleKey getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<HandleKey>(create);
  static HandleKey? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get slatId => $_getSZ(0);
  @$pb.TagNumber(1)
  set slatId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasSlatId() => $_has(0);
  @$pb.TagNumber(1)
  void clearSlatId() => clearField(1);

  @$pb.TagNumber(2)
  $core.int get position => $_getIZ(1);
  @$pb.TagNumber(2)
  set position($core.int v) { $_setSignedInt32(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasPosition() => $_has(1);
  @$pb.TagNumber(2)
  void clearPosition() => clearField(2);

  @$pb.TagNumber(3)
  $core.int get side => $_getIZ(2);
  @$pb.TagNumber(3)
  set side($core.int v) { $_setSignedInt32(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasSide() => $_has(2);
  @$pb.TagNumber(3)
  void clearSide() => clearField(3);
}

/// Phantom slat with parent relationship
class PhantomSlatEntry extends $pb.GeneratedMessage {
  factory PhantomSlatEntry({
    $core.String? phantomSlatId,
    $core.String? parentSlatId,
    CoordinateList? coordinates,
  }) {
    final $result = create();
    if (phantomSlatId != null) {
      $result.phantomSlatId = phantomSlatId;
    }
    if (parentSlatId != null) {
      $result.parentSlatId = parentSlatId;
    }
    if (coordinates != null) {
      $result.coordinates = coordinates;
    }
    return $result;
  }
  PhantomSlatEntry._() : super();
  factory PhantomSlatEntry.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory PhantomSlatEntry.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'PhantomSlatEntry', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'phantomSlatId', protoName: 'phantomSlatId')
    ..aOS(2, _omitFieldNames ? '' : 'parentSlatId', protoName: 'parentSlatId')
    ..aOM<CoordinateList>(3, _omitFieldNames ? '' : 'coordinates', subBuilder: CoordinateList.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  PhantomSlatEntry clone() => PhantomSlatEntry()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  PhantomSlatEntry copyWith(void Function(PhantomSlatEntry) updates) => super.copyWith((message) => updates(message as PhantomSlatEntry)) as PhantomSlatEntry;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static PhantomSlatEntry create() => PhantomSlatEntry._();
  PhantomSlatEntry createEmptyInstance() => create();
  static $pb.PbList<PhantomSlatEntry> createRepeated() => $pb.PbList<PhantomSlatEntry>();
  @$core.pragma('dart2js:noInline')
  static PhantomSlatEntry getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<PhantomSlatEntry>(create);
  static PhantomSlatEntry? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get phantomSlatId => $_getSZ(0);
  @$pb.TagNumber(1)
  set phantomSlatId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasPhantomSlatId() => $_has(0);
  @$pb.TagNumber(1)
  void clearPhantomSlatId() => clearField(1);

  @$pb.TagNumber(2)
  $core.String get parentSlatId => $_getSZ(1);
  @$pb.TagNumber(2)
  set parentSlatId($core.String v) { $_setString(1, v); }
  @$pb.TagNumber(2)
  $core.bool hasParentSlatId() => $_has(1);
  @$pb.TagNumber(2)
  void clearParentSlatId() => clearField(2);

  @$pb.TagNumber(3)
  CoordinateList get coordinates => $_getN(2);
  @$pb.TagNumber(3)
  set coordinates(CoordinateList v) { setField(3, v); }
  @$pb.TagNumber(3)
  $core.bool hasCoordinates() => $_has(2);
  @$pb.TagNumber(3)
  void clearCoordinates() => clearField(3);
  @$pb.TagNumber(3)
  CoordinateList ensureCoordinates() => $_ensure(2);
}

/// Link group with optional enforced value
class HandleLinkGroup extends $pb.GeneratedMessage {
  factory HandleLinkGroup({
    $core.String? groupId,
    $core.Iterable<HandleKey>? handles,
    $core.bool? hasEnforcedValue,
    $core.int? enforcedValue_4,
  }) {
    final $result = create();
    if (groupId != null) {
      $result.groupId = groupId;
    }
    if (handles != null) {
      $result.handles.addAll(handles);
    }
    if (hasEnforcedValue != null) {
      $result.hasEnforcedValue = hasEnforcedValue;
    }
    if (enforcedValue_4 != null) {
      $result.enforcedValue_4 = enforcedValue_4;
    }
    return $result;
  }
  HandleLinkGroup._() : super();
  factory HandleLinkGroup.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory HandleLinkGroup.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'HandleLinkGroup', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..aOS(1, _omitFieldNames ? '' : 'groupId', protoName: 'groupId')
    ..pc<HandleKey>(2, _omitFieldNames ? '' : 'handles', $pb.PbFieldType.PM, subBuilder: HandleKey.create)
    ..aOB(3, _omitFieldNames ? '' : 'hasEnforcedValue', protoName: 'hasEnforcedValue')
    ..a<$core.int>(4, _omitFieldNames ? '' : 'enforcedValue', $pb.PbFieldType.O3, protoName: 'enforcedValue')
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  HandleLinkGroup clone() => HandleLinkGroup()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  HandleLinkGroup copyWith(void Function(HandleLinkGroup) updates) => super.copyWith((message) => updates(message as HandleLinkGroup)) as HandleLinkGroup;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static HandleLinkGroup create() => HandleLinkGroup._();
  HandleLinkGroup createEmptyInstance() => create();
  static $pb.PbList<HandleLinkGroup> createRepeated() => $pb.PbList<HandleLinkGroup>();
  @$core.pragma('dart2js:noInline')
  static HandleLinkGroup getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<HandleLinkGroup>(create);
  static HandleLinkGroup? _defaultInstance;

  @$pb.TagNumber(1)
  $core.String get groupId => $_getSZ(0);
  @$pb.TagNumber(1)
  set groupId($core.String v) { $_setString(0, v); }
  @$pb.TagNumber(1)
  $core.bool hasGroupId() => $_has(0);
  @$pb.TagNumber(1)
  void clearGroupId() => clearField(1);

  @$pb.TagNumber(2)
  $core.List<HandleKey> get handles => $_getList(1);

  @$pb.TagNumber(3)
  $core.bool get hasEnforcedValue => $_getBF(2);
  @$pb.TagNumber(3)
  set hasEnforcedValue($core.bool v) { $_setBool(2, v); }
  @$pb.TagNumber(3)
  $core.bool hasHasEnforcedValue() => $_has(2);
  @$pb.TagNumber(3)
  void clearHasEnforcedValue() => clearField(3);

  @$pb.TagNumber(4)
  $core.int get enforcedValue_4 => $_getIZ(3);
  @$pb.TagNumber(4)
  set enforcedValue_4($core.int v) { $_setSignedInt32(3, v); }
  @$pb.TagNumber(4)
  $core.bool hasEnforcedValue_4() => $_has(3);
  @$pb.TagNumber(4)
  void clearEnforcedValue_4() => clearField(4);
}

/// Complete link/phantom data
class HandleLinkData extends $pb.GeneratedMessage {
  factory HandleLinkData({
    $core.Iterable<HandleLinkGroup>? linkGroups,
    $core.Iterable<HandleKey>? blockedHandles,
    $core.Iterable<PhantomSlatEntry>? phantomSlats,
  }) {
    final $result = create();
    if (linkGroups != null) {
      $result.linkGroups.addAll(linkGroups);
    }
    if (blockedHandles != null) {
      $result.blockedHandles.addAll(blockedHandles);
    }
    if (phantomSlats != null) {
      $result.phantomSlats.addAll(phantomSlats);
    }
    return $result;
  }
  HandleLinkData._() : super();
  factory HandleLinkData.fromBuffer($core.List<$core.int> i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromBuffer(i, r);
  factory HandleLinkData.fromJson($core.String i, [$pb.ExtensionRegistry r = $pb.ExtensionRegistry.EMPTY]) => create()..mergeFromJson(i, r);

  static final $pb.BuilderInfo _i = $pb.BuilderInfo(_omitMessageNames ? '' : 'HandleLinkData', package: const $pb.PackageName(_omitMessageNames ? '' : 'evoService'), createEmptyInstance: create)
    ..pc<HandleLinkGroup>(1, _omitFieldNames ? '' : 'linkGroups', $pb.PbFieldType.PM, protoName: 'linkGroups', subBuilder: HandleLinkGroup.create)
    ..pc<HandleKey>(2, _omitFieldNames ? '' : 'blockedHandles', $pb.PbFieldType.PM, protoName: 'blockedHandles', subBuilder: HandleKey.create)
    ..pc<PhantomSlatEntry>(3, _omitFieldNames ? '' : 'phantomSlats', $pb.PbFieldType.PM, protoName: 'phantomSlats', subBuilder: PhantomSlatEntry.create)
    ..hasRequiredFields = false
  ;

  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.deepCopy] instead. '
  'Will be removed in next major version')
  HandleLinkData clone() => HandleLinkData()..mergeFromMessage(this);
  @$core.Deprecated(
  'Using this can add significant overhead to your binary. '
  'Use [GeneratedMessageGenericExtensions.rebuild] instead. '
  'Will be removed in next major version')
  HandleLinkData copyWith(void Function(HandleLinkData) updates) => super.copyWith((message) => updates(message as HandleLinkData)) as HandleLinkData;

  $pb.BuilderInfo get info_ => _i;

  @$core.pragma('dart2js:noInline')
  static HandleLinkData create() => HandleLinkData._();
  HandleLinkData createEmptyInstance() => create();
  static $pb.PbList<HandleLinkData> createRepeated() => $pb.PbList<HandleLinkData>();
  @$core.pragma('dart2js:noInline')
  static HandleLinkData getDefault() => _defaultInstance ??= $pb.GeneratedMessage.$_defaultFor<HandleLinkData>(create);
  static HandleLinkData? _defaultInstance;

  @$pb.TagNumber(1)
  $core.List<HandleLinkGroup> get linkGroups => $_getList(0);

  @$pb.TagNumber(2)
  $core.List<HandleKey> get blockedHandles => $_getList(1);

  @$pb.TagNumber(3)
  $core.List<PhantomSlatEntry> get phantomSlats => $_getList(2);
}


const _omitFieldNames = $core.bool.fromEnvironment('protobuf.omit_field_names');
const _omitMessageNames = $core.bool.fromEnvironment('protobuf.omit_message_names');
