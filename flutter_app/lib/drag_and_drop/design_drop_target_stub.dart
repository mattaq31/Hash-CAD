import 'dart:typed_data';
import 'package:flutter/material.dart';

typedef OnDesignDrop = Future<void> Function(Uint8List bytes, String name);

class DesignDropTarget extends StatelessWidget {
  const DesignDropTarget({
    super.key,
    required this.child,
    required this.onDrop,
    this.acceptExtensions,
    this.highlightBuilder,
  });

  final Widget child;
  final OnDesignDrop onDrop;
  final List<String>? acceptExtensions;
  final Widget Function(BuildContext context)? highlightBuilder;

  @override
  Widget build(BuildContext context) => child; // no-op on unsupported platforms
}