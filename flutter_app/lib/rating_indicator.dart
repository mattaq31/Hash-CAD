import 'package:flutter/material.dart';

class RatingIndicator extends StatelessWidget {
  final double rating; // Value from 0 to 100

  const RatingIndicator({super.key, required this.rating});

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
            value: rating / 100,
            strokeWidth: 8,
            valueColor: AlwaysStoppedAnimation<Color>(_getColor(rating)),
            backgroundColor: Colors.transparent,
          ),
        ),

        // Rating text in center
        Text(
          "${rating.toInt()}", // Convert double to integer for cleaner display
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
    if (rating < 50) {
      return Colors.red;
    } else if (rating < 80) {
      return Colors.orange;
    } else {
      return Colors.green;
    }
  }
}