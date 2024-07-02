import { willVertBeOnLine, willHorzBeOnLine, isCargoOnCargo } from './helper_functions_overlap.js';
import { startDrag } from './helper_functions_dragging.js';
import { getInventoryItemById } from './inventory.js';




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
            //I'M EDITING HERE
            tmpLine.on('pointerdown', function(event) {
                startDrag(event, layerList, minorGridSize);
            });
            //tmpLine.on('pointerdown', startDrag)

            slatCounter += 1;
        }
    }
    else if(horizontal){
        if(!willHorzBeOnLine(roundedX, roundedY, activeSlatLayer, minorGridSize, 32)) {
            let defaultColor = activeLayerColor 
            let tmpLine = activeSlatLayer.line(roundedX - 0.5 * minorGridSize, roundedY, roundedX + 31.5 * minorGridSize, roundedY )
                                        .stroke({ width: 3, color:defaultColor, opacity: shownOpacity });
            //tmpLine.attr('id',activeLayerId+'_number:' + slatCounter)

            tmpLine.attr('id', slatCounter)
            tmpLine.attr('layer', activeLayerId)

            tmpLine.attr('class',"line")
            tmpLine.attr({ 'pointer-events': 'stroke' })
            tmpLine.attr('data-default-color', defaultColor);
            tmpLine.attr('data-horizontal',horizontal)

            //Adding draggability:
            //tmpLine.on('pointerdown', startDrag)
            tmpLine.on('pointerdown', function(event) {
                startDrag(event, layerList, minorGridSize);
            });

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
export function placeCargo(roundedX, roundedY, activeCargoLayer, activeLayerId, minorGridSize, activeLayerColor, shownCargoOpacity, cargoCounter, selectedCargoId, layerList) {
    
    
    const cargoItem = getInventoryItemById(selectedCargoId);
    let defaultColor = activeLayerColor; 

    if(cargoItem){
        if(!isCargoOnCargo(roundedX, roundedY, activeCargoLayer)){
            const circleRadius = minorGridSize * 0.375; // Diameter is 75% of minorGridSize
            let tmpCircle = activeCargoLayer.circle(2 * circleRadius) // SVG.js uses diameter, not radius
                                            .attr({ cx: roundedX, cy: roundedY })
                                            .fill(cargoItem.color) // You can set the fill color here
                                            .stroke(activeLayerColor) // You can set the stroke color here
                                            .opacity(shownCargoOpacity);//shownOpacity * 1.25);
            tmpCircle.attr('class',"cargo")
            tmpCircle.attr('data-cargo-component', 'circle')
            tmpCircle.attr('data-default-color', defaultColor)
            tmpCircle.attr('pointer-events', 'none');
    
            // Adding text (acronym) to the cargo
            let text = activeCargoLayer.text(cargoItem.acronym)
                .attr({ x: roundedX, y: roundedY - circleRadius, 'dominant-baseline': 'middle', 'text-anchor': 'middle' })
                .attr({'stroke-width': circleRadius/20})
                .font({ size: minorGridSize * 0.4, family: 'Arial', weight: 'bold' , stroke: '#000000'})
                .fill('#FFFFFF'); // White text
            text.attr('pointer-events', 'none');
            text.attr('data-cargo-component', 'text')
            
    
            // Function to adjust text size
            function adjustTextSize() {
                let fontSize = circleRadius;
                text.font({ size: fontSize });
                
                while (text.length() > circleRadius * 1.8) {
                    fontSize *= 0.9;
                    text.font({ size: fontSize });
                }
            }
    
            adjustTextSize();
    
            // Group the circle and text
            let group = activeCargoLayer.group()
            group.add(tmpCircle).add(text);
            //group.on('pointerdown', startDrag);
            group.on('pointerdown', function(event) {
                startDrag(event, layerList, minorGridSize);
            });
    
            // Set pointer-events attribute to the group
            group.attr('pointer-events', 'bounding-box');
            group.attr('id'  ,  cargoCounter    )
            group.attr('type',  selectedCargoId )
            group.attr('layer', activeLayerId   )

    
            cargoCounter += 1;
        }

    }
    return cargoCounter;
}