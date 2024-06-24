///////////////////////////////
//     Global Variables!     //
///////////////////////////////

//Configure grid
var minorGridSize = 10;                 //Size of minor grid squares
var majorGridSize = 5*minorGridSize;    //Size of major grid squares
var gridStyle = 1;                      //0 for off, 1 for grid, 2 for dots

//For dragging
let dragSelectedElement = null;         //Item selected to drag
let dragOffset = { x: 0, y: 0 };        //Offset between mouse position and item position

//For adding elements
let placeRoundedX = 0;                  //Snapped position of mouse (X)
let placeRoundedY = 0;                  //Snapped posiiton of mouse (Y)

//For drag & drop
var activeHandleLayer = null;
var activeSlatLayer   = null;
var activeCargoLayer  = null;

//var activeLayer = null;

var activeLayerId = null;
var activeLayerColor = null;

//Layers
let layerList = new Map();
let layerArray = null

//Opacity
let shownOpacity = 0.5
let hiddenOpacity = 0.2

let placeHorizontal = false;

//ID counter for slat IDs
let slatCounter = 0;
let cargoCounter = 0;

//Select
let drawEraseSelectMode = 0; //0 for draw, 1 for erase, 2 for select
let selectedColor = '#93f5f2';

//Draw mode
let drawSlatCargoHandleMode = 0; //0 for slats, 1 for cargo, 2 for handles



///////////////////////////////
//     Helper Functions!     //
///////////////////////////////

//Draw grid:
function drawGrid(gridGroup, width, height, style, majorSize, minorSize) {
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
function isPointOnLine(Layer, x, y, selectedLine = false) {
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


function isLineOnLine(startX, startY, layer, GridSize, selectedLine) {
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


function willVertBeOnLine(startX, startY, layer, gridSize, length=32){
    let overlap = false
    for (let i = 0; i<= length; i++) {
        let x = startX 
        let y = startY + i*gridSize
        overlap = overlap || isPointOnLine(layer, x, y)
    }
    return overlap
}

function willHorzBeOnLine(startX, startY, layer, gridSize, length=32){
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

function isCargoOnCargo(x, y, layer, selectedPoint = false){
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
//     Drawing Functions     //
///////////////////////////////
function placeSlat(roundedX, roundedY, activeSlatLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, slatCounter, horizontal) {
    if(!horizontal){
        if(!willVertBeOnLine(roundedX, roundedY, activeSlatLayer, minorGridSize, 32)) {
            let defaultColor = activeLayerColor; 
            let tmpLine = activeSlatLayer.line(roundedX, roundedY, roundedX, roundedY + 32 * minorGridSize)
                                        .stroke({ width: 3, color:defaultColor, opacity: shownOpacity });
            tmpLine.attr('id','ID-'+activeLayerId + '-N' + slatCounter)
            tmpLine.attr('class',"line")
            tmpLine.attr({ 'pointer-events': 'stroke' })
            tmpLine.attr('data-default-color', defaultColor);

            //Adding draggability:
            tmpLine.on('pointerdown', startDrag)

            slatCounter += 1;
        }
    }
    else if(horizontal){
        if(!willHorzBeOnLine(roundedX, roundedY, activeSlatLayer, minorGridSize, 32)) {
            let defaultColor = activeLayerColor 
            let tmpLine = activeSlatLayer.line(roundedX, roundedY, roundedX + 32 * minorGridSize, roundedY )
                                        .stroke({ width: 3, color:defaultColor, opacity: shownOpacity });
            tmpLine.attr('id','ID-'+activeLayerId+'-N' + slatCounter)
            tmpLine.attr('class',"line")
            tmpLine.attr({ 'pointer-events': 'stroke' })
            tmpLine.attr('data-default-color', defaultColor);

            //Adding draggability:
            tmpLine.on('pointerdown', startDrag)

            slatCounter += 1;
        }
    }

    return slatCounter;
}


function placeCargo(roundedX, roundedY, activeCargoLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, cargoCounter) {
        
    let defaultColor = activeLayerColor; 

    if(!isCargoOnCargo(roundedX, roundedY, activeCargoLayer)){
        let tmpCircle = activeCargoLayer.circle(minorGridSize * 0.75) // SVG.js uses diameter, not radius
                                        .attr({ cx: roundedX, cy: roundedY })
                                        .fill(activeLayerColor) // You can set the fill color here
                                        .opacity(1);//shownOpacity * 1.25);
        tmpCircle.attr('id','CargoID-'+activeLayerId + '-N' + cargoCounter)
        tmpCircle.attr('class',"cargo")
        tmpCircle.attr('data-default-color', defaultColor)

        //tmpLine.attr({ 'pointer-events': 'stroke' })

        //Adding draggability:
        tmpCircle.on('pointerdown', startDrag)

        cargoCounter += 1;
    }

    
    return cargoCounter;
}



///////////////////////////////
//       Drag and Drop       //
///////////////////////////////


//Start dragging (OR SELECTING OR ERASING)
function startDrag(event) {
        
    dragSelectedElement = event.target.instance;

    let tmpActiveLayer = null;
    if(drawSlatCargoHandleMode == 0){
        tmpActiveLayer = activeSlatLayer;
    }
    else if(drawSlatCargoHandleMode == 1){
        tmpActiveLayer = activeCargoLayer;
    }


    if(tmpActiveLayer.children().includes(dragSelectedElement)){
        
        //drawEraseSelectMode == 0 corresponds to drawing
        //drawEraseSelectMode == 1 corresponds to erasing
        //drawEraseSelectMode == 2 corresponds to selecting
        if(drawEraseSelectMode == 0){ //Drawing!
            const point = dragSelectedElement.point(event.clientX, event.clientY);
    
            dragOffset.x = point.x - dragSelectedElement.x();
            dragOffset.y = point.y - dragSelectedElement.y();

            // Add event listeners for drag and end drag
            document.addEventListener('pointermove', drag)
            document.addEventListener('pointerup', endDrag);
        }
        else if(drawEraseSelectMode == 1){ //Erasing!
            dragSelectedElement.remove()
            console.log("deleted!")
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
function drag(event) {
    if (dragSelectedElement) {
        let point = dragSelectedElement.point(event.clientX, event.clientY) 
        point.x = point.x - dragOffset.x
        point.y = point.y - dragOffset.y
        let roundedX = Math.round(point.x/(minorGridSize))*minorGridSize ;
        let roundedY = Math.round(point.y/(minorGridSize))*minorGridSize ;   


        if(drawSlatCargoHandleMode == 0){
            if(!isLineOnLine(roundedX, roundedY, activeSlatLayer,minorGridSize, dragSelectedElement)) {
                dragSelectedElement.move(roundedX, roundedY);
            }
        }
        else if(drawSlatCargoHandleMode == 1){
            if(!isCargoOnCargo(roundedX, roundedY, activeCargoLayer, dragSelectedElement)) {
                dragSelectedElement.attr({ cx: roundedX, cy: roundedY })
            }
        }
        
    }
}


// Function to end dragging
function endDrag() {
    
    console.log("Dragging ended!")
    dragSelectedElement = null;
    dragOffset.x = 0
    dragOffset.y = 0

    // Remove event listeners for drag and end drag
    document.removeEventListener('pointermove', drag);
    document.removeEventListener('pointerup', endDrag);
  }



///////////////////////////////
//   Creating Slat Array     //
///////////////////////////////


// Initialize the sparse 3D grid dictionary
function initializeSparseGridDictionary() {
    return {};
}


// Convert grid coordinates to a string key for the dictionary
function gridKey(x, y, layer) {
    return `${x},${y},${layer}`;
}


// Populate the sparse grid dictionary with slat IDs
function populateSparseGridDictionary(gridDict, layers) {
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
function createGridArray(layerList) {
    // Initialize the sparse grid dictionary
    let gridDict = initializeSparseGridDictionary();

    // Populate the sparse grid dictionary with slat IDs
    populateSparseGridDictionary(gridDict, Array.from(layerList.values()));

    // You can now use the gridDict as needed
    console.log(gridDict);

    return gridDict
}
  






///////////////////////////////
//         Main Code!        //
///////////////////////////////

SVG.on(document, 'DOMContentLoaded', function() {
    
    //Configure Grid
    
    var width = document.getElementById('svg-container').getBoundingClientRect().width
    var height = document.getElementById('svg-container').getBoundingClientRect().height
    var fullDrawing = SVG().addTo('#svg-container').size(width, height)
    
    //Layers
    var drawGridLayer = fullDrawing.group();


    //Initialize Grid
    drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)


    //Change grid configuration by radio buttons
        //Get radio buttons
        var graphModeRadios = document.querySelectorAll('input[name="graphMode');

        //Add a change event listener to each radio button:
        graphModeRadios.forEach(function(radio) {
            radio.addEventListener('change', function() {
                gridStyle = this.value;
                drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)

            })
        })

    //Change edit mode by radio buttons
        //Get radio buttons
        var editModeRadios = document.querySelectorAll('input[name="editMode');

        //Add a change event listener to each radio button:
        editModeRadios.forEach(function(radio) {
            radio.addEventListener('change', function() {
                drawEraseSelectMode = this.value;
            })
        })


    const svgcontainer = document.getElementById('svg-container')
    
    
    const panzoom = Panzoom(svgcontainer, {
        maxScale: 5,
        minScale: 0.25,
        contain: "outside",
      })
    
    //Turn of pan by default
    let disablePanStatus = true; 

    //Initial setup: Zoom & Pan
    setTimeout(() => {
        panzoom.pan(-width/4,-height/4);
        panzoom.setOptions({ disablePan: disablePanStatus });
        panzoom.zoom(2)
    });
    

    //Allow zoom with touchpad
    svgcontainer.parentElement.addEventListener('wheel', panzoom.zoomWithWheel)

    // Event listener to enable pan only when shift is down
    document.addEventListener('keydown', (event) => {
        if( event.key === 'Shift') {
            disablePanStatus = false;
            panzoom.setOptions({ disablePan: disablePanStatus })
        }
    });

    // Turn off pan when shift key is lifted
    document.addEventListener('keyup', (event) => {
        if( event.key === 'Shift') {
            disablePanStatus = true;
            panzoom.setOptions({ disablePan: disablePanStatus })
        }
    });

    // Place horiztonal slats instead of vertical when alt is down
    document.addEventListener('keydown', (event) => {
        if( event.key === 'Alt') {
            placeHorizontal = true;
        }
    });

    // Place vertical slats instead of horizontal when alt is up
    document.addEventListener('keyup', (event) => {
        if( event.key === 'Alt') {
            placeHorizontal = false;
        }
    });
    




    const targetElement = document.getElementById('svg-container');
    
    // Event listener to track mouse movement over the target element
    targetElement.addEventListener('mousemove', (event) => {
        // Calculate mouse position relative to the element
        let selectedElement = event.target.instance;
        let mousePoints = selectedElement.point(event.clientX, event.clientY);
        
        placeRoundedX = Math.round(mousePoints.x/(minorGridSize))*minorGridSize ;
        placeRoundedY = Math.round(mousePoints.y/(minorGridSize))*minorGridSize ;
    });




    

    // Event listener to print slat when mouse is pressed
    targetElement.addEventListener('pointerdown', (event) => {
        if(disablePanStatus == true){
            console.log(`Rounded mouse position - X: ${placeRoundedX}, Y: ${placeRoundedY}`);

            if(drawSlatCargoHandleMode == 0){
                //Record old number of slats places
                let oldSlatCounter = slatCounter;

                //Place slat
                slatCounter = placeSlat(placeRoundedX, placeRoundedY, activeSlatLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, slatCounter, placeHorizontal)

                //Create grid array if a slat has been sucessfully placed!
                if(oldSlatCounter < slatCounter){
                    createGridArray(layerList)
                }
            }
            else if(drawSlatCargoHandleMode == 1){
                //Record old number of cargo places
                let oldCargoCounter = cargoCounter;

                //Place cargo
                cargoCounter = placeCargo(placeRoundedX, placeRoundedY, activeCargoLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, cargoCounter)
                
                //Create grid array if a cargo has been sucessfully placed!
                if(oldCargoCounter < cargoCounter){
                //    createGridArray(layerList)
                }
            }
            



            
            
        }        
    });


    //Layers Event Listeners
    document.addEventListener('layerAdded', (event) => {
        console.log(`Layer added: ${event.detail.layerId}`, event.detail.layerElement);
        //Layer added
        let handleGroup = fullDrawing.group();
        let slatGroup = fullDrawing.group();
        let cargoGroup = fullDrawing.group();
        const tmpFullLayer = [handleGroup, slatGroup, cargoGroup];

        layerList.set(event.detail.layerId, tmpFullLayer)

        //layerList.set(event.detail.layerId, fullDrawing.group());
    });

    document.addEventListener('layerRemoved', (event) => {
        console.log(`Layer removed: ${event.detail.layerId}`, event.detail.layerElement);
        //Layer removed
        //layerList.get(event.detail.layerId).remove()
        const fullLayer = layerList.get(event.detail.layerId);
        fullLayer[0].remove();
        fullLayer[1].remove();
        fullLayer[2].remove();
        layerList.delete(event.detail.layerId)
    });

    document.addEventListener('layerShown', (event) => {
        console.log(`Layer shown: ${event.detail.layerId}`, event.detail.layerElement);
        // Deal with layer shown
        //layerList.get(event.detail.layerId).attr('opacity',1)
        const fullLayer = layerList.get(event.detail.layerId)
        fullLayer[0].attr('opacity',1)
        fullLayer[1].attr('opacity',1)
        fullLayer[2].attr('opacity',1)
    });

    document.addEventListener('layerHidden', (event) => {
        console.log(`Layer hidden: ${event.detail.layerId}`, event.detail.layerElement);
        // Deal with layer hidden
        //layerList.get(event.detail.layerId).attr('opacity',hiddenOpacity)
        const fullLayer = layerList.get(event.detail.layerId)
        fullLayer[0].attr('opacity', hiddenOpacity)
        fullLayer[1].attr('opacity', hiddenOpacity)
        fullLayer[2].attr('opacity', hiddenOpacity)
        
    });

    document.addEventListener('layerMarkedActive', (event) => {
        console.log(`Layer marked active: ${event.detail.layerId}`, event.detail.layerElement);
        // Deal with layer marked active


        activeLayerId = event.detail.layerId

        const fullLayer = layerList.get(event.detail.layerId)
        activeHandleLayer = fullLayer[0]
        activeSlatLayer   = fullLayer[1]
        activeCargoLayer  = fullLayer[2]

        activeLayerColor = event.detail.layerColor

    });


    document.addEventListener('layerColorChanged', (event) => {
        console.log(`Layer color changed: ${event.detail.layerId}`, event.detail.layerElement);
        const layerId = event.detail.layerId;
        const layerColor = event.detail.layerColor;
        console.log(`New color for ${layerId}: ${layerColor}`);


        //Only change slat layer colors
        const fullLayer = layerList.get(event.detail.layerId)
        const layerToChange = fullLayer[1]

        layerToChange.children().forEach(child => {
            child.stroke({ color: layerColor });
            child.attr('data-default-color', layerColor); // Update the default color attribute
        });

        if(layerId == activeLayerId){
            activeLayerColor = layerColor
        }
        
        //Also change cargo layer color?
        const layerToChangeCargo = fullLayer[2]

        layerToChangeCargo.children().forEach(child => {
            child.fill({ color: layerColor });
            child.attr('data-default-color', layerColor); // Update the default color attribute
        });

    
        // Your code to handle the color change, e.g., updating a UI element, applying the color to a canvas, etc.
    });


    //Allow switching between draw modes
        //0 for slats
        //1 for cargo
        //2 for handles
    const drawModeSelector = document.getElementById('palette-type-selector');
    drawModeSelector.addEventListener('change', function () {
        drawSlatCargoHandleMode = drawModeSelector.value;
        console.log("draw mode: "+drawSlatCargoHandleMode)
    });
    

        






})
    

