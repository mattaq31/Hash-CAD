import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';

import '../../crisscross_core/slats.dart';
import '../../crisscross_core/cargo.dart';
import '../../crisscross_core/seed.dart';
import '../../crisscross_core/handle_plates.dart';
import '../../crisscross_core/common_utilities.dart';
import '../slat_undo_stack.dart';
import '../shared_app_state.dart';
import 'design_state_handle_link_mixin.dart';

/// Contract defining all shared members between DesignState mixins.
/// This enables IDE navigation (Find Usages) to work across mixins by
/// providing a single source of truth for all shared method signatures.
///
/// To find which mixin implements a method, search for the === comment section.
mixin DesignStateContract on ChangeNotifier {
  // === State properties (provided by DesignState) ===
  double get gridSize;
  double get x60Jump;
  double get y60Jump;
  String get gridMode;
  set gridMode(String value);
  bool get standardTilt;
  set standardTilt(bool value);
  HoverPreview? get hoverPreview;
  set hoverPreview(HoverPreview? value);
  Map<(String, int), Offset> get multiSlatGenerators;
  set multiSlatGenerators(Map<(String, int), Offset> value);
  Map<(String, int), Offset> get multiSlatGeneratorsAlternate;
  set multiSlatGeneratorsAlternate(Map<(String, int), Offset> value);
  List<String> get colorPalette;
  Map<String, Map<String, dynamic>> get layerMap;
  set layerMap(Map<String, Map<String, dynamic>> value);
  SlatUndoStack get undoStack;
  set undoStack(SlatUndoStack value);
  Map<String, Slat> get slats;
  set slats(Map<String, Slat> value);
  String get selectedLayerKey;
  set selectedLayerKey(String value);
  List<String> get selectedSlats;
  set selectedSlats(List<String> value);
  String get nextLayerKey;
  set nextLayerKey(String value);
  String get nextSeedID;
  set nextSeedID(String value);
  int get nextColorIndex;
  set nextColorIndex(int value);
  int get slatAddCount;
  set slatAddCount(int value);
  String get slatAddDirection;
  set slatAddDirection(String value);
  Color get uniqueSlatColor;
  set uniqueSlatColor(Color value);
  int get currentMaxValency;
  set currentMaxValency(int value);
  double get currentEffValency;
  set currentEffValency(double value);
  bool get hammingValueValid;
  set hammingValueValid(bool value);
  int get cargoAddCount;
  set cargoAddCount(int value);
  String? get cargoAdditionType;
  set cargoAdditionType(String? value);
  String get slatAdditionType;
  set slatAdditionType(String value);
  List<Offset> get selectedHandlePositions;
  set selectedHandlePositions(List<Offset> value);
  List<Offset> get selectedAssemblyPositions;
  set selectedAssemblyPositions(List<Offset> value);
  String get designName;
  set designName(String value);
  Map<String, Map<Offset, String>> get occupiedCargoPoints;
  set occupiedCargoPoints(Map<String, Map<Offset, String>> value);
  Map<(String, String, Offset), Seed> get seedRoster;
  set seedRoster(Map<(String, String, Offset), Seed> value);
  Map<String, List<Color>> get uniqueSlatColorsByLayer;
  set uniqueSlatColorsByLayer(Map<String, List<Color>> value);
  bool get currentlyLoadingDesign;
  set currentlyLoadingDesign(bool value);
  bool get currentlyComputingHamming;
  set currentlyComputingHamming(bool value);
  Map<String, Map<Offset, String>> get occupiedGridPoints;
  set occupiedGridPoints(Map<String, Map<Offset, String>> value);
  Map<String, Map<int, String>> get phantomMap;
  set phantomMap(Map<String, Map<int, String>> value);
  HandleLinkManager get assemblyLinkManager;
  set assemblyLinkManager(HandleLinkManager value);
  Map<String, Cargo> get cargoPalette;
  set cargoPalette(Map<String, Cargo> value);
  PlateLibrary get plateStack;

  // === Methods from DesignStateCoreMixin ===
  void setHoverPreview(HoverPreview? preview);
  void initializeUndoStack();
  Offset convertRealSpacetoCoordinateSpace(Offset inputPosition);
  Offset convertCoordinateSpacetoRealSpace(Offset inputPosition);
  String? getLayerByOrder(int order);
  String flipSlatSide(String side);
  bool layerNumberValid(int layerOrder);
  void resetDefaults();
  void setGridMode(String value);
  void setDesignName(String newName);
  void setUniqueSlatColor(Color color);
  void saveUndoState();
  void undo2DAction({bool redo = false});

  // === Methods from DesignStateFileIOMixin ===
  void exportCurrentDesign();
  void importNewDesign(BuildContext context, {String? fileName, Uint8List? fileBytes});
  void clearAll();

  // === Methods from DesignStateLayerMixin ===
  String? getAdjacentLayer(String layerID, String slatSide);
  void updateActiveLayer(String value);
  void cycleActiveLayer(bool upDirection);
  void updateLayerColor(String layer, Color color);
  void clearSelection();
  void rotateLayerDirection(String layerKey);
  void flipLayer(String layer, BuildContext context);
  void flipLayerVisibility(String layer);
  void flipMultiSlatGenerator();
  void flipSlatAddDirection();
  void deleteLayer(String layer);
  void reOrderLayers(List<String> newOrder, BuildContext context);
  void addLayer();

  // === Methods from DesignStateSlatMixin ===
  void setSlatAdditionType(String type);
  void addSlats(String layer, Map<int, Map<int, Offset>> slatCoordinates);
  void updateSlatPosition(String slatID, Map<int, Offset> slatCoordinates, {bool skipStateUpdate = false, requestFlip = false});
  void updateMultiSlatPosition(List<String> slatIDs, List<Map<int, Offset>> allCoordinates, {bool requestFlip = false});
  void removeSlat(String ID, {bool skipStateUpdate = false});
  void removeSlats(List<String> IDs);
  void flipSlat(String ID);
  void flipSlats(List<String> IDs);
  void selectSlat(String ID, {bool addOnly = false});
  void updateSlatAddCount(int value);

  // === Methods from DesignStateHandleMixin ===
  bool handleWithinBounds(Slat slat, int position, int side, String layerID);
  Set<HandleKey> smartSetHandle(Slat slat, int position, int side, String handlePayload, String category, {bool requestStateUpdate = false});
  Set<(String, Offset)> smartDeleteHandle(Slat slat, int position, int side, {bool cascadeDelete = false, bool requestStateUpdate = false});
  void selectAssemblyHandle(Offset coordinate, {bool addOnly = false});
  void clearAssemblySelection();
  void deleteSelectedHandles(String slatSide);
  void moveAssemblyHandle(Map<Offset, Offset> coordinateTransferMap, String layerID, String slatSide);
  Set<(String, Offset)> deleteHandleWithPhantomPropagation(Slat slat, int position, int side);
  void assignAssemblyHandleArray(List<List<List<int>>> handleArray, Offset? minPos, Offset? maxPos);
  void updateDesignHammingValue();
  void generateRandomAssemblyHandles(int uniqueHandleCount, bool splitLayerHandles, {bool allAvailableHandles = false});
  Future<bool> updateAssemblyHandlesFromFile(BuildContext context);
  void fullHandleValidationWithWarning(BuildContext context);
  String? checkLinkManagerConstraints();
  String? checkPhantomSlatConsistency();
  List<List<List<int>>> getSlatArray();
  Map<String, List<(int, int)>> getSlatCoords({bool getPhantoms = false});
  List<List<List<int>>> getHandleArray();
  Map<String, String> getSlatTypes();
  void clearAssemblyHandles();
  void syncAllAssemblyHandles();
  Map<String, String> getPhantomParentsForGrpc();

  // === Methods from DesignStateSlatColorMixin ===
  void assignColorToSelectedSlats(Color color);
  void editSlatColorSearch(String layerKey, int oldColorIndex, Color newColor);
  void removeSlatColorFromLayer(String layerKey, int colorIndex);
  void clearAllSlatColors();
  void clearSlatColorsFromLayer(String layer);

  // === Methods from DesignStatePhantomMixin ===
  void addPhantomSlats(String layer, Map<int, Map<int, Offset>> slatCoordinates, Map<int, Slat> referenceSlats);
  void removeAllPhantomSlats();
  void clearPhantomSlatSelection();
  bool selectionHasPhantoms();
  bool selectionInvolvesPhantoms();
  void spawnAndPlacePhantomSlats();
  void unLinkSelectedPhantoms();

  // === Methods from DesignStateCargoMixin ===
  void addCargoType(Cargo cargo);
  void deleteCargoType(String cargoName);
  Cargo getCargoFromCoordinate(Offset coordinate, String layerID, String slatSide);
  void deleteAllCargo();
  void moveCargo(Map<Offset, Offset> coordinateTransferMap, String layerID, String slatSide, {bool skipStateUpdate = false});
  void updateCargoAddCount(int value);
  void selectCargoType(String ID);
  void selectHandle(Offset coordinate, {bool addOnly = false});
  void attachCargo(Cargo cargo, String layerID, String slatSide, Map<int, Offset> coordinates, {bool skipStateUpdate = false});
  void removeCargo(String slatID, String slatSide, Offset coordinate, {bool skipStateUpdate = false});
  void removeSelectedCargo(String slatSide);

  // === Methods from DesignStateSeedMixin ===
  (String, String, Offset)? isHandlePartOfActiveSeed(String layerID, String slatSide, Offset coordinate);
  List<Offset> getAllSeedHandleCoordinates((String, String, Offset) seedKey);
  void dissolveSeed((String, String, Offset) seedKey, {bool skipStateUpdate = false});
  void attachSeed(String layerID, String slatSide, Map<int, Offset> coordinates, BuildContext context);
  void checkAndReinstateSeeds(String layerID, String slatSide, {bool skipStateUpdate = false});
  void removeSeed(String layerID, String slatSide, Offset coordinate);
  void removeSingleSeedHandle(String slatID, String slatSide, Offset coordinate, {bool skipStateUpdate = false});

  // === Methods from DesignStatePlateMixin ===
  void importPlates();
  void removePlate(String plateName);
  void removeAllPlates();
  void plateAssignAllHandles();

  // === Methods from DesignStateHandleLinkMixin ===
  void clearAllHandleLinks();
  void importHandleLinks(List<List<dynamic>> data);
  List<List<dynamic>> exportHandleLinks();
  void linkHandles(List<HandleKey> keys);
  void unlinkHandle(HandleKey key);
  void toggleHandleBlock(HandleKey key);
  void setHandleEnforcedValue(HandleKey key, int value, {bool requestStateUpdate = true});
  void linkHandlesAndPropagate(List<HandleKey> keys);
  void toggleHandleBlockAndApply(HandleKey key);
  void setHandleEnforcedValueAndApply(HandleKey key, int value);
}
