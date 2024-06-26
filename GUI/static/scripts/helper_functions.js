let dragOffset = { x: 0, y: 0 };    //Offset between mouse position and item position
let handleDrag = null;              //Function to call when a drag event is happening


///////////////////////////////
//       Grid Drawing        //
///////////////////////////////
//Draw grid:
export function drawGrid(gridGroup, width, height, style, majorSize, minorSize) {
    //Grid style: 
        //0 corresponds to no grid
        //1 corresponds to normal grid
        //2 corresponds to dot grid
    
    //First reset grid:
    gridGroup.clear()

    //Now draw the grid itself:
    if(style != 0){
        // Draw vertical lines
        //Minor
        for (var x = 0; x < width; x += minorSize) {
            let tmpLine = gridGroup.line(x, 0, x, height).stroke({ width: 0.5, color:'#000'})
            if(style==2){
                tmpLine.stroke({dasharray:`${minorSize*0.1},${minorSize*0.9}`, dashoffset:`${minorSize*0.05}`})
            }
        }

        //Major
        for (var x = 0; x < width; x += majorSize) {
            let tmpLine = gridGroup.line(x, 0, x, height).stroke({ width: 1, color:'#000' })
            if(style==2){
                tmpLine.stroke({dasharray:`${majorSize*0.05},${majorSize*0.95}`, dashoffset:`${majorSize*0.025}`})
            }
        }

        // Draw horizontal lines
        //Minor
        for (var y = 0; y < height; y += minorSize) {
            let tmpLine = gridGroup.line(0, y, width, y).stroke({ width: 0.5, color:'#000'})
            if(style==2){
                tmpLine.stroke({dasharray:`${minorSize*0.1},${minorSize*0.9}`, dashoffset:`${minorSize*0.05}`})
            }
        }

        //Major
        for (var y = 0; y < height; y += majorSize) {
            let tmpLine = gridGroup.line(0, y, width, y).stroke({ width: 1, color:'#000' })
            if(style==2){
                tmpLine.stroke({dasharray:`${majorSize*0.05},${majorSize*0.95}`, dashoffset:`${majorSize*0.025}`})
            }
        }
    }
    
    
    return gridGroup;
  }


///////////////////////////////
//  Slat Overlap Checkers    //
///////////////////////////////

// Check if a point is on any existing line
export function isPointOnLine(Layer, x, y, selectedLine = false) {
    const lines = Layer.find('.line');
    return lines.some(line => {
      
      //Check if overlapping with any lines in general
        const bbox = line.bbox();
        let onOther = (x >= bbox.x && x <= bbox.x2 && y >= bbox.y && y <= bbox.y2)
      
      //Check if overlapping with self (but only if a self is given!)
        let selfBbox = null;
        let onItself = false
        if(selectedLine){
            selfBbox = selectedLine.bbox();
            onItself = (x >= selfBbox.x && x <= selfBbox.x2 && y >= selfBbox.y && y <= selfBbox.y2)
        }
      
      return (
        onOther && (!onItself)
      );
    });
  }


export function isLineOnLine(startX, startY, layer, GridSize, selectedLine) {
    const x1 = selectedLine.attr('x1');
    const y1 = selectedLine.attr('y1');
    const x2 = selectedLine.attr('x2');
    const y2 = selectedLine.attr('y2');

    //console.log("selected line is: "+x1 + ","+y1+" to "+x2+","+y2)

    let dX = x2-x1;
    let dY = y2-y1

    const lineLength = Math.sqrt(dX * dX + dY * dY)
    const numPoints = Math.floor(lineLength/GridSize)

    let overlap = false

    for (let i = 0; i<= numPoints; i++) {
        const ratio = i / numPoints;
        let x = startX + ratio * dX
        let y = startY + ratio * dY
        overlap = overlap || isPointOnLine(layer, x, y, selectedLine)
    }

    return overlap


}


export function willVertBeOnLine(startX, startY, layer, gridSize, length=32){
    let overlap = false
    for (let i = 0; i<= length; i++) {
        let x = startX 
        let y = startY + i*gridSize
        overlap = overlap || isPointOnLine(layer, x, y)
    }
    return overlap
}

export function willHorzBeOnLine(startX, startY, layer, gridSize, length=32){
    let overlap = false
    for (let i = 0; i<= length; i++) {
        let x = startX + i*gridSize
        let y = startY 
        overlap = overlap || isPointOnLine(layer, x, y)
    }
    return overlap
}



///////////////////////////////
//  Cargo Overlap Checkers   //
///////////////////////////////

export function isCargoOnCargo(x, y, layer, selectedPoint = false){
    const cargos = layer.find('.cargo');
    return cargos.some(cargo => {
      
        //Check if overlapping with any lines in general
        const bbox = cargo.bbox();
        let onOther = (x >= bbox.x && x <= bbox.x2 && y >= bbox.y && y <= bbox.y2)

        //Check if overlapping with itself
        let onItself = false
        if(selectedPoint){
            const selfBbox = selectedPoint.bbox();
            onItself = (x >= selfBbox.x && x <= selfBbox.x2 && y >= selfBbox.y && y <= selfBbox.y2)
        }
      
        return (
            (onOther && (!onItself))
        );
    });
}








///////////////////////////////
//       Drag and Drop       //
///////////////////////////////

export function getActiveLayer(layerList) {
    const activeRadio = document.querySelector('input[name="active-layer"]:checked');
    if (activeRadio) {
        const activeLayer = activeRadio.parentElement;
        let layerId = activeLayer.dataset.layerId
        
        console.log('get active layer')
        console.log(layerList)
        console.log(layerId)
        
        const fullLayer = layerList.get(layerId)
        return {
            fullLayer
            //layerId: activeLayer.dataset.layerId,
            //layerElement: activeLayer
        };
    }
    return null;
}


function getSelectedEditMode() {
    var editModeRadios = document.querySelectorAll('input[name="editMode"]');
    for (const radio of editModeRadios) {
        if (radio.checked) {
            return radio.value;
        }
    }
    return null; // Return null if no radio button is selected
}


//Start dragging (OR SELECTING OR ERASING)
export function startDrag(event, layerList, minorGridSize) {

    let drawEraseSelectMode = getSelectedEditMode()

    let activeLayer = null

    let drawModeSelector = document.getElementById('palette-type-selector');
    let drawSlatCargoHandleMode = drawModeSelector.value;

    if(drawSlatCargoHandleMode == 0){
        activeLayer = getActiveLayer(layerList).fullLayer[1]
    } else if(drawSlatCargoHandleMode == 1){
        activeLayer = getActiveLayer(layerList).fullLayer[2]
    } else if(drawSlatCargoHandleMode == 2){
        activeLayer = getActiveLayer(layerList).fullLayer[0]
    }
        
    let dragSelectedElement = event.target.instance;

    console.log("Draw-erase-select mode is set to: "+drawEraseSelectMode+"with element: "+dragSelectedElement)

    if(activeLayer.children().includes(dragSelectedElement)){

        //drawEraseSelectMode == 0 corresponds to drawing
        //drawEraseSelectMode == 1 corresponds to erasing
        //drawEraseSelectMode == 2 corresponds to selecting
        if(drawEraseSelectMode == 0){ //Drawing!
            const point = dragSelectedElement.point(event.clientX, event.clientY);
    
            dragOffset.x = point.x - dragSelectedElement.x();
            dragOffset.y = point.y - dragSelectedElement.y();

            // Define the dragging function with proper arguments to pass to the event listener
            handleDrag = function(event) {
                drag(event, layerList, dragSelectedElement, minorGridSize);
            }

            // Add event listeners for drag and end drag
            document.addEventListener('pointermove', handleDrag)
            document.addEventListener('pointerup', endDrag);
        }
        else if(drawEraseSelectMode == 1){ //Erasing!
            dragSelectedElement.remove()
            event.stopPropagation(); //needed or else delete doesn't work... oh well!
        }
        else if(drawEraseSelectMode == 2){ //Selecting!
            //check if selected already
            var checkSelected = dragSelectedElement.hasClass("selected")
            if(!checkSelected){
                dragSelectedElement.attr({stroke: selectedColor})
                dragSelectedElement.addClass("selected");
            }
            else if(checkSelected){
                let unselectedColor = dragSelectedElement.attr('data-default-color'); 
                dragSelectedElement.attr({stroke: unselectedColor})
                dragSelectedElement.removeClass("selected");
            }
        } 
    }
  }


//Actually drag the element
export function drag(event, layerList, selectedElement, minorGridSize) {

    let activeLayer = null

    let drawModeSelector = document.getElementById('palette-type-selector');
    let drawSlatCargoHandleMode = drawModeSelector.value;

    if(drawSlatCargoHandleMode == 0){
        activeLayer = getActiveLayer(layerList).fullLayer[1]
    } else if(drawSlatCargoHandleMode == 1){
        activeLayer = getActiveLayer(layerList).fullLayer[2]
    } else if(drawSlatCargoHandleMode == 2){
        activeLayer = getActiveLayer(layerList).fullLayer[0]
    }

    if (selectedElement) {
        let point = selectedElement.point(event.clientX, event.clientY) 
        point.x = point.x - dragOffset.x
        point.y = point.y - dragOffset.y
        let roundedX = Math.round(point.x/(minorGridSize))*minorGridSize ;
        let roundedY = Math.round(point.y/(minorGridSize))*minorGridSize ; 

        let drawModeSelector = document.getElementById('palette-type-selector');
        let drawSlatCargoHandleMode = drawModeSelector.value;
        

        if(drawSlatCargoHandleMode == 0){
            if(!isLineOnLine(roundedX, roundedY, activeLayer, minorGridSize, selectedElement)) {
                let moveOffset = 0.5 * minorGridSize

                let isHorizontal = selectedElement.attr('data-horizontal')
                
                if(isHorizontal=='true'){
                    selectedElement.move(roundedX-moveOffset, roundedY);
                    console.log("moving a horizontal element")
                }
                else {
                    selectedElement.move(roundedX, roundedY-moveOffset);
                    console.log("moving a vertical element")
                }
                
            }
        }
        else if(drawSlatCargoHandleMode == 1){
            if(!isCargoOnCargo(roundedX, roundedY, activeLayer, selectedElement)) {
                let bbox = selectedElement.bbox();
                let xOffset = bbox.width / 2
                let yOffset = bbox.height / 2
                selectedElement.move(roundedX-xOffset, roundedY-yOffset)
            }
        }
    }
}


// Function to end dragging
export function endDrag() {
    
    console.log("Dragging ended!")
    //dragSelectedElement = null;
    dragOffset.x = 0
    dragOffset.y = 0

    // Remove event listeners for drag and end drag
    document.removeEventListener('pointermove', handleDrag);
    document.removeEventListener('pointerup', endDrag);
  }




  import { getInventoryItemById } from './inventory.js';




///////////////////////////////
//     Drawing Functions     //
///////////////////////////////
export function placeSlat(roundedX, roundedY, activeSlatLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, slatCounter, horizontal, layerList) {
    
    if(!horizontal){
        if(!willVertBeOnLine(roundedX, roundedY, activeSlatLayer, minorGridSize, 32)) {
            let defaultColor = activeLayerColor; 
            let tmpLine = activeSlatLayer.line(roundedX, roundedY - 0.5 * minorGridSize, roundedX, roundedY + 31.5 * minorGridSize)
                                        .stroke({ width: 3, color:defaultColor, opacity: shownOpacity });
            tmpLine.attr('id','ID-'+activeLayerId + '-N' + slatCounter)
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
            tmpLine.attr('id','ID-'+activeLayerId+'-N' + slatCounter)
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
            tmpCircle.attr('id','CargoID-'+activeLayerId + '-N' + cargoCounter)
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
            group.attr('data-cargo-Id', selectedCargoId)
    
            //tmpLine.attr({ 'pointer-events': 'stroke' })
    
            //Adding draggability:
            //tmpCircle.on('pointerdown', startDrag)
    
            cargoCounter += 1;
        }

    }

    

    
    return cargoCounter;
}













///////////////////////////////
//   Creating Slat Array     //
///////////////////////////////


// Initialize the sparse 3D grid dictionary
export function initializeSparseGridDictionary() {
    return {};
}


// Convert grid coordinates to a string key for the dictionary
export function gridKey(x, y, layer) {
    return `${x},${y},${layer}`;
}


// Populate the sparse grid dictionary with slat IDs
export function populateSparseGridDictionary(gridDict, layers, minorGridSize) {
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


//Create array
export function createGridArray(layerList, minorGridSize) {
    // Initialize the sparse grid dictionary
    let gridDict = initializeSparseGridDictionary();

    // Populate the sparse grid dictionary with slat IDs
    populateSparseGridDictionary(gridDict, Array.from(layerList.values()), minorGridSize);

    // You can now use the gridDict as needed
    console.log(gridDict);

    return gridDict
}
  




