//Functions
import { placeSlat, placeCargo, placeSeed, showSlat, getFullDrawing, undo, placeHandleMatcher } from './functions_drawing.js';
import { copyCargo, showCopiedCargo, pasteCargo } from './functions_copypaste.js';
import { getPanStatus, configurePanzoom } from './functions_panzoom.js'
import { showCopiedMatchers, pasteMatchers } from './functions_handle_matching.js';
import { drawGrid, changePlacementMode } from './functions_misc.js';
import { getLayerList } from './functions_layers.js'


//Constants & Variables
import {minorGridSize, majorGridSize, shownOpacity, shownCargoOpacity, shownHandleMatchOpacity } from './constants.js'
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
        else if(getVariable("placeMatchers") == true){
            showCopiedMatchers(getVariable("matcherDict"), placeRoundedX, placeRoundedY, fullDrawing, minorGridSize)        
        }
        else{
            let slatCountToPlace = document.getElementById('slatNumber').value
            showSlat(mousePoints.x, mousePoints.y, fullDrawing, minorGridSize, getVariable("placeHorizontal"), slatCountToPlace)
        }
    });

    // Handle clicks 
    svgcontainer.addEventListener('pointerdown', (event) => {

        let eraseMode = document.getElementById('erase-button').classList.contains('draw-erase-select-toggle-selected')
    
        if(getPanStatus() == true && !eraseMode){
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
            else if(getVariable("drawSlatCargoHandleMode") == 2){
                if(getVariable("placeMatchers") == true){
                    writeVariable("placeMatchers", false)
                    pasteMatchers(getVariable("matcherDict"), 
                                  getVariable("handleMatchGroup"), 
                                  placeRoundedX, 
                                  placeRoundedY, 
                                  getVariable("activeHandleLayer"), 
                                  getVariable("activeLayerId"), 
                                  minorGridSize, 
                                  getVariable("activeLayerColor"), 
                                  shownHandleMatchOpacity, 
                                  layerList)

                }
                else{
                    let handleMatchCounter = placeHandleMatcher(placeRoundedX,
                                                                placeRoundedY, 
                                                                getVariable("activeHandleLayer"), 
                                                                getVariable("activeLayerId"), 
                                                                minorGridSize, 
                                                                getVariable("activeLayerColor"), 
                                                                shownHandleMatchOpacity, 
                                                                getVariable("handleMatchCounter"), 
                                                                getVariable("handleMatchGroup"), 
                                                                layerList,
                                                                true)

                    writeVariable("handleMatchCounter", handleMatchCounter)
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
        drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize, getVariable("gridAngle"))
    })

    dotsButton.addEventListener('click', (event)=>{
        dotsButton.classList.add('grid-dots-blank-toggle-selected')
        gridButton.classList.remove('grid-dots-blank-toggle-selected')
        blankButton.classList.remove('grid-dots-blank-toggle-selected')

        writeVariable("gridStyle", 2);
        drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize, getVariable("gridAngle"))
    })

    blankButton.addEventListener('click', (event)=>{
        blankButton.classList.add('grid-dots-blank-toggle-selected')
        gridButton.classList.remove('grid-dots-blank-toggle-selected')
        dotsButton.classList.remove('grid-dots-blank-toggle-selected')

        writeVariable("gridStyle", 0);
        drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize, getVariable("gridAngle"))
    })

    //Change grid angle
    const grid60Button = document.getElementById('button-60')
    const grid90Button = document.getElementById('button-90')
    grid90Button.classList.add('grid-angle-toggle-selected')

    grid60Button.addEventListener('click', (event)=>{
        grid60Button.classList.add('grid-angle-toggle-selected')
        grid90Button.classList.remove('grid-angle-toggle-selected')

        writeVariable("gridAngle", 60)
        drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize, getVariable("gridAngle"))
    })

    grid90Button.addEventListener('click', (event)=>{
        grid90Button.classList.add('grid-angle-toggle-selected')
        grid60Button.classList.remove('grid-angle-toggle-selected')

        writeVariable("gridAngle", 45)
        drawGrid(drawGridLayer, width, height, getVariable("gridStyle"), majorGridSize, minorGridSize, getVariable("gridAngle"))
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

// Undo when ctrl + z is pressed
document.addEventListener('keydown', (event) => {
    if(event.ctrlKey && (event.key === 'z')) {
        undo()
        console.log("Undo")
    }
});


// Toggle erase mode when "e" is pressed
document.addEventListener('keydown', (event) => {
    if(event.key === 'e') {
        const eraseButton = document.getElementById('erase-button')
        eraseButton.click()
        console.log("Toggled erase mode")
    }
});

// Toggle draw mode when "d" is pressed
document.addEventListener('keydown', (event) => {
    if(event.key === 'd') {
        const drawButton = document.getElementById('draw-button')
        drawButton.click()
        console.log("Toggled draw mode")
    }
});

// Toggle select mode when "s" is pressed
document.addEventListener('keydown', (event) => {
    if(event.key === 's') {
        const selectButton = document.getElementById('select-button')
        selectButton.click()
        console.log("Toggled select mode")
    }
});

// Toggle slat mode when "S" is pressed
document.addEventListener('keydown', (event) => {
    if(event.key === 'S') {
        const drawModeSelector = document.getElementById('palette-type-selector');
        drawModeSelector.value = 0
        drawModeSelector.dispatchEvent(new Event('change'))
        console.log("Toggled slat mode")
    }
});

// Toggle slat mode when "C" is pressed
document.addEventListener('keydown', (event) => {
    if(event.key === 'C') {
        const drawModeSelector = document.getElementById('palette-type-selector');
        drawModeSelector.value = 1
        drawModeSelector.dispatchEvent(new Event('change'))
        console.log("Toggled cargo mode")
    }
});

// Toggle slat mode when "H" is pressed
document.addEventListener('keydown', (event) => {
    if(event.key === 'H') {
        const drawModeSelector = document.getElementById('palette-type-selector');
        drawModeSelector.value = 2
        drawModeSelector.dispatchEvent(new Event('change'))
        console.log("Toggled handle mode")
    }
});

// Add layer when "+" is pressed
document.addEventListener('keydown', (event) => {
    if(event.key === '+') {
        const addLayerButton = document.getElementById('add-layer');
        addLayerButton.click()
        console.log("Added new layer via shortcut")
    }
});
