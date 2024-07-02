
///////////////////////////////
//   Creating Slat Array     //
///////////////////////////////

import {placeCargo, placeSlat} from './helper_functions_drawing.js'



/** Converts coordinates into a (string) key for the dictionary of slats/cargo/handles
 * 
 * @param x X-coordinate of dictionary/array
 * @param y Y-coordinate of dictionary/array
 * @param layer Layer coordinate of dictionary/array
 * @returns {string}
 */
export function gridKey(x, y, layer) {
    return `${x},${y},${layer}`;
}

/** Populates a grid dictionary with slat IDs keyed by (x, y, layer)
 * 
 * @param gridDict Dictionary in which to save slats
 * @param layers List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 */
export function populateSparseGridDictionarySlats(gridDict, layers, minorGridSize) {
    layers.forEach((layer, layerIndex) => {
        layer[1].children().forEach(child => {
            let slatId = child.attr('id');
            let bbox = child.bbox();
            let startX = Math.round(bbox.x / minorGridSize);
            let startY = Math.round(bbox.y / minorGridSize);
            let endX = Math.round((bbox.x + bbox.width) / minorGridSize);
            let endY = Math.round((bbox.y + bbox.height) / minorGridSize);

            // Populate the grid dictionary with the slat ID for the occupied positions
            for (let x = startX; x <= endX; x++) {
                for (let y = startY; y <= endY; y++) {
                    let key = gridKey(x, y, layerIndex);
                    gridDict[key] = slatId;
                }
            }
        });
    });
}

/** Populates a grid dictionary with cargo type IDs keyed by (x, y, layer)
 * 
 * @param gridDict Dictionary in which to save slats
 * @param layers List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param minorGridSizeThe snapping grid size. Corresponds to the distance between two handles. 
 */
// Populate the sparse grid dictionary with cargo IDs
export function populateSparseGridDictionaryCargo(gridDict, layers, minorGridSize) {
    layers.forEach((layer, layerIndex) => {
        layer[2].children().forEach(child => {
            let cargoId = child.attr('type');
            let bbox = child.bbox();
            
            let centerX = Math.round((bbox.x + bbox.width / 2) / minorGridSize);
            let centerY = Math.round((bbox.y + bbox.height/ 2) / minorGridSize);

            // Populate the grid dictionary with the cargo ID for the occupied positions
            let key = gridKey(centerX, centerY, layerIndex);
            gridDict[key] = cargoId;
        });
    });
}

/** Creates a filled grid dictionary containing slat and cargo information.
 * 
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @returns {{}[]}
 */
//Create array
export function createGridArray(layerList, minorGridSize) {
    // Initialize the sparse grid dictionary
    let gridDictSlats = {};
    let gridDictCargo = {};

    // Populate the sparse grid dictionary with slat IDs
    populateSparseGridDictionarySlats(gridDictSlats, Array.from(layerList.values()), minorGridSize);

    // Populate the sparse grid dictionary with cargo IDs
    populateSparseGridDictionaryCargo(gridDictCargo, Array.from(layerList.values()), minorGridSize);

    // You can now use the gridDict as needed
    let gridDict = [gridDictSlats, gridDictCargo];
    //console.log(gridDict);

    return gridDict
}

/** Removes all layers from the crisscross design
 * 
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 */
function removeAllLayers(layerList){
    const layerRemoveButtons = document.querySelectorAll('.layer-remove-button');
    
    // Click each button
    layerRemoveButtons.forEach(button => {
        button.click(); // Simulate a click on each button
    });
}

/** Draws cargo on canvas as described in a cargo dictionary passed to the function
 * 
 * @param cargoDict Cargo dictionary describing cargo types (ID) by locations (x, y, layer)
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param shownCargoOpacity Opacity at which cargo should be drawn when shown -- default.
 */
function importCargo(cargoDict, layerList, minorGridSize, shownCargoOpacity){
    //Now add new cargo:
    let cargoCounter = 1;

    // Iterate through the dictionary
    for (const [key, value] of Object.entries(cargoDict)) {
        
        let keyArray = key.split(',')

        let dictX   = Number(keyArray[0])
        let dictY   = Number(keyArray[1])
        let layerId = keyArray[2]

        let cargoId = value

        while(!layerList.has(layerId)){
            const addLayerButton = document.getElementById('add-layer');
            addLayerButton.click();
        }

        let fullLayer = layerList.get(layerId);
        let activeCargoLayer = fullLayer[2]

        let placeX = dictX * minorGridSize
        let placeY = dictY * minorGridSize

        let activeLayerColor = fullLayer[3]// '#ff0000'

        cargoCounter = placeCargo(placeX, placeY, activeCargoLayer, layerId, minorGridSize, 
                                    activeLayerColor, shownCargoOpacity, cargoCounter, cargoId, layerList)

    }

}

/** Within a slat dictionary, finds a slat with a particular ID. Then identifies starting coordinates, orientation (horizontal/vertical)
 * 
 * @param slatDict Slat dictionary describing slat IDs by locations (x, y, layer)
 * @param slatNum SlatID/Number of slat to be found/oriented
 * @returns {number[]}
 */
function findSlatStartOrientation(slatDict, slatNum){
    let minX = Infinity;
    let maxX = -Infinity;

    let minY = Infinity;
    let maxY = -Infinity;

    let horizontal = null;

    let layerId = null;

    for (const [key, value] of Object.entries(slatDict)) {
        
        if(value == slatNum){
            let keyArray = key.split(',')
            let tmpX = Number(keyArray[0])
            let tmpY = Number(keyArray[1])
            layerId = keyArray[2]

            if(tmpX < minX){
                minX = tmpX
            }
            if(tmpX > maxX){
                maxX = tmpX
            }

            if(tmpY < minY){
                minY = tmpY
            }
            if(tmpY > maxY){
                maxY = tmpY
            }
        }
    }

    if(minY == maxY){
        horizontal = true
    }
    else if(minX == maxX){
        horizontal = false; 
    }

    return [minX, minY, layerId, horizontal]
}

/** Draws slats on canvas as described in a slat dictionary passed to the function
 * 
 * @param slatDict Slat dictionary describing slat IDs by location (x, y, layer)
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param shownOpacity Opacity at which slats should be drawn when shown -- default
 * @returns {number}
 */
function importSlats(slatDict, layerList, minorGridSize, shownOpacity){

    //Get unique slat numbers
    let slatNums = Object.values(slatDict)
    const uniqueSlatNums = new Set(slatNums);
    const maxSlatNum = Math.max(...uniqueSlatNums); // The ... convert this slat to an array basically?

    for (const slatNum of uniqueSlatNums) {
        //console.log(slatNum);

        let orientation = findSlatStartOrientation(slatDict, slatNum)

        let dictX = orientation[0]
        let dictY = orientation[1]
        let layerId = orientation[2]
        let horizontal = orientation[3]

        while(!layerList.has(layerId)){
            const addLayerButton = document.getElementById('add-layer');
            addLayerButton.click();
        }

        let fullLayer = layerList.get(layerId);
        let activeSlatLayer = fullLayer[1]

        let placeX = dictX * minorGridSize
        let placeY = dictY * minorGridSize

        let activeLayerColor = fullLayer[3] //fullLayer[3] store the layer color! '#ff0000'

        //MAKE SURE TO SOMEHOW PASS THE MAX COUNTER VALUE TO THE MAIN GLOBAL SO THAT WE CAN ACTUALLY CONTINUE MODIFYING THE DESIGN...
        placeSlat(placeX, placeY, activeSlatLayer, layerId, minorGridSize, 
                    activeLayerColor, shownOpacity, slatNum, horizontal, layerList)
            
        //console.log("new slat is placed!")
    }

    return (maxSlatNum + 1)
}

/** Draws full design on canvas as described in slat and cargo dictionaries
 * 
 * @param slatDict Slat dictionary describing slat IDs by location (x, y, layer)
 * @param cargoDict Cargo dictionary describing cargo types (ID) by locations (x, y, layer)
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param shownOpacity Opacity at which slats should be drawn when shown -- default
 * @param shownCargoOpacity Opacity at which cargo should be drawn when shown -- default.
 * @returns {number}
 */
export function importDesign(slatDict, cargoDict, layerList, minorGridSize, shownOpacity, shownCargoOpacity){
    removeAllLayers(layerList)
    let slatCounter = importSlats(slatDict, layerList, minorGridSize, shownOpacity)
    importCargo(cargoDict, layerList, minorGridSize, shownCargoOpacity)

    return slatCounter;
}
