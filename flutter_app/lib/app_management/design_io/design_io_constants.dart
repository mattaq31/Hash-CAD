/// Single source of truth for the #-CAD Excel file format.
///
/// All sheet names, cell positions, category strings, and naming conventions
/// used by both [exportDesign] and [parseDesignInIsolate] are defined here.
/// Changing a format detail in this file updates both export and import.
library;

// --- Sheet name patterns ---
const String slatLayerPrefix = 'slat_layer_';
const String cargoLayerPrefix = 'cargo_layer_';
const String seedLayerPrefix = 'seed_layer_';
const String handleInterfacePrefix = 'handle_interface_';
const String metadataSheetName = 'metadata';
const String slatTypesSheetName = 'slat_types';
const String slatHandleLinksSheetName = 'slat_handle_links';
const String echoPlateSheetPrefix = 'p';
const String inputPlateSheetName = 'input_source_plates';
const String inputPlateTitlePrefix = '=== PLATE: ';
const String inputPlateTitleSuffix = ' ===';
const String labMetadataSheetName = 'lab_metadata';

// --- Sheet name builders ---
String slatLayerSheetName(int layerOrder) => '$slatLayerPrefix${layerOrder + 1}';
String handleInterfaceSheetName(int layerOrder) => '$handleInterfacePrefix${layerOrder + 1}';
String cargoSheetName(int layerOrder, String side, String helix) => '$cargoLayerPrefix${layerOrder + 1}_${side}_$helix';
String seedSheetName(int layerOrder, String side, String helix) => '$seedLayerPrefix${layerOrder + 1}_${side}_$helix';

// --- Side name mapping (top/upper, bottom/lower duality) ---
String sideToPositionalName(String side) => side == 'top' ? 'upper' : 'lower';
String positionalToSide(String positional) => positional == 'upper' ? 'top' : 'bottom';
String sideToHelixKey(String side) => '${side}_helix';

// --- Metadata cell positions ---
const String metaCellLayerInterface = 'B1';
const String metaCellGridMode = 'B2';
const String metaCellFileFormat = 'B3';
const String metaCellMinX = 'B4';
const String metaCellMinY = 'C4';
const String metaCellMaxX = 'B5';
const String metaCellMaxY = 'C5';
const int metaLayerStartRow = 8;

// --- Metadata section markers ---
const String metaSectionLayerInfo = 'LAYER INFO';
const String metaSectionCargoInfo = 'CARGO INFO';
const String metaSectionSlatColorInfo = 'UNIQUE SLAT COLOUR INFO';

// --- Handle category strings ---
const String categoryAssemblyHandle = 'ASSEMBLY_HANDLE';
const String categoryAssemblyAntihandle = 'ASSEMBLY_ANTIHANDLE';
const String categoryCargo = 'CARGO';
const String categorySeed = 'SEED';
const String categoryAssembly = 'ASSEMBLY';

// --- Phantom slat cell format: P{phantomNumericID}_{parentNumericID}-{position} ---
String encodePhantomCellValue(int phantomNumericID, int parentNumericID, int position) =>
    'P${phantomNumericID}_$parentNumericID-$position';

// --- Handle highlight color ---
const String handleHighlightHex = '#1AFF1A';
