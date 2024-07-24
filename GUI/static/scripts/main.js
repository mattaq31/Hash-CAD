// TODO: consider moving such global variables to their own file
///////////////////////////////
//     Global Variables!     //
///////////////////////////////

//Configure grid
var minorGridSize = 10;                 //Size of minor grid squares
var majorGridSize = 4*minorGridSize;    //Size of major grid squares
var gridStyle = 2;                      //0 for off, 1 for grid, 2 for dots


//For adding elements
let placeRoundedX = 0;                  //Snapped position of mouse (X)
let placeRoundedY = 0;                  //Snapped posiiton of mouse (Y)

//For drag & drop
var activeHandleLayer = null;
var activeSlatLayer   = null;
var activeCargoLayer  = null;

var activeTopCargoLayer = null;
var activeBottomCargoLayer = null;

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
let cargoSeedMode = null; //0 for cargo, 1 for seeds

//Cargo options
let selectedCargoId = null;

var socket = io();



///////////////////////////////
//     Helper Functions!     //
///////////////////////////////

import { drawGrid, changeCursorEvents } from './helper_functions_misc.js';
import { placeSlat, placeCargo, placeSeed, showSlat } from './helper_functions_drawing.js';
import { createGridArray, importDesign, importHandles, downloadFile, downloadOutputs } from './helper_functions_io.js';
import { updateHandleLayers, updateHandleLayerButtons, getHandleLayerDict, clearHandles } from './helper_functions_handles.js';
import { delete3DSlatLayer } from './helper_functions_3D.js';


import { populateCargoPalette, renderInventoryTable, addInventoryItem, updateInventoryItems} from './cargo.js';



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
    //var graphModeRadios = document.querySelectorAll('input[name="graphMode');

    //Change grid style if radio buttons change
    //graphModeRadios.forEach(function(radio) {
    //    radio.addEventListener('change', function() {
    //        gridStyle = this.value;
    //        drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)
    //    })
    //})

    const svgcontainer = document.getElementById('svg-container')
    
    //Configure panning and zooming
    const panzoom = Panzoom(svgcontainer, {
        maxScale: 5,
        minScale: 0.25,
        contain: "outside",
        cursor: "crosshair"
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
            panzoom.setOptions({ cursor: "move" })
        }
    });

    // Turn off pan when shift key is lifted
    document.addEventListener('keyup', (event) => {
        if( event.key === 'Shift') {
            disablePanStatus = true;
            panzoom.setOptions({ disablePan: disablePanStatus })
            panzoom.setOptions({ cursor: "crosshair" })
        }
    });

    // Place horiztonal slats instead of vertical when alt is down
    document.addEventListener('keydown', (event) => {
        if( event.key === 'Alt') {
            if(placeHorizontal == false){
                // Remove any existing cursor slats with the id 'cursor-slat'
                let cursorSlat = document.getElementById('cursor-slat')
                if(cursorSlat){
                    cursorSlat.remove()
                }
            }

            event.preventDefault();
            placeHorizontal = true;

            
        }
    });


    // Place vertical slats instead of horizontal when alt is up
    document.addEventListener('keyup', (event) => {
        if( event.key === 'Alt') {
            if(placeHorizontal == true){
                // Remove any existing cursor slats with the id 'cursor-slat'
                let cursorSlat = document.getElementById('cursor-slat')
                if(cursorSlat){
                    cursorSlat.remove()
                }
            }

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
                let slatCountToPlace = document.getElementById('slatNumber').value
                for (let i = 0; i < slatCountToPlace; i++) {
                    let xIterator = minorGridSize * i * (!placeHorizontal)
                    let yIterator = minorGridSize * i * placeHorizontal

                    //Place slat
                    slatCounter = placeSlat(placeRoundedX + xIterator, 
                                            placeRoundedY + yIterator, 
                                            activeSlatLayer, activeLayerId, 
                                            minorGridSize, activeLayerColor, 
                                            shownOpacity, slatCounter, 
                                            placeHorizontal, layerList)

                }
                    
                    
                
            }
            else if(drawSlatCargoHandleMode == 1){

                const topLayerButton = document.getElementById('top-layer-selector')
                const bottomLayerButton = document.getElementById('bottom-layer-selector')

                let top = false;
                if(topLayerButton.classList.contains('h25-toggle-selected')){
                    top = true
                }

                if(seedButton.classList.contains('h25-toggle-selected')){
                    //Place seed
                    placeSeed(placeRoundedX, placeRoundedY, activeBottomCargoLayer, 
                        activeLayerId, minorGridSize, activeLayerColor, 
                        placeHorizontal, layerList)
                }
                else{
                    //Place cargo
                    cargoCounter = placeCargo(placeRoundedX, placeRoundedY, activeCargoLayer, 
                        activeLayerId, minorGridSize, activeLayerColor, 
                        shownCargoOpacity, cargoCounter, selectedCargoId, 
                        layerList, top) 
                }

            }
             
        }        
    });

    //Layers Event Listeners
    document.addEventListener('layerAdded', (event) => {
        console.log(`Layer added: ${event.detail.layerId}`, event.detail.layerElement);
        //Layer added
        
        let bottomCargoGroup = fullDrawing.group();
        let slatGroup = fullDrawing.group();
        let topCargoGroup = fullDrawing.group();
        let handleGroup = fullDrawing.group();

        //let handleGroup = fullDrawing.group();
        //let slatGroup = fullDrawing.group();
        //let topCargoGroup = fullDrawing.group();
        //let bottomCargoGroup = fullDrawing.group();
        //let cargoGroup = fullDrawing.group();
        const tmpFullLayer = [handleGroup, slatGroup, bottomCargoGroup, topCargoGroup, event.detail.layerColor];

        layerList.set(event.detail.layerId, tmpFullLayer)
        updateHandleLayers(layerList)
        getHandleLayerDict(layerList)
    });

    document.addEventListener('layerRemoved', (event) => {
        console.log(`Layer removed: ${event.detail.layerId}`, event.detail.layerElement);
        //Layer removed
        const fullLayer = layerList.get(event.detail.layerId);

        delete3DSlatLayer(fullLayer[1])

        fullLayer[0].remove();
        fullLayer[1].remove();
        fullLayer[2].remove();
        fullLayer[3].remove();
        layerList.delete(event.detail.layerId)
        updateHandleLayers(layerList)
        getHandleLayerDict(layerList)

    });

    document.addEventListener('layerShown', (event) => {
        console.log(`Layer shown: ${event.detail.layerId}`, event.detail.layerElement);
        // Deal with layer shown
        const fullLayer = layerList.get(event.detail.layerId)
        fullLayer[0].attr('opacity',1)
        fullLayer[1].attr('opacity',1)
        fullLayer[2].attr('opacity',1)
        fullLayer[3].attr('opacity',1)
    });

    document.addEventListener('layerHidden', (event) => {
        console.log(`Layer hidden: ${event.detail.layerId}`, event.detail.layerElement);
        // Deal with layer hidden
        const fullLayer = layerList.get(event.detail.layerId)
        fullLayer[0].attr('opacity', hiddenOpacity)
        fullLayer[1].attr('opacity', hiddenOpacity)
        fullLayer[2].attr('opacity', hiddenOpacity)
        fullLayer[3].attr('opacity', hiddenOpacity)
        
    });

    document.addEventListener('layerMarkedActive', (event) => {
        console.log(`Layer marked active: ${event.detail.layerId}`, event.detail.layerElement);
        
        //First remove pointer events from all layers!
        layerList.forEach((layer, layerIndex) => {
            changeCursorEvents(layer[0], 'none')
            changeCursorEvents(layer[1], 'none')
            changeCursorEvents(layer[2], 'none')
            changeCursorEvents(layer[3], 'none')
            //layer[0].style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //layer[1].style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //layer[2].style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //layer[3].style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
        });

        //TODO: ADD POINTER EVENTS TO ACTIVE LAYER



        // Deal with layer marked active

        activeLayerId = event.detail.layerId

        const fullLayer = layerList.get(event.detail.layerId)
        activeHandleLayer = fullLayer[0]
        activeSlatLayer   = fullLayer[1]
        activeBottomCargoLayer  = fullLayer[2]  
        activeTopCargoLayer     = fullLayer[3]  

        activeCargoLayer = null;

        const topLayerButton = document.getElementById('top-layer-selector')
        const bottomLayerButton = document.getElementById('bottom-layer-selector')
        if(topLayerButton.classList.contains('h25-toggle-selected')){
            activeCargoLayer = activeTopCargoLayer
        }
        else if(bottomLayerButton.classList.contains('h25-toggle-selected')){
            activeCargoLayer = activeBottomCargoLayer
        }

        
        const drawSlatCargoHandleMode = document.getElementById('palette-type-selector').value;

        if(drawSlatCargoHandleMode == 0){ //Slat mode
            changeCursorEvents(activeSlatLayer, 'stroke')
            changeCursorEvents(activeTopCargoLayer, 'none')
            changeCursorEvents(activeBottomCargoLayer, 'none')
            changeCursorEvents(activeHandleLayer, 'none')
            //activeSlatLayer.style.pointerEvents = 'auto'; //.attr({ 'pointer-events': 'auto' })
            //activeTopCargoLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //activeBottomCargoLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //activeHandleLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
        }
        else if (drawSlatCargoHandleMode == 1) { // Cargo mode
            changeCursorEvents(activeSlatLayer, 'none')
            changeCursorEvents(activeTopCargoLayer, 'none')
            changeCursorEvents(activeBottomCargoLayer, 'none')
            changeCursorEvents(activeHandleLayer, 'none')
            if(activeCargoLayer){
                changeCursorEvents(activeCargoLayer, 'bounding-box')
            }

            //activeSlatLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //activeHandleLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //if(activeCargoLayer){
            //    activeCargoLayer.style.pointerEvents = 'auto';
            //}
        } 
        else if(drawSlatCargoHandleMode == 2){
            changeCursorEvents(activeSlatLayer, 'none')
            changeCursorEvents(activeTopCargoLayer, 'none')
            changeCursorEvents(activeBottomCargoLayer, 'none')
            changeCursorEvents(activeHandleLayer, 'stroke')
            //activeSlatLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //activeTopCargoLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //activeBottomCargoLayer.style.pointerEvents = 'auto';
            //activeHandleLayer.style.pointerEvents = 'auto'; //.attr({ 'pointer-events': 'auto' })
        }

        


        activeLayerColor = event.detail.layerColor

        updateHandleLayerButtons(layerList, activeLayerId)

        console.log(fullLayer)

    });


    document.addEventListener('layerColorChanged', (event) => {
        const layerId = event.detail.layerId;
        const layerColor = event.detail.layerColor;

        //Only change slat layer colors
        const fullLayer = layerList.get(event.detail.layerId)
        const layerToChange = fullLayer[1]

        //First, change color attribute of layer element
        fullLayer[4] = layerColor
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
        const layerToChangeBottomCargo = fullLayer[2] 
        const layerToChangeTopCargo = fullLayer[3] 
        
        layerToChangeTopCargo.children().forEach(child => {

            child.children().forEach(childChild => {
                if(childChild.attr('data-cargo-component') === 'shape'){
                    childChild.stroke({ color: layerColor });
                    childChild.attr('data-default-color', layerColor); // Update the default color attribute
                }
            })
        });

        layerToChangeBottomCargo.children().forEach(child => {

            child.children().forEach(childChild => {
                if(childChild.attr('data-cargo-component') === 'shape'){
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
    const slatPalette = document.getElementById('slat-palette')
    const cargoPalette = document.getElementById('cargo-palette');
    const handlePalette = document.getElementById('handle-palette');

    drawModeSelector.addEventListener('change', function () {
        drawSlatCargoHandleMode = drawModeSelector.value;
        console.log("draw mode: "+drawSlatCargoHandleMode)

        // Show/hide cargo palette based on selection
        slatPalette.style.display = 'none'
        handlePalette.style.display = 'none'
        cargoPalette.style.display = 'none'

        if(drawSlatCargoHandleMode == 0){ //Slat mode
            slatPalette.style.display = 'block'
            changeCursorEvents(activeSlatLayer, 'stroke')
            changeCursorEvents(activeTopCargoLayer, 'none')
            changeCursorEvents(activeBottomCargoLayer, 'none')
            changeCursorEvents(activeHandleLayer, 'none')
            //activeSlatLayer.style.pointerEvents = 'auto'; //.attr({ 'pointer-events': 'auto' })
            //activeTopCargoLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //activeBottomCargoLayer.style.pointerEvents = 'none';
            //activeHandleLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
        }
        else if (drawSlatCargoHandleMode == 1) { // Cargo mode
            cargoPalette.style.display = 'block';
            populateCargoPalette(); // Populate the cargo palette
            getHandleLayerDict(layerList)
            updateHandleLayerButtons(layerList, activeLayerId)

            changeCursorEvents(activeSlatLayer, 'none')
            changeCursorEvents(activeTopCargoLayer, 'none')
            changeCursorEvents(activeBottomCargoLayer, 'none')
            changeCursorEvents(activeHandleLayer, 'none')
            if(activeCargoLayer){
                changeCursorEvents(activeCargoLayer, 'bounding-box')
            }

            //activeSlatLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //if(activeCargoLayer){
            //    activeCargoLayer.style.pointerEvents = 'auto';
            //}
            //activeHandleLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })

        } 
        else if(drawSlatCargoHandleMode == 2){
            handlePalette.style.display = 'block'
            getHandleLayerDict(layerList)
            updateHandleLayers(layerList)

            changeCursorEvents(activeSlatLayer, 'none')
            changeCursorEvents(activeTopCargoLayer, 'none')
            changeCursorEvents(activeBottomCargoLayer, 'none')
            changeCursorEvents(activeHandleLayer, 'stroke')
            
            //activeSlatLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //activeTopCargoLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
            //activeBottomCargoLayer.style.pointerEvents = 'none';
            //activeHandleLayer.style.pointerEvents = 'auto'; //.attr({ 'pointer-events': 'auto' })
        }

    });


    //Add event listener for cargo option selection
    document.getElementById('cargo-options').addEventListener('click', function(event) {
        if (event.target.classList.contains('cargo-option')) {
            selectedCargoId = event.target.dataset.id;
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
        addInventoryItem('Cargo Name', 'ABC', '#000000',"", "")
        renderInventoryTable();
    })


    document.getElementById('generate-megastructure-button').addEventListener('click',function(event){
        let gridArray = createGridArray(layerList, minorGridSize)
        let handleConfigs = getHandleLayerDict(layerList)

        let checkboxOldHandles = document.getElementById('checkbox-old-handles').checked;
        let checkboxGraphics = document.getElementById('checkbox-graphics').checked;
        let checkboxEcho = document.getElementById('checkbox-echo').checked;

        let generalConfigs = [checkboxOldHandles, checkboxGraphics, checkboxEcho]


        socket.emit('generate_megastructures', [gridArray, handleConfigs, generalConfigs])
    })

    document.getElementById('generate-handles-button').addEventListener('click',function(event){
        let gridArray = createGridArray(layerList, minorGridSize)
        let handleConfigs = getHandleLayerDict(layerList)
        let handleIterations = document.getElementById('handle-iteration-number').value
        console.log('generating handles now...')
        socket.emit('generate_handles', [gridArray, handleConfigs, handleIterations])
    })

    socket.on('handles_sent', function(handleDict){
        console.log('handles have been generated and recieved:', handleDict)
        importHandles(handleDict, layerList, minorGridSize)

    })

    document.getElementById('clear-handles-button').addEventListener('click', function(event){
        clearHandles(layerList)
    })


    //socket.on('slat dict made', function(data) {
    //    console.log("slat array read from python: ", data)
    //    slatCounter = importDesign(data, data, layerList, minorGridSize, shownOpacity, shownCargoOpacity)
    //});
    

    //Add event listener for design saving
    document.getElementById('save-design').addEventListener('click', function(event) {
        console.log("design to be saved now!")
        let gridArray = createGridArray(layerList, minorGridSize)
        console.log("Grid array: ", gridArray)
        socket.emit('design_to_backend_for_download', gridArray);
        console.log("save emit has been sent!")


        
    });

    socket.on('saved_design_ready_to_download', function(){
        downloadFile('/download/crisscross_design.npz')
    })

    socket.on('megastructure_output_ready_to_download', function(){
        downloadOutputs('/download/outputs.zip')
    })


    socket.on('design_imported', function(data) {
        console.log("Imported design!", data)
        let seedDict = data[0]
        let slatDict = data[1]
        let cargoDict = data[2]
        let handleDict = data[3]
        slatCounter, cargoCounter = importDesign(seedDict, slatDict, cargoDict, handleDict, layerList, minorGridSize, shownOpacity, shownCargoOpacity)
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

    document.getElementById('update-inventory-from-import').addEventListener('click', function(){
        

        populateCargoPalette();
        renderInventoryTable();
    })



    const topLayerButton = document.getElementById('top-layer-selector')
    const bottomLayerButton = document.getElementById('bottom-layer-selector')
    const seedButton = document.getElementById('seed-mode-selector')

    topLayerButton.addEventListener('click', (event)=>{
        changeCursorEvents(activeTopCargoLayer, 'bounding-box')
        changeCursorEvents(activeBottomCargoLayer, 'none')
        //activeTopCargoLayer.style.pointerEvents = 'auto'; //.attr({ 'pointer-events': 'auto' })
        //activeBottomCargoLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
        activeCargoLayer = activeTopCargoLayer
    })

    bottomLayerButton.addEventListener('click', (event)=>{
        changeCursorEvents(activeTopCargoLayer, 'none')
        changeCursorEvents(activeBottomCargoLayer, 'bounding-box')
        //activeTopCargoLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
        //activeBottomCargoLayer.style.pointerEvents = 'auto'; //.attr({ 'pointer-events': 'auto' })
        activeCargoLayer = activeBottomCargoLayer
    })

    seedButton.addEventListener('click', (event)=>{
        changeCursorEvents(activeTopCargoLayer, 'none')
        changeCursorEvents(activeBottomCargoLayer, 'bounding-box')
        //activeTopCargoLayer.style.pointerEvents = 'none'; //.attr({ 'pointer-events': 'none' })
        //activeBottomCargoLayer.style.pointerEvents = 'auto'; //.attr({ 'pointer-events': 'auto' })
        activeCargoLayer = activeBottomCargoLayer
    })




    const drawButton = document.getElementById('draw-button')
    const eraseButton = document.getElementById('erase-button')
    const selectButton = document.getElementById('select-button')

    drawButton.addEventListener('click', (event)=>{
        drawButton.classList.add('draw-erase-select-toggle-selected')
        eraseButton.classList.remove('draw-erase-select-toggle-selected')
        selectButton.classList.remove('draw-erase-select-toggle-selected')
    })

    eraseButton.addEventListener('click', (event)=>{
        eraseButton.classList.add('draw-erase-select-toggle-selected')
        drawButton.classList.remove('draw-erase-select-toggle-selected')
        selectButton.classList.remove('draw-erase-select-toggle-selected')
    })

    selectButton.addEventListener('click', (event)=>{
        selectButton.classList.add('draw-erase-select-toggle-selected')
        eraseButton.classList.remove('draw-erase-select-toggle-selected')
        drawButton.classList.remove('draw-erase-select-toggle-selected')
    })




    const gridButton = document.getElementById('grid-button')
    const dotsButton = document.getElementById('dot-button')
    const blankButton = document.getElementById('blank-button')

    gridButton.addEventListener('click', (event)=>{
        gridButton.classList.add('grid-dots-blank-toggle-selected')
        dotsButton.classList.remove('grid-dots-blank-toggle-selected')
        blankButton.classList.remove('grid-dots-blank-toggle-selected')

        gridStyle = 1;
        drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)

    })

    dotsButton.addEventListener('click', (event)=>{
        dotsButton.classList.add('grid-dots-blank-toggle-selected')
        gridButton.classList.remove('grid-dots-blank-toggle-selected')
        blankButton.classList.remove('grid-dots-blank-toggle-selected')

        gridStyle = 2;
        drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)
    })

    blankButton.addEventListener('click', (event)=>{
        blankButton.classList.add('grid-dots-blank-toggle-selected')
        gridButton.classList.remove('grid-dots-blank-toggle-selected')
        dotsButton.classList.remove('grid-dots-blank-toggle-selected')

        gridStyle = 0;
        drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)
    })




    svgcontainer.addEventListener('mousemove', function(event){
        let selectedElement = event.target.instance;
        let mousePoints = selectedElement.point(event.clientX, event.clientY);
        let slatCountToPlace = document.getElementById('slatNumber').value

        showSlat(mousePoints.x, mousePoints.y, fullDrawing, minorGridSize, placeHorizontal, slatCountToPlace)
        
    })



});




// File uploading
let plateUploadForm = document.getElementById('plate-upload-form')

plateUploadForm.addEventListener('submit', function(event) {
    console.log("Plate upload form submitted!")
    event.preventDefault(); // Prevent the default form submission

    var fileInput = document.getElementById('plate-file-input');
    if (fileInput.files.length == 0) {
        console.log("No file selected.")
        return
    }

    Array.from(fileInput.files).forEach(file => {
        var reader = new FileReader();

        reader.onload = function(event) {
            var data = {
                'file': {
                    'filename': file.name,
                    'data': new Uint8Array(event.target.result)
                }
            };

            console.log("reader.onload executed!")
            socket.emit('upload_plates', data);
        };

        reader.readAsArrayBuffer(file)
    });
})


socket.on('plate_upload_response', function(data) {
    console.log(data.message)
    updateInventoryItems();
});
    

        






    

