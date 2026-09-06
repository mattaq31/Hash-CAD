import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../crisscross_core/common_utilities.dart';
import '../app_management/shared_app_state.dart';


void showWarning(BuildContext context, String title, String message){
  showDialog<String>(
      context: context,
      builder: (BuildContext context) =>
          AlertDialog(
            title: Text(title),
            content: RichText(
              text: TextSpan(
                style: TextStyle(color: Colors.black87, fontSize: 16),
                children: [
                  TextSpan(text: message),
                ],
              ),
            ),
            actions: <Widget>[
              TextButton(
                onPressed: () =>
                    Navigator.pop(context, 'OK'),
                child: const Text('OK'),
              ),
            ],
          ));
}

/// Shows dialog for selecting seed handles with options for group or individual selection.
/// Returns 'group', 'single', or null (if cancelled).
Future<String?> showSeedHandleSelectionDialog(BuildContext context, String seedID) async {
  return showDialog<String>(
    context: context,
    builder: (BuildContext context) => AlertDialog(
      title: Text('Seed Handle Selection'),
      content: RichText(
        text: TextSpan(
          style: TextStyle(color: Colors.black87, fontSize: 16),
          children: [
            TextSpan(text: 'This handle belongs to Seed $seedID. How would you like to proceed?'),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context, 'group'),
          child: const Text('Select all seed handles'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, 'single'),
          child: const Text('Select just this handle'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, null),
          child: const Text('Cancel'),
        ),
      ],
    ),
  );
}

/// Shows dialog for deleting seed handles with options for group or individual deletion.
/// Returns 'group', 'single', or null (if cancelled).
Future<String?> showSeedHandleDeletionDialog(BuildContext context, String seedID) async {
  return showDialog<String>(
    context: context,
    builder: (BuildContext context) => AlertDialog(
      title: Text('Delete Seed Handle'),
      content: RichText(
        text: TextSpan(
          style: TextStyle(color: Colors.black87, fontSize: 16),
          children: [
            TextSpan(text: 'This handle belongs to Seed $seedID. How would you like to proceed?'),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.pop(context, 'group'),
          child: const Text('Delete entire seed'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, 'single'),
          child: const Text('Delete just this handle'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, null),
          child: const Text('Cancel'),
        ),
      ],
    ),
  );
}

void showKeyboardShortcutsDialog(BuildContext context) {
  showDialog(
    context: context,
    builder: (context) {
      return AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: Text(
          "Keyboard Shortcuts",
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _shortcutItem("'R'", "Rotate slat draw direction"),
              _shortcutItem("'F'", "Flip multi-slat draw direction"),
              _shortcutItem("'T'", "Transpose slat draw direction (only for straight slats in move mode)"),
              _shortcutItem("'Up/Down arrow keys'", "Change layer"),
              _shortcutItem("'A'", "Add new layer"),
              _shortcutItem("'1'", "Switch to 'Add' mode"),
              _shortcutItem("'2'", "Switch to 'Delete' mode"),
              _shortcutItem("'3'", "Switch to 'Edit' mode"),
              _shortcutItem("'E'", "Edit selected handles while in the Assembly Handles panel"),
              _shortcutItem("'L'", "Lock / unlock all edits"),
              _shortcutItem("'CMD/Ctrl-Z'", "Undo last action"),
              _shortcutItem("'CMD-Shift-Z/Ctrl-Y'", "Redo last action"),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text("Close"),
          ),
        ],
      );
    },
  );
}

Widget _shortcutItem(String key, String description) {
  return Padding(
    padding: const EdgeInsets.symmetric(vertical: 4.0),
    child: Text.rich(
      TextSpan(
        children: [
          TextSpan(
            text: "$key ",
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black),
          ),
          TextSpan(
            text: description,
            style: TextStyle(color: Colors.grey.shade700),
          ),
        ],
      ),
      style: TextStyle(fontSize: 14),
    ),
  );
}

/// Shows dialog for editing assembly handle value and enforce status.
/// Returns a map with:
/// - 'value' (int): The new handle value (ignored if enforceInPlace is true)
/// - 'enforce' (bool): Whether to enforce the value
/// - 'enforceInPlace' (bool): If true, enforce current values without changing them
/// Returns null if cancelled.
Future<Map<String, dynamic>?> showAssemblyHandleEditDialog(
  BuildContext context,
  DesignState appState,
  String currentValue,
  HandleKey handleKey,
) async {
  final controller = TextEditingController(text: currentValue);
  bool enforce = appState.assemblyLinkManager.getEnforceValue(handleKey) != null &&
      appState.assemblyLinkManager.getEnforceValue(handleKey)! > 0;
  bool enforceInPlace = false;

  return showDialog<Map<String, dynamic>>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (context, setDialogState) => AlertDialog(
        title: const Text('Edit Assembly Handle'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: controller,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              decoration: const InputDecoration(
                labelText: 'Handle Value (1-999)',
                border: OutlineInputBorder(),
              ),
              autofocus: true,
              enabled: !enforceInPlace,
            ),
            const SizedBox(height: 16),
            CheckboxListTile(
              title: const Text('Enforce this value'),
              subtitle: const Text('Lock this handle to the specified value'),
              value: enforceInPlace || enforce,
              onChanged: enforceInPlace
                  ? null
                  : (value) {
                      setDialogState(() => enforce = value ?? false);
                    },
            ),
            const SizedBox(height: 16),
            CheckboxListTile(
              title: const Text('Enforce in-place'),
              subtitle: const Text('Lock selected handles to their current values'),
              value: enforceInPlace,
              onChanged: (value) {
                setDialogState(() => enforceInPlace = value ?? false);
              },
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              if (enforceInPlace) {
                Navigator.pop(ctx, {'value': 0, 'enforce': true, 'enforceInPlace': true});
              } else {
                int? val = int.tryParse(controller.text);
                if (val != null && val > 0 && val <= 999) {
                  Navigator.pop(ctx, {'value': val, 'enforce': enforce, 'enforceInPlace': false});
                }
              }
            },
            child: const Text('Apply'),
          ),
        ],
      ),
    ),
  );
}