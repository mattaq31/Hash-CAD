import 'dart:math';

List<List<List<int>>> generateRandomSlatHandles(List<List<List<int>>> baseArray, int uniqueSequences, {int seed=8}) {
  int xSize = baseArray.length;
  int ySize = baseArray[0].length;
  int numLayers = baseArray[0][0].length;

  List<List<List<int>>> handleArray = List.generate(xSize, (_) => List.generate(ySize, (_) => List.filled(numLayers-1, 0)));

  Random rand = Random(seed);
  for (int i = 0; i < xSize; i++) {
    for (int j = 0; j < ySize; j++) {
      for (int k = 0; k < numLayers - 1; k++) {
        // Check if slats exist in the current and next layer
        if (baseArray[i][j][k] != 0 && baseArray[i][j][k + 1] != 0) {
          handleArray[i][j][k] = rand.nextInt(uniqueSequences) + 1; // Random value between 1 and uniqueSequences
        }
      }
    }
  }
  return handleArray;
}
