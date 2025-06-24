import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';


class FloatingEditableTitle extends StatefulWidget {
  const FloatingEditableTitle({super.key});

  @override
  State<FloatingEditableTitle> createState() => _FloatingEditableTitleState();
}

class _FloatingEditableTitleState extends State<FloatingEditableTitle> {
  bool minimized = false;

  void _showEditDialog(BuildContext context, DesignState appState) {
    final controller = TextEditingController(text: appState.designName);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Design Name'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'Enter design name',
          ),
          onSubmitted: (value) {
            appState.setDesignName(value);
            Navigator.pop(context);
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              appState.setDesignName(controller.text);
              Navigator.pop(context);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<DesignState>();
    final colorScheme = Theme.of(context).colorScheme;

    // Define the maximum height of the container
    const double expandedHeight = 48;
    const double minimizedHeight = 36;
    const double fixedHeight = expandedHeight; // Choose the tallest height

    return SizedBox(
      height: fixedHeight,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        switchInCurve: Curves.easeOut,
        switchOutCurve: Curves.easeIn,
        transitionBuilder: (child, animation) {
          return FadeTransition(
            opacity: animation,
            child: SlideTransition(
              position: Tween<Offset>(
                begin: const Offset(0.0, 0.1),
                end: Offset.zero,
              ).animate(animation),
              child: child,
            ),
          );
        },
        child: minimized
            ? GestureDetector(
          key: const ValueKey('minimized'),
          onTap: () => setState(() => minimized = false),
          child: Container(
            width: minimizedHeight,
            height: minimizedHeight,
            decoration: BoxDecoration(
              color: colorScheme.primary,
              shape: BoxShape.circle,
              boxShadow: const [
                BoxShadow(
                  color: Colors.black45,
                  blurRadius: 8,
                  offset: Offset(0, 2),
                )
              ],
            ),
            child: const Icon(Icons.title, color: Colors.white, size: 20),
          ),
        )
            : // inside your expanded state:
        GestureDetector(
          key: const ValueKey('expanded'),
          onTap: () => setState(() => minimized = true),
          child: IntrinsicWidth(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: colorScheme.primary,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: const [
                    BoxShadow(
                      color: Colors.black45,
                      blurRadius: 8,
                      offset: Offset(0, 2),
                    )
                  ],
                ),
                height: expandedHeight,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Flexible(
                      child: Text(
                        appState.designName,
                        style: const TextStyle(
                          fontSize: 18,
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          overflow: TextOverflow.ellipsis,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: () {
                        _showEditDialog(context, appState);
                      },
                      child: const Icon(Icons.edit, size: 20, color: Colors.white70),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}