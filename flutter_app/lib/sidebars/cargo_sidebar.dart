import 'package:provider/provider.dart';
import '../app_management/shared_app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import  '../crisscross_core/cargo.dart';
import 'package:flutter/services.dart';



class CargoDesignTools extends StatefulWidget {
  const CargoDesignTools({super.key});

  @override
  State<CargoDesignTools> createState() => _CargoDesignTools();
}

Widget _buildCargoSquare(Cargo cargo, DesignState appState) {
  bool isSelected = appState.cargoAdditionType == cargo.name;
  return GestureDetector(
    onTap: () {
      appState.selectCargoType(cargo.name);
    },
    child: Container(
      width: 40, // Shrunk size
      height: 40,
      margin: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: cargo.color,
        borderRadius: BorderRadius.circular(6),
        border: isSelected
            ? Border.all(color: Colors.black, width: 2)
            : null,
        boxShadow: isSelected
            ? [
          BoxShadow(
            color: Colors.black.withOpacity(0.5),
            blurRadius: 6,
            spreadRadius: 1,
          )
        ]
            : [],
      ),
      child: Center(
        child: Text(
          cargo.shortName,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 10,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    ),
  );
}


class _CargoDesignTools extends State<CargoDesignTools> with WidgetsBindingObserver {

  FocusNode cargoAddFocusNode = FocusNode();

  TextEditingController cargoAddTextController = TextEditingController(text: '1');
  int cargoAddCount = 1;

  void _updateCargoAddCount(DesignState appState) {
    int? newValue = int.tryParse(cargoAddTextController.text);
    if (newValue != null && newValue >= 1 && newValue <= 32) {
      cargoAddCount = newValue;
    } else if (newValue != null && newValue < 1) {
      cargoAddCount = 1;
    } else {
      cargoAddCount = 32;
    }
    cargoAddTextController.text = cargoAddCount.toString();
    appState.updateCargoAddCount(cargoAddCount);
  }

  void _showAddDialog(DesignState appState, bool editMode) {
    final TextEditingController nameController = TextEditingController();
    final TextEditingController shortNameController = TextEditingController();

    Color selectedColor = Colors.blue;
    bool shortNameEditedManually = false;

    nameController.addListener(() {
      if (!shortNameEditedManually) {
        final name = nameController.text;
        final autoShort = generateShortName(name);
        shortNameController.text = autoShort;
      }
    });

    if (editMode) {
      nameController.text = appState.cargoPalette[appState.cargoAdditionType!]!.name;
      shortNameController.text = appState.cargoPalette[appState.cargoAdditionType!]!.shortName;
      selectedColor = appState.cargoPalette[appState.cargoAdditionType!]!.color;
    }

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(editMode ? 'Edit Cargo' : 'Add Cargo'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Cargo Name'),
                enabled: !editMode,  // TODO: add a way for changing cargo name instead of preventing editing...
              ),
              TextField(
                controller: shortNameController,
                decoration: const InputDecoration(labelText: 'Short Name'),
                onChanged: (_) {
                  shortNameEditedManually = true;
                },
              ),
              const SizedBox(height: 16),
              ColorPicker(
                pickerColor: selectedColor,
                onColorChanged: (color) {
                  selectedColor = color;
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              child: const Text('Cancel'),
              onPressed: () => Navigator.of(context).pop(),
            ),
            ElevatedButton(
              child: const Text('Add'),
              onPressed: () {
                final name = nameController.text.trim();
                final shortName = shortNameController.text.trim();
                if (name.isNotEmpty) {
                  appState.addCargoType(Cargo(name: name, shortName: shortName, color: selectedColor));
                  Navigator.of(context).pop();
                }
              },
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    var serverState = context.watch<ServerState>();

    return Column(children: [
      Text("Cargo and Seed Placement",
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 5),
      Text(
        "Cargo Edit Mode", // Title above the segmented button
        style:
        TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      SizedBox(height: 5),
      SegmentedButton<String>(
        segments: <ButtonSegment<String>>[
          ButtonSegment<String>(
              value: "Add",
              label: Text('Add'),
              icon: Icon(Icons.add_circle_outline, color: Theme.of(context).colorScheme.primary)),
          ButtonSegment<String>(
              value: "Delete",
              label: Text('Delete'),
              icon: Icon(Icons.delete_outline, color: Theme.of(context).colorScheme.primary)),
          ButtonSegment<String>(
              value: 'Move',
              label: Text('Move'),
              icon: Icon(Icons.pan_tool, color: Theme.of(context).colorScheme.primary)),
        ],
        selected: <String>{actionState.cargoMode},
        onSelectionChanged: (Set<String> newSelection) {
          setState(() {
            actionState.updateCargoMode(newSelection.first);
          });
        },
      ),
      CheckboxListTile(
        title: const Text('Display Assembly Handles'),
        value: actionState.displayAssemblyHandles,
        onChanged: (bool? value) {
          setState(() {
            actionState.setAssemblyHandleDisplay(value ?? false);
          });
        },
      ),
      CheckboxListTile(
        title: const Text('Display Cargo Handles'),
        value: actionState.displayCargoHandles,
        onChanged: (bool? value) {
          setState(() {
            actionState.setCargoHandleDisplay(value ?? false);
          });
        },
      ),
      SizedBox(height: 5),
      Text(
        "Cargo Palette", // Title above the segmented button
        style:
        TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      Container(
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade400, width: 1),
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.all(6),
        height: (40 + 4) * 3 + 12, // 3 rows of cargo (height + margin) + some padding
        width: (40 + 4) * 8 + 12, // 8 squares per row + spacing + padding
        child: SingleChildScrollView(
          child: Wrap(
            spacing: 4,
            runSpacing: 4,
            children: appState.cargoPalette.values
                .map((cargo) => _buildCargoSquare(cargo, appState))
                .toList(),
          ),
        ),
      ),
      SizedBox(height: 5),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          FilledButton.icon(
            onPressed: (){_showAddDialog(appState, false);},
            icon: Icon(Icons.add, size: 18),
            label: Text("Add"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8), // Rounded edges
              ),
            ),
          ),
          SizedBox(width: 5),
          FilledButton.icon(
            onPressed: appState.cargoAdditionType == null
                ? null
                : () {
                    appState.deleteCargoType(appState.cargoAdditionType!);
                  },
            icon: Icon(Icons.delete, size: 18),
            label: Text("Delete"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8), // Rounded edges
              ),
            ),
          ),
          SizedBox(width: 5),
          FilledButton.icon(
            onPressed: appState.cargoAdditionType == null
                ? null
                : () {
              _showAddDialog(appState, true);
            },
            icon: Icon(Icons.edit, size: 18),
            label: Text("Edit"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8), // Rounded edges
              ),
            ),
          ),
        ],
      ),
      SizedBox(height: 10),
      Divider(thickness: 1, color: Colors.grey.shade200),
      SizedBox(height: 10),
      Text(
        "Number of Cargo Units to Draw", // Title above the segmented button
        style:
        TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      SizedBox(height: 10),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 180,
            child: TextField(
              controller: cargoAddTextController,
              focusNode: cargoAddFocusNode,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'Manual Input',
              ),
              textInputAction: TextInputAction.done,
              inputFormatters: <TextInputFormatter>[FilteringTextInputFormatter.digitsOnly],
              onSubmitted: (value) {
                _updateCargoAddCount(appState);
              },
            ),
          ),
          IconButton(
            icon: Icon(Icons.arrow_upward),
            onPressed: () {
              if (cargoAddCount < 32) {
                cargoAddCount++;
                cargoAddTextController.text = cargoAddCount.toString();
                appState.updateCargoAddCount(cargoAddCount);
              }
            },
          ),
          IconButton(
            icon: Icon(Icons.arrow_downward),
            onPressed: () {
              if (cargoAddCount > 1) {
                cargoAddCount--;
                cargoAddTextController.text = cargoAddCount.toString();
                appState.updateCargoAddCount(cargoAddCount);
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
              cargoAddCount = 1;
              cargoAddTextController.text = cargoAddCount.toString();
              appState.updateCargoAddCount(cargoAddCount);
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('8'),
            onPressed: () {
              cargoAddCount = 8;
              cargoAddTextController.text = cargoAddCount.toString();
              appState.updateCargoAddCount(cargoAddCount);
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('16'),
            onPressed: () {
              cargoAddCount = 16;
              cargoAddTextController.text = cargoAddCount.toString();
              appState.updateCargoAddCount(cargoAddCount);
            },
          ),
          SizedBox(width: 10),
          ActionChip(
            label: Text('32'),
            onPressed: () {
              cargoAddCount = 32;
              cargoAddTextController.text = cargoAddCount.toString();
              appState.updateCargoAddCount(cargoAddCount);
            },
          ),
        ],
      ),
      SizedBox(height: 10),
      Text(
        "Cargo Attachment", // Title above the segmented button
        style:
        TextStyle(fontSize: 16, color: Colors.grey.shade600),
      ),
      SizedBox(height: 10),
      SegmentedButton<String>(
        segments: <ButtonSegment<String>>[
          ButtonSegment<String>(
              value: "top",
              label: Text('Top'),
              icon: Icon(Icons.arrow_upward, color: Theme.of(context).colorScheme.primary)),
          ButtonSegment<String>(
              value: 'bottom',
              label: Text('Bottom'),
              icon: Icon(Icons.arrow_downward, color: Theme.of(context).colorScheme.primary)),
        ],
        selected: <String>{actionState.cargoAttachMode},
        onSelectionChanged: (Set<String> newSelection) {
          setState(() {
            actionState.updateCargoAttachMode(newSelection.first);
          });
        },
      ),
      Divider(thickness: 1, color: Colors.grey.shade200),
    ]);
  }
}
