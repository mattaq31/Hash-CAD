import '../app_management/shared_app_state.dart';

import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:math';


Widget slatIcon(DesignState appState) {
  bool isSelected = appState.slatAdditionType == 'tube';
  return GestureDetector(
    onTap: () {
      appState.setSlatAdditionType('tube');
    },
    child: Container(
      width: 40, // Shrunk size
      height: 40,
      margin: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
        borderRadius: BorderRadius.circular(6),
        border: isSelected
            ? Border.all(color: Colors.black, width: 2)
            : null,
        boxShadow: isSelected
            ? [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.5),
            blurRadius: 6,
            spreadRadius: 1,
          )
        ]
            : [],
      ),
    ),
  );
}

Widget dBSlatIcon(DesignState appState) {
  bool isSelected = appState.slatAdditionType == 'DB-L-120';
  return GestureDetector(
    onTap: () {
      appState.setSlatAdditionType('DB-L-120');
    },
    child: Container(
      width: 40, // Shrunk size
      height: 40,
      margin: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
        borderRadius: BorderRadius.circular(6),
        border: isSelected
            ? Border.all(color: Colors.black, width: 2)
            : null,
        boxShadow: isSelected
            ? [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.5),
            blurRadius: 6,
            spreadRadius: 1,
          )
        ]
            : [],
      ),
    ),
  );
}

//  Widgets/painters for labeled pictographs in slat palette
typedef GlyphPainterBuilder = CustomPainter Function(Color color);

class SlatOption extends StatelessWidget {
  final String label;
  final bool isSelected;
  final Color color;
  final VoidCallback onTap;
  final GlyphPainterBuilder painterBuilder;

  const SlatOption({
    super.key,
    required this.label,
    required this.isSelected,
    required this.color,
    required this.painterBuilder,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? Colors.black : Colors.grey.shade300,
            width: isSelected ? 2 : 1,
          ),
          boxShadow: isSelected
              ? [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.08),
              blurRadius: 6,
              spreadRadius: 1,
              offset: const Offset(0, 1),
            )
          ]
              : [],
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey.shade800,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
            ),
            SizedBox(
              width: 40,
              height: 40,
              child: CustomPaint(
                painter: painterBuilder(color),
              ),
            ),
            SizedBox(width: 10)
          ],
        ),
      ),
    );
  }
}

class SlatGlyphPainter extends CustomPainter {
  final Color color;
  SlatGlyphPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final double padding = 6;
    final double barHeight = 8;

    final rect = Rect.fromLTWH(
      - padding * 7,
      (size.height - barHeight) / 2,
      size.width + 6 * padding,
      barHeight,
    );

    canvas.drawRect(rect, paint);
  }

  @override
  bool shouldRepaint(covariant SlatGlyphPainter oldDelegate) => oldDelegate.color != color;
}

class DoubleBarrelGlyphPainter extends CustomPainter {
  final Color color;
  final String dBType;

  DoubleBarrelGlyphPainter(this.dBType, {required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final double padding = 6;
    final double barHeight = 8;
    final double spacing = 6;
    final totalHeight = barHeight * 2 + spacing;
    final top = (size.height - totalHeight) / 2;

    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = barHeight;

    // Compute the four points used by the path so we can derive direction for arrow
    late Offset p1, p2, p3, p4;
    Path path = Path();

    if (dBType == 'DB-L-60') {
      p3 = Offset(-padding * 9 + size.width + 6 * padding, top + barHeight * 2.5);
      p4 = Offset(-padding * 9, top + barHeight * 2.5);
      p1 = Offset(-padding * 9 + 2 * padding, top + barHeight / 2);
      p2 = Offset(-padding * 9 + size.width + 6 * padding + 2 * padding, top + barHeight / 2);
    }
    else if (dBType == 'DB-R-60') {
      p3 = Offset(-padding * 9 + size.width + 6 * padding, top + barHeight / 2);
      p4 = Offset(-padding * 9, top + barHeight / 2);
      p1 = Offset(-padding * 9 + 2 * padding, top + barHeight * 2.5);
      p2 = Offset(-padding * 9 + size.width + 6 * padding + 2 * padding, top + barHeight * 2.5);
    }
    else if (dBType == 'DB-L-120') {
      p3 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight * 2.5);
      p4 = Offset(-padding * 7, top + barHeight * 2.5);
      p1 = Offset(-padding * 7 - 2 * padding, top + barHeight / 2);
      p2 = Offset(-padding * 7 + size.width + 6 * padding - 2 * padding, top + barHeight / 2);
    }
    else if (dBType == 'DB-R-120') {
      p3 = Offset(-padding * 7 + size.width + 6 * padding,top + barHeight / 2);
      p4 = Offset(-padding * 7, top + barHeight / 2);
      p1 = Offset(-padding * 7 - 2 * padding, top + barHeight * 2.5);
      p2 = Offset(-padding * 7 + size.width + 6 * padding - 2 * padding, top + barHeight * 2.5);
    }
    else if (dBType == 'DB-L') {
      p3 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight * 2.5);
      p4 = Offset(-padding * 7, top + barHeight * 2.5);
      p1 = Offset(-padding * 7, top + barHeight / 2);
      p2 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight / 2);
    }
    else if (dBType == 'DB-R') {
      p3 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight / 2);
      p4 = Offset(-padding * 7, top + barHeight / 2);
      p1 = Offset(-padding * 7, top + barHeight * 2.5);
      p2 = Offset(-padding * 7 + size.width + 6 * padding, top + barHeight * 2.5);
    }
    else {
      // nothing to draw
      return;
    }

    // Draw the stroked path
    path.moveTo(p1.dx, p1.dy);
    path.lineTo(p2.dx, p2.dy);
    path.lineTo(p3.dx, p3.dy);
    path.lineTo(p4.dx, p4.dy);
    canvas.drawPath(path, paint);

    // Arrowhead (at p4) and tail (near p1), styled to match SlatPainter aids
    final Offset endDir = p4 - p3;
    final Offset startDir = p2 - p1;

    if (endDir.distance > 0.001 && startDir.distance > 0.001) {
      final Offset vEnd = endDir / endDir.distance;   // normalized
      final Offset vStart = startDir / startDir.distance;

      // Arrowhead — filled triangle pointing along vEnd
      final double arrowSize = barHeight * 1.8;          // modest size for sidebar glyph
      final double arrowAngle = pi / 4.5; // ~40° wings
      final Offset tip = p4 - Offset(5,0); // added offset for beauty
      final double theta = vEnd.direction;
      final Offset left  = tip - Offset.fromDirection(theta - arrowAngle, arrowSize);
      final Offset right = tip - Offset.fromDirection(theta + arrowAngle, arrowSize);

      final Path arrowPath = Path()
        ..moveTo(tip.dx, tip.dy)
        ..lineTo(left.dx, left.dy)
        ..lineTo(right.dx, right.dy)
        ..close();

      final Paint fillPaint = Paint()
        ..color = color
        ..style = PaintingStyle.fill;

      canvas.drawPath(arrowPath, fillPaint);

      // Tail — short transverse line near the start
      final double tailHalfLen = barHeight * 0.6; // length each side from center
      final double phi = vStart.direction;
      final Offset tailCenter = p1 - vStart * (barHeight * 0.4); // pull slightly "behind" start
      final Offset tailA = tailCenter + Offset.fromDirection(phi - pi / 2, tailHalfLen);
      final Offset tailB = tailCenter + Offset.fromDirection(phi + pi / 2, tailHalfLen);

      final Paint tailPaint = Paint()
        ..color = color
        ..strokeWidth = barHeight / 2
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      canvas.drawLine(tailA, tailB, tailPaint);
    }

  }

  @override
  bool shouldRepaint(covariant DoubleBarrelGlyphPainter oldDelegate) => oldDelegate.color != color;
}


class SlatAddPanel extends StatefulWidget {
  const SlatAddPanel({super.key});

  @override
  State<SlatAddPanel> createState() => _SlatAddPanel();
}


class _SlatAddPanel extends State<SlatAddPanel> with WidgetsBindingObserver {
  FocusNode slatAddFocusNode = FocusNode();
  TextEditingController slatAddTextController = TextEditingController();
  late final ScrollController _slatPaletteCtrl;

  @override
  void initState() {
    super.initState();
    _slatPaletteCtrl = ScrollController();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      var appState = context.read<DesignState>(); // Use read instead of watch
      slatAddTextController.text = appState.slatAddCount.toString();
      slatAddFocusNode.addListener(() {
        if (!slatAddFocusNode.hasFocus) {
          _updateSlatAddCount(appState);
        }
      });
    });
  }

  void _updateSlatAddCount(DesignState appState) {
    int? newValue = int.tryParse(slatAddTextController.text);
    if (newValue != null && newValue >= 1 && newValue <= 32) {
      appState.updateSlatAddCount(newValue);
    } else if (newValue != null && newValue < 1) {
      appState.updateSlatAddCount(1);
    } else {
      appState.updateSlatAddCount(32);
    }
    slatAddTextController.text = appState.slatAddCount.toString();
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();

    // to handle resets such as changing the grid mode
    if (!slatAddFocusNode.hasFocus && slatAddTextController.text != appState.slatAddCount.toString()) {
      slatAddTextController.text = appState.slatAddCount.toString();
    }

    final List<Widget> slatTiles = [
      SlatOption(
        label: 'Standard Slat',
        isSelected: appState.slatAdditionType == 'tube',
        color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
        painterBuilder: (color) => SlatGlyphPainter(color: color),
        onTap: () => appState.setSlatAdditionType('tube'),
      ),
      if (appState.gridMode == '90') ...[
        SlatOption(
          label: 'DB-L',
          isSelected: appState.slatAdditionType == 'DB-L',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-L', color: color),
          onTap: () => appState.setSlatAdditionType('DB-L'),
        ),
        SlatOption(
          label: 'DB-R',
          isSelected: appState.slatAdditionType == 'DB-R',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-R', color: color),
          onTap: () => appState.setSlatAdditionType('DB-R'),
        ),
      ] else ...[
        SlatOption(
          label: 'DB-L-60',
          isSelected: appState.slatAdditionType == 'DB-L-60',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-L-60', color: color),
          onTap: () => appState.setSlatAdditionType('DB-L-60'),
        ),
        SlatOption(
          label: 'DB-L-120',
          isSelected: appState.slatAdditionType == 'DB-L-120',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-L-120', color: color),
          onTap: () => appState.setSlatAdditionType('DB-L-120'),
        ),
        SlatOption(
          label: 'DB-R-60',
          isSelected: appState.slatAdditionType == 'DB-R-60',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-R-60', color: color),
          onTap: () => appState.setSlatAdditionType('DB-R-60'),
        ),
        SlatOption(
          label: 'DB-R-120',
          isSelected: appState.slatAdditionType == 'DB-R-120',
          color: appState.layerMap[appState.selectedLayerKey]?['color'] ?? Colors.grey,
          painterBuilder: (color) => DoubleBarrelGlyphPainter('DB-R-120', color: color),
          onTap: () => appState.setSlatAdditionType('DB-R-120'),
        ),
      ],
    ];

    return Column(
        children: [
          Divider(thickness: 1, color: Colors.grey.shade200),
          Text(
            "Slat Palette", // Title above the segmented button
            style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
          ),
          Container(
            width: (40 + 4) * 6 + 12,
            padding: const EdgeInsets.all(6),
            child: SizedBox(
              height: 180, // ~3 tiles visible
              child: Scrollbar(
                thumbVisibility: true,
                controller: _slatPaletteCtrl,
                child: ListView.separated(
                  controller: _slatPaletteCtrl,
                  itemCount: slatTiles.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 6),
                  itemBuilder: (_, i) => slatTiles[i],
                ),
              ),
            ),
          ),
          Divider(thickness: 1, color: Colors.grey.shade200),
          Text(
            "Number of Slats to Draw", // Title above the segmented button
            style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
          ),
          SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SizedBox(
                width: 180,
                child: TextField(
                  controller: slatAddTextController,
                  focusNode: slatAddFocusNode,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: 'Manual Input',
                  ),
                  textInputAction: TextInputAction.done,
                  inputFormatters: <TextInputFormatter>[FilteringTextInputFormatter.digitsOnly],
                  onSubmitted: (value) {
                    _updateSlatAddCount(appState);
                  },
                ),
              ),
              IconButton(
                icon: Icon(Icons.arrow_upward),
                onPressed: () {
                  if (appState.slatAddCount < 32) {
                    appState.updateSlatAddCount(appState.slatAddCount + 1);
                    slatAddTextController.text = appState.slatAddCount.toString();
                  }
                },
              ),
              IconButton(
                icon: Icon(Icons.arrow_downward),
                onPressed: () {
                  if (appState.slatAddCount > 1) {
                    appState.updateSlatAddCount(appState.slatAddCount - 1);
                    slatAddTextController.text = appState.slatAddCount.toString();
                  }
                },
              ),
            ],
          ),
          SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ActionChip(
                label: Text('1'),
                onPressed: () {
                  appState.updateSlatAddCount(1);
                  slatAddTextController.text = appState.slatAddCount.toString();
                },
              ),
              SizedBox(width: 10),
              ActionChip(
                label: Text('8'),
                onPressed: () {
                  appState.updateSlatAddCount(8);
                  slatAddTextController.text = appState.slatAddCount.toString();
                },
              ),
              SizedBox(width: 10),
              ActionChip(
                label: Text('16'),
                onPressed: () {
                  appState.updateSlatAddCount(16);
                  slatAddTextController.text = appState.slatAddCount.toString();
                },
              ),
              SizedBox(width: 10),
              ActionChip(
                label: Text('32'),
                onPressed: () {
                  appState.updateSlatAddCount(32);
                  slatAddTextController.text = appState.slatAddCount.toString();
                },
              ),
            ],
          ),
          ]
    );
  }

  @override
  void dispose() {
    slatAddFocusNode.dispose();
    _slatPaletteCtrl.dispose();
    slatAddTextController.dispose();
    super.dispose();
  }
}