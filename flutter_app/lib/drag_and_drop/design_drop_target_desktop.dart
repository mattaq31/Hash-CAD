import 'dart:io';
import 'dart:typed_data';
import 'package:desktop_drop/desktop_drop.dart';
import 'package:flutter/material.dart';

typedef OnDesignDrop = Future<void> Function(Uint8List bytes, String name);

class DesignDropTarget extends StatefulWidget {
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
  State<DesignDropTarget> createState() => _DesignDropTargetState();
}

class _DesignDropTargetState extends State<DesignDropTarget> {
  bool _hover = false;

  bool _accepts(String name) {
    if (widget.acceptExtensions == null || widget.acceptExtensions!.isEmpty) return true;
    final lower = name.toLowerCase();
    return widget.acceptExtensions!.any((ext) => lower.endsWith('.$ext'));
  }

  Future<void> _handleDrop(List<DropItem> uris) async {
    for (final uri in uris) {
      if (!uri.path.startsWith('/')) continue;
      final file = File(uri.path);
      final name = file.uri.pathSegments.isNotEmpty
          ? file.uri.pathSegments.last
          : file.path.split(Platform.pathSeparator).last;
      if (!_accepts(name)) continue;
      final bytes = await file.readAsBytes();
      await widget.onDrop(bytes, name);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DropTarget(
      onDragEntered: (_) => setState(() => _hover = true),
      onDragExited: (_) => setState(() => _hover = false),
      onDragDone: (detail) async {
        setState(() => _hover = false);
        await _handleDrop(detail.files);
      },
      child: Stack(
        fit: StackFit.expand,
        children: [
          widget.child,
          if (_hover)
            IgnorePointer(
              child: widget.highlightBuilder?.call(context) ?? _DefaultHighlight(),
            ),
        ],
      ),
    );
  }
}

class _DefaultHighlight extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return  Stack(
      fit: StackFit.expand,
      children: [
        // The existing blue border + tint
        DecoratedBox(
          decoration: BoxDecoration(
            border: Border.all(color: Colors.blueAccent, width: 3),
            color: Colors.blue.withValues(alpha: 0.08),
          ),
        ),
        // Centered instruction
        Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: const [
              Icon(Icons.file_download, size: 64, color: Colors.black),
              SizedBox(height: 12),
              Text(
                'Drop your design here to import',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: Colors.black,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}