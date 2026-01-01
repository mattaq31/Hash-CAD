import 'slats.dart';

/// Typedef for handle key (slatID, position, side) - matches Python convention
typedef HandleKey = (String slatID, int position, int side);

/// Parses integer slat side (2 or 5) from helix string like 'H5' or 'H2'
int parseHelixSide(String helixString) {
  return int.parse(helixString.replaceAll(RegExp(r'[^0-9]'), ''));
}

/// Gets integer slat side from layer map for a given layer and position (top/bottom)
int getSlatSideFromLayer(Map<String, Map<String, dynamic>> layerMap, String layerID, String slatSide) {
  return parseHelixSide(layerMap[layerID]?['${slatSide}_helix']);
}

/// Calculates adjacent layer order (order +1 for top, -1 for bottom)
int getAdjacentLayerOrder(Map<String, Map<String, dynamic>> layerMap, String layerID, String slatSide) {
  return layerMap[layerID]?['order'] + (slatSide == 'top' ? 1 : -1);
}

/// Gets the appropriate handle dictionary from a slat based on side (2 or 5)
Map<int, Map<String, dynamic>> getHandleDict(Slat slat, int side) {
  return side == 5 ? slat.h5Handles : slat.h2Handles;
}

/// Generates a layer-side key string for occupiedCargoPoints indexing
String generateLayerSideKey(String layerID, String slatSide) {
  return '$layerID-$slatSide';
}

/// Determines the layer offset direction for a given layer and slat side
/// Returns 1 if the side points upward, -1 if it points downward
int getLayerOffsetForSide(Map<String, Map<String, dynamic>> layerMap, String layerID, int side) {
  return (layerMap[layerID]!['top_helix'] == 'H5' && side == 5 ||  layerMap[layerID]!['top_helix'] == 'H2' && side == 2) ? 1 : -1;
}

/// Gets the opposing helix side for a given layer based on direction
/// direction: 1 for looking up (returns bottom helix of adjacent), -1 for looking down (returns top helix of adjacent)
int getOpposingSide(Map<String, Map<String, dynamic>> layerMap, String adjacentLayerID, int direction) {
  String helixKey = direction == 1 ? 'bottom_helix' : 'top_helix';
  return parseHelixSide(layerMap[adjacentLayerID]?[helixKey]);
}
