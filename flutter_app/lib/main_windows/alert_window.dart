import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../crisscross_core/handle_plates.dart';
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
              _shortcutItem("'T'", "Transpose slat draw direction"),
              _shortcutItem("'Up/Down arrow keys'", "Change layer"),
              _shortcutItem("'A'", "Add new layer"),
              _shortcutItem("'1'", "Switch to 'Add' mode"),
              _shortcutItem("'2'", "Switch to 'Delete' mode"),
              _shortcutItem("'3'", "Switch to 'Edit' mode"),
              _shortcutItem("'E'", "Edit selected handles while in the Assembly Handles panel"),
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


void displayPlateInfo(BuildContext context, String plateName, HashCadPlate plate) {
  showDialog(
    context: context,
    builder: (_) {
      return AlertDialog(
        title: Text('Detailed Plate View: $plateName'),
        content: SizedBox(
          width: 800, // Smaller width like your warning box
          height: 500, // Explicit height to avoid intrinsic measurement
          child: ListView.builder(
            itemCount: plate.uniqueIds.length,
            itemBuilder: (context, index) {
              final id = plate.uniqueIds[index];
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4.0),
                child: _buildSlatPictograph(id, plate),
              );
            },
          ),
        ),
        actions: [
          TextButton(
            child: Text('Close'),
            onPressed: () => Navigator.of(context).pop(),
          )
        ],
      );
    },
  );
}

Widget _buildSlatPictograph(String id, HashCadPlate plate) {
  const armCount = 32;
  const armWidth = 10.0;
  const armSpacing = 5.0;
  const rodWidth = armCount * (armWidth + armSpacing);
  const armHeight = 20.0;
  const rodHeight = 25.0;
  const labelWidth = 100.0;

  bool isArmAvailable(int pos, {required bool isTop}) {
    return plate.contains(plate.getCategoryFromID(id), pos + 1, isTop ? 5 : 2, id);
  }

  Widget buildArms(bool isTop) {
    return SizedBox(
      width: rodWidth,
      height: armHeight,
      child: Row(
        children: [
          SizedBox(width: armSpacing / 2), // Leading spacing
          ...List.generate(armCount, (i) {
            return Container(
              width: armWidth,
              height: armHeight,
              margin: EdgeInsets.only(right: i == armCount - 1 ? 0 : armSpacing),
              color: isArmAvailable(i, isTop: isTop) ? Colors.green : Colors.grey[400],
            );
          }),
        ],
      ),
    );
  }

  Widget buildRod() {
    return Stack(
      children: [
        // The rod background
        Container(
          width: rodWidth,
          height: rodHeight,
          color: Colors.black,
        ),
        // Number overlays
        Positioned.fill(
          child: Row(
            children: List.generate(armCount, (i) {
              return SizedBox(
                width: armWidth + armSpacing,
                child: Center(
                  child: Text(
                    '${i + 1}',
                    style: TextStyle(
                      fontSize: 8,
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
      ],
    );
  }

  return Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Left label
        SizedBox(
          width: labelWidth,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('H5', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
              Text('Handle ID:', style: TextStyle(fontSize: 10)),
              Tooltip(
                message: id == "BLANK" ? "FLAT" : id,
                child: Text(
                  id == "BLANK" ? "FLAT" : id,
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                  softWrap: false,
                  overflow: TextOverflow.ellipsis,
                  maxLines: 1,
                ),
              ),
              Text('H2', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        SizedBox(width: 8),
        // Pictograph centered
        Column(
          children: [
            buildArms(true),
            buildRod(),
            buildArms(false),
          ],
        ),
        SizedBox(width: 8),
        // Right label
        SizedBox(
          width: labelWidth,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('H5', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
              RichText(
                textAlign: TextAlign.start,
                text: TextSpan(
                  style: TextStyle(fontSize: 10, color: Colors.black),
                  children: [
                    TextSpan(text: 'Total Staples: '),
                    TextSpan(
                      text: '${plate.countID(id)}',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
              Tooltip(
                message: plate.getCategoryFromID(id),
                child: SizedBox(
                  width: 100, // Adjust width as needed
                  child: Text.rich(
                    TextSpan(
                      style: TextStyle(fontSize: 10, color: Colors.black),
                      children: [
                        TextSpan(text: 'Category: '),
                        TextSpan(
                          text: plate.getCategoryFromID(id),
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    softWrap: false,
                  ),
                ),
              ),
              Text('H2', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ],
    ),
  );
}

/// Shows dialog for editing assembly handle value and enforce status.
/// Returns a map with 'value' (int) and 'enforce' (bool), or null if cancelled.
Future<Map<String, dynamic>?> showAssemblyHandleEditDialog(
  BuildContext context,
  DesignState appState,
  String currentValue,
  HandleKey handleKey,
) async {
  final controller = TextEditingController(text: currentValue);
  bool enforce = appState.assemblyLinkManager.getEnforceValue(handleKey) != null &&
      appState.assemblyLinkManager.getEnforceValue(handleKey)! > 0;

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
            ),
            const SizedBox(height: 16),
            CheckboxListTile(
              title: const Text('Enforce this value'),
              subtitle: const Text('Lock this handle to the specified value'),
              value: enforce,
              onChanged: (value) {
                setDialogState(() => enforce = value ?? false);
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
              int? val = int.tryParse(controller.text);
              if (val != null && val > 0 && val <= 999) {
                Navigator.pop(ctx, {'value': val, 'enforce': enforce});
              }
            },
            child: const Text('Apply'),
          ),
        ],
      ),
    ),
  );
}