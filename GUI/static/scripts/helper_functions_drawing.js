import { willVertBeOnLine, willHorzBeOnLine, isCargoOnCargo, wasSeedOnCargo } from './helper_functions_overlap.js';
import { startDrag } from './helper_functions_dragging.js';
import { getInventoryItemById } from './cargo.js';
import { place3DSlat, place3DCargo } from './helper_functions_3D.js';



/** Function to draw a slat
 * 
 * @param roundedX Starting (top-left) X-coordinate of slat to be drawn
 * @param roundedY Starting (top-left) Y-coordinate of slat to be drawn
 * @param activeSlatLayer Selected layer of the SVG canvas/crisscross design
 * @param activeLayerId ID of the selected layer
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param activeLayerColor Color of the active layer
 * @param shownOpacity Default opacity of a shown element
 * @param slatCounter Number of slats placed so far. Serves as a unique ID for each slat
 * @param horizontal True if slat should be placed horizontally. False if slat should be placed vertically
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @returns {*}
 */
export function placeSlat(roundedX, roundedY, activeSlatLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, slatCounter, horizontal, layerList) {
    if(!horizontal){
        if(!willVertBeOnLine(roundedX, roundedY, activeSlatLayer, minorGridSize, 32)) {
            let defaultColor = activeLayerColor; 
            let tmpLine = activeSlatLayer.line(roundedX, roundedY - 0.5 * minorGridSize, roundedX, roundedY + 31.5 * minorGridSize)
                                        .stroke({ width: 3, color:defaultColor, opacity: shownOpacity });
            //tmpLine.attr('id',activeLayerId + '_number:' + slatCounter)

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
            

            slatCounter += 1;
        }
    }
    else if(horizontal){
        if(!willHorzBeOnLine(roundedX, roundedY, activeSlatLayer, minorGridSize, 32)) {
            let defaultColor = activeLayerColor 
            let tmpLine = activeSlatLayer.line(roundedX - 0.5 * minorGridSize, roundedY, roundedX + 31.5 * minorGridSize, roundedY )
                                        .stroke({ width: 3, color:defaultColor, opacity: shownOpacity });

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
            

            slatCounter += 1;
        }
    }

    

    return slatCounter;
}

/** Function to draw cargo item
 * 
 * @param roundedX X-coordinate of cargo to be drawn
 * @param roundedY Y-coordinate of cargo to be drawn
 * @param activeCargoLayer Selected layer of the SVG canvas/crisccross design
 * @param activeLayerId ID of the selected layer
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param activeLayerColor Color of the active layer
 * @param shownCargoOpacity Default opacity of a shown element
 * @param cargoCounter Number of cargo placed so far. Serves as a unique ID for each cargo
 * @param selectedCargoId ID of cargo to be placed. Serves as an identifier of cargo type
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @returns {*}
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
                                           .fill(cargoItem.color) // You can set the fill color here
                                           .stroke(activeLayerColor) // You can set the stroke color here
                                           .opacity(shownCargoOpacity);//shownOpacity * 1.25);
            }
            else {
                tmpShape = activeCargoLayer.rect(2 * radius, 2 * radius) // SVG.js uses diameter, not radius
                                           .move(roundedX - radius, roundedY - radius)
                                           .fill(cargoItem.color) // You can set the fill color here
                                           .stroke(activeLayerColor) // You can set the stroke color here
                                           .opacity(shownCargoOpacity);//shownOpacity * 1.25);
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
            
    
            // Function to adjust text size
            function adjustTextSize() {
                let fontSize = radius;
                text.font({ size: fontSize });
                
                while (text.length() > radius * 1.8) {
                    fontSize *= 0.9;
                    text.font({ size: fontSize });
                    text.attr({ x: roundedX, y: roundedY - 1.25*fontSize, 'dominant-baseline': 'middle', 'text-anchor': 'middle' })
                }
            }
    
            adjustTextSize();
    
            // Group the circle and text
            let group = activeCargoLayer.group()
            //group.add(tmpCircle).add(text);
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
            
            cargoCounter += 1;
        }

        



    }
    return cargoCounter;
}





export function placeHandle(roundedX, roundedY, activeHandleLayer, minorGridSize, handleId, layerList) {
    let text = activeHandleLayer.text(handleId)
        .attr({ x: roundedX, y: roundedY - 0.8*minorGridSize, 'dominant-baseline': 'middle', 'text-anchor': 'middle' })
        .font({ size: minorGridSize * 0.66, family: 'Arial' , weight: 'lighter', stroke: '#000000'})
    
    //text.attr('pointer-events', 'none');

}





export function placeSeed(roundedX, roundedY, cargoLayer, activeLayerId, minorGridSize, activeLayerColor, horizontal, layerList) {
    
    
    const cols = 16;
    const rows = 5;
    const step = minorGridSize;
    const width = step * cols;
    const height = step * rows;

    //Only draw if no other seeds:
    if(document.querySelectorAll('.seed').length == 0){
        let pathString = `M ${roundedX - step/2} ${roundedY} `;
    
        //Start with horizontal lines
        for (let i = 0; i < rows; i++) {
            if (i === rows-1){ //Last line
                if (i % 2 === 0) {
                    // Forward direction
                    pathString += `l ${width-step/2} 0`;
                    } else {
                    // Backward direction
                    pathString += `l ${-width+step/2} 0`;
                    }
            }
            else{ //All other horizontal lines
                if (i % 2 === 0) {
                    // Forward direction
                    pathString += `l ${width} 0  l 0 ${step}`;
                    } else {
                    // Backward direction
                    pathString += `l ${-width} 0 l 0 ${step}`;
                    }
            }
        }

        // Now start vertical snaking
        for (let j = 0; j < cols; j++) {
            if (j === 0){
                pathString += ` l 0 ${-height + step/2} l ${-step} 0`;
            }
            else if(j === cols - 1){
                if (j % 2 === 0) {
                    // Up direction
                    pathString += ` l 0 ${-height} l ${-step} ${step}`;
                    } else {
                    // Down direction
                    pathString += ` l 0 ${height} l ${-step} ${step}`;
                    }
            }
            else if (j % 2 === 0) {
            // Up direction
            pathString += ` l 0 ${-height} l ${-step} 0`;
            } else {
            // Down direction
            pathString += ` l 0 ${height} l ${-step} 0`;
            }}

        // Draw the path
        let tmpPath = cargoLayer.path(pathString).stroke({ width: 3, color: activeLayerColor }).fill('none');
        
        tmpPath.attr('id', "seed")
        tmpPath.attr('layer', activeLayerId)
        tmpPath.attr('class',"seed")
        tmpPath.attr({'pointer-events': 'stroke' })

        if(horizontal){
            const bbox = tmpPath.bbox();

            // Rotate the path 90 degrees around its top-left corner
            tmpPath.rotate(-90, bbox.x + bbox.width + minorGridSize/2, bbox.y - minorGridSize/2);

            // Translate the path to its original top-left corner
            tmpPath.translate(-bbox.width - minorGridSize/2, 0);
        }

        tmpPath.on('pointerdown', function(event) {
            startDrag(event, layerList, minorGridSize);
        });

        if(wasSeedOnCargo(cargoLayer)){
            tmpPath.remove()
        }

    }


    
}







export function showSlat(roundedX, roundedY, fullDrawing, minorGridSize, horizontal, numSlats=1) {
    let defaultColor = '#808080'; 
    let tmpLine = null;
    let group = fullDrawing.group()

    // Remove any existing lines with the id 'cursor-slat'
    let cursorSlat = document.getElementById('cursor-slat')
    
    if(cursorSlat){
        cursorSlat.remove()
    }



    let drawModeSelector = document.getElementById('palette-type-selector');
    let drawSlatCargoHandleMode = drawModeSelector.value;

    if(drawSlatCargoHandleMode == 0){
        for (let i = 0; i < numSlats; i++) {
            let xIterator = minorGridSize * i * (!horizontal)
            let yIterator = minorGridSize * i * horizontal
    
            if(horizontal){
                tmpLine = fullDrawing.line(roundedX - 0.5 * minorGridSize + xIterator, 
                                           roundedY + yIterator, 
                                           roundedX + 31.5 * minorGridSize + xIterator, 
                                           roundedY + yIterator)
                                     .stroke({ width: 3, color:defaultColor, opacity: 0.33 });       
            }
            else{
                tmpLine = fullDrawing.line(roundedX + xIterator, 
                                           roundedY - 0.5 * minorGridSize + yIterator, 
                                           roundedX + xIterator, 
                                           roundedY + 31.5 * minorGridSize + yIterator)
                                     .stroke({ width: 3, color:defaultColor, opacity: 0.33 });
            }
    
            group.add(tmpLine)
    
        }
    
        group.attr('id','cursor-slat')
        group.attr({ 'pointer-events': 'none' })
        
    }
    else{
        // Remove any existing lines with the id 'cursor-slat'
        let cursorSlat = document.getElementById('cursor-slat')
        
        if(cursorSlat){
            cursorSlat.remove()
        }
    }





    

    
}