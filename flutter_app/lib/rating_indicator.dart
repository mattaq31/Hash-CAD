import 'package:flutter/material.dart';

class HammingIndicator extends StatelessWidget {
  final double value; // Value from 0 to 32

  const HammingIndicator({super.key, required this.value});

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        SizedBox(
          width: 60,
          height: 60,
          child: CircularProgressIndicator(
            value: 1.0,
            strokeWidth: 8,
            valueColor: AlwaysStoppedAnimation<Color>(Colors.grey.shade300),
          ),
        ),

        SizedBox(
          width: 60,
          height: 60,
          child: CircularProgressIndicator(
            value: value / 32,
            strokeWidth: 8,
            valueColor: AlwaysStoppedAnimation<Color>(_getColor(value)),
            backgroundColor: Colors.transparent,
          ),
        ),

        // Rating text in center
        Text(
          "${(32-value).toInt()}", // Convert double to integer for cleaner display
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.black,
          ),
        ),
      ],
    );
  }

  // Function to determine color based on rating value
  Color _getColor(double rating) {
    if (rating < 25) {
      return Colors.red;
    } else if (rating < 28) {
      return Colors.orange;
    } else {
      return Colors.green;
    }
  }
}