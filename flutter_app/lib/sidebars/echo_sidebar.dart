import 'dart:math';
import 'dart:convert';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

import '../app_management/shared_app_state.dart';
import '../app_management/app_preferences.dart';
import '../crisscross_core/handle_plates.dart';
import '../dialogs/alert_window.dart' show displayPlateInfo;
import '../app_management/action_state.dart';
import '../echo_and_experimental_helpers/echo_plate_constants.dart' show slatDisplayName;

class EchoTools extends StatefulWidget {
  const EchoTools({super.key});

  @override
  State<EchoTools> createState() => _EchoTools();
}

Widget buildCategoryIcon({
  required IconData icon,
  required String label,
  required int count,
  Color? color,
}) {
  return Tooltip(
    message: label,
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: color ?? Colors.grey[700]),
        SizedBox(width: 4),
        Text(
          '$count',
          style: TextStyle(fontSize: 14),
        ),
      ],
    ),
  );
}

class _EchoTools extends State<EchoTools> with WidgetsBindingObserver {
  Future<void> _showSyncDialog(BuildContext context, DesignState appState) async {
    final existingPlateNames = appState.plateStack.plates.keys.toSet();
    final result = await showDialog<({String serverUrl, List<Map<String, dynamic>> selected})>(
      context: context,
      builder: (ctx) => _PlateSyncSelectionDialog(existingPlateNames: existingPlateNames),
    );

    if (result == null || result.selected.isEmpty) return;

    // Download selected plates concurrently
    final serverUrl = result.serverUrl;
    final futures = result.selected.map((plate) async {
      try {
        final plateUrl = '$serverUrl/plates/${plate['path']}';
        final response = await http.get(Uri.parse(plateUrl));
        if (response.statusCode == 200) {
          return (name: plate['name'] as String, bytes: Uint8List.fromList(response.bodyBytes));
        }
      } catch (_) {}
      return null;
    });
    final results = (await Future.wait(futures)).whereType<({String name, Uint8List bytes})>().toList();
    final plateFiles = results.map((r) => r.bytes).toList();
    final plateNames = results.map((r) => r.name).toList();

    if (plateFiles.isNotEmpty) {
      final replacedCount = plateNames.where((n) => existingPlateNames.contains(n)).length;
      appState.plateStack.readPlates(plateFiles, plateNames);
      syncCargoFromPlates(appState.plateStack, appState.cargoPalette);
      appState.notifyListeners();
      if (context.mounted) {
        final msg = replacedCount > 0
            ? 'Loaded ${plateFiles.length} plate(s) from server (replaced $replacedCount existing)'
            : 'Loaded ${plateFiles.length} plate(s) from server';
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
    }
  }

  /// Computes per-category counts of handle positions that have a category assigned
  /// on a slat but no sequence from an input plate.
  Map<String, List<({String slatId, int position, int side})>> _computeMissingSequences(DesignState appState) {
    final missing = <String, List<({String slatId, int position, int side})>>{};
    for (var cat in ['FLAT', 'ASSEMBLY_HANDLE', 'ASSEMBLY_ANTIHANDLE', 'SEED', 'CARGO']) {
      missing[cat] = [];
    }

    for (var slat in appState.slats.values) {
      if (slat.phantomParent != null) continue;
      for (int pos = 1; pos <= slat.maxLength; pos++) {
        for (var side in [2, 5]) {
          final handles = side == 2 ? slat.h2Handles : slat.h5Handles;
          if (handles.containsKey(pos)) {
            final handle = handles[pos]!;
            var category = handle['category'] as String?;
            // Blocked handles (value '0') are effectively flat staples
            if (category != null && handle['value'] == '0' &&
                (category == 'ASSEMBLY_HANDLE' || category == 'ASSEMBLY_ANTIHANDLE')) {
              category = 'FLAT';
            }
            if (category != null && handle['sequence'] == null) {
              missing.putIfAbsent(category, () => []);
              missing[category]!.add((slatId: slatDisplayName(slat, appState.layerMap), position: pos, side: side));
            }
          } else {
            // No handle at this position — needs a FLAT staple
            missing['FLAT']!.add((slatId: slatDisplayName(slat, appState.layerMap), position: pos, side: side));
          }
        }
      }
    }
    return missing;
  }

  bool _hasFlatPlate(DesignState appState) {
    for (var plate in appState.plateStack.plates.values) {
      if (plate.countCategory('FLAT') > 0) return true;
    }
    return false;
  }

  void _showMissingDetailsDialog(BuildContext context, String category, List<({String slatId, int position, int side})> items) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('Missing: $category'),
        content: SizedBox(
          width: 350,
          height: 300,
          child: ListView.builder(
            itemCount: items.length > 100 ? 101 : items.length,
            itemBuilder: (_, i) {
              if (i == 100) return Text('... and ${items.length - 100} more', style: TextStyle(fontStyle: FontStyle.italic));
              final item = items[i];
              final sideStr = item.side == 2 ? 'H2' : 'H5';
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 1),
                child: Text('${item.slatId}  pos ${item.position}  ($sideStr)', style: TextStyle(fontSize: 12)),
              );
            },
          ),
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: Text('Close'))],
      ),
    );
  }

  Widget _buildValidationSummary(DesignState appState) {
    final missing = _computeMissingSequences(appState);
    final hasFlatPlate = _hasFlatPlate(appState);
    final hasSlats = appState.slats.values.any((s) => s.phantomParent == null);

    // Check if all sequences are assigned
    final totalMissing = missing.values.fold<int>(0, (sum, list) => sum + list.length);
    final needsFlatWarning = !hasFlatPlate && missing['FLAT']!.isNotEmpty;

    if (!hasSlats) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Text('No slats in design', style: TextStyle(color: Colors.grey[500], fontSize: 13)),
      );
    }

    if (totalMissing == 0 && !needsFlatWarning) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 20),
            SizedBox(width: 6),
            Text('All sequences assigned', style: TextStyle(color: Colors.green[700], fontSize: 13, fontWeight: FontWeight.w500)),
          ],
        ),
      );
    }

    final categoryConfig = <String, ({IconData icon, Color color, String label})>{
      'FLAT': (icon: Icons.power_input, color: Colors.green, label: 'Flat Staples'),
      'ASSEMBLY_HANDLE': (icon: Icons.join_left, color: Colors.blue, label: 'Assembly Handles'),
      'ASSEMBLY_ANTIHANDLE': (icon: Icons.join_right, color: Colors.red, label: 'Assembly AntiHandles'),
      'SEED': (icon: Icons.nature, color: Colors.brown, label: 'Seed Handles'),
      'CARGO': (icon: Icons.precision_manufacturing, color: Colors.orange, label: 'Cargo Handles'),
    };

    return Column(
      children: [
        if (needsFlatWarning)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.warning_amber, color: Colors.orange, size: 18),
                SizedBox(width: 4),
                Text('Flat staples plate required', style: TextStyle(color: Colors.orange[800], fontSize: 12)),
              ],
            ),
          ),
        Wrap(
          spacing: 10,
          runSpacing: 4,
          alignment: WrapAlignment.center,
          children: [
            for (var cat in categoryConfig.entries)
              if (missing[cat.key]!.isNotEmpty)
                InkWell(
                  onTap: () => _showMissingDetailsDialog(context, cat.value.label, missing[cat.key]!),
                  borderRadius: BorderRadius.circular(4),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 2),
                    child: buildCategoryIcon(
                      icon: cat.value.icon,
                      label: '${cat.value.label} missing',
                      count: missing[cat.key]!.length,
                      color: cat.value.color,
                    ),
                  ),
                ),
          ],
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    var appState = context.watch<DesignState>();
    var actionState = context.watch<ActionState>();
    return Column(children: [
      Text("Echo Export Tools",
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
      SizedBox(height: 5),
      Text(
        "Plate Stack",
        style: TextStyle(fontSize: 18, color: Colors.grey.shade600),
      ),
      SizedBox(height: 5),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          FilledButton.icon(
            onPressed: () {
              appState.importPlates();
            },
            icon: Icon(Icons.lens_blur, size: 18),
            label: Text("File Import"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
          SizedBox(width: 10),
          OutlinedButton.icon(
            onPressed: () => _showSyncDialog(context, appState),
            icon: Icon(Icons.cloud_download, size: 18),
            label: Text("Server Sync"),
            style: OutlinedButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              textStyle: TextStyle(fontSize: 16),
            ),
          ),
        ],
      ),
      SizedBox(height: 5),
      Container(
          constraints: BoxConstraints(
            maxHeight: appState.plateStack.plates.isEmpty
                ? 20
                : appState.plateStack.plates.length <= 6
                    ? double.infinity
                    : 6 * 72.0, // Cap at ~6 collapsed tiles
          ),
          child: appState.plateStack.plates.isEmpty
              ? Center(
                  child: Text(
                    'Import plates to see them here!',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[600],
                    ),
                  ),
                )
              : ListView(
                  shrinkWrap: true,
                  children: appState.plateStack.plates.entries.map((entry) {
                    String plateName = entry.key;
                    HashCadPlate plate = entry.value;

                    return ExpansionTile(
                      shape: RoundedRectangleBorder(
                        side: BorderSide(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      collapsedShape: RoundedRectangleBorder(
                        side: BorderSide(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      key: Key(plateName),
                      title: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(sanitizePlateMap(plateName),
                                    style:
                                        TextStyle(fontWeight: FontWeight.w500)),
                                SizedBox(height: 4),
                                Text('Total staples: ${plate.wells.length}',
                                    style: TextStyle(
                                        fontSize: 12, color: Colors.grey[700])),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: Icon(Icons.info,
                                size: 20, color: Colors.blueAccent),
                            tooltip: 'Further Info',
                            onPressed: () {
                              displayPlateInfo(context, plateName, plate);
                            },
                          ),
                          IconButton(
                            icon: Icon(Icons.close,
                                size: 20, color: Colors.redAccent),
                            tooltip: 'Delete Plate',
                            onPressed: () {
                              appState.removePlate(plateName);
                            },
                          ),
                        ],
                      ),
                      children: [
                        Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16.0, vertical: 4.0),
                          child: Wrap(
                            spacing: 12,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              buildCategoryIcon(
                                icon: Icons.power_input,
                                label: 'Flat Staples',
                                count: plate.countCategory("FLAT"),
                                color: Colors.green,
                              ),
                              buildCategoryIcon(
                                icon: Icons.join_left,
                                label: 'Assembly Handles',
                                count: plate.countCategory("ASSEMBLY_HANDLE"),
                                color: Colors.blue,
                              ),
                              buildCategoryIcon(
                                icon: Icons.join_right,
                                label: 'Assembly AntiHandles',
                                count:
                                    plate.countCategory("ASSEMBLY_ANTIHANDLE"),
                                color: Colors.red,
                              ),
                              buildCategoryIcon(
                                icon: Icons.nature,
                                label: 'Seed Handles',
                                count: plate.countCategory("SEED"),
                                color: Colors.brown,
                              ),
                              buildCategoryIcon(
                                icon: Icons.precision_manufacturing,
                                label: 'Cargo Handles',
                                count: plate.countCategory("CARGO"),
                                color: Colors.orange,
                              ),
                            ],
                          ),
                        ),
                      ],
                    );
                  }).toList(),
                )),
      SizedBox(height: 5),
      FilledButton.icon(
        onPressed: appState.plateStack.plates.isEmpty ? null : () {
          appState.removeAllPlates();
        },
        label: Text("Clear Plates"),
        icon: Icon(Icons.delete),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.red,
          foregroundColor: Colors.white,
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: TextStyle(fontSize: 16),
        ),
      ),
      Divider(thickness: 2, color: Colors.grey.shade300),
      Text(
        "Missing Staples & Validation",
        style: TextStyle(fontSize: 18, color: Colors.grey.shade600),
      ),
      SizedBox(height: 5),
      _buildValidationSummary(appState),
      SizedBox(height: 10),
      FilledButton.icon(
        onPressed: appState.plateStack.plates.isEmpty ? null : () {
          appState.plateAssignAllHandles();
        },
        label: Text("Assign Sequences"),
        icon: Icon(Icons.polyline),
        style: ElevatedButton.styleFrom(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: TextStyle(fontSize: 16),
        ),
      ),
      Divider(thickness: 2, color: Colors.grey.shade300),
      SizedBox(
        width: double.infinity,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: FilledButton.icon(
            onPressed: () {
              actionState.activateEchoPlateWindow();
            },
            icon: Icon(Icons.grid_view, size: 20),
            label: Text("Echo Export"),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(horizontal: 24, vertical: 14),
              textStyle: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
          ),
        ),
      ),
    ]);
  }
}

/// Dialog for selecting plates to sync from a server manifest.
/// Shows a URL field first, then fetches the manifest on "Go".
class _PlateSyncSelectionDialog extends StatefulWidget {
  final Set<String> existingPlateNames;
  const _PlateSyncSelectionDialog({this.existingPlateNames = const {}});

  @override
  State<_PlateSyncSelectionDialog> createState() => _PlateSyncSelectionDialogState();
}

class _PlateSyncSelectionDialogState extends State<_PlateSyncSelectionDialog> {
  final TextEditingController _urlController = TextEditingController();
  final Set<int> _selectedIndices = {};
  List<Map<String, dynamic>>? _plateList;
  bool _loading = false;
  String? _error;
  String _activeUrl = '';

  @override
  void initState() {
    super.initState();
    _loadSavedUrl();
  }

  Future<void> _loadSavedUrl() async {
    final url = await AppPreferences().getPlateServerUrl();
    setState(() => _urlController.text = url);
  }

  Future<void> _fetchManifest() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
      _plateList = null;
      _selectedIndices.clear();
    });

    // Save URL to preferences
    await AppPreferences().setPlateServerUrl(url);
    _activeUrl = url;

    try {
      final response = await http.get(Uri.parse('$url/plates/manifest.json'));
      if (response.statusCode != 200) {
        setState(() {
          _error = 'HTTP ${response.statusCode}';
          _loading = false;
        });
        return;
      }
      final manifest = jsonDecode(response.body);
      setState(() {
        _plateList = List<Map<String, dynamic>>.from(manifest['plates']);
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Sync Plates from Server'),
      content: SizedBox(
        width: 400,
        height: 450,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _urlController,
                    decoration: InputDecoration(
                      labelText: 'Server URL',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                    style: TextStyle(fontSize: 13),
                    onSubmitted: (_) => _fetchManifest(),
                  ),
                ),
                SizedBox(width: 8),
                FilledButton(
                  onPressed: _loading ? null : _fetchManifest,
                  child: Text('Go'),
                ),
              ],
            ),
            SizedBox(height: 8),
            if (_loading)
              Expanded(child: Center(child: CircularProgressIndicator()))
            else if (_error != null)
              Expanded(child: Center(child: Text('Error: $_error', style: TextStyle(color: Colors.red, fontSize: 13))))
            else if (_plateList == null)
              Expanded(child: Center(child: Text('Enter a server URL and press Go', style: TextStyle(color: Colors.grey[600], fontSize: 13))))
            else
              Expanded(child: _buildPlateList()),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text('Cancel')),
        FilledButton(
          onPressed: _selectedIndices.isEmpty || _plateList == null
              ? null
              : () => Navigator.pop(context, (
                  serverUrl: _activeUrl,
                  selected: _selectedIndices.map((i) => _plateList![i]).toList(),
                )),
          child: Text('Download${_selectedIndices.isEmpty ? '' : ' (${_selectedIndices.length})'}'),
        ),
      ],
    );
  }

  Widget _buildPlateList() {
    final categories = <String, List<int>>{};
    for (var i = 0; i < _plateList!.length; i++) {
      final cat = _plateList![i]['category']?.toString() ?? 'other';
      categories.putIfAbsent(cat, () => []).add(i);
    }

    return ListView(
      children: [
        for (var catEntry in categories.entries) ...[
          Padding(
            padding: const EdgeInsets.only(top: 8, bottom: 4),
            child: Text(
              catEntry.key.replaceAll('_', ' '),
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.grey[700]),
            ),
          ),
          for (var idx in catEntry.value)
            CheckboxListTile(
              dense: true,
              title: Row(
                children: [
                  Expanded(child: Text(_plateList![idx]['name'] ?? '', style: TextStyle(fontSize: 13))),
                  if (widget.existingPlateNames.contains(_plateList![idx]['name']))
                    Tooltip(
                      message: 'Will replace currently loaded plate',
                      child: Icon(Icons.warning_amber, size: 18, color: Colors.orange),
                    ),
                ],
              ),
              value: _selectedIndices.contains(idx),
              onChanged: (v) {
                setState(() {
                  if (v == true) {
                    _selectedIndices.add(idx);
                  } else {
                    _selectedIndices.remove(idx);
                  }
                });
              },
            ),
        ],
      ],
    );
  }
}
