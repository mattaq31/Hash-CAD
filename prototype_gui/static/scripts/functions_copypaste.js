import { placeCargo } from "./functions_drawing.js";

/**
 * Function to copy all selected cargo on a particular layer into a dictionary
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Boolean} top True if cargo goes on top layer of slats. False if cargo goes on bottom layer of slats
 * @param {Number} activeLayerId ID of the selected layer
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles
 * @returns {Map} Dictionary encoding copied cargo items by position. Trimmed so minimum X = minimum Y = 0
 */
export function copyCargo(layerList, top, activeLayerId, minorGridSize){
    const fullLayer = layerList.get(activeLayerId)

    //Get proper cargo layer
    let layerToCopyFrom = null;
    if(top){
        layerToCopyFrom = fullLayer[3]
    }
    else{
        layerToCopyFrom = fullLayer[2]
    }

    //Collect selected cargos into a dictionary
    let selectedCargoDict = {}
    let minX = Infinity
    let minY = Infinity
    layerToCopyFrom.children().forEach(child => {
        if(child.hasClass("selected")){
            let cargoId = child.attr('type');
            let bbox = child.bbox();
            
            let centerX = Math.round((bbox.x + bbox.width / 2) / minorGridSize);
            let centerY = Math.round((bbox.y + bbox.height/ 2) / minorGridSize);

            if(centerX < minX){ minX = centerX }
            if(centerY < minY){ minY = centerY }

            // Populate the grid dictionary with the cargo ID for the occupied positions
            let key = [centerX, centerY]; 
            selectedCargoDict[key] = cargoId
        }
    });

    //Shift keys so that top LH cargo has coordinates (0, 0)
    let shiftedCargoDict = {}
    for (const [key, cargoId] of Object.entries(selectedCargoDict)) {
        let keyArray = key.split(',')
        let shiftedX = Number(keyArray[0]) - minX
        let shiftedY = Number(keyArray[1]) - minY
        let shiftedKey = [shiftedX, shiftedY]
        shiftedCargoDict[shiftedKey] = cargoId
    }
    return shiftedCargoDict
}

/**
 * Function to show shadow version of the copied cargo before pasting, for placement purposes
 * @param {Map} cargoDict Dictionary encoding copied cargo items by position. Trimmed so minimum X = minimum Y = 0
 * @param {Number} roundedX X-coordinate of top LH corner where copied cargo should be placed
 * @param {Number} roundedY Y-coordinate of top LH corner where copied cargo should be placed
 * @param {SVG.Doc} fullDrawing Full SVG document for the canvas
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles
 */
export function showCopiedCargo(cargoDict, roundedX, roundedY, fullDrawing, minorGridSize){
    let radius = minorGridSize * 0.2
    let defaultColor = '#808080'; //Grey

    // Remove any existing shadow cargo with the id 'shadow-copied-cargo'
    let oldShadowCargo = document.getElementById('shadow-copied-cargo')
    if(oldShadowCargo){
        oldShadowCargo.remove()
    }

    // Create new group to hold shadow coppied cargo
    let group = fullDrawing.group()

    for (const [key, cargoId] of Object.entries(cargoDict)) {
        let keyArray = key.split(',')
        let shiftedX = Number(keyArray[0]) * minorGridSize + roundedX
        let shiftedY = Number(keyArray[1]) * minorGridSize + roundedY

        let tmpShape = fullDrawing.circle(2 * radius) // SVG.js uses diameter, not radius
                                  .attr({ cx: shiftedX, cy: shiftedY })
                                  .fill(defaultColor) 
                                  .stroke(defaultColor) 
                                  .opacity(0.33);
        group.add(tmpShape)   
    }

    group.attr('id','shadow-copied-cargo')
    group.attr({ 'pointer-events': 'none' })
}

/**
 * Function to paste copied cargo into design
 * @param {Map} cargoDict Dictionary encoding copied cargo items by position. Trimmed so minimum X = minimum Y = 0
 * @param {Number} startingX X-coordinate of top LH corner where copied cargo should be placed
 * @param {Number} startingY Y-coordinate of top LH corner where copied cargo should be placed
 * @param {SVG.G} activeCargoLayer Selected layer of the SVG canvas/crisccross design
 * @param {Number} activeLayerId ID of the selected layer
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles
 * @param {String} activeLayerColor Color of the active layer
 * @param {Number} shownCargoOpacity Default opacity of a shown element. Between 0 & 1 
 * @param {Number} cargoCounter Number of cargo placed so far. Serves as a unique ID for each cargo
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Boolean} top True if cargo goes on top layer of slats. False if cargo goes on bottom layer of slats
 * @returns {Number} cargoCounter - number of cargo placed so far, after pasting
 */
export function pasteCargo(cargoDict, startingX, startingY, activeCargoLayer, activeLayerId, minorGridSize, activeLayerColor, shownCargoOpacity, cargoCounter, layerList, top){
    
    //iterate through cargo, placing them!
    for (const [key, cargoId] of Object.entries(cargoDict)) {
        let keyArray = key.split(',')
        let shiftedX = Number(keyArray[0]) * minorGridSize + startingX
        let shiftedY = Number(keyArray[1]) * minorGridSize + startingY

        cargoCounter = placeCargo(shiftedX, shiftedY, 
                                  activeCargoLayer, activeLayerId, 
                                  minorGridSize, activeLayerColor, 
                                  shownCargoOpacity, cargoCounter, 
                                  cargoId, layerList, top)
    }

    return cargoCounter
}