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

  const PlateHeaderBar({
    super.key,
    required this.onClose,
    required this.onExport,
    required this.onToggleCollapse,
    required this.isHovered,
    required this.onHoverChanged,
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
              const Align(
                alignment: Alignment.center,
                child: Text(
                  'Echo Plate Layout',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 22),
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

// ---------------------------------------------------------------------------
// PlateActionBar — contains Remove All button
// ---------------------------------------------------------------------------

class PlateActionBar extends StatelessWidget {
  final VoidCallback onRemoveAll;
  final VoidCallback onDeleteSelected;
  final VoidCallback onDuplicateSelected;
  final bool hasSelection;

  const PlateActionBar({
    super.key,
    required this.onRemoveAll,
    required this.onDeleteSelected,
    required this.onDuplicateSelected,
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

  const PlateColorKeyBar({super.key});

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
    );
  }
}
