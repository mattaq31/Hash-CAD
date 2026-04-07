import 'package:flutter/material.dart';
import 'echo_plate_constants.dart' show echoMaxWellVolumeNl;
import 'plate_layout_state.dart' show WellConfig;

/// Shows a dialog to configure per-well Echo dispensing parameters.
///
/// Returns the configured [WellConfig] on "Apply", or null on cancel.
///
/// When [estimateVolumeNl] is provided, it is called with the current config
/// to compute the estimated total transfer volume in nL. A warning is shown
/// if this exceeds 25000 nL (25 µL).
Future<WellConfig?> showWellConfigDialog(
  BuildContext context, {
  String title = 'Configure Wells',
  WellConfig initial = const WellConfig(),
  double Function(WellConfig config)? estimateVolumeNl,
}) {
  return showDialog<WellConfig>(
    context: context,
    builder: (ctx) {
      final ratioCtrl = TextEditingController(text: initial.ratio.toStringAsFixed(0));
      final volumeCtrl = TextEditingController(text: initial.volume.toStringAsFixed(0));
      final scaffoldConcCtrl = TextEditingController(text: initial.scaffoldConc.toStringAsFixed(0));

      return StatefulBuilder(
        builder: (ctx, setDialogState) {
          double ratio = double.tryParse(ratioCtrl.text) ?? 0;
          double volume = double.tryParse(volumeCtrl.text) ?? 0;
          double scaffoldConc = double.tryParse(scaffoldConcCtrl.text) ?? 0;
          double materialPerHandle = scaffoldConc * ratio * volume / 1000;
          double totalSlatQuantity = scaffoldConc * volume / 1000;
          bool isValid = ratio > 0 && volume > 0 && scaffoldConc > 0;

          // Compute volume warning if estimator is provided
          double? estimatedNl;
          bool volumeTooHigh = false;
          if (estimateVolumeNl != null && isValid) {
            estimatedNl = estimateVolumeNl(WellConfig(ratio: ratio, volume: volume, scaffoldConc: scaffoldConc));
            volumeTooHigh = estimatedNl > echoMaxWellVolumeNl;
          }

          void rebuild() => setDialogState(() {});

          return AlertDialog(
            title: Text(title),
            content: SizedBox(
              width: 320,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _ConfigField(label: 'Handle : Scaffold Ratio', controller: ratioCtrl, suffix: 'x', onChanged: rebuild),
                  const SizedBox(height: 12),
                  _ConfigField(label: 'Volume', controller: volumeCtrl, suffix: 'µL', onChanged: rebuild),
                  const SizedBox(height: 12),
                  _ConfigField(
                      label: 'Scaffold Concentration', controller: scaffoldConcCtrl, suffix: 'nM', onChanged: rebuild),
                  const Divider(height: 24),
                  _ComputedRow(label: 'Material per Handle', value: '${materialPerHandle.toStringAsFixed(1)} pmol'),
                  const SizedBox(height: 6),
                  _ComputedRow(label: 'Total Slat Quantity', value: '${totalSlatQuantity.toStringAsFixed(1)} pmol'),
                  if (volumeTooHigh && estimatedNl != null) ...[
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Icon(Icons.warning, size: 16, color: Colors.orange.shade700),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            'Estimated transfer volume (${(estimatedNl / 1000).toStringAsFixed(1)} µL) exceeds 25 µL',
                            style: TextStyle(fontSize: 12, color: Colors.orange.shade700),
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
              FilledButton(
                onPressed: isValid
                    ? () => Navigator.pop(ctx, WellConfig(ratio: ratio, volume: volume, scaffoldConc: scaffoldConc))
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

class _ConfigField extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final String suffix;
  final VoidCallback onChanged;

  const _ConfigField({required this.label, required this.controller, required this.suffix, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        suffixText: suffix,
        isDense: true,
        border: const OutlineInputBorder(),
      ),
      onChanged: (_) => onChanged(),
    );
  }
}

class _ComputedRow extends StatelessWidget {
  final String label;
  final String value;

  const _ComputedRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: TextStyle(fontSize: 13, color: Colors.grey.shade700)),
        Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
      ],
    );
  }
}
