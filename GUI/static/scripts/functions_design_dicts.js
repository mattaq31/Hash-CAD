import {placeCargo, placeSlat, placeHandle, placeSeed} from './functions_drawing.js'
import {getHandleLayerDict} from './functions_handles.js'

/** 
 * Converts coordinates into a (string) key for the dictionary of slats/cargo/handles
 * @param x X-coordinate of dictionary/array
 * @param y Y-coordinate of dictionary/array
 * @param layer Layer coordinate of dictionary/array
 * @returns {string} Key for dictionary of slats/cargo/handles
 */
function gridKey(x, y, layer) {
    return `${x},${y},${layer}`;
}

/**
 * Populates a grid dictionary with slat IDs keyed by (x, y, layer)
 * @param {Array} layers List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @returns {Map} Slat dictionary
 */
function populateSparseGridDictionarySlats(layers, minorGridSize) {
    let gridDict = {}
    
    layers.forEach((layer, layerIndex) => {
        layer[1].children().forEach(child => {
            if(child.attr('id') != 'seed'){
                let slatId = child.attr('id');
                let bbox = child.bbox();
                let startX = Math.ceil(bbox.x / minorGridSize);
                let startY = Math.ceil(bbox.y / minorGridSize);
                let endX = Math.floor((bbox.x + bbox.width) / minorGridSize);
                let endY = Math.floor((bbox.y + bbox.height) / minorGridSize);

                // Populate the grid dictionary with the slat ID for the occupied positions
                for (let x = startX; x <= endX; x++) {
                    for (let y = startY; y <= endY; y++) {
                        let key = gridKey(x, y, layerIndex + 1);
                        gridDict[key] = slatId;
                    }
                }
            }
        });
    });

    return gridDict
}

/** 
 * Populates a grid dictionary with cargo type IDs keyed by ([x, y], layer, orientation)
 * @param {Array} layers List of layers containing the SVG.js layer group items
 * @param {Number} minorGridSizeThe The snapping grid size. Corresponds to the distance between two handles. 
 * @returns {Map} Cargo dictionary
 */
function populateSparseGridDictionaryCargo(layers, minorGridSize) {
    let gridDict = {}
    let handleOrientations = getHandleLayerDict(layers)

    layers.forEach((layer, layerIndex) => {
        //BOTTOM LAYER
        layer[2].children().forEach(child => {
            if(child.attr('id') != 'seed'){
                let cargoId = child.attr('type');
                let bbox = child.bbox();
                
                let centerX = Math.round((bbox.x + bbox.width / 2) / minorGridSize);
                let centerY = Math.round((bbox.y + bbox.height/ 2) / minorGridSize);

                // Populate the grid dictionary with the cargo ID for the occupied positions
                let key = [([centerX, centerY]), layerIndex + 1, handleOrientations[layerIndex][1]]; 
                gridDict[key] = cargoId
            }
        });

        //TOP LAYER
        layer[3].children().forEach(child => {
            let cargoId = child.attr('type');
            let bbox = child.bbox();
            
            let centerX = Math.round((bbox.x + bbox.width / 2) / minorGridSize);
            let centerY = Math.round((bbox.y + bbox.height/ 2) / minorGridSize);

            // Populate the grid dictionary with the cargo ID for the occupied positions
            let key = [[centerX, centerY], layerIndex + 1, handleOrientations[layerIndex][0]]; 
            gridDict[key] = cargoId
        });
    });

    return gridDict 
}

/**
 * Populates a grid dictionary with seed keyed by (x, y, layer)
 * @param {Array} layers List of layers containing the SVG.js layer group items
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @returns {Map} Seed dictionary
 */
function populateSparseGridDictionarySeed(layers, minorGridSize) {
    let gridDict = {}
    
    layers.forEach((layer, layerIndex) => {
        layer[2].children().forEach(child => {
            if(child.attr('id') == 'seed'){                
                let bbox = child.rbox(layer[1]);

                let horizontal = true
                if(bbox.width < bbox.height){
                    horizontal = false
                }
                
                let startX = Math.ceil( Math.round(bbox.x) / minorGridSize);
                let startY = Math.ceil( Math.round(bbox.y) / minorGridSize);
                let endX = Math.floor(( Math.round(bbox.x + bbox.width) ) / minorGridSize);
                let endY = Math.floor(( Math.round(bbox.y + bbox.height)) / minorGridSize);

                if(horizontal){
                    startX = startX + 1 //Trimming because of the lower LH overhang
                    endY = endY - 1 //Trimming because of the lower LH overhang

                    // Populate the grid dictionary with the slat ID for the occupied positions
                    for (let x = startX; x <= endX; x++) {
                        for (let y = startY; y <= endY; y++) {
                            let key = gridKey(x, y, layerIndex + 1);
                            gridDict[key] = x - startX + 1;
                        }
                    }
                }
                else{
                    endY = endY - 1 //Trimming because of lower RH overhang
                    endX = endX - 1 //Trimming because of lower RH overhang

                    // Populate the grid dictionary with the slat ID for the occupied positions
                    for (let y = startY; y <= endY; y++) {
                        for (let x = startX; x <= endX; x++) {
                            let key = gridKey(x, y, layerIndex + 1);
                            gridDict[key] = y - startY + 1;
                        }
                    }
                }     
            }
        });
    });

    return gridDict
}

/**
 * Populate a grid dictionary with handle IDs keyed by (x, y, layer)
 * @param {Array} layers List of layers containing the SVG.js layer group items
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @returns {Map} Handle dictionary
 */
function populateSparseGridDictionaryHandles(layers, minorGridSize) {
    let gridDict = {}

    layers.forEach((layer, layerIndex) => {
        layer[0].children().forEach(child => {
            let handleId = child.text()
            let bbox = child.bbox();

            let centerX = Math.round((bbox.x + bbox.width / 2) / minorGridSize);
            let centerY = Math.round((bbox.y + bbox.height/ 2) / minorGridSize);

            // Populate the grid dictionary with the handle ID for the occupied positions
            let key = [centerX, centerY, layerIndex + 1]; 
            gridDict[key] = handleId
        })
    });

    return gridDict 
}

/**
 * Function to save full design into dictionaries
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @returns {Array} Array holding [SeedDict, SlatDict, CargoDict, HandleDict]
 */
export function createGridArray(layerList, minorGridSize) {
    // Initialize the sparse grid dictionary
    let gridDictSeed = {}
    let gridDictSlats = {};
    let gridDictCargo = {}
    let gridDictHandles = {};    

    // Populate the sparse grid dictionary with seed
    gridDictSeed = populateSparseGridDictionarySeed(Array.from(layerList.values()), minorGridSize);

    // Populate the sparse grid dictionary with slat IDs
    gridDictSlats = populateSparseGridDictionarySlats(Array.from(layerList.values()), minorGridSize);

    // Populate the sparse grid dictionary with cargo IDs
    gridDictCargo = populateSparseGridDictionaryCargo(Array.from(layerList.values()), minorGridSize);

    // Populate the sparse grid dictionary with handle IDs
    gridDictHandles = populateSparseGridDictionaryHandles(Array.from(layerList.values()), minorGridSize);

    // You can now use the gridDict as needed
    let gridDict = [gridDictSeed, gridDictSlats, gridDictCargo, gridDictHandles];

    return gridDict
}

/**
 * Function to remove all layers from the crisscross design
 */
function removeAllLayers(){
    const layerRemoveButtons = document.querySelectorAll('.layer-remove-button');
    
    // Click each button
    layerRemoveButtons.forEach(button => {
        button.click(); // Simulate a click on each button
    });
}

/** 
 * Within a slat dictionary, finds a slat with a particular ID. 
 * Then identifies starting coordinates, orientation (horizontal/vertical)
 * @param {Map} slatDict Slat dictionary describing slat IDs by locations (x, y, layer)
 * @param {Number} slatNum ID of slat to be found/oriented
 * @returns {Array} Orientation array [minX, minY, layer, horizontal]
 */
export function findSlatStartOrientation(slatDict, slatNum){
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

/** 
 * Draws slats on canvas as described in a slat dictionary passed to the function
 * @param {Map} slatDict Slat dictionary describing slat IDs by location (x, y, layer)
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param {Number} shownOpacity Opacity at which slats should be drawn when shown - default
 * @returns {number} Slat counter after all slats have been placed
 */
function importSlats(slatDict, layerList, minorGridSize, shownOpacity){

    //Get unique slat numbers
    let slatNums = Object.values(slatDict)
    const uniqueSlatNums = new Set(slatNums);
    const maxSlatNum = Math.max(...uniqueSlatNums); // The ... convert this slat to an array basically

    for (const slatNum of uniqueSlatNums) {
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

        let activeLayerColor = fullLayer[4] //fullLayer[4] store the layer color! '#ff0000'

        placeSlat(placeX, placeY, activeSlatLayer, layerId, minorGridSize, 
                    activeLayerColor, shownOpacity, slatNum, horizontal, layerList)
    }
    return (maxSlatNum + 1)
}

/**
 * Function to place cargo into design as described in a dictionary
 * @param {Map} cargoDict Cargo dictionary with items keyed by ([x,y], layer, orientation)
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param {Number} shownCargoOpacity Opacity at which cargo should be drawn when shown - default.
 * @param {Map} handleOrientations Map of handle orientations by layer
 * @returns {Number} Cargo counter after all cargo is placed
 */
function importCargo(cargoDict, layerList, minorGridSize, shownCargoOpacity, handleOrientations){
    //Now add new cargo:
    let cargoCounter = 1;

    // Iterate through the dictionary
    for (const [key, value] of Object.entries(cargoDict)) {
        
        let keyArray = key.split(',')

        let dictX   = Number(keyArray[0])
        let dictY   = Number(keyArray[1])
        let layerId = keyArray[2]
        let orientation = Number(keyArray[3])

        let cargoId = value

        while(!layerList.has(layerId)){
            const addLayerButton = document.getElementById('add-layer');
            addLayerButton.click();
        }

        let fullLayer = layerList.get(layerId);
        let activeCargoLayer = null

        let top = true;
        if(handleOrientations[layerId][0] == orientation){
            activeCargoLayer = fullLayer[3]
            top = true
        }
        else{
            activeCargoLayer = fullLayer[2]
            top = false
        }

        let placeX = dictX * minorGridSize
        let placeY = dictY * minorGridSize

        let activeLayerColor = fullLayer[4]

        cargoCounter = placeCargo(placeX, placeY, activeCargoLayer, layerId, minorGridSize, 
                                    activeLayerColor, shownCargoOpacity, cargoCounter, cargoId, layerList, top)

    }
    return cargoCounter
}

/** 
 * Draws handles on canvas as described in a handle dictionary passed to the function
 * @param {Map} handleDict Handle dictionary describing handle IDs by locations (x, y, layer)
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 */
export function importHandles(handleDict, layerList, minorGridSize){

    //First, clear old handles!
    layerList.forEach((layer, layerIndex) => {
        const layerElement = layer[0]; 
        layerElement.children().forEach(child => {
            child.remove();
        });
    })

    // Iterate through the dictionary
    for (const [key, value] of Object.entries(handleDict)) {
        
        let keyArray = key.split(',')

        let dictX   = Number(keyArray[0])
        let dictY   = Number(keyArray[1])
        let layerId = keyArray[2]

        let handleId = value.toString()

        let fullLayer = layerList.get(layerId);
        let activeHandleLayer = fullLayer[0]

        let placeX = dictX * minorGridSize
        let placeY = dictY * minorGridSize

        placeHandle(placeX, placeY, activeHandleLayer, minorGridSize, handleId)
    }
}

/**
 * Draws seed on canvas as described in a seed dictionary passed to the function
 * @param {Map} seedDict Seed dictionary describing seed by locations (x, y, layer)
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 */
function importSeed(seedDict, layerList, minorGridSize){

    let seedKeys = Object.keys(seedDict)
    let minX = Infinity
    let minY = Infinity
    let maxX = 0
    let maxY = 0
    let layerId = null

    for (const key of seedKeys){
        let keyArray = key.split(',')

        let dictX   = Number(keyArray[0])
        let dictY   = Number(keyArray[1])
        let layer = keyArray[2]

        if (dictX < minX){
            minX = dictX
        }

        if (dictY < minY){
            minY = dictY
        }

        if (dictX > maxX){
            maxX = dictX
        }

        if (dictY > maxY){
            maxY = dictY
        }

        layerId = layer
    }

    let width = maxX - minX
    let height = maxY - minY
    let horizontal = !(Boolean(width > height))
    console.log("Horizontal? ", horizontal, "With width, height of ", width, height)

    let placeX = minX * minorGridSize
    let placeY = minY * minorGridSize

    while(!layerList.has(layerId)){
        const addLayerButton = document.getElementById('add-layer');
        addLayerButton.click();
    }

    let fullLayer = layerList.get(layerId);
    let activeBottomCargoLayer = fullLayer[2]
    let activeLayerColor = fullLayer[4]

    placeSeed(placeX, placeY, activeBottomCargoLayer, layerId, minorGridSize, 
                activeLayerColor, horizontal, layerList)
}

/** 
 * Function to draw full design on canvas as described in slat, handle, seed, and cargo dictionaries
 * 
 * @param {Map} seedDict Seed dictionary describing seed by location (x, y, layer)
 * @param {Map} slatDict Slat dictionary describing slat IDs by location (x, y, layer)
 * @param {Map} cargoDict Cargo dictionary describing cargo types (ID) by locations ([x, y], layer, orientation)
 * @param {Map} handleDict Handle dictionary describing handles by location (x, y, layer)
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param {number} shownOpacity Opacity at which slats should be drawn when shown - default
 * @param {number} shownCargoOpacity Opacity at which cargo should be drawn when shown - default.
 * @returns {Array} Array of [slatCounter, cargoCounter]
 */
export function importDesign(seedDict, slatDict, cargoDict, handleDict, layerList, minorGridSize, shownOpacity, shownCargoOpacity){

    removeAllLayers()
    
    let slatCounter = importSlats(slatDict, layerList, minorGridSize, shownOpacity)

    if(Object.keys(seedDict).length != 0){
        importSeed(seedDict, layerList, minorGridSize)
    }

    let handleOrientations = getHandleLayerDict(layerList)
    let cargoCounter = importCargo(cargoDict, layerList, minorGridSize, shownCargoOpacity, handleOrientations)

    if(Object.keys(handleDict).length != 0){
        importHandles(handleDict, layerList, minorGridSize)
    }

    return [slatCounter, cargoCounter];
}




















