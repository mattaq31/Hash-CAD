import 'package:flutter/material.dart';

enum CoreStaplesMode { standard, doubleBarrel }

/// User-configurable constants for master mix preparation calculations.
class MasterMixConfig {
  final double scaffoldStockConc;
  final CoreStaplesMode coreStaplesMode;
  final double coreStaplesStockConc; // standard mode
  final List<double> coreStaplesGroupConcs; // double barrel mode (4 values)
  final double dbLStockConc;
  final double dbRStockConc;
  final double coreStaplesRatio;
  final double tefStock;
  final double tefFinal;
  final double mgcl2Stock;
  final double mgcl2Final;
  final int bufferSlats;

  const MasterMixConfig({
    this.scaffoldStockConc = 1062,
    this.coreStaplesMode = CoreStaplesMode.standard,
    this.coreStaplesStockConc = 3937,
    this.coreStaplesGroupConcs = const [10000, 10000, 10000, 10000],
    this.dbLStockConc = 10000,
    this.dbRStockConc = 10000,
    this.coreStaplesRatio = 10,
    this.tefStock = 10,
    this.tefFinal = 1,
    this.mgcl2Stock = 1000,
    this.mgcl2Final = 6,
    this.bufferSlats = 3,
  });

  /// Serializes to a key-value map for persistence in the lab_metadata sheet.
  Map<String, String> toMap() => {
        'scaffold_stock_conc': scaffoldStockConc.toString(),
        'core_staples_mode': coreStaplesMode.name,
        'core_staples_stock_conc': coreStaplesStockConc.toString(),
        'core_staples_1_stock_conc': coreStaplesGroupConcs[0].toString(),
        'core_staples_2_stock_conc': coreStaplesGroupConcs[1].toString(),
        'core_staples_3_stock_conc': coreStaplesGroupConcs[2].toString(),
        'core_staples_4_stock_conc': coreStaplesGroupConcs[3].toString(),
        'db_l_stock_conc': dbLStockConc.toString(),
        'db_r_stock_conc': dbRStockConc.toString(),
        'core_staples_ratio': coreStaplesRatio.toString(),
        'tef_stock': tefStock.toString(),
        'tef_final': tefFinal.toString(),
        'mgcl2_stock': mgcl2Stock.toString(),
        'mgcl2_final': mgcl2Final.toString(),
        'buffer_slats': bufferSlats.toString(),
      };

  /// Reconstructs from a key-value map. Missing keys fall back to defaults.
  static MasterMixConfig fromMap(Map<String, String> m) {
    return MasterMixConfig(
      scaffoldStockConc: double.tryParse(m['scaffold_stock_conc'] ?? '') ?? 1062,
      coreStaplesMode: m['core_staples_mode'] == 'doubleBarrel' ? CoreStaplesMode.doubleBarrel : CoreStaplesMode.standard,
      coreStaplesStockConc: double.tryParse(m['core_staples_stock_conc'] ?? '') ?? 3937,
      coreStaplesGroupConcs: [
        double.tryParse(m['core_staples_1_stock_conc'] ?? '') ?? 10000,
        double.tryParse(m['core_staples_2_stock_conc'] ?? '') ?? 10000,
        double.tryParse(m['core_staples_3_stock_conc'] ?? '') ?? 10000,
        double.tryParse(m['core_staples_4_stock_conc'] ?? '') ?? 10000,
      ],
      dbLStockConc: double.tryParse(m['db_l_stock_conc'] ?? '') ?? 10000,
      dbRStockConc: double.tryParse(m['db_r_stock_conc'] ?? '') ?? 10000,
      coreStaplesRatio: double.tryParse(m['core_staples_ratio'] ?? '') ?? 10,
      tefStock: double.tryParse(m['tef_stock'] ?? '') ?? 10,
      tefFinal: double.tryParse(m['tef_final'] ?? '') ?? 1,
      mgcl2Stock: double.tryParse(m['mgcl2_stock'] ?? '') ?? 1000,
      mgcl2Final: double.tryParse(m['mgcl2_final'] ?? '') ?? 6,
      bufferSlats: int.tryParse(m['buffer_slats'] ?? '') ?? 3,
    );
  }
}

/// Shows the unified export settings dialog.
///
/// Returns an updated record of (export flags, master mix config) on "Apply", or null on cancel.
Future<({bool pdf, bool csv, bool helper, bool normalize, MasterMixConfig config})?> showExportSettingsDialog(
  BuildContext context, {
  required bool generatePdf,
  required bool generateCsv,
  required bool generateHelperSheets,
  required bool normalizeVolumes,
  required MasterMixConfig config,
}) {
  return showDialog(
    context: context,
    builder: (ctx) {
      bool pdf = generatePdf;
      bool csv = generateCsv;
      bool helper = generateHelperSheets;
      bool normalize = normalizeVolumes;

      CoreStaplesMode mode = config.coreStaplesMode;
      final scaffoldStockCtrl = TextEditingController(text: _fmt(config.scaffoldStockConc));
      final coreStockCtrl = TextEditingController(text: _fmt(config.coreStaplesStockConc));
      final core1Ctrl = TextEditingController(text: _fmt(config.coreStaplesGroupConcs[0]));
      final core2Ctrl = TextEditingController(text: _fmt(config.coreStaplesGroupConcs[1]));
      final core3Ctrl = TextEditingController(text: _fmt(config.coreStaplesGroupConcs[2]));
      final core4Ctrl = TextEditingController(text: _fmt(config.coreStaplesGroupConcs[3]));
      final dbLCtrl = TextEditingController(text: _fmt(config.dbLStockConc));
      final dbRCtrl = TextEditingController(text: _fmt(config.dbRStockConc));
      final coreRatioCtrl = TextEditingController(text: _fmt(config.coreStaplesRatio));
      final tefStockCtrl = TextEditingController(text: _fmt(config.tefStock));
      final tefFinalCtrl = TextEditingController(text: _fmt(config.tefFinal));
      final mgcl2StockCtrl = TextEditingController(text: _fmt(config.mgcl2Stock));
      final mgcl2FinalCtrl = TextEditingController(text: _fmt(config.mgcl2Final));
      final bufferCtrl = TextEditingController(text: config.bufferSlats.toString());

      MasterMixConfig? buildConfig() {
        final scaffoldStock = double.tryParse(scaffoldStockCtrl.text);
        final coreStock = double.tryParse(coreStockCtrl.text);
        final c1 = double.tryParse(core1Ctrl.text);
        final c2 = double.tryParse(core2Ctrl.text);
        final c3 = double.tryParse(core3Ctrl.text);
        final c4 = double.tryParse(core4Ctrl.text);
        final dbL = double.tryParse(dbLCtrl.text);
        final dbR = double.tryParse(dbRCtrl.text);
        final coreRatio = double.tryParse(coreRatioCtrl.text);
        final tefS = double.tryParse(tefStockCtrl.text);
        final tefF = double.tryParse(tefFinalCtrl.text);
        final mgS = double.tryParse(mgcl2StockCtrl.text);
        final mgF = double.tryParse(mgcl2FinalCtrl.text);
        final buf = int.tryParse(bufferCtrl.text);
        if ([scaffoldStock, coreStock, coreRatio, tefS, tefF, mgS, mgF].any((v) => v == null || v <= 0)) return null;
        if (mode == CoreStaplesMode.doubleBarrel) {
          if ([c1, c2, c3, c4, dbL, dbR].any((v) => v == null || v <= 0)) return null;
        }
        if (buf == null || buf < 0) return null;
        return MasterMixConfig(
          scaffoldStockConc: scaffoldStock!,
          coreStaplesMode: mode,
          coreStaplesStockConc: coreStock!,
          coreStaplesGroupConcs: [c1 ?? 10000, c2 ?? 10000, c3 ?? 10000, c4 ?? 10000],
          dbLStockConc: dbL ?? 10000,
          dbRStockConc: dbR ?? 10000,
          coreStaplesRatio: coreRatio!,
          tefStock: tefS!,
          tefFinal: tefF!,
          mgcl2Stock: mgS!,
          mgcl2Final: mgF!,
          bufferSlats: buf,
        );
      }

      return StatefulBuilder(
        builder: (ctx, setDialogState) {
          final isValid = buildConfig() != null;
          void rebuild() => setDialogState(() {});

          return AlertDialog(
            title: const Text('Export Settings'),
            content: SizedBox(
              width: 400,
              height: 520,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // --- Export Formats ---
                    Text('Export Formats', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey.shade700)),
                    const SizedBox(height: 4),
                    _CheckRow(label: 'Generate PDF plate layouts', value: pdf, onChanged: (v) => setDialogState(() => pdf = v)),
                    _CheckRow(label: 'Generate Echo CSV instructions', value: csv, onChanged: (v) => setDialogState(() => csv = v)),
                    _CheckRow(label: 'Generate lab helper sheets', value: helper, onChanged: (v) => setDialogState(() => helper = v)),
                    _CheckRow(label: 'Normalize volumes', value: normalize, onChanged: (v) => setDialogState(() => normalize = v)),
                    const Divider(height: 24),
                    // --- Master Mix Config ---
                    Text('Master Mix Configuration', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey.shade700)),
                    const SizedBox(height: 10),
                    _MixField(label: 'Scaffold Stock Conc.', controller: scaffoldStockCtrl, suffix: 'nM', onChanged: rebuild),
                    const SizedBox(height: 10),
                    // Core staples mode dropdown
                    Row(
                      children: [
                        Text('Core Staples Config', style: TextStyle(fontSize: 13, color: Colors.grey.shade700)),
                        const Spacer(),
                        DropdownButton<CoreStaplesMode>(
                          value: mode,
                          isDense: true,
                          items: const [
                            DropdownMenuItem(value: CoreStaplesMode.standard, child: Text('Standard', style: TextStyle(fontSize: 13))),
                            DropdownMenuItem(value: CoreStaplesMode.doubleBarrel, child: Text('Double Barrel', style: TextStyle(fontSize: 13))),
                          ],
                          onChanged: (v) => setDialogState(() { mode = v!; rebuild(); }),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    if (mode == CoreStaplesMode.standard) ...[
                      _MixField(label: 'Core Staples Stock Conc.', controller: coreStockCtrl, suffix: 'nM', onChanged: rebuild),
                    ] else ...[
                      _MixField(label: 'Core Staples 1 Stock', controller: core1Ctrl, suffix: 'nM', onChanged: rebuild),
                      const SizedBox(height: 8),
                      _MixField(label: 'Core Staples 2 Stock', controller: core2Ctrl, suffix: 'nM', onChanged: rebuild),
                      const SizedBox(height: 8),
                      _MixField(label: 'Core Staples 3 Stock', controller: core3Ctrl, suffix: 'nM', onChanged: rebuild),
                      const SizedBox(height: 8),
                      _MixField(label: 'Core Staples 4 Stock', controller: core4Ctrl, suffix: 'nM', onChanged: rebuild),
                      const SizedBox(height: 8),
                      _MixField(label: 'DB-L Stock Conc.', controller: dbLCtrl, suffix: 'nM', onChanged: rebuild),
                      const SizedBox(height: 8),
                      _MixField(label: 'DB-R Stock Conc.', controller: dbRCtrl, suffix: 'nM', onChanged: rebuild),
                    ],
                    const SizedBox(height: 10),
                    _MixField(label: 'Core Staples : Scaffold Ratio', controller: coreRatioCtrl, suffix: 'x', onChanged: rebuild),
                    const SizedBox(height: 10),
                    _MixField(label: 'TEF Stock', controller: tefStockCtrl, suffix: 'X', onChanged: rebuild),
                    const SizedBox(height: 10),
                    _MixField(label: 'TEF Final', controller: tefFinalCtrl, suffix: 'X', onChanged: rebuild),
                    const SizedBox(height: 10),
                    _MixField(label: 'MgCl\u2082 Stock', controller: mgcl2StockCtrl, suffix: 'mM', onChanged: rebuild),
                    const SizedBox(height: 10),
                    _MixField(label: 'MgCl\u2082 Final', controller: mgcl2FinalCtrl, suffix: 'mM', onChanged: rebuild),
                    const SizedBox(height: 10),
                    _MixField(label: 'Buffer Slats', controller: bufferCtrl, suffix: '', onChanged: rebuild),
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
              FilledButton(
                onPressed: isValid
                    ? () => Navigator.pop(ctx, (pdf: pdf, csv: csv, helper: helper, normalize: normalize, config: buildConfig()!))
                    : null,
                child: const Text('Apply'),
              ),
            ],
          );
        },
      );
    },
  );
}

String _fmt(double v) => v == v.roundToDouble() ? v.toStringAsFixed(0) : v.toString();

class _CheckRow extends StatelessWidget {
  final String label;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _CheckRow({required this.label, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(
          height: 20,
          width: 20,
          child: Checkbox(
            value: value,
            onChanged: (v) => onChanged(v ?? false),
            materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
        ),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(fontSize: 13)),
      ],
    );
  }
}

class _MixField extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final String suffix;
  final VoidCallback onChanged;

  const _MixField({required this.label, required this.controller, required this.suffix, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        suffixText: suffix.isNotEmpty ? suffix : null,
        isDense: true,
        border: const OutlineInputBorder(),
      ),
      onChanged: (_) => onChanged(),
    );
  }
}
