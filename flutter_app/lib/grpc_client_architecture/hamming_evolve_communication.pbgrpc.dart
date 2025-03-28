//
//  Generated code. Do not modify.
//  source: hamming_evolve_communication.proto
//
// @dart = 2.12

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names, library_prefixes
// ignore_for_file: non_constant_identifier_names, prefer_final_fields
// ignore_for_file: unnecessary_import, unnecessary_this, unused_import

import 'dart:async' as $async;
import 'dart:core' as $core;

import 'package:grpc/service_api.dart' as $grpc;
import 'package:protobuf/protobuf.dart' as $pb;

import 'hamming_evolve_communication.pb.dart' as $0;

export 'hamming_evolve_communication.pb.dart';

@$pb.GrpcServiceName('evoService.HandleEvolve')
class HandleEvolveClient extends $grpc.Client {
  static final _$evolveQuery = $grpc.ClientMethod<$0.EvolveRequest, $0.ProgressUpdate>(
      '/evoService.HandleEvolve/evolveQuery',
      ($0.EvolveRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $0.ProgressUpdate.fromBuffer(value));
  static final _$pauseProcessing = $grpc.ClientMethod<$0.PauseRequest, $0.PauseRequest>(
      '/evoService.HandleEvolve/PauseProcessing',
      ($0.PauseRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $0.PauseRequest.fromBuffer(value));
  static final _$stopProcessing = $grpc.ClientMethod<$0.StopRequest, $0.FinalResponse>(
      '/evoService.HandleEvolve/StopProcessing',
      ($0.StopRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $0.FinalResponse.fromBuffer(value));
  static final _$requestExport = $grpc.ClientMethod<$0.ExportRequest, $0.ExportResponse>(
      '/evoService.HandleEvolve/requestExport',
      ($0.ExportRequest value) => value.writeToBuffer(),
      ($core.List<$core.int> value) => $0.ExportResponse.fromBuffer(value));

  HandleEvolveClient($grpc.ClientChannel channel,
      {$grpc.CallOptions? options,
      $core.Iterable<$grpc.ClientInterceptor>? interceptors})
      : super(channel, options: options,
        interceptors: interceptors);

  $grpc.ResponseStream<$0.ProgressUpdate> evolveQuery($0.EvolveRequest request, {$grpc.CallOptions? options}) {
    return $createStreamingCall(_$evolveQuery, $async.Stream.fromIterable([request]), options: options);
  }

  $grpc.ResponseFuture<$0.PauseRequest> pauseProcessing($0.PauseRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$pauseProcessing, request, options: options);
  }

  $grpc.ResponseFuture<$0.FinalResponse> stopProcessing($0.StopRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$stopProcessing, request, options: options);
  }

  $grpc.ResponseFuture<$0.ExportResponse> requestExport($0.ExportRequest request, {$grpc.CallOptions? options}) {
    return $createUnaryCall(_$requestExport, request, options: options);
  }
}

@$pb.GrpcServiceName('evoService.HandleEvolve')
abstract class HandleEvolveServiceBase extends $grpc.Service {
  $core.String get $name => 'evoService.HandleEvolve';

  HandleEvolveServiceBase() {
    $addMethod($grpc.ServiceMethod<$0.EvolveRequest, $0.ProgressUpdate>(
        'evolveQuery',
        evolveQuery_Pre,
        false,
        true,
        ($core.List<$core.int> value) => $0.EvolveRequest.fromBuffer(value),
        ($0.ProgressUpdate value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$0.PauseRequest, $0.PauseRequest>(
        'PauseProcessing',
        pauseProcessing_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $0.PauseRequest.fromBuffer(value),
        ($0.PauseRequest value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$0.StopRequest, $0.FinalResponse>(
        'StopProcessing',
        stopProcessing_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $0.StopRequest.fromBuffer(value),
        ($0.FinalResponse value) => value.writeToBuffer()));
    $addMethod($grpc.ServiceMethod<$0.ExportRequest, $0.ExportResponse>(
        'requestExport',
        requestExport_Pre,
        false,
        false,
        ($core.List<$core.int> value) => $0.ExportRequest.fromBuffer(value),
        ($0.ExportResponse value) => value.writeToBuffer()));
  }

  $async.Stream<$0.ProgressUpdate> evolveQuery_Pre($grpc.ServiceCall call, $async.Future<$0.EvolveRequest> request) async* {
    yield* evolveQuery(call, await request);
  }

  $async.Future<$0.PauseRequest> pauseProcessing_Pre($grpc.ServiceCall call, $async.Future<$0.PauseRequest> request) async {
    return pauseProcessing(call, await request);
  }

  $async.Future<$0.FinalResponse> stopProcessing_Pre($grpc.ServiceCall call, $async.Future<$0.StopRequest> request) async {
    return stopProcessing(call, await request);
  }

  $async.Future<$0.ExportResponse> requestExport_Pre($grpc.ServiceCall call, $async.Future<$0.ExportRequest> request) async {
    return requestExport(call, await request);
  }

  $async.Stream<$0.ProgressUpdate> evolveQuery($grpc.ServiceCall call, $0.EvolveRequest request);
  $async.Future<$0.PauseRequest> pauseProcessing($grpc.ServiceCall call, $0.PauseRequest request);
  $async.Future<$0.FinalResponse> stopProcessing($grpc.ServiceCall call, $0.StopRequest request);
  $async.Future<$0.ExportResponse> requestExport($grpc.ServiceCall call, $0.ExportRequest request);
}
