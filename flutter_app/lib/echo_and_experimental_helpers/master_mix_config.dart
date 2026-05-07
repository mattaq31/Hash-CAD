// Configuration classes and export settings dialog for master mix preparation.
import 'package:flutter/material.dart';

enum CoreStaplesMode { standard, doubleBarrel }

enum BufferSlatsMode { percentage, count }

/// User-configurable constants for master mix preparation calculations.
class MasterMixConfig {
  // --- Shared fields (apply regardless of mode) ---
  final double scaffoldStockConc;
  final CoreStaplesMode coreStaplesMode;
  final double tefStock;
  final double tefFinal;
  final double mgcl2Stock;
  final double mgcl2Final;

  // --- Standard mode fields ---
  final bool coreStaplesUseSingleStock;
  final double coreStaplesStockConc;
  final List<double> coreStaplesHelixConcs; // Helix 0, 1, 3, 4
  final double coreStaplesRatio;
  final BufferSlatsMode bufferSlatsMode;
  final double bufferSlatsPercentage;
  final int bufferSlats;

  // --- Double Barrel mode fields ---
  final bool dbCoreStaplesUseSingleStock;
  final double dbCoreStaplesStockConc;
  final List<double> dbCoreStaplesHelixConcs; // Helix 0, 1, 3, 4
  final double dbCoreStaplesRatio;
  final BufferSlatsMode dbBufferSlatsMode;
  final double dbBufferSlatsPercentage;
  final int dbBufferSlats;

  const MasterMixConfig({
    this.scaffoldStockConc = 1062,
    this.coreStaplesMode = CoreStaplesMode.standard,
    this.tefStock = 10,
    this.tefFinal = 1,
    this.mgcl2Stock = 1000,
    this.mgcl2Final = 6,
    // Standard
    this.coreStaplesUseSingleStock = false,
    this.coreStaplesStockConc = 10000,
    this.coreStaplesHelixConcs = const [10000, 10000, 10000, 10000],
    this.coreStaplesRatio = 10,
    this.bufferSlatsMode = BufferSlatsMode.percentage,
    this.bufferSlatsPercentage = 10,
    this.bufferSlats = 3,
    // Double Barrel
    this.dbCoreStaplesUseSingleStock = false,
    this.dbCoreStaplesStockConc = 10000,
    this.dbCoreStaplesHelixConcs = const [10000, 10000, 10000, 10000],
    this.dbCoreStaplesRatio = 10,
    this.dbBufferSlatsMode = BufferSlatsMode.percentage,
    this.dbBufferSlatsPercentage = 10,
    this.dbBufferSlats = 3,
  });

  /// Returns the effective buffer slat count for the active mode.
  int resolvedBufferSlats(int slatCount) {
    if (coreStaplesMode == CoreStaplesMode.standard) {
      return bufferSlatsMode == BufferSlatsMode.percentage
          ? (slatCount * bufferSlatsPercentage / 100).ceil()
          : bufferSlats;
    } else {
      return dbBufferSlatsMode == BufferSlatsMode.percentage
          ? (slatCount * dbBufferSlatsPercentage / 100).ceil()
          : dbBufferSlats;
    }
  }

  /// Returns the active core staples ratio for the current mode.
  double get activeCoreStaplesRatio =>
      coreStaplesMode == CoreStaplesMode.standard ? coreStaplesRatio : dbCoreStaplesRatio;

  // --- Legacy getters for export compatibility (will be removed when export is restructured) ---

  /// Returns the group concentrations used by the export in double barrel mode.
  List<double> get coreStaplesGroupConcs => dbCoreStaplesUseSingleStock
      ? [dbCoreStaplesStockConc, dbCoreStaplesStockConc, dbCoreStaplesStockConc, dbCoreStaplesStockConc]
      : dbCoreStaplesHelixConcs;

  /// Placeholder for DB-L stock (no longer a separate concept — returns 0).
  double get dbLStockConc => 0;

  /// Placeholder for DB-R stock (no longer a separate concept — returns 0).
  double get dbRStockConc => 0;

  /// Serializes to a key-value map for persistence in the lab_metadata sheet.
  Map<String, String> toMap() => {
        'scaffold_stock_conc': scaffoldStockConc.toString(),
        'core_staples_mode': coreStaplesMode.name,
        'tef_stock': tefStock.toString(),
        'tef_final': tefFinal.toString(),
        'mgcl2_stock': mgcl2Stock.toString(),
        'mgcl2_final': mgcl2Final.toString(),
        // Standard
        'core_staples_use_single_stock': coreStaplesUseSingleStock.toString(),
        'core_staples_stock_conc': coreStaplesStockConc.toString(),
        'core_staples_helix_0_conc': coreStaplesHelixConcs[0].toString(),
        'core_staples_helix_1_conc': coreStaplesHelixConcs[1].toString(),
        'core_staples_helix_3_conc': coreStaplesHelixConcs[2].toString(),
        'core_staples_helix_4_conc': coreStaplesHelixConcs[3].toString(),
        'core_staples_ratio': coreStaplesRatio.toString(),
        'buffer_slats_mode': bufferSlatsMode.name,
        'buffer_slats_percentage': bufferSlatsPercentage.toString(),
        'buffer_slats': bufferSlats.toString(),
        // Double Barrel
        'db_core_staples_use_single_stock': dbCoreStaplesUseSingleStock.toString(),
        'db_core_staples_stock_conc': dbCoreStaplesStockConc.toString(),
        'db_core_staples_helix_0_conc': dbCoreStaplesHelixConcs[0].toString(),
        'db_core_staples_helix_1_conc': dbCoreStaplesHelixConcs[1].toString(),
        'db_core_staples_helix_3_conc': dbCoreStaplesHelixConcs[2].toString(),
        'db_core_staples_helix_4_conc': dbCoreStaplesHelixConcs[3].toString(),
        'db_core_staples_ratio': dbCoreStaplesRatio.toString(),
        'db_buffer_slats_mode': dbBufferSlatsMode.name,
        'db_buffer_slats_percentage': dbBufferSlatsPercentage.toString(),
        'db_buffer_slats': dbBufferSlats.toString(),
      };

  /// Reconstructs from a key-value map. Missing keys fall back to defaults.
  static MasterMixConfig fromMap(Map<String, String> m) {
    return MasterMixConfig(
      scaffoldStockConc: double.tryParse(m['scaffold_stock_conc'] ?? '') ?? 1062,
      coreStaplesMode: m['core_staples_mode'] == 'doubleBarrel' ? CoreStaplesMode.doubleBarrel : CoreStaplesMode.standard,
      tefStock: double.tryParse(m['tef_stock'] ?? '') ?? 10,
      tefFinal: double.tryParse(m['tef_final'] ?? '') ?? 1,
      mgcl2Stock: double.tryParse(m['mgcl2_stock'] ?? '') ?? 1000,
      mgcl2Final: double.tryParse(m['mgcl2_final'] ?? '') ?? 6,
      // Standard
      coreStaplesUseSingleStock: m['core_staples_use_single_stock'] == 'true',
      coreStaplesStockConc: double.tryParse(m['core_staples_stock_conc'] ?? '') ?? 10000,
      coreStaplesHelixConcs: [
        double.tryParse(m['core_staples_helix_0_conc'] ?? '') ?? 10000,
        double.tryParse(m['core_staples_helix_1_conc'] ?? '') ?? 10000,
        double.tryParse(m['core_staples_helix_3_conc'] ?? '') ?? 10000,
        double.tryParse(m['core_staples_helix_4_conc'] ?? '') ?? 10000,
      ],
      coreStaplesRatio: double.tryParse(m['core_staples_ratio'] ?? '') ?? 10,
      bufferSlatsMode: m['buffer_slats_mode'] == 'count' ? BufferSlatsMode.count : BufferSlatsMode.percentage,
      bufferSlatsPercentage: double.tryParse(m['buffer_slats_percentage'] ?? '') ?? 10,
      bufferSlats: int.tryParse(m['buffer_slats'] ?? '') ?? 3,
      // Double Barrel
      dbCoreStaplesUseSingleStock: m['db_core_staples_use_single_stock'] == 'true',
      dbCoreStaplesStockConc: double.tryParse(m['db_core_staples_stock_conc'] ?? '') ?? 10000,
      dbCoreStaplesHelixConcs: [
        double.tryParse(m['db_core_staples_helix_0_conc'] ?? '') ?? 10000,
        double.tryParse(m['db_core_staples_helix_1_conc'] ?? '') ?? 10000,
        double.tryParse(m['db_core_staples_helix_3_conc'] ?? '') ?? 10000,
        double.tryParse(m['db_core_staples_helix_4_conc'] ?? '') ?? 10000,
      ],
      dbCoreStaplesRatio: double.tryParse(m['db_core_staples_ratio'] ?? '') ?? 10,
      dbBufferSlatsMode: m['db_buffer_slats_mode'] == 'count' ? BufferSlatsMode.count : BufferSlatsMode.percentage,
      dbBufferSlatsPercentage: double.tryParse(m['db_buffer_slats_percentage'] ?? '') ?? 10,
      dbBufferSlats: int.tryParse(m['db_buffer_slats'] ?? '') ?? 3,
    );
  }
}

// =============================================================================
// Export Settings Dialog
// =============================================================================

/// Shows the tabbed export settings dialog.
///
/// Returns an updated record of (export flags, master mix config, runExport flag) on Save/Export,
/// or null on Cancel.
Future<({bool pdf, bool csv, bool helper, bool normalize, double maxWellVolumeNl, MasterMixConfig config, bool runExport})?> showExportSettingsDialog(
  BuildContext context, {
  required bool generatePdf,
  required bool generateCsv,
  required bool generateHelperSheets,
  required bool normalizeVolumes,
  required double maxWellVolumeNl,
  required MasterMixConfig config,
}) {
  return showDialog(
    context: context,
    builder: (ctx) {
      // Export format flags
      bool pdf = generatePdf;
      bool csv = generateCsv;
      bool helper = generateHelperSheets;
      bool normalize = normalizeVolumes;
      final maxWellVolCtrl = TextEditingController(text: _fmt(maxWellVolumeNl / 1000));

      // Shared fields
      CoreStaplesMode mode = config.coreStaplesMode;
      final scaffoldStockCtrl = TextEditingController(text: _fmt(config.scaffoldStockConc));
      final tefStockCtrl = TextEditingController(text: _fmt(config.tefStock));
      final tefFinalCtrl = TextEditingController(text: _fmt(config.tefFinal));
      final mgcl2StockCtrl = TextEditingController(text: _fmt(config.mgcl2Stock));
      final mgcl2FinalCtrl = TextEditingController(text: _fmt(config.mgcl2Final));

      // Standard mode fields
      bool stdSingleStock = config.coreStaplesUseSingleStock;
      final stdStockCtrl = TextEditingController(text: _fmt(config.coreStaplesStockConc));
      final stdHelix0Ctrl = TextEditingController(text: _fmt(config.coreStaplesHelixConcs[0]));
      final stdHelix1Ctrl = TextEditingController(text: _fmt(config.coreStaplesHelixConcs[1]));
      final stdHelix3Ctrl = TextEditingController(text: _fmt(config.coreStaplesHelixConcs[2]));
      final stdHelix4Ctrl = TextEditingController(text: _fmt(config.coreStaplesHelixConcs[3]));
      final stdRatioCtrl = TextEditingController(text: _fmt(config.coreStaplesRatio));
      BufferSlatsMode stdBufferMode = config.bufferSlatsMode;
      final stdBufferPctCtrl = TextEditingController(text: _fmt(config.bufferSlatsPercentage));
      final stdBufferCountCtrl = TextEditingController(text: config.bufferSlats.toString());

      // Double Barrel mode fields
      bool dbSingleStock = config.dbCoreStaplesUseSingleStock;
      final dbStockCtrl = TextEditingController(text: _fmt(config.dbCoreStaplesStockConc));
      final dbHelix0Ctrl = TextEditingController(text: _fmt(config.dbCoreStaplesHelixConcs[0]));
      final dbHelix1Ctrl = TextEditingController(text: _fmt(config.dbCoreStaplesHelixConcs[1]));
      final dbHelix3Ctrl = TextEditingController(text: _fmt(config.dbCoreStaplesHelixConcs[2]));
      final dbHelix4Ctrl = TextEditingController(text: _fmt(config.dbCoreStaplesHelixConcs[3]));
      final dbRatioCtrl = TextEditingController(text: _fmt(config.dbCoreStaplesRatio));
      BufferSlatsMode dbBufferMode = config.dbBufferSlatsMode;
      final dbBufferPctCtrl = TextEditingController(text: _fmt(config.dbBufferSlatsPercentage));
      final dbBufferCountCtrl = TextEditingController(text: config.dbBufferSlats.toString());

      MasterMixConfig? buildConfig() {
        final scaffoldStock = double.tryParse(scaffoldStockCtrl.text);
        final tefS = double.tryParse(tefStockCtrl.text);
        final tefF = double.tryParse(tefFinalCtrl.text);
        final mgS = double.tryParse(mgcl2StockCtrl.text);
        final mgF = double.tryParse(mgcl2FinalCtrl.text);
        if ([scaffoldStock, tefS, tefF, mgS, mgF].any((v) => v == null || v <= 0)) return null;

        // Standard fields
        final stdStock = double.tryParse(stdStockCtrl.text);
        final stdH0 = double.tryParse(stdHelix0Ctrl.text);
        final stdH1 = double.tryParse(stdHelix1Ctrl.text);
        final stdH3 = double.tryParse(stdHelix3Ctrl.text);
        final stdH4 = double.tryParse(stdHelix4Ctrl.text);
        final stdRatio = double.tryParse(stdRatioCtrl.text);
        final stdBufPct = double.tryParse(stdBufferPctCtrl.text);
        final stdBufCount = int.tryParse(stdBufferCountCtrl.text);
        if (stdStock == null || stdStock <= 0) return null;
        if (!stdSingleStock && [stdH0, stdH1, stdH3, stdH4].any((v) => v == null || v <= 0)) return null;
        if (stdRatio == null || stdRatio <= 0) return null;
        if (stdBufferMode == BufferSlatsMode.percentage && (stdBufPct == null || stdBufPct < 0)) return null;
        if (stdBufferMode == BufferSlatsMode.count && (stdBufCount == null || stdBufCount < 0)) return null;

        // Double Barrel fields
        final dbStock = double.tryParse(dbStockCtrl.text);
        final dbH0 = double.tryParse(dbHelix0Ctrl.text);
        final dbH1 = double.tryParse(dbHelix1Ctrl.text);
        final dbH3 = double.tryParse(dbHelix3Ctrl.text);
        final dbH4 = double.tryParse(dbHelix4Ctrl.text);
        final dbRatio = double.tryParse(dbRatioCtrl.text);
        final dbBufPct = double.tryParse(dbBufferPctCtrl.text);
        final dbBufCount = int.tryParse(dbBufferCountCtrl.text);
        if (dbStock == null || dbStock <= 0) return null;
        if (!dbSingleStock && [dbH0, dbH1, dbH3, dbH4].any((v) => v == null || v <= 0)) return null;
        if (dbRatio == null || dbRatio <= 0) return null;
        if (dbBufferMode == BufferSlatsMode.percentage && (dbBufPct == null || dbBufPct < 0)) return null;
        if (dbBufferMode == BufferSlatsMode.count && (dbBufCount == null || dbBufCount < 0)) return null;

        return MasterMixConfig(
          scaffoldStockConc: scaffoldStock!,
          coreStaplesMode: mode,
          tefStock: tefS!,
          tefFinal: tefF!,
          mgcl2Stock: mgS!,
          mgcl2Final: mgF!,
          // Standard
          coreStaplesUseSingleStock: stdSingleStock,
          coreStaplesStockConc: stdStock,
          coreStaplesHelixConcs: [stdH0 ?? 10000, stdH1 ?? 10000, stdH3 ?? 10000, stdH4 ?? 10000],
          coreStaplesRatio: stdRatio,
          bufferSlatsMode: stdBufferMode,
          bufferSlatsPercentage: stdBufPct ?? 10,
          bufferSlats: stdBufCount ?? 3,
          // Double Barrel
          dbCoreStaplesUseSingleStock: dbSingleStock,
          dbCoreStaplesStockConc: dbStock,
          dbCoreStaplesHelixConcs: [dbH0 ?? 10000, dbH1 ?? 10000, dbH3 ?? 10000, dbH4 ?? 10000],
          dbCoreStaplesRatio: dbRatio,
          dbBufferSlatsMode: dbBufferMode,
          dbBufferSlatsPercentage: dbBufPct ?? 10,
          dbBufferSlats: dbBufCount ?? 3,
        );
      }

      return StatefulBuilder(
        builder: (ctx, setDialogState) {
          final isValid = buildConfig() != null;
          void rebuild() => setDialogState(() {});

          return DefaultTabController(
            length: 4,
            child: AlertDialog(
              title: const Text('Export Settings'),
              content: SizedBox(
                width: 480,
                height: 560,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const TabBar(
                      isScrollable: true,
                      tabAlignment: TabAlignment.start,
                      tabs: [
                        Tab(text: 'Output'),
                        Tab(text: 'Echo'),
                        Tab(text: 'Slat Master Mixes'),
                        Tab(text: 'PEG Helpers'),
                      ],
                    ),
                    const Divider(height: 1),
                    const SizedBox(height: 16),
                    Expanded(
                      child: TabBarView(
                        children: [
                          // --- Tab 0: Output ---
                          _buildOutputTab(pdf, csv, helper, (p, c, h) {
                            setDialogState(() { pdf = p; csv = c; helper = h; });
                          }),
                          // --- Tab 1: Echo ---
                          _buildEchoTab(normalize, (v) => setDialogState(() => normalize = v), maxWellVolCtrl, rebuild),
                          // --- Tab 2: Slat Master Mixes ---
                          _buildMasterMixTab(
                            mode: mode,
                            onModeChanged: (v) => setDialogState(() => mode = v),
                            scaffoldStockCtrl: scaffoldStockCtrl,
                            tefStockCtrl: tefStockCtrl,
                            tefFinalCtrl: tefFinalCtrl,
                            mgcl2StockCtrl: mgcl2StockCtrl,
                            mgcl2FinalCtrl: mgcl2FinalCtrl,
                            stdSingleStock: stdSingleStock,
                            onStdSingleChanged: (v) => setDialogState(() => stdSingleStock = v),
                            stdStockCtrl: stdStockCtrl,
                            stdHelix0Ctrl: stdHelix0Ctrl,
                            stdHelix1Ctrl: stdHelix1Ctrl,
                            stdHelix3Ctrl: stdHelix3Ctrl,
                            stdHelix4Ctrl: stdHelix4Ctrl,
                            stdRatioCtrl: stdRatioCtrl,
                            stdBufferMode: stdBufferMode,
                            onStdBufferModeChanged: (v) => setDialogState(() => stdBufferMode = v),
                            stdBufferPctCtrl: stdBufferPctCtrl,
                            stdBufferCountCtrl: stdBufferCountCtrl,
                            dbSingleStock: dbSingleStock,
                            onDbSingleChanged: (v) => setDialogState(() => dbSingleStock = v),
                            dbStockCtrl: dbStockCtrl,
                            dbHelix0Ctrl: dbHelix0Ctrl,
                            dbHelix1Ctrl: dbHelix1Ctrl,
                            dbHelix3Ctrl: dbHelix3Ctrl,
                            dbHelix4Ctrl: dbHelix4Ctrl,
                            dbRatioCtrl: dbRatioCtrl,
                            dbBufferMode: dbBufferMode,
                            onDbBufferModeChanged: (v) => setDialogState(() => dbBufferMode = v),
                            dbBufferPctCtrl: dbBufferPctCtrl,
                            dbBufferCountCtrl: dbBufferCountCtrl,
                            onChanged: rebuild,
                          ),
                          // --- Tab 3: PEG Helpers ---
                          const Center(child: Text('Coming soon', style: TextStyle(color: Colors.grey))),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                OutlinedButton(
                  onPressed: isValid
                      ? () {
                          final maxVol = (double.tryParse(maxWellVolCtrl.text) ?? 25) * 1000;
                          Navigator.pop(ctx, (pdf: pdf, csv: csv, helper: helper, normalize: normalize, maxWellVolumeNl: maxVol, config: buildConfig()!, runExport: false));
                        }
                      : null,
                  child: const Text('Save'),
                ),
                FilledButton(
                  onPressed: isValid
                      ? () {
                          final maxVol = (double.tryParse(maxWellVolCtrl.text) ?? 25) * 1000;
                          Navigator.pop(ctx, (pdf: pdf, csv: csv, helper: helper, normalize: normalize, maxWellVolumeNl: maxVol, config: buildConfig()!, runExport: true));
                        }
                      : null,
                  child: const Text('Export'),
                ),
              ],
            ),
          );
        },
      );
    },
  );
}

// =============================================================================
// Tab builders
// =============================================================================

Widget _buildOutputTab(bool pdf, bool csv, bool helper, void Function(bool, bool, bool) onChanged) {
  return SingleChildScrollView(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _CheckRow(label: 'Generate PDF plate layouts', value: pdf, onChanged: (v) => onChanged(v, csv, helper)),
        const SizedBox(height: 4),
        _CheckRow(label: 'Generate Echo CSV instructions', value: csv, onChanged: (v) => onChanged(pdf, v, helper)),
        const SizedBox(height: 4),
        _CheckRow(label: 'Generate lab helper sheets', value: helper, onChanged: (v) => onChanged(pdf, csv, v)),
      ],
    ),
  );
}

Widget _buildEchoTab(bool normalize, ValueChanged<bool> onChanged, TextEditingController maxWellVolCtrl, VoidCallback onFieldChanged) {
  return SingleChildScrollView(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _CheckRow(label: 'Normalize volumes', value: normalize, onChanged: onChanged),
        const SizedBox(height: 16),
        _MixField(label: 'Max Well Volume', controller: maxWellVolCtrl, suffix: 'µL', onChanged: onFieldChanged),
      ],
    ),
  );
}

Widget _buildMasterMixTab({
  required CoreStaplesMode mode,
  required ValueChanged<CoreStaplesMode> onModeChanged,
  required TextEditingController scaffoldStockCtrl,
  required TextEditingController tefStockCtrl,
  required TextEditingController tefFinalCtrl,
  required TextEditingController mgcl2StockCtrl,
  required TextEditingController mgcl2FinalCtrl,
  // Standard
  required bool stdSingleStock,
  required ValueChanged<bool> onStdSingleChanged,
  required TextEditingController stdStockCtrl,
  required TextEditingController stdHelix0Ctrl,
  required TextEditingController stdHelix1Ctrl,
  required TextEditingController stdHelix3Ctrl,
  required TextEditingController stdHelix4Ctrl,
  required TextEditingController stdRatioCtrl,
  required BufferSlatsMode stdBufferMode,
  required ValueChanged<BufferSlatsMode> onStdBufferModeChanged,
  required TextEditingController stdBufferPctCtrl,
  required TextEditingController stdBufferCountCtrl,
  // Double Barrel
  required bool dbSingleStock,
  required ValueChanged<bool> onDbSingleChanged,
  required TextEditingController dbStockCtrl,
  required TextEditingController dbHelix0Ctrl,
  required TextEditingController dbHelix1Ctrl,
  required TextEditingController dbHelix3Ctrl,
  required TextEditingController dbHelix4Ctrl,
  required TextEditingController dbRatioCtrl,
  required BufferSlatsMode dbBufferMode,
  required ValueChanged<BufferSlatsMode> onDbBufferModeChanged,
  required TextEditingController dbBufferPctCtrl,
  required TextEditingController dbBufferCountCtrl,
  required VoidCallback onChanged,
}) {
  return SingleChildScrollView(
    child: Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Shared fields
          _MixField(label: 'Scaffold Stock Conc.', controller: scaffoldStockCtrl, suffix: 'nM', onChanged: onChanged),
        const SizedBox(height: 8),
        _MixField(label: 'TEF Stock', controller: tefStockCtrl, suffix: 'X', onChanged: onChanged),
        const SizedBox(height: 8),
        _MixField(label: 'TEF Final', controller: tefFinalCtrl, suffix: 'X', onChanged: onChanged),
        const SizedBox(height: 8),
        _MixField(label: 'MgCl₂ Stock', controller: mgcl2StockCtrl, suffix: 'mM', onChanged: onChanged),
        const SizedBox(height: 8),
        _MixField(label: 'MgCl₂ Final', controller: mgcl2FinalCtrl, suffix: 'mM', onChanged: onChanged),
        const Divider(height: 24),

        // Mode selector
        Row(
          children: [
            Text('Core Staples Config', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey.shade700)),
            const Spacer(),
            DropdownButton<CoreStaplesMode>(
              value: mode,
              isDense: true,
              items: const [
                DropdownMenuItem(value: CoreStaplesMode.standard, child: Text('Standard', style: TextStyle(fontSize: 13))),
                DropdownMenuItem(value: CoreStaplesMode.doubleBarrel, child: Text('Double Barrel', style: TextStyle(fontSize: 13))),
              ],
              onChanged: (v) { onModeChanged(v!); onChanged(); },
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Mode-specific section
        if (mode == CoreStaplesMode.standard)
          _buildCoreStaplesSection(
            singleStock: stdSingleStock,
            onSingleChanged: onStdSingleChanged,
            stockCtrl: stdStockCtrl,
            helix0Ctrl: stdHelix0Ctrl,
            helix1Ctrl: stdHelix1Ctrl,
            helix3Ctrl: stdHelix3Ctrl,
            helix4Ctrl: stdHelix4Ctrl,
            ratioCtrl: stdRatioCtrl,
            bufferMode: stdBufferMode,
            onBufferModeChanged: onStdBufferModeChanged,
            bufferPctCtrl: stdBufferPctCtrl,
            bufferCountCtrl: stdBufferCountCtrl,
            onChanged: onChanged,
          )
        else
          _buildCoreStaplesSection(
            singleStock: dbSingleStock,
            onSingleChanged: onDbSingleChanged,
            stockCtrl: dbStockCtrl,
            helix0Ctrl: dbHelix0Ctrl,
            helix1Ctrl: dbHelix1Ctrl,
            helix3Ctrl: dbHelix3Ctrl,
            helix4Ctrl: dbHelix4Ctrl,
            ratioCtrl: dbRatioCtrl,
            bufferMode: dbBufferMode,
            onBufferModeChanged: onDbBufferModeChanged,
            bufferPctCtrl: dbBufferPctCtrl,
            bufferCountCtrl: dbBufferCountCtrl,
            onChanged: onChanged,
          ),
        ],
      ),
    ),
  );
}

/// Builds the per-mode core staples section (used for both Standard and Double Barrel).
Widget _buildCoreStaplesSection({
  required bool singleStock,
  required ValueChanged<bool> onSingleChanged,
  required TextEditingController stockCtrl,
  required TextEditingController helix0Ctrl,
  required TextEditingController helix1Ctrl,
  required TextEditingController helix3Ctrl,
  required TextEditingController helix4Ctrl,
  required TextEditingController ratioCtrl,
  required BufferSlatsMode bufferMode,
  required ValueChanged<BufferSlatsMode> onBufferModeChanged,
  required TextEditingController bufferPctCtrl,
  required TextEditingController bufferCountCtrl,
  required VoidCallback onChanged,
}) {
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      // Single stock toggle
      Row(
        children: [
          const Text('All Core Staples Mix', style: TextStyle(fontSize: 13)),
          const Spacer(),
          Switch(
            value: singleStock,
            onChanged: (v) { onSingleChanged(v); onChanged(); },
          ),
        ],
      ),
      const SizedBox(height: 8),

      if (singleStock) ...[
        _MixField(label: 'Core Staples Stock Conc.', controller: stockCtrl, suffix: 'nM', onChanged: onChanged),
      ] else ...[
        _MixField(label: 'Core Staples Helix 0', controller: helix0Ctrl, suffix: 'nM', onChanged: onChanged),
        const SizedBox(height: 8),
        _MixField(label: 'Core Staples Helix 1', controller: helix1Ctrl, suffix: 'nM', onChanged: onChanged),
        const SizedBox(height: 8),
        _MixField(label: 'Core Staples Helix 3', controller: helix3Ctrl, suffix: 'nM', onChanged: onChanged),
        const SizedBox(height: 8),
        _MixField(label: 'Core Staples Helix 4', controller: helix4Ctrl, suffix: 'nM', onChanged: onChanged),
      ],
      const SizedBox(height: 12),

      _MixField(label: 'Core Staples : Scaffold Ratio', controller: ratioCtrl, suffix: 'x', onChanged: onChanged),
      const SizedBox(height: 12),

      // Buffer slats
      Text('Extra Slats', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.grey.shade700)),
      const SizedBox(height: 8),
      SegmentedButton<BufferSlatsMode>(
        segments: const [
          ButtonSegment(value: BufferSlatsMode.percentage, label: Text('Percentage')),
          ButtonSegment(value: BufferSlatsMode.count, label: Text('Count')),
        ],
        selected: {bufferMode},
        onSelectionChanged: (v) { onBufferModeChanged(v.first); onChanged(); },
        style: ButtonStyle(visualDensity: VisualDensity.compact),
      ),
      const SizedBox(height: 8),
      if (bufferMode == BufferSlatsMode.percentage)
        _MixField(label: 'Extra Slats', controller: bufferPctCtrl, suffix: '%', onChanged: onChanged)
      else
        _MixField(label: 'Extra Slats', controller: bufferCountCtrl, suffix: '', onChanged: onChanged),
    ],
  );
}

// =============================================================================
// Helper widgets
// =============================================================================

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
