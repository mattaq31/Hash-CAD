//Functions
import { placeSlat, placeCargo, placeSeed, showSlat, getFullDrawing } from './functions_drawing.js';
import { copyCargo, showCopiedCargo, pasteCargo } from './functions_copypaste.js';
import { getPanStatus, configurePanzoom } from './functions_panzoom.js'
import { drawGrid, changePlacementMode } from './functions_misc.js';
import { getLayerList } from './functions_layers.js'

//Constants & Variables
import {minorGridSize, majorGridSize, shownOpacity, shownCargoOpacity } from './constants.js'
import {getVariable, writeVariable} from './variables.js'

let placeRoundedX = 0;  //Snapped position of mouse (X)
let placeRoundedY = 0;  //Snapped position of mouse (Y)

SVG.on(document, 'DOMContentLoaded', function() {

    const svgcontainer = document.getElementById('svg-container')
    var fullDrawing = getFullDrawing()
    var layerList = getLayerList()
    
    var width = svgcontainer.getBoundingClientRect().width
    var height = svgcontainer.getBoundingClientRect().height
    
    //Set up Grid
    var drawGridLayer = fullDrawing.group();
    drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize)

    //Configure panning and zooming
    configurePanzoom(svgcontainer)

    // Track mouse over svgcontainer
    svgcontainer.addEventListener('mousemove', (event) => {
        let selectedElement = event.target.instance;
        let mousePoints = selectedElement.point(event.clientX, event.clientY);
        
        placeRoundedX = Math.round(mousePoints.x/(minorGridSize))*minorGridSize ;
        placeRoundedY = Math.round(mousePoints.y/(minorGridSize))*minorGridSize ;

        if(getVariable("pasteMode")==true){
            showCopiedCargo(getVariable("copiedCargo"), placeRoundedX, placeRoundedY, fullDrawing, minorGridSize)
        }
        else{
            let slatCountToPlace = document.getElementById('slatNumber').value
            showSlat(mousePoints.x, mousePoints.y, fullDrawing, minorGridSize, getVariable("placeHorizontal"), slatCountToPlace)
        }
    });

    // Handle clicks 
    svgcontainer.addEventListener('pointerdown', (event) => {

        let drawMode = document.getElementById('draw-button').classList.contains('draw-erase-select-toggle-selected')
    
        if(getPanStatus() == true && drawMode){
            console.log(`Rounded mouse position - X: ${placeRoundedX}, Y: ${placeRoundedY}`);

            if(getVariable("drawSlatCargoHandleMode") == 0){
                let numberSlatsToPlace = document.getElementById('slatNumber').value
                for (let i = 0; i < numberSlatsToPlace; i++) {
                    let xIterator = minorGridSize * i * (!getVariable("placeHorizontal"))
                    let yIterator = minorGridSize * i * getVariable("placeHorizontal")

                    //Place slat
                    let slatCounter = placeSlat(placeRoundedX + xIterator, 
                                                placeRoundedY + yIterator, 
                                                getVariable("activeSlatLayer"), 
                                                getVariable("activeLayerId"), 
                                                minorGridSize, 
                                                getVariable("activeLayerColor"), 
                                                shownOpacity, 
                                                getVariable("slatCounter"), 
                                                getVariable("placeHorizontal"), 
                                                layerList)

                    writeVariable("slatCounter", slatCounter)
                }
            }
            else if(getVariable("drawSlatCargoHandleMode") == 1){
                const topLayerButton = document.getElementById('top-layer-selector')
                let top = topLayerButton.classList.contains('h25-toggle-selected')

                const seedButton = document.getElementById('seed-mode-selector')
                if(seedButton.classList.contains('h25-toggle-selected')){
                    placeSeed(placeRoundedX, 
                              placeRoundedY, 
                              getVariable("activeBottomCargoLayer"), 
                              getVariable("activeLayerId"), 
                              minorGridSize, 
                              getVariable("activeLayerColor"), 
                              getVariable("placeHorizontal"), 
                              layerList)
                }
                else{ //Cargo placement
                    if(getVariable("pasteMode") == true){ //Paste cargo that has been copied
                        let cargoCounter = pasteCargo(getVariable("copiedCargo"), 
                                                      placeRoundedX,
                                                      placeRoundedY,
                                                      getVariable("activeCargoLayer"),
                                                      getVariable("activeLayerId"), 
                                                      minorGridSize,
                                                      getVariable("activeLayerColor"), 
                                                      shownCargoOpacity,
                                                      getVariable("cargoCounter"),
                                                      layerList,
                                                      top)
                        writeVariable("cargoCounter", cargoCounter)
                        writeVariable("pasteMode", false)
                        let oldShadowCargo = document.getElementById('shadow-copied-cargo')
                        if(oldShadowCargo){
                            oldShadowCargo.remove()
                        }
                    }
                    else{ //Place individual cargo
                        let cargoCounter = placeCargo(placeRoundedX, 
                            placeRoundedY, 
                            getVariable("activeCargoLayer"), 
                            getVariable("activeLayerId"), 
                            minorGridSize, 
                            getVariable("activeLayerColor"), 
                            shownCargoOpacity, 
                            getVariable("cargoCounter"), 
                            getVariable("selectedCargoId"), 
                            layerList, 
                            top) 
                        writeVariable("cargoCounter", cargoCounter)
                    }
                }
            }
        }        
    });

    // Change drawing mode
    const drawModeSelector = document.getElementById('palette-type-selector');
    drawModeSelector.addEventListener('change', function () {
        writeVariable("drawSlatCargoHandleMode", drawModeSelector.value);
        changePlacementMode(getVariable("drawSlatCargoHandleMode"), layerList)
    });

    // Change editing mode
    const drawButton = document.getElementById('draw-button')
    const eraseButton = document.getElementById('erase-button')
    const selectButton = document.getElementById('select-button')
    drawButton.classList.add('draw-erase-select-toggle-selected') //Set default mode to draw

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

    // Change grid mode
    const gridButton = document.getElementById('grid-button')
    const dotsButton = document.getElementById('dot-button')
    const blankButton = document.getElementById('blank-button')
    dotsButton.classList.add('grid-dots-blank-toggle-selected') //Set default mode to dots

    gridButton.addEventListener('click', (event)=>{
        gridButton.classList.add('grid-dots-blank-toggle-selected')
        dotsButton.classList.remove('grid-dots-blank-toggle-selected')
        blankButton.classList.remove('grid-dots-blank-toggle-selected')

        writeVariable("gridStyle", 1);
        drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize)
    })

    dotsButton.addEventListener('click', (event)=>{
        dotsButton.classList.add('grid-dots-blank-toggle-selected')
        gridButton.classList.remove('grid-dots-blank-toggle-selected')
        blankButton.classList.remove('grid-dots-blank-toggle-selected')

        writeVariable("gridStyle", 2);
        drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize)
    })

    blankButton.addEventListener('click', (event)=>{
        blankButton.classList.add('grid-dots-blank-toggle-selected')
        gridButton.classList.remove('grid-dots-blank-toggle-selected')
        dotsButton.classList.remove('grid-dots-blank-toggle-selected')

        writeVariable("gridStyle", 0);
        drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize)
    })
});


////////////////////////////////
// STANDALONE EVENT LISTENERS //
////////////////////////////////

// Toggle horizontal slat mode when ALT is pressed
document.addEventListener('keydown', (event) => {
    if( event.key === 'Alt') {
        if(getVariable("placeHorizontal") == false){
            // Remove any existing cursor slats with the id 'cursor-slat'
            let cursorSlat = document.getElementById('cursor-slat')
            if(cursorSlat){
                cursorSlat.remove()
            }
        }
        event.preventDefault();
        writeVariable("placeHorizontal", true);
    }
});

// Toggle vertical slat mode when ALT is not pressed
document.addEventListener('keyup', (event) => {
    if( event.key === 'Alt') {
        if(getVariable("placeHorizontal") == true){
            // Remove any existing cursor slats with the id 'cursor-slat'
            let cursorSlat = document.getElementById('cursor-slat')
            if(cursorSlat){
                cursorSlat.remove()
            }
        }
        writeVariable("placeHorizontal", false);
    }
});

// Copy cargo when ctrl + c is pressed
document.addEventListener('keydown', (event) => {
    if(event.ctrlKey && (event.key === 'c')) {
        console.log("Copy has been started!")

        const topLayerButton = document.getElementById('top-layer-selector')
        let top = topLayerButton.classList.contains('h25-toggle-selected')
        let copiedCargo = copyCargo(getLayerList(), top, getVariable("activeLayerId"), minorGridSize)
        writeVariable("copiedCargo", copiedCargo)
    }
});

// Paste cargo when ctrl + v is pressed
document.addEventListener('keydown', (event) => {
    if(event.ctrlKey && (event.key === 'v')) {
        writeVariable("pasteMode", true)
        console.log("Paste has been started!")
    }
});