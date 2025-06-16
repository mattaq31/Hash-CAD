import 'package:flutter/material.dart';
import '../crisscross_core/handle_plates.dart';


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