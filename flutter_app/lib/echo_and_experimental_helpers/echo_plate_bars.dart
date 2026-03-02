import 'package:flutter/material.dart';
import 'echo_category_colors.dart';

// ---------------------------------------------------------------------------
// PlateHeaderBar — title bar with close/export and collapse toggle
// ---------------------------------------------------------------------------

class PlateHeaderBar extends StatelessWidget {
  final VoidCallback onClose;
  final VoidCallback onExport;
  final VoidCallback onToggleCollapse;
  final bool isHovered;
  final ValueChanged<bool> onHoverChanged;
  final String experimentTitle;
  final VoidCallback? onRenameExperiment;

  const PlateHeaderBar({
    super.key,
    required this.onClose,
    required this.onExport,
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
              Positioned(
                right: 0,
                child: IconButton(
                  icon: const Icon(Icons.download, size: 24),
                  color: Colors.white,
                  tooltip: 'Export PDF',
                  onPressed: onExport,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
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
  final bool hasSelection;

  const PlateActionBar({
    super.key,
    required this.onRemoveAll,
    required this.onDeleteSelected,
    required this.onDuplicateSelected,
    required this.onConfigAll,
    required this.onEditSelected,
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
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
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
            icon: Icon(Icons.delete_outline, size: 18, color: hasSelection ? Colors.orange.shade700 : Colors.grey),
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
    ('Undefined', defaultCategoryColorHex),
  ];

  final bool showMetricView;
  final VoidCallback onToggleMetricView;

  const PlateColorKeyBar({super.key, required this.showMetricView, required this.onToggleMetricView});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12)),
        border: Border(top: BorderSide(color: Colors.grey.shade300)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
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
          ),
          _MetricViewToggle(active: showMetricView, onTap: onToggleMetricView),
        ],
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
