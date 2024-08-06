import { willVertBeOnLine, willHorzBeOnLine, isCargoOnCargo, wasSeedOnCargo } from './functions_overlap.js';
import { startDrag } from './functions_dragging.js';
import { getInventoryItemById } from './functions_inventory.js';
import { place3DSlat, place3DCargo, place3DSeed, delete3DElement } from './functions_3D.js';
import { drawDefaultSeed, drawRotatedSeed } from './functions_seed_path.js';

var historyArray = []

var width = document.getElementById('svg-container').getBoundingClientRect().width
var height = document.getElementById('svg-container').getBoundingClientRect().height
var fullDrawing = SVG().addTo('#svg-container').size(width, height)

/**
 * Function to return main SVG drawing, within which everything is placed
 * @returns {SVG} SVG drawing
 */
export function getFullDrawing(){
    return fullDrawing
}

/** 
 * Function to draw a slat
 * @param {Number} roundedX Starting (top-left) X-coordinate of slat to be drawn
 * @param {Number} roundedY Starting (top-left) Y-coordinate of slat to be drawn
 * @param {SVG.G} activeSlatLayer Selected layer of the SVG canvas/crisscross design
 * @param {Number} activeLayerId ID of the selected layer
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param {String} activeLayerColor Color of the active layer
 * @param {Number} shownOpacity Default opacity of a shown element. Between 0 & 1
 * @param {Number} slatCounter Number of slats placed so far. Serves as a unique ID for each slat
 * @param {Boolean} horizontal True if slat should be placed horizontally. False if slat should be placed vertically
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @returns {Boolean} Number of slats placed so far, after the slat has been drawn
 */
export function placeSlat(roundedX, roundedY, activeSlatLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, slatCounter, horizontal, layerList) {
    if(!horizontal){
        if(!willVertBeOnLine(roundedX, roundedY, activeSlatLayer, minorGridSize, 32)) {
            let defaultColor = activeLayerColor; 
            let tmpLine = activeSlatLayer.line(roundedX, roundedY - 0.5 * minorGridSize, roundedX, roundedY + 31.5 * minorGridSize)
                                        .stroke({ width: 4, color:defaultColor, opacity: shownOpacity });

            tmpLine.attr('id', slatCounter)
            tmpLine.attr('layer', activeLayerId)

            tmpLine.attr('class',"line")
            tmpLine.attr({ 'pointer-events': 'stroke' })
            tmpLine.attr('data-default-color', defaultColor);
            tmpLine.attr('data-horizontal', horizontal)

            //Adding draggability:
            tmpLine.on('pointerdown', function(event) {
                startDrag(event, layerList, minorGridSize);
            });

            let xPos3D = (roundedX)/minorGridSize
            let yPos3D = (roundedY)/minorGridSize
            place3DSlat(xPos3D, yPos3D, activeLayerId, slatCounter, activeLayerColor, horizontal)

            historyArray.push(tmpLine)
            
            slatCounter += 1;
        }
    }
    else if(horizontal){
        if(!willHorzBeOnLine(roundedX, roundedY, activeSlatLayer, minorGridSize, 32)) {
            let defaultColor = activeLayerColor 
            let tmpLine = activeSlatLayer.line(roundedX - 0.5 * minorGridSize, roundedY, roundedX + 31.5 * minorGridSize, roundedY )
                                        .stroke({ width: 4, color:defaultColor, opacity: shownOpacity });

            tmpLine.attr('id', slatCounter)
            tmpLine.attr('layer', activeLayerId)

            tmpLine.attr('class',"line")
            tmpLine.attr({ 'pointer-events': 'stroke' })
            tmpLine.attr('data-default-color', defaultColor);
            tmpLine.attr('data-horizontal',horizontal)

            //Adding draggability:
            tmpLine.on('pointerdown', function(event) {
                startDrag(event, layerList, minorGridSize);
            });

            let xPos3D = (roundedX)/minorGridSize
            let yPos3D = (roundedY)/minorGridSize
            place3DSlat(xPos3D, yPos3D, activeLayerId, slatCounter, activeLayerColor, horizontal)

            historyArray.push(tmpLine)

            slatCounter += 1;
        }
    }

    return slatCounter;
}

/** 
 * Function to draw cargo item
 * @param {Number} roundedX X-coordinate of cargo to be drawn
 * @param {Number} roundedY Y-coordinate of cargo to be drawn
 * @param {SVG.G} activeCargoLayer Selected layer of the SVG canvas/crisccross design
 * @param {Number} activeLayerId ID of the selected layer
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param {String} activeLayerColor Color of the active layer
 * @param {Number} shownCargoOpacity Default opacity of a shown element. Between 0 & 1
 * @param {Number} cargoCounter Number of cargo placed so far. Serves as a unique ID for each cargo
 * @param {Number} selectedCargoId ID of cargo to be placed. Serves as an identifier of cargo type
 * @param {Map} layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Boolean} top True if cargo goes on top layer of slats. False if cargo goes on bottom layer of slats
 * @returns {Boolean} Number of cargo placed so far, after the cargo has been drawn
 */
export function placeCargo(roundedX, roundedY, activeCargoLayer, activeLayerId, minorGridSize, activeLayerColor, shownCargoOpacity, cargoCounter, selectedCargoId, layerList, top=true) {
    
    const cargoItem = getInventoryItemById(selectedCargoId);
    let defaultColor = activeLayerColor; 

    if(cargoItem){
        if(!isCargoOnCargo(roundedX, roundedY, activeCargoLayer)){
            const radius = minorGridSize * 0.375
            let tmpShape = null

            if(top){
                tmpShape = activeCargoLayer.circle(2 * radius) // SVG.js uses diameter, not radius
                                           .attr({ cx: roundedX, cy: roundedY })
                                           .fill(cargoItem.color) 
                                           .stroke(activeLayerColor) 
                                           .opacity(shownCargoOpacity);
            }
            else {
                tmpShape = activeCargoLayer.rect(2 * radius, 2 * radius) // SVG.js uses diameter, not radius
                                           .move(roundedX - radius, roundedY - radius)
                                           .fill(cargoItem.color) 
                                           .stroke(activeLayerColor) 
                                           .opacity(shownCargoOpacity);
            }

            tmpShape.attr('class',"cargo")
            tmpShape.attr('data-cargo-component', 'shape')
            tmpShape.attr('data-default-color', defaultColor)
            tmpShape.attr('pointer-events', 'none');
    
            // Adding text (tag) to the cargo
            let text = activeCargoLayer.text(cargoItem.tag)
                .attr({ x: roundedX, y: roundedY - radius, 'dominant-baseline': 'middle', 'text-anchor': 'middle' })
                .attr({'stroke-width': radius/20})
                .font({ size: minorGridSize * 0.4, family: 'Arial', weight: 'bold' , stroke: '#000000'})
                .fill('#FFFFFF'); // White text
            text.attr('pointer-events', 'none');
            text.attr('data-cargo-component', 'text')
            
            // Adjust text size
            let fontSize = radius;
            text.font({ size: fontSize });
            
            while (text.length() > radius * 1.8) {
                fontSize *= 0.9;
                text.font({ size: fontSize });
                text.attr({ x: roundedX, y: roundedY - 1.25*fontSize, 'dominant-baseline': 'middle', 'text-anchor': 'middle' })
            }
        
            // Group the circle and text
            let group = activeCargoLayer.group()
            group.add(tmpShape).add(text);
            group.on('pointerdown', function(event) {
                startDrag(event, layerList, minorGridSize);
            });
    
            // Set pointer-events attribute to the group
            group.attr('pointer-events', 'bounding-box');
            group.attr('id'  ,  cargoCounter    )
            group.attr('type',  selectedCargoId )
            group.attr('plate', cargoItem.plate )
            group.attr('layer', activeLayerId   )
            group.attr('class', "cargo")

            place3DCargo(roundedX / minorGridSize, roundedY / minorGridSize, activeLayerId, selectedCargoId, cargoCounter, top, 0.5)

            historyArray.push(group)
            
            cargoCounter += 1;
        }
    }
    return cargoCounter;
}

/** 
 * Function to place handle
 * @param {Number} roundedX X-coordinate of the handle to be drawn
 * @param {Number} roundedY Y-coordinate of the handle to be drawn
 * @param {SVG.G} activeHandleLayer Selected layer of the SVG canvas/crisscross design
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles
 * @param {String} handleId ID of handle to be placed. 
 */
export function placeHandle(roundedX, roundedY, activeHandleLayer, minorGridSize, handleId) {
    let text = activeHandleLayer.text(handleId)
        .attr({ x: roundedX, y: roundedY - 0.8*minorGridSize, 'dominant-baseline': 'middle', 'text-anchor': 'middle' })
        .font({ size: minorGridSize * 0.66, family: 'Arial' , weight: 'lighter', stroke: '#000000'})
}

/** 
 * Function to place seed
 * @param {Number} roundedX X-coordinate of the seed to be drawn (top LH corner)
 * @param {Number} roundedY Y-coordinate of the seed to be drawn (top LH corner)
 * @param {SVG.G} cargoLayer Selected layer of the SVG canvas/crisscross design. Should be a bottom cargo layer
 * @param {Number} activeLayerId ID of the selected layer
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles
 * @param {String} activeLayerColor Color of the active layer
 * @param {Boolean} rotated True if the the seed should be placed vertically. False if horizontally. 
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 */
export function placeSeed(roundedX, roundedY, cargoLayer, activeLayerId, minorGridSize, activeLayerColor, rotated, layerList) {
    const cols = 16;
    const rows = 5;

    //Only draw if no other seeds:
    if(document.querySelectorAll('.seed').length == 0){
        let pathString = ``
        
        if(rotated){
            pathString = drawRotatedSeed(roundedX, roundedY, minorGridSize, rows, cols)
        }
        else{
            pathString = drawDefaultSeed(roundedX, roundedY, minorGridSize, rows, cols)
        }
    
        // Draw the path
        let tmpPath = cargoLayer.path(pathString).stroke({ width: 3, color: activeLayerColor }).fill('none');
        
        tmpPath.attr('id', "seed")
        tmpPath.attr('layer', activeLayerId)
        tmpPath.attr('class',"seed")
        tmpPath.attr({'pointer-events': 'stroke' })
        tmpPath.attr({'data-horizontal': Boolean(rotated)})

        tmpPath.on('pointerdown', function(event) {
            startDrag(event, layerList, minorGridSize);
        });

        place3DSeed(roundedX / minorGridSize, roundedY / minorGridSize, activeLayerId, activeLayerColor, rotated)

        historyArray.push(tmpPath)

        if(wasSeedOnCargo(cargoLayer)){
            tmpPath.remove()
            historyArray.pop()
        }
    }
}

/** 
 * Function to show shaddow slat under cursor
 * @param {Number} roundedX X-coordinate of the shaddow slat to be drawn (top LH point)
 * @param {Number} roundedY Y-coordinate of the shaddow slat to be drawn (top LH point)
 * @param {SVG.Doc} fullDrawing Full SVG document for the canvas
 * @param {Number} minorGridSize The snapping grid size. Corresponds to the distance between two handles
 * @param {Boolean} horizontal True if slat should be placed horizontally. False if slat should be placed vertically
 * @param {Number} numSlats Number of slats to show at once
 */
export function showSlat(roundedX, roundedY, fullDrawing, minorGridSize, horizontal, numSlats=1) {
    let defaultColor = '#808080'; //Grey
    let tmpLine = null;
    let group = fullDrawing.group()

    // Remove any existing lines with the id 'cursor-slat'
    let cursorSlat = document.getElementById('cursor-slat')
    if(cursorSlat){
        cursorSlat.remove()
    }

    let drawModeSelector = document.getElementById('palette-type-selector');
    let drawSlatCargoHandleMode = drawModeSelector.value;

    //Only show slat if we are in slat mode!
    if(drawSlatCargoHandleMode == 0){
        for (let i = 0; i < numSlats; i++) {
            let xIterator = minorGridSize * i * (!horizontal)
            let yIterator = minorGridSize * i * horizontal
    
            if(horizontal){
                tmpLine = fullDrawing.line(roundedX - 0.5 * minorGridSize + xIterator, 
                                           roundedY + yIterator, 
                                           roundedX + 31.5 * minorGridSize + xIterator, 
                                           roundedY + yIterator)
                                     .stroke({ width: 4, color:defaultColor, opacity: 0.33 });       
            }
            else{
                tmpLine = fullDrawing.line(roundedX + xIterator, 
                                           roundedY - 0.5 * minorGridSize + yIterator, 
                                           roundedX + xIterator, 
                                           roundedY + 31.5 * minorGridSize + yIterator)
                                     .stroke({ width: 4, color:defaultColor, opacity: 0.33 });
            }

            group.add(tmpLine)
        }
    
        group.attr('id','cursor-slat')
        group.attr({ 'pointer-events': 'none' })
    }
}


/**
 * Function to remove last placed item
 */
export function undo(){
    let oldElement = historyArray.pop()
    delete3DElement(oldElement)
    oldElement.remove()
}






//TODO: WiP
/** 
 */
export function placeHandleMatcher(roundedX, roundedY, activeHandleLayer, activeLayerId, minorGridSize, activeLayerColor, shownHandleOpacity, handleMatchCounter, matchGroupNumber, layerList) {
    
    let defaultColor = '#808080'; 

    if(/*!isMatcherOnMatcher(roundedX, roundedY, activeCargoLayer)*/ true){
        const width = minorGridSize * 0.85

        let tmpSquare = activeHandleLayer.rect(width, width) // SVG.js uses diameter, not radius
                                     .move(roundedX - width/2, roundedY - width/2)
                                     .fill(defaultColor) 
                                     .stroke(activeLayerColor) 
                                     .opacity(shownHandleOpacity);
        

        tmpSquare.attr('data-match-component', 'shape')
        tmpSquare.attr('data-default-color', defaultColor)
        tmpSquare.attr('pointer-events', 'none');

        // Adding text (tag) to the cargo
        let text = activeHandleLayer.text(matchGroupNumber)
            .attr({ x: roundedX, y: roundedY - width/2, 'dominant-baseline': 'middle', 'text-anchor': 'middle' })
            .attr({'stroke-width': width/40})
            .font({ size: minorGridSize * 0.4, family: 'Arial', weight: 'bold' , stroke: '#000000'})
            .fill('#FFFFFF'); // White text
        text.attr('pointer-events', 'none');
        text.attr('data-match-component', 'text')
        
        // Adjust text size
        let fontSize = width/2;
        text.font({ size: fontSize });
        
        while (text.length() > width * 0.9) {
            fontSize *= 0.9;
            text.font({ size: fontSize });
            text.attr({ x: roundedX, y: roundedY - 1.25*fontSize, 'dominant-baseline': 'middle', 'text-anchor': 'middle' })
        }
    
        // Group the circle and text
        let group = activeHandleLayer.group()
        group.add(tmpSquare).add(text);
        group.on('pointerdown', function(event) {
            startDrag(event, layerList, minorGridSize);
        });

        // Set pointer-events attribute to the group
        group.attr('pointer-events', 'bounding-box');
        group.attr('id'  ,  handleMatchCounter    )
        group.attr('type',  matchGroupNumber )
        group.attr('layer', activeLayerId   )
        group.attr('class', "handle-matcher")
        
        handleMatchCounter += 1;
    }
    return handleMatchCounter;
}