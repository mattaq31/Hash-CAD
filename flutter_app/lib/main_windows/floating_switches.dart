import 'package:flutter/material.dart';

Widget buildToggleSwitch({
  required String label,
  required bool value,
  required void Function(bool) onChanged,
}) {
  return Row(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.center,
    children: [
      SizedBox(
        width: 115, // Fixed width for label column
        child: Text(
          label,
          style: const TextStyle(fontSize: 12),
          overflow: TextOverflow.ellipsis,
        ),
      ),
      Transform.scale(
        scale: 0.75,
        child: Switch(
          value: value,
          onChanged: onChanged,
        ),
      ),
    ],
  );
}


Widget buildFreeToggleSwitch({
  required String label,
  required bool value,
  required void Function(bool) onChanged,
}) {
  return Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Text(label, style: const TextStyle(fontSize: 12)),
      Transform.scale(
        scale: 0.75, // Scale down the switch
        child: Switch(
          value: value,
          onChanged: onChanged,
        ),
      ),
    ],
  );
}