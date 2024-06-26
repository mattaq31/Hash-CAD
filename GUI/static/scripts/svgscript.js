///////////////////////////////
//     Global Variables!     //
///////////////////////////////

//Configure grid
var minorGridSize = 10;                 //Size of minor grid squares
var majorGridSize = 5*minorGridSize;    //Size of major grid squares
var gridStyle = 1;                      //0 for off, 1 for grid, 2 for dots

//For dragging
//let dragSelectedElement = null;         //Item selected to drag


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
let shownCargoOpacity = 0.9
let hiddenOpacity = 0.2

let placeHorizontal = false;

//ID counter for slat IDs
let slatCounter = 0;
let cargoCounter = 0;

//Select
//let drawEraseSelectMode = 0; //0 for draw, 1 for erase, 2 for select
let selectedColor = '#93f5f2';

//Draw mode
let drawSlatCargoHandleMode = 0; //0 for slats, 1 for cargo, 2 for handles

//Cargo options
let selectedCargoId = null;
let selectedCargoName = null;
let selectedCargoAcronym = null;
let selectedCargoColor = null;


var socket = io();

///////////////////////////////
//     Helper Functions!     //
///////////////////////////////

import { drawGrid } from './helper_functions.js';
import { placeSlat, placeCargo } from './helper_functions.js';
import { createGridArray } from './helper_functions.js';

import { populateCargoPalette, getInventoryItemById, renderInventoryTable, addInventoryItem } from './inventory.js';




///////////////////////////////
//  Custom Events for Server //
///////////////////////////////
// Function to dispatch custom events
function dispatchServerEvent(eventName, eventItem) {
    const event = new CustomEvent(eventName, {detail: eventItem});
    document.dispatchEvent(event);
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
                slatCounter = placeSlat(placeRoundedX, placeRoundedY, activeSlatLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, slatCounter, placeHorizontal, layerList)

                //Create grid array if a slat has been sucessfully placed!
                if(oldSlatCounter < slatCounter){
                    let slatArray = createGridArray(layerList, minorGridSize)
                    dispatchServerEvent('slatPlaced', slatArray)
                }
            }
            else if(drawSlatCargoHandleMode == 1){
                //Record old number of cargo places
                let oldCargoCounter = cargoCounter;

                //Place cargo
                cargoCounter = placeCargo(placeRoundedX, placeRoundedY, activeCargoLayer, activeLayerId, minorGridSize, activeLayerColor, shownCargoOpacity, cargoCounter, selectedCargoId, layerList)
                
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

        
        socket.emit('my layer removed event', {data: 'Layer removed'});
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
        //console.log(`Layer color changed: ${event.detail.layerId}`, event.detail.layerElement);
        const layerId = event.detail.layerId;
        const layerColor = event.detail.layerColor;
        //console.log(`New color for ${layerId}: ${layerColor}`);


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

            child.children().forEach(childChild => {
                if(childChild.type === 'circle'){
                    childChild.stroke({ color: layerColor });
                    childChild.attr('data-default-color', layerColor); // Update the default color attribute
                }
            })
           
            
        });

    
        // Your code to handle the color change, e.g., updating a UI element, applying the color to a canvas, etc.
    });


    //Allow switching between draw modes
        //0 for slats
        //1 for cargo
        //2 for handles
    const drawModeSelector = document.getElementById('palette-type-selector');
    const cargoPalette = document.getElementById('cargo-palette');

    drawModeSelector.addEventListener('change', function () {
        drawSlatCargoHandleMode = drawModeSelector.value;
        console.log("draw mode: "+drawSlatCargoHandleMode)

        // Show/hide cargo palette based on selection
        if (drawSlatCargoHandleMode == 1) { // Cargo mode
            cargoPalette.style.display = 'block';
            populateCargoPalette(); // Populate the cargo palette
        } 
        else {
            cargoPalette.style.display = 'none';
        }
    });



    //Add event listener for cargo option selection
    document.getElementById('cargo-options').addEventListener('click', function(event) {
        if (event.target.classList.contains('cargo-option')) {
            selectedCargoId = parseInt(event.target.dataset.id);
            console.log("Selected cargo ID: " + selectedCargoId);
        }
        else if(event.target.id == 'cargo-editor'){
            let modal = document.getElementById('cargoInventoryModal')
            modal.style.display = "block";
            renderInventoryTable();
        }
    });



    // When the user clicks on <span> (x), close the modal
    document.getElementById('inventory-modal-close').addEventListener('click',function(event){
        let modal = document.getElementById('cargoInventoryModal')
        modal.style.display = "none";
    })

    document.getElementById('add-inventory-cargo-element').addEventListener('click',function(event){
        addInventoryItem('Cargo Name', 'ABC', '#000000')
        renderInventoryTable();
    })




    document.addEventListener('slatPlaced', (event) => {
        console.log('Slat placed:', event.detail);
        socket.emit('slat placed', event.detail);
    });

  
    
    


});

    

        





    

