// TODO: consider moving such global variables to their own file
///////////////////////////////
//     Global Variables!     //
///////////////////////////////

//Configure grid
var minorGridSize = 10;                 //Size of minor grid squares
var majorGridSize = 5*minorGridSize;    //Size of major grid squares
var gridStyle = 1;                      //0 for off, 1 for grid, 2 for dots


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

//Opacity
let shownOpacity = 0.5
let shownCargoOpacity = 0.9
let hiddenOpacity = 0.2

let placeHorizontal = false;

//ID counter for slat IDs
let slatCounter = 1;
let cargoCounter = 1;

//Draw mode
let drawSlatCargoHandleMode = 0; //0 for slats, 1 for cargo, 2 for handles

//Cargo options
let selectedCargoId = null;

var socket = io();



///////////////////////////////
//     Helper Functions!     //
///////////////////////////////

import { drawGrid } from './helper_functions_misc.js';
import { placeSlat, placeCargo } from './helper_functions_drawing.js';
import { createGridArray, importDesign } from './helper_functions_io.js';
import { updateHandleLayers } from './helper_functions_layers.js';

import { populateCargoPalette, renderInventoryTable, addInventoryItem } from './inventory.js';



///////////////////////////////
//         Main Code!        //
///////////////////////////////

SVG.on(document, 'DOMContentLoaded', function() {
    
    //Configure Grid
    var width = document.getElementById('svg-container').getBoundingClientRect().width
    var height = document.getElementById('svg-container').getBoundingClientRect().height
    var fullDrawing = SVG().addTo('#svg-container').size(width, height)

    //Initialize Grid
    var drawGridLayer = fullDrawing.group();
    drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)


    //Get grid configuration radio buttons
    var graphModeRadios = document.querySelectorAll('input[name="graphMode');

    //Change grid style if radio buttons change
    graphModeRadios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            gridStyle = this.value;
            drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)
        })
    })

    const svgcontainer = document.getElementById('svg-container')
    
    //Configure panning and zooming
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

    /////////////////////////////////
    //  Keyboard event listeners   //
    /////////////////////////////////

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
        // TODO: pycharm is complaining that these == functions could result in type coercion.  Investigate if === is needed.
        if(disablePanStatus == true){
            console.log(`Rounded mouse position - X: ${placeRoundedX}, Y: ${placeRoundedY}`);

            if(drawSlatCargoHandleMode == 0){
                //Record old number of slats places
                let oldSlatCounter = slatCounter;

                //Place slat
                slatCounter = placeSlat(placeRoundedX, placeRoundedY, activeSlatLayer, activeLayerId, minorGridSize, activeLayerColor, shownOpacity, slatCounter, placeHorizontal, layerList)

                //Create grid array if a slat has been sucessfully placed!
                if(oldSlatCounter < slatCounter){
                    // TODO: remove this if not in use
                    //let gridArray = createGridArray(layerList, minorGridSize)
                    //dispatchServerEvent('slatPlaced', gridArray)
                }
            }
            else if(drawSlatCargoHandleMode == 1){
                //Record old number of cargo places
                let oldCargoCounter = cargoCounter;

                //Place cargo
                cargoCounter = placeCargo(placeRoundedX, placeRoundedY, activeCargoLayer, activeLayerId, minorGridSize, activeLayerColor, shownCargoOpacity, cargoCounter, selectedCargoId, layerList)
                
                //Create grid array if a cargo has been sucessfully placed!
                if(oldCargoCounter < cargoCounter){
                     // TODO: remove this if not in use
                    //let gridArray = createGridArray(layerList, minorGridSize)
                    //dispatchServerEvent('cargoPlaced', gridArray)
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
        const tmpFullLayer = [handleGroup, slatGroup, cargoGroup, event.detail.layerColor];

        layerList.set(event.detail.layerId, tmpFullLayer)
        updateHandleLayers(layerList)
    });

    document.addEventListener('layerRemoved', (event) => {
        console.log(`Layer removed: ${event.detail.layerId}`, event.detail.layerElement);
        //Layer removed
        const fullLayer = layerList.get(event.detail.layerId);
        fullLayer[0].remove();
        fullLayer[1].remove();
        fullLayer[2].remove();
        layerList.delete(event.detail.layerId)
        updateHandleLayers(layerList)

        //socket.emit('my layer removed event', {data: 'Layer removed'});
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

        //First, change color attribute of layer element
        fullLayer[3] = layerColor
        updateHandleLayers(layerList)

        layerToChange.children().forEach(child => {
            child.stroke({ color: layerColor });
            child.attr('data-default-color', layerColor); // Update the default color attribute
        });

        // TODO === as before
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
    });


    //Allow switching between draw modes
        //0 for slats
        //1 for cargo
        //2 for handles
    const drawModeSelector = document.getElementById('palette-type-selector');
    const cargoPalette = document.getElementById('cargo-palette');
    const handlePalette = document.getElementById('handle-palette');

    drawModeSelector.addEventListener('change', function () {
        drawSlatCargoHandleMode = drawModeSelector.value;
        console.log("draw mode: "+drawSlatCargoHandleMode)

        // Show/hide cargo palette based on selection
        handlePalette.style.display = 'none'
        cargoPalette.style.display = 'none'

        if (drawSlatCargoHandleMode == 1) { // Cargo mode
            cargoPalette.style.display = 'block';
            populateCargoPalette(); // Populate the cargo palette
        } 
        else if(drawSlatCargoHandleMode == 2){
            handlePalette.style.display = 'block'
            updateHandleLayers(layerList)
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


    document.getElementById('generate-handles-button').addEventListener('click',function(event){
        let gridArray = createGridArray(layerList, minorGridSize)
        socket.emit('generate_handles', gridArray)
    })

    // TODO: remove if done
    //document.addEventListener('slatPlaced', (event) => {
    //    console.log('Slat placed:', event.detail);
    //    socket.emit('slat placed', event.detail);
    //});

    //document.addEventListener('cargoPlaced', (event) => {
    //    console.log('Cargo placed:', event.detail);
    //    socket.emit('cargo placed', event.detail);
    //});


    socket.on('slat dict made', function(data) {
        // TODO: why is there a ? here?
        console.log("slat array read from python? If so, here it is: ", data)
        slatCounter = importDesign(data, data, layerList, minorGridSize, shownOpacity, shownCargoOpacity)
    });
    

    //Add event listener for design saving
    document.getElementById('save-design').addEventListener('click', function(event) {
        console.log("design to be saved now!")
        let gridArray = createGridArray(layerList, minorGridSize)
        socket.emit('design_saved', gridArray);
        console.log("save emit has been sent!")

        const filename = 'crisscross_design.npz';
        window.location.href = '/download/' + filename;
    });

    socket.on('design_imported', function(data) {
        console.log("Imported design!", data)
        slatCounter = importDesign(data[0], data[1], layerList, minorGridSize, shownOpacity, shownCargoOpacity)
    });




    //File uploading
    let uploadForm = document.getElementById('upload-form')

    uploadForm.addEventListener('submit', function(event){
        console.log("Upload form submitted!")
        event.preventDefault(); // Prevent the default form submission
        
        var fileInput = document.getElementById('file-input');
        if (fileInput.files.length == 0) {
            console.log("No file selected.")
            return
        }

        var file = fileInput.files[0];
        console.log(file)
        var reader = new FileReader();

        reader.onload = function(event) {
            var data = {
                'file': {
                    'filename': file.name,
                    'data': new Uint8Array(event.target.result)
                }
            };

            console.log("reader.onload executed!")
            socket.emit('upload_file', data);
        };

        reader.readAsArrayBuffer(file)
    })


    socket.on('upload_response', function(data) {
        console.log(data.message)
    });


});

    

        





    

