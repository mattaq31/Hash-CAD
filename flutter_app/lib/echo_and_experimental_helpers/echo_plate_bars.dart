import 'package:flutter/material.dart';
import 'echo_category_colors.dart';
import 'echo_plate_constants.dart' show EchoWellColorMode;

// ---------------------------------------------------------------------------
// PlateHeaderBar — title bar with close/export and collapse toggle
// ---------------------------------------------------------------------------

class PlateHeaderBar extends StatelessWidget {
  final VoidCallback onClose;
  final VoidCallback onToggleCollapse;
  final bool isHovered;
  final ValueChanged<bool> onHoverChanged;
  final String experimentTitle;
  final VoidCallback? onRenameExperiment;

  const PlateHeaderBar({
    super.key,
    required this.onClose,
    required this.onToggleCollapse,
    required this.isHovered,
    required this.onHoverChanged,
    required this.experimentTitle,
    this.onRenameExperiment,
  });

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => onHoverChanged(true),
      onExit: (_) => onHoverChanged(false),
      child: GestureDetector(
        onTap: onToggleCollapse,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: isHovered ? Colors.blueGrey.shade800 : Colors.blueGrey,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              Positioned(
                left: 0,
                child: IconButton(
                  icon: const Icon(Icons.close, size: 24),
                  color: Colors.white,
                  onPressed: onClose,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ),
              Align(
                alignment: Alignment.center,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Echo Export: $experimentTitle',
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 22),
                    ),
                    if (onRenameExperiment != null) ...[
                      const SizedBox(width: 6),
                      _HeaderEditButton(onTap: onRenameExperiment!),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _HeaderEditButton extends StatefulWidget {
  final VoidCallback onTap;
  const _HeaderEditButton({required this.onTap});

  @override
  State<_HeaderEditButton> createState() => _HeaderEditButtonState();
}

class _HeaderEditButtonState extends State<_HeaderEditButton> {
  bool _hovering = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hovering = true),
      onExit: (_) => setState(() => _hovering = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: Icon(Icons.edit, size: 18, color: _hovering ? Colors.white : Colors.white54),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// PlateActionBar — contains Remove All button
// ---------------------------------------------------------------------------

class PlateActionBar extends StatelessWidget {
  final VoidCallback onRemoveAll;
  final VoidCallback onDeleteSelected;
  final VoidCallback onDuplicateSelected;
  final VoidCallback onConfigAll;
  final VoidCallback onEditSelected;
  final VoidCallback onSelectAll;
  final VoidCallback onMarkManualHandles;
  final VoidCallback onMassManualEdit;
  final bool hasSelection;

  const PlateActionBar({
    super.key,
    required this.onRemoveAll,
    required this.onDeleteSelected,
    required this.onDuplicateSelected,
    required this.onConfigAll,
    required this.onEditSelected,
    required this.onSelectAll,
    required this.onMarkManualHandles,
    required this.onMassManualEdit,
    required this.hasSelection,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        border: Border(bottom: BorderSide(color: Colors.grey.shade200)),
      ),
      child: Row(
        children: [
          // Manual handle buttons on the left
          TextButton.icon(
            onPressed: hasSelection ? onMarkManualHandles : null,
            icon: Icon(Icons.zoom_in, size: 18,
                color: hasSelection ? Colors.deepPurple.shade700 : Colors.grey),
            label: Text('Zoom In on Handles',
                style: TextStyle(fontSize: 12,
                    color: hasSelection ? Colors.deepPurple.shade700 : Colors.grey)),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          const SizedBox(width: 8),
          TextButton.icon(
            onPressed: onMassManualEdit,
            icon: Icon(Icons.auto_fix_high, size: 18, color: Colors.deepPurple.shade700),
            label: Text('Mass Manual Handle Marking',
                style: TextStyle(fontSize: 12, color: Colors.deepPurple.shade700)),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          const Spacer(),
          // Rest of the toolbar on the right
          TextButton.icon(
            onPressed: onSelectAll,
            icon: Icon(Icons.select_all, size: 18, color: Colors.indigo.shade700),
            label: Text('Select All', style: TextStyle(fontSize: 12, color: Colors.indigo.shade700)),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          const SizedBox(width: 8),
          TextButton.icon(
            onPressed: onConfigAll,
            icon: Icon(Icons.tune, size: 18, color: Colors.teal.shade700),
            label: Text('Config All', style: TextStyle(fontSize: 12, color: Colors.teal.shade700)),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          const SizedBox(width: 8),
          TextButton.icon(
            onPressed: hasSelection ? onEditSelected : null,
            icon: Icon(Icons.edit_note, size: 18, color: hasSelection ? Colors.teal.shade700 : Colors.grey),
            label: Text('Edit Selected',
                style: TextStyle(fontSize: 12, color: hasSelection ? Colors.teal.shade700 : Colors.grey)),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          const SizedBox(width: 16),
          TextButton.icon(
            onPressed: hasSelection ? onDuplicateSelected : null,
            icon: Icon(Icons.copy, size: 18, color: hasSelection ? Colors.blue.shade700 : Colors.grey),
            label: Text('Duplicate',
                style: TextStyle(fontSize: 12, color: hasSelection ? Colors.blue.shade700 : Colors.grey)),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          const SizedBox(width: 8),
          TextButton.icon(
            onPressed: hasSelection ? onDeleteSelected : null,
            icon: Icon(Icons.delete_outline, size: 18,
                color: hasSelection ? Colors.orange.shade700 : Colors.grey),
            label: Text('Remove Selected',
                style: TextStyle(fontSize: 12, color: hasSelection ? Colors.orange.shade700 : Colors.grey)),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          const SizedBox(width: 8),
          TextButton.icon(
            onPressed: onRemoveAll,
            icon: Icon(Icons.clear_all, size: 18, color: Colors.red.shade700),
            label: Text('Remove All', style: TextStyle(fontSize: 12, color: Colors.red.shade700)),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// PlateColorKeyBar — shows color legend at bottom
// ---------------------------------------------------------------------------

class PlateColorKeyBar extends StatelessWidget {
  static final _entries = [
    ('Flat', handleCategoryColors['FLAT']!),
    ('Assembly Handle', handleCategoryColors['ASSEMBLY_HANDLE']!),
    ('Seed', handleCategoryColors['SEED']!),
    ('Cargo', handleCategoryColors['CARGO']!),
    ('Manual', handleCategoryColors['MANUAL']!),
    ('Fluorophore', handleCategoryColors['FLUOROPHORE']!),
  ];

  final bool showMetricView;
  final VoidCallback onToggleMetricView;
  final EchoWellColorMode colorMode;
  final ValueChanged<EchoWellColorMode> onColorModeChanged;

  const PlateColorKeyBar({
    super.key,
    required this.showMetricView,
    required this.onToggleMetricView,
    required this.colorMode,
    required this.onColorModeChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        border: Border(top: BorderSide(color: Colors.grey.shade300)),
      ),
      child: Row(
        children: [
          const Expanded(child: SizedBox.shrink()),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (var i = 0; i < _entries.length; i++) ...[
                if (i > 0) const SizedBox(width: 16),
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: Color(_entries[i].$2),
                    borderRadius: BorderRadius.circular(2),
                    border: Border.all(color: Colors.grey.shade400, width: 0.5),
                  ),
                ),
                const SizedBox(width: 4),
                Text(_entries[i].$1, style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
              ],
            ],
          ),
          Expanded(
            child: Align(
              alignment: Alignment.centerRight,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _ColorModeSelector(colorMode: colorMode, onChanged: onColorModeChanged),
                  const SizedBox(width: 16),
                  _MetricViewToggle(active: showMetricView, onTap: onToggleMetricView),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ColorModeSelector extends StatefulWidget {
  final EchoWellColorMode colorMode;
  final ValueChanged<EchoWellColorMode> onChanged;
  const _ColorModeSelector({required this.colorMode, required this.onChanged});

  @override
  State<_ColorModeSelector> createState() => _ColorModeSelectorState();
}

class _ColorModeSelectorState extends State<_ColorModeSelector> {
  bool _hovering = false;

  String get _label => switch (widget.colorMode) {
    EchoWellColorMode.natural => 'Natural',
    EchoWellColorMode.layer => 'By Layer',
    EchoWellColorMode.group => 'By Group',
  };

  @override
  Widget build(BuildContext context) {
    final color = _hovering ? Colors.teal.shade900 : Colors.teal.shade700;
    return PopupMenuButton<EchoWellColorMode>(
      tooltip: 'Coloring Scheme',
      onSelected: widget.onChanged,
      itemBuilder: (context) => [
        PopupMenuItem(
          value: EchoWellColorMode.natural,
          child: Row(children: [
            Icon(Icons.palette, size: 16,
                color: widget.colorMode == EchoWellColorMode.natural ? Colors.teal : null),
            const SizedBox(width: 8),
            const Text('Natural', style: TextStyle(fontSize: 12)),
          ]),
        ),
        PopupMenuItem(
          value: EchoWellColorMode.layer,
          child: Row(children: [
            Icon(Icons.layers, size: 16,
                color: widget.colorMode == EchoWellColorMode.layer ? Colors.teal : null),
            const SizedBox(width: 8),
            const Text('By Layer', style: TextStyle(fontSize: 12)),
          ]),
        ),
        PopupMenuItem(
          value: EchoWellColorMode.group,
          child: Row(children: [
            Icon(Icons.workspaces, size: 16,
                color: widget.colorMode == EchoWellColorMode.group ? Colors.teal : null),
            const SizedBox(width: 8),
            const Text('By Group', style: TextStyle(fontSize: 12)),
          ]),
        ),
      ],
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        onEnter: (_) => setState(() => _hovering = true),
        onExit: (_) => setState(() => _hovering = false),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.palette, size: 16, color: color),
            const SizedBox(width: 4),
            Text(_label, style: TextStyle(fontSize: 11, color: color)),
          ],
        ),
      ),
    );
  }
}

class _MetricViewToggle extends StatefulWidget {
  final bool active;
  final VoidCallback onTap;
  const _MetricViewToggle({required this.active, required this.onTap});

  @override
  State<_MetricViewToggle> createState() => _MetricViewToggleState();
}

class _MetricViewToggleState extends State<_MetricViewToggle> {
  bool _hovering = false;

  @override
  Widget build(BuildContext context) {
    final color = widget.active
        ? Colors.teal.shade700
        : (_hovering ? Colors.grey.shade600 : Colors.grey.shade400);
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hovering = true),
      onExit: (_) => setState(() => _hovering = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: Tooltip(
          message: widget.active ? 'Hide quantities' : 'Show quantities',
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(widget.active ? Icons.visibility : Icons.visibility_off, size: 16, color: color),
              const SizedBox(width: 4),
              Text('Material Quantities', style: TextStyle(fontSize: 11, color: color)),
            ],
          ),
        ),
      ),
    );
  }
}
