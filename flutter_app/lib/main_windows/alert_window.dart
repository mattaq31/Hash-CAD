import 'package:flutter/material.dart';


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