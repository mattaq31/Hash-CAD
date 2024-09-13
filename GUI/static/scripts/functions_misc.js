import { getHandleLayerDict, updateHandleLayerButtons, updateHandleLayers } from './functions_handles.js';
import { populateHandleMatchPalette } from './functions_handle_matching.js';
import { populateCargoPalette } from './functions_inventory.js';
import { getVariable } from './variables.js';

/**
 * Function to change the drawing mode between slats, cargo, and handles
 * @param {Number} mode 0 corresponds to slat placement, 1 to cargo placement, 2 to handle placement
 * @param {Map} layerList Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 */
export function changePlacementMode(mode, layerList){
    const slatPalette = document.getElementById('slat-palette')
    const cargoPalette = document.getElementById('cargo-palette');
    const handlePalette = document.getElementById('handle-palette');

    slatPalette.style.display = 'none'
    handlePalette.style.display = 'none'
    cargoPalette.style.display = 'none'

    changeCursorEvents(getVariable("activeSlatLayer"),        'none')
    changeCursorEvents(getVariable("activeTopCargoLayer"),    'none')
    changeCursorEvents(getVariable("activeBottomCargoLayer"), 'none')
    changeCursorEvents(getVariable("activeHandleLayer"),      'none')

    if(mode == 0){ //Slat mode
        slatPalette.style.display = 'block'
        changeCursorEvents(getVariable("activeSlatLayer"), 'stroke')
    }
    else if (mode == 1) { // Cargo mode
        cargoPalette.style.display = 'block';
        populateCargoPalette(); 
        getHandleLayerDict(layerList)
        updateHandleLayerButtons(layerList, getVariable("activeLayerId"))
        if(getVariable("activeCargoLayer")){
            changeCursorEvents(getVariable("activeCargoLayer"), 'bounding-box')
        }
    } 
    else if(mode == 2){ //Handle mode
        handlePalette.style.display = 'block'
        getHandleLayerDict(layerList)
        updateHandleLayers(layerList)
        changeCursorEvents(getVariable("activeHandleLayer"), 'stroke')
        populateHandleMatchPalette(getVariable("matchGroupNumber"))
    }
}

/** 
 * Draw background grid on canvas (in the bottom-most layer)
 * @param {SVG.G} gridGroup Layer of SVG.js canvas corresponding to the grid - bottom layer.
 * @param {Number} width Width of SVG.js canvas
 * @param {Number} height Height of SVG.js canvas
 * @param {Number} style 0 corresponds to no grid, 1 to line grid, and 2  to dot grid
 * @param {Number} majorSize The major grid size. Ensure an integer multiple of minorSize
 * @param {Number} minorSize The snapping grid size. Corresponds to the distance between two handles. 
 * @returns {SVG.G} SVG group element containing grid
 */
export function drawGrid(gridGroup, width, height, style, majorSize, minorSize, diagAngle=45) {

    //Calculate appropriate scaling terms for x and y distances
    let minorSizeX = minorSize * Math.sin(diagAngle * (Math.PI / 180)) //0.86602540378
    let majorSizeX = majorSize * Math.sin(diagAngle * (Math.PI / 180)) //0.86602540378
    let minorSizeY = minorSize * Math.cos(diagAngle * (Math.PI / 180)) //0.5
    let majorSizeY = majorSize * Math.cos(diagAngle * (Math.PI / 180)) //0.5

    if(diagAngle == 45){
        minorSizeX = minorSize
        majorSizeX = majorSize
        minorSizeY = minorSize
        majorSizeY = majorSize
    }
    
    
    //First reset grid:
    gridGroup.clear()

    //Now draw the grid itself:
    if(style != 0){
        // Draw vertical lines
        //Minor
        for (var x = 0; x < width; x += minorSizeX ) {
            let tmpLine = gridGroup.line(x, 0, x, height).stroke({ width: 0.5, color:'#000'})
            if(style == 2){
                tmpLine.stroke({dasharray:`${minorSizeX*0.1},${minorSizeY - minorSizeX*0.1}`, dashoffset:`${minorSizeX*0.05}`})
            }
        }

        //Major
        for (var x = 0; x < width; x += majorSizeX ) {
            let tmpLine = gridGroup.line(x, 0, x, height).stroke({ width: 1, color:'#000' })
            if(style == 2){
                tmpLine.stroke({dasharray:`${majorSizeX*0.05},${majorSizeY - majorSizeX*0.05}`, dashoffset:`${majorSizeX*0.025}`})
            }
        }

        // Draw horizontal lines
        //Minor
        for (var y = 0; y < height; y += minorSizeY ) {
            let tmpLine = gridGroup.line(0, y, width, y).stroke({ width: 0.5, color:'#000'})
            if(style == 2){
                tmpLine.stroke({dasharray:`${minorSizeX*0.1},${minorSizeX*0.9}`, dashoffset:`${minorSizeX*0.05}`})
            }
        }

        //Major
        for (var y = 0; y < height; y += majorSizeY ) {
            let tmpLine = gridGroup.line(0, y, width, y).stroke({ width: 1, color:'#000' })
            if(style == 2){
                tmpLine.stroke({dasharray:`${majorSizeX*0.05},${majorSizeX*0.95}`, dashoffset:`${majorSizeX*0.025 }`})
            }
        }
    }
    
    return gridGroup;
}

/**
 * Function to change cursor event types for all elements of a particular layer
 * @param {SVG.G} layer Target layer
 * @param {String} type Type of pointer event to set for all children of target layer
 */
export function changeCursorEvents(layer, type){
    layer.children().forEach(child => {
        child.attr('pointer-events', type);
    });
}

/**
 * Function to download a file
 * @param {String} url URL of file to download
 * @param {String} filename Filename to set for file when downloaded
 */
export function downloadFile(url, filename) {
    fetch(url)
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Network response was not ok.');
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}




