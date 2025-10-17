import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_dropzone/flutter_dropzone.dart';

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
  late DropzoneViewController _dz;
  bool _hover = false;

  bool _accepts(String name) {
    if (widget.acceptExtensions == null || widget.acceptExtensions!.isEmpty) return true;
    final lower = name.toLowerCase();
    return widget.acceptExtensions!.any((ext) => lower.endsWith('.$ext'));
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [

        // 1) Place the dropzone underneath everything else
        IgnorePointer(
          ignoring: true, // keep normal clicks/gestures going to your canvas
          child: DropzoneView(
            operation: DragOperation.copy,
            onCreated: (c) => _dz = c,
            onHover: () => setState(() => _hover = true),
            onLeave: () => setState(() => _hover = false),
            onDropFile: (ev) async {
              setState(() => _hover = false);
              final name = await _dz.getFilename(ev);
              if (!_accepts(name)) return;
              final bytes = await _dz.getFileData(ev);
              await widget.onDrop(bytes, name);
            },
          ),
        ),
        widget.child,
        if (_hover)
          IgnorePointer(
            child: widget.highlightBuilder?.call(context) ?? _DefaultHighlight(),
          ),
      ],
    );
  }
}

class _DefaultHighlight extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Stack(
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