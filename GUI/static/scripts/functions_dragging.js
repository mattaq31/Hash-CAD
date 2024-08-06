import { isLineOnLine,  isCargoOnCargo } from './functions_overlap.js';
import { delete3DElement, move3DSlat, move3DCargo, move3DSeed} from './functions_3D.js';

let dragOffset = { x: 0, y: 0 };    //Offset between mouse position and item position
let handleDrag = null;              //Function to call when a drag event is happening
let selectedColor = '#69F5EE'

/** 
 * Function to return active layer
 * @param layerList  List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @returns {{fullLayer: Array}|null} Array of sublayers for active layer [handles, slats, bottomCargo, topCargo, color]
 */
export function getActiveFullLayer(layerList) {
    const activeRadio = document.querySelector('input[name="active-layer"]:checked');
    if (activeRadio) {
        const activeLayer = activeRadio.parentElement;
        let layerId = activeLayer.dataset.layerId
        
        const fullLayer = layerList.get(layerId)
        return {
            fullLayer
        };
    }
    return null;
}

/**
 * Function to return active sublayer
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @returns {SVG.G} SVG Group element corresponding to active sublayer of active layer (ie cargoLayer, HandleLayer, etc) 
 */
function getActiveSublayer(layerList){
    let drawModeSelector = document.getElementById('palette-type-selector');
    let drawSlatCargoHandleMode = drawModeSelector.value; //0 for slats, 1 for cargo, 2 for handles

    let fullLayer = getActiveFullLayer(layerList)
    let activeLayer = null

    if(drawSlatCargoHandleMode == 0){
        activeLayer = fullLayer.fullLayer[1]
    } 
    else if(drawSlatCargoHandleMode == 1){
        let topCargoButton = document.getElementById('top-layer-selector')
        let bottomCargoButton = document.getElementById('bottom-layer-selector')
        
        if(topCargoButton.classList.contains('h25-toggle-selected')){
            activeLayer = fullLayer.fullLayer[3]
        }
        else if(bottomCargoButton.classList.contains('h25-toggle-selected')){
            activeLayer = fullLayer.fullLayer[2]
        }
    } 
    else if(drawSlatCargoHandleMode == 2){
        activeLayer = fullLayer.fullLayer[0]
    }

    return activeLayer
}

/** 
 * Function to identify current editing mode
 * @returns {Number|null} 0 for drawing, 1 for erasing, 2 for selecting, null for none
 */
function getSelectedEditMode() {
    const drawButton = document.getElementById('draw-button')
    const eraseButton = document.getElementById('erase-button')
    const selectButton = document.getElementById('select-button')

    if(drawButton.classList.contains('draw-erase-select-toggle-selected')){
        return 0
    }
    else if(eraseButton.classList.contains('draw-erase-select-toggle-selected')){
        return 1
    }
    else if(selectButton.classList.contains('draw-erase-select-toggle-selected')){
        return 2
    }
    else{
        return null
    }
}

/** 
 * Function for interactions with elements. 
 * In particular, deals with initiating drag, selecting, and erasing. 
 * When assigned as an event function, will add draggability (& selectability, erasability) to an element.
 * 
 * @param event Event associated with the initiation of a drag/interaction
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 */
export function startDrag(event, layerList, minorGridSize) {
    let drawEraseSelectMode = getSelectedEditMode() //0 for drawing, 1 for erasing, 2 for selecting

    let activeLayer = getActiveSublayer(layerList)
    let dragSelectedElement = event.target.instance;

    console.log("Draw-erase-select mode is set to: "+drawEraseSelectMode+"with element: "+dragSelectedElement)

    if(activeLayer.children().includes(dragSelectedElement)){
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
            delete3DElement(dragSelectedElement)
            dragSelectedElement.remove()
            event.stopPropagation(); //needed or else delete doesn't work... oh well!
        }
        else if(drawEraseSelectMode == 2){ //Selecting!
            //check if selected already
            var checkSelected = dragSelectedElement.hasClass("selected")
            if(!checkSelected){
                dragSelectedElement.addClass("selected");
                //Change color
                if(dragSelectedElement.hasClass("cargo")){
                    dragSelectedElement.children()[0].attr({stroke: selectedColor})
                }
                else{
                    dragSelectedElement.attr({stroke: selectedColor})
                }
            }
            else if(checkSelected){
                dragSelectedElement.removeClass("selected");

                if(dragSelectedElement.hasClass("cargo")){
                    console.log("drag selected element: ", dragSelectedElement)
                    let unselectedColor = dragSelectedElement.children()[0].attr('data-default-color')
                    dragSelectedElement.children()[0].attr({stroke: unselectedColor})
                }
                else{
                    let unselectedColor = dragSelectedElement.attr('data-default-color'); 
                    dragSelectedElement.attr({stroke: unselectedColor})
                }                
            }
        } 
    }
}

/** 
 * Function for moving draggable elements, while making sure they comply with snapgrid
 * @param event Event associated with the initiation of a drag
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param selectedElement Element to be dragged
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 */
export function drag(event, layerList, selectedElement, minorGridSize) {

    let activeLayer = getActiveSublayer(layerList)    

    if (selectedElement) {
        let point = selectedElement.point(event.clientX, event.clientY) 
        point.x = point.x - dragOffset.x
        point.y = point.y - dragOffset.y
        let roundedX = Math.round(point.x/(minorGridSize))*minorGridSize ;
        let roundedY = Math.round(point.y/(minorGridSize))*minorGridSize ; 

        let drawModeSelector = document.getElementById('palette-type-selector');
        let drawSlatCargoHandleMode = drawModeSelector.value;
        
        if(drawSlatCargoHandleMode == 0){ //Slat Mode!
            if(!isLineOnLine(roundedX, roundedY, activeLayer, minorGridSize, selectedElement)) {
                let moveOffset = 0.5 * minorGridSize
                let isHorizontal = selectedElement.attr('data-horizontal')
                
                if(isHorizontal=='true'){ //for some reason, converting to string. Not sure why, but this does the job for now
                    selectedElement.move(roundedX-moveOffset, roundedY);

                    let slatToMoveId = selectedElement.attr('id')
                    let x3D = (roundedX - moveOffset)/minorGridSize
                    let y3D = roundedY/minorGridSize
                    let layerNum = selectedElement.attr('layer')

                    move3DSlat(slatToMoveId, x3D, y3D, layerNum, true, 32)
                    console.log("moving a horizontal element")
                }
                else {
                    selectedElement.move(roundedX, roundedY-moveOffset);
                    let slatToMoveId = selectedElement.attr('id')
                    let x3D = roundedX/minorGridSize
                    let y3D = (roundedY - moveOffset)/minorGridSize
                    let layerNum = selectedElement.attr('layer')

                    move3DSlat(slatToMoveId, x3D, y3D, layerNum, false, 32)
                    console.log("moving a vertical element")
                }
                
            }
        }
        else if(drawSlatCargoHandleMode == 1){
            if(selectedElement.attr('class') == "seed"){
                let isHorizontal = selectedElement.attr('data-horizontal')

                if(isHorizontal == 'true'){
                    selectedElement.move(roundedX + minorGridSize/2, roundedY - minorGridSize/2);

                    let x3D = roundedX/minorGridSize + 0.5
                    let y3D = roundedY/minorGridSize + 15.5
                    let layerNum = selectedElement.attr('layer')
                    move3DSeed(x3D, y3D, layerNum)
                }
                else{
                    selectedElement.move(roundedX, roundedY - minorGridSize/2);
                    let x3D = roundedX/minorGridSize + 1
                    let y3D = roundedY/minorGridSize
                    let layerNum = selectedElement.attr('layer')
                    move3DSeed(x3D, y3D, layerNum)
                }
            }
            else{
                if(!isCargoOnCargo(roundedX, roundedY, activeLayer, selectedElement)) {
                    let bbox = selectedElement.bbox();
                    let xOffset = bbox.width / 2
                    let yOffset = bbox.height / 2
                    selectedElement.move(roundedX-xOffset, roundedY-yOffset)
    
                    let cargoToMoveId = selectedElement.attr('id')
                    let x3D = (roundedX)/minorGridSize
                    let y3D = (roundedY)/minorGridSize
                    let layerNum = selectedElement.attr('layer')
                    move3DCargo(cargoToMoveId, x3D, y3D, layerNum, true, 0.5)
                }
            }
        }
    }
}

/**
 * Function to end dragging
 */
export function endDrag() {
    
    console.log("Dragging ended!")
    //dragSelectedElement = null;
    dragOffset.x = 0
    dragOffset.y = 0

    // Remove event listeners for drag and end drag
    document.removeEventListener('pointermove', handleDrag);
    document.removeEventListener('pointerup', endDrag);
  }

