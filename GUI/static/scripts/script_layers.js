import { updateHandleLayers, updateHandleLayerButtons, getHandleLayerDict } from './functions_handles.js';
import { addLayer, getLayerList } from './functions_layers.js'
import { getFullDrawing } from './functions_drawing.js';
import { changeCursorEvents} from './functions_misc.js';
import { delete3DSlatLayer } from './functions_3D.js';

import { hiddenOpacity} from './constants.js'
import { getVariable, writeVariable } from './variables.js'

let layerList = getLayerList()

document.addEventListener('DOMContentLoaded', () => {
    const addLayerButton = document.getElementById('add-layer');
    addLayerButton.addEventListener('click', () => {
        addLayer();
    });

    // Add initial layers
    addLayer();
    addLayer();
});



// Respond to "layerAdded" event
document.addEventListener('layerAdded', (event) => {
    let fullDrawing = getFullDrawing()

    console.log(`Layer added: ${event.detail.layerId}`, event.detail.layerElement);
    
    //This order of assignment ensures proper ordering of layers
    let bottomCargoGroup = fullDrawing.group();
    let slatGroup = fullDrawing.group();
    let topCargoGroup = fullDrawing.group();
    let handleGroup = fullDrawing.group();

    const tmpFullLayer = [handleGroup, slatGroup, bottomCargoGroup, topCargoGroup, event.detail.layerColor];

    layerList.set(event.detail.layerId, tmpFullLayer)
    updateHandleLayers(layerList)
    getHandleLayerDict(layerList)
});

// Responds to "layerShown" event
document.addEventListener('layerShown', (event) => {
    console.log(`Layer shown: ${event.detail.layerId}`, event.detail.layerElement);
    const fullLayer = layerList.get(event.detail.layerId)
    fullLayer[0].attr('opacity',1)
    fullLayer[1].attr('opacity',1)
    fullLayer[2].attr('opacity',1)
    fullLayer[3].attr('opacity',1)
});

// Responds to "layerHidden" event
document.addEventListener('layerHidden', (event) => {
    console.log(`Layer hidden: ${event.detail.layerId}`, event.detail.layerElement);
    const fullLayer = layerList.get(event.detail.layerId)
    fullLayer[0].attr('opacity', hiddenOpacity)
    fullLayer[1].attr('opacity', hiddenOpacity)
    fullLayer[2].attr('opacity', hiddenOpacity)
    fullLayer[3].attr('opacity', hiddenOpacity)
});

// Respond to "layerRemoved" event
document.addEventListener('layerRemoved', (event) => {
    console.log(`Layer removed: ${event.detail.layerId}`, event.detail.layerElement);
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

// Respond to "layerColorChanged" event
document.addEventListener('layerColorChanged', (event) => {
    const layerId = event.detail.layerId;
    const layerColor = event.detail.layerColor;
    const fullLayer = layerList.get(event.detail.layerId)

    //Change color attribute of layer element
    fullLayer[4] = layerColor
    updateHandleLayers(layerList)

    //Change slat colors on layer
    const layerToChangeSlats = fullLayer[1]
    layerToChangeSlats.children().forEach(child => {
        child.stroke({ color: layerColor });
        child.attr('data-default-color', layerColor); 
    });

    //Change top cargo colors on layer
    const layerToChangeTopCargo = fullLayer[3] 
    layerToChangeTopCargo.children().forEach(child => {
        child.children().forEach(childChild => {
            if(childChild.attr('data-cargo-component') === 'shape'){
                childChild.stroke({ color: layerColor });
                childChild.attr('data-default-color', layerColor);
            }
        })
    });

    //Change bottom cargo colors on layer
    const layerToChangeBottomCargo = fullLayer[2] 
    layerToChangeBottomCargo.children().forEach(child => {
        child.children().forEach(childChild => {
            if(childChild.attr('data-cargo-component') === 'shape'){
                childChild.stroke({ color: layerColor });
                childChild.attr('data-default-color', layerColor); 
            }
        })
    });

    //Set active layer color if necessary
    if(layerId == getVariable("activeLayerId")){
        writeVariable("activeLayerColor", layerColor)
    }
});

// Respond to "layerMarkedActive" event
document.addEventListener('layerMarkedActive', (event) => {
    console.log(`Layer marked active: ${event.detail.layerId}`, event.detail.layerElement);
    writeVariable("activeLayerId", event.detail.layerId)
    layerList = getLayerList()
    const fullLayer = layerList.get(event.detail.layerId)
    
    //Remove pointer events from all layers!
    layerList.forEach((layer, layerIndex) => {
        changeCursorEvents(layer[0], 'none')
        changeCursorEvents(layer[1], 'none')
        changeCursorEvents(layer[2], 'none')
        changeCursorEvents(layer[3], 'none')
    });
    
    //Assign proper sublayers to active variables
    let activeHandleLayer = writeVariable("activeHandleLayer", fullLayer[0])
    let activeSlatLayer   = writeVariable("activeSlatLayer", fullLayer[1])
    let activeBottomCargoLayer  = writeVariable("activeBottomCargoLayer", fullLayer[2])
    let activeTopCargoLayer     = writeVariable("activeTopCargoLayer", fullLayer[3])
    let activeCargoLayer = null;

    //Check if top or bottom cargo layer is selected
    const topLayerButton = document.getElementById('top-layer-selector')
    const bottomLayerButton = document.getElementById('bottom-layer-selector')
    if(topLayerButton.classList.contains('h25-toggle-selected')){
        activeCargoLayer = getVariable("activeTopCargoLayer")
    }
    else if(bottomLayerButton.classList.contains('h25-toggle-selected')){
        activeCargoLayer = getVariable("activeBottomCargoLayer")
    }

    //Assign proper sublayer to active cargo variable
    writeVariable("activeCargoLayer", activeCargoLayer)

    //Reset cursors on all layers
    changeCursorEvents(activeSlatLayer, 'none')
    changeCursorEvents(activeTopCargoLayer, 'none')
    changeCursorEvents(activeBottomCargoLayer, 'none')
    changeCursorEvents(activeHandleLayer, 'none')
    if(activeCargoLayer){
        changeCursorEvents(activeCargoLayer, 'none')
    }
    
    //Configure cursor to match drawing mode
    const drawSlatCargoHandleMode = document.getElementById('palette-type-selector').value;
    if(drawSlatCargoHandleMode == 0){ //Slat mode
        changeCursorEvents(activeSlatLayer, 'stroke')
    }
    else if (drawSlatCargoHandleMode == 1) { // Cargo mode
        if(activeCargoLayer){
            changeCursorEvents(activeCargoLayer, 'bounding-box')
        }
    } 
    else if(drawSlatCargoHandleMode == 2){
        changeCursorEvents(activeHandleLayer, 'stroke')
    }

    //Update active layer color
    writeVariable("activeLayerColor", event.detail.layerColor)

    //Update handle layer buttons
    updateHandleLayerButtons(layerList, getVariable("activeLayerId"))
});