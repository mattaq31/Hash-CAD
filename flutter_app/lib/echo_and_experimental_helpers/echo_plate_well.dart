import 'package:flutter/material.dart';
import '../crisscross_core/slats.dart';
import 'echo_barcode_painter.dart';
import 'echo_plate_constants.dart';
import 'plate_layout_state.dart' show baseSlatId;

// ---------------------------------------------------------------------------
// WellWidget — renders a single well, accepts drags from sidebar + plates
// ---------------------------------------------------------------------------

class WellWidget extends StatefulWidget {
  final String wellName;
  final String? slatId;
  final Slat? slat;
  final int plateIndex;
  final Color? designColor;
  final bool isSelected;
  final ({bool isValid, String? ghostSlatId})? ghostState;
  final bool isDimmedSource;
  final void Function(int fromPlate, String fromWell, int toPlate, String toWell) onWellToWell;
  final void Function(String slatId, int toPlate, String toWell) onSidebarToWell;
  final VoidCallback onWellClick;
  final VoidCallback onRightClick;
  final bool isGroupDragging;
  final VoidCallback onGroupDragStart;
  final VoidCallback onGroupDragHover;
  final bool isInDuplicateGroup;

  const WellWidget({
    super.key,
    required this.wellName,
    required this.slatId,
    required this.slat,
    required this.plateIndex,
    required this.designColor,
    required this.isSelected,
    required this.ghostState,
    required this.isDimmedSource,
    this.isInDuplicateGroup = false,
    required this.onWellToWell,
    required this.onSidebarToWell,
    required this.onWellClick,
    required this.onRightClick,
    required this.isGroupDragging,
    required this.onGroupDragStart,
    required this.onGroupDragHover,
  });

  @override
  State<WellWidget> createState() => WellWidgetState();
}

class WellWidgetState extends State<WellWidget> with SingleTickerProviderStateMixin {
  bool _isHovered = false;
  late final AnimationController _flashController;
  Color _flashStartColor = Colors.green.shade300;

  @override
  void initState() {
    super.initState();
    _flashController = AnimationController(vsync: this, duration: const Duration(milliseconds: 400));
    _flashController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _flashController.dispose();
    super.dispose();
  }

  /// Triggers a border flash. Green for the drop target, amber for the source well.
  void triggerFlash({bool sourceWell = false}) {
    _flashStartColor = sourceWell ? Colors.amber.shade400 : Colors.green.shade300;
    _flashController.forward(from: 0);
  }

  Widget _buildWellContent({double opacity = 1.0}) {
    final slat = widget.slat;
    final slatId = widget.slatId;
    final flashActive = _flashController.status == AnimationStatus.forward;
    final flashColor =
        Color.lerp(_flashStartColor, Colors.grey.shade300, Curves.easeOut.transform(_flashController.value));

    final defaultBorderColor = widget.designColor ?? Colors.grey.shade300;
    final defaultBorderWidth = widget.designColor != null ? 1.5 : 1.0;

    Color borderColor;
    double borderWidth;
    Color bgColor;

    if (widget.isSelected) {
      borderColor = Colors.blue.shade700;
      borderWidth = 2.0;
      bgColor = Colors.blue.shade50;
    } else if (flashActive) {
      borderColor = flashColor ?? defaultBorderColor;
      borderWidth = 2.0;
      bgColor = slat != null ? Colors.white : Colors.grey.shade100;
    } else if (_isHovered) {
      borderColor = Colors.blue;
      borderWidth = 2.0;
      bgColor = slat != null ? Colors.white : Colors.grey.shade100;
    } else {
      borderColor = defaultBorderColor;
      borderWidth = defaultBorderWidth;
      bgColor = slat != null ? Colors.white : Colors.grey.shade100;
    }

    // Ghost overlay styling
    if (widget.ghostState != null) {
      if (!widget.ghostState!.isValid) {
        borderColor = Colors.red.shade400;
        borderWidth = 2.0;
        bgColor = Colors.red.shade50;
      } else {
        borderColor = Colors.blue.shade300;
        borderWidth = 1.5;
        bgColor = Colors.blue.shade50;
      }
    }

    // Strip ~N suffix for display
    final displayId = slatId != null ? baseSlatId(slatId).replaceFirst('-I', '-') : '';

    return Container(
      width: echoWellWidth,
      height: echoWellHeight,
      decoration: BoxDecoration(
        color: bgColor,
        border: Border.all(color: borderColor, width: borderWidth),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Stack(
        children: [
          Opacity(
            opacity: widget.isDimmedSource ? 0.3 : opacity,
            child: slat != null
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          displayId,
                          style: const TextStyle(fontSize: 8, fontWeight: FontWeight.w600),
                          overflow: TextOverflow.ellipsis,
                          maxLines: 1,
                        ),
                        const SizedBox(height: 2),
                        SizedBox(
                          width: echoWellWidth - 8,
                          height: 20,
                          child: CustomPaint(
                            painter: HandleBarcodePainter(
                              h2Handles: slat.h2Handles,
                              h5Handles: slat.h5Handles,
                              maxLength: slat.maxLength,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                : (widget.ghostState != null && widget.ghostState!.ghostSlatId != null
                    ? Opacity(
                        opacity: 0.5,
                        child: Center(
                          child: Text(
                            baseSlatId(widget.ghostState!.ghostSlatId!).replaceFirst('-I', '-'),
                            style: TextStyle(
                              fontSize: 8,
                              fontWeight: FontWeight.w600,
                              color: widget.ghostState!.isValid ? Colors.blue.shade700 : Colors.red.shade700,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                    : null),
          ),
          // Duplicate badge
          if (widget.isInDuplicateGroup && slat != null)
            Positioned(
              top: 1,
              right: 1,
              child: Icon(Icons.copy, size: 10, color: Colors.grey.shade500),
            ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final dragData = <String, dynamic>{
      'source': 'plate',
      'plateIndex': widget.plateIndex,
      'wellName': widget.wellName,
      'slatId': widget.slatId,
    };

    return GestureDetector(
      onTap: () {
        if (!widget.isGroupDragging) {
          widget.onWellClick();
        }
      },
      onSecondaryTap: () {
        if (widget.slatId != null) {
          widget.onRightClick();
        }
      },
      child: MouseRegion(
        onEnter: (_) {
          if (widget.isGroupDragging) {
            widget.onGroupDragHover();
          }
        },
        child: DragTarget<Map<String, dynamic>>(
          onWillAcceptWithDetails: (details) {
            setState(() => _isHovered = true);
            return true;
          },
          onLeave: (_) {
            setState(() => _isHovered = false);
          },
          onAcceptWithDetails: (details) {
            setState(() => _isHovered = false);
            triggerFlash();
            final data = details.data;
            if (data['source'] == 'sidebar') {
              widget.onSidebarToWell(data['slatId'] as String, widget.plateIndex, widget.wellName);
            } else {
              widget.onWellToWell(
                data['plateIndex'] as int,
                data['wellName'] as String,
                widget.plateIndex,
                widget.wellName,
              );
            }
          },
          builder: (context, candidateData, rejectedData) {
            // Group drag: use pointer-based system instead of Draggable
            if (widget.isSelected && !widget.isGroupDragging) {
              return GestureDetector(
                onPanStart: (_) => widget.onGroupDragStart(),
                child: _buildWellContent(),
              );
            }
            if (widget.isGroupDragging) {
              return _buildWellContent();
            }
            // Standard single-well drag
            if (widget.slat != null) {
              return Draggable<Map<String, dynamic>>(
                data: dragData,
                feedback: Material(
                  elevation: 4,
                  borderRadius: BorderRadius.circular(4),
                  child: Transform.scale(
                    scale: 1.1,
                    child: Opacity(opacity: 0.85, child: _buildWellContent()),
                  ),
                ),
                childWhenDragging: Opacity(opacity: 0.3, child: _buildWellContent()),
                child: _buildWellContent(),
              );
            }
            return _buildWellContent();
          },
        ),
      ),
    );
  }
}
