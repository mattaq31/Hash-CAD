///////////////////////////////
//       Drag and Drop       //
///////////////////////////////


import { isLineOnLine,  isCargoOnCargo } from './helper_functions_overlap.js';

let dragOffset = { x: 0, y: 0 };    //Offset between mouse position and item position
let handleDrag = null;              //Function to call when a drag event is happening
let selectedColor = '#69F5EE'




/** Function to return active layer -- in particular, the active SVG.js layer group
 * 
 * @param layerList  List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @returns {{fullLayer: *}|null}
 */
export function getActiveLayer(layerList) {
    const activeRadio = document.querySelector('input[name="active-layer"]:checked');
    if (activeRadio) {
        const activeLayer = activeRadio.parentElement;
        let layerId = activeLayer.dataset.layerId
        
        //console.log('get active layer')
        //console.log(layerList)
        //console.log(layerId)
        
        const fullLayer = layerList.get(layerId)
        return {
            fullLayer
            //layerId: activeLayer.dataset.layerId,
            //layerElement: activeLayer
        };
    }
    return null;
}

/** Function to find what editting mode the program is currently set to
 * 
 * @returns {*|null}
 */
function getSelectedEditMode() {
    var editModeRadios = document.querySelectorAll('input[name="editMode"]');
    for (const radio of editModeRadios) {
        if (radio.checked) {
            return radio.value;
        }
    }
    return null; // Return null if no radio button is selected
}


/** Function for interactions with elements. 
 * In particular, deals with initiating drag, selecting, and erasing. 
 * When assigned as an event function, will add draggability (& selectability, erasability) to an element.
 * 
 * @param event Event associated with the initiation of a drag/interaction
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 */
export function startDrag(event, layerList, minorGridSize) {

    let drawEraseSelectMode = getSelectedEditMode()

    let activeLayer = null

    let drawModeSelector = document.getElementById('palette-type-selector');
    let drawSlatCargoHandleMode = drawModeSelector.value;

    if(drawSlatCargoHandleMode == 0){
        activeLayer = getActiveLayer(layerList).fullLayer[1]
    } else if(drawSlatCargoHandleMode == 1){

        let topCargoButton = document.getElementById('top-layer-selector')
        let bottomCargoButton = document.getElementById('bottom-layer-selector')
        
        if(topCargoButton.classList.contains('h25-toggle-selected')){
            activeLayer = getActiveLayer(layerList).fullLayer[3]
        }
        else if(bottomCargoButton.classList.contains('h25-toggle-selected')){
            activeLayer = getActiveLayer(layerList).fullLayer[2]
        }

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

/** Function for moving draggable elements, while making sure they comply with snapgrid
 * 
 * @param event Event associated with the initiation of a drag
 * @param layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param selectedElement Element to be dragged
 * @param minorGridSize The snapping grid size. Corresponds to the distance between two handles. 
 */
export function drag(event, layerList, selectedElement, minorGridSize) {

    let activeLayer = null

    let drawModeSelector = document.getElementById('palette-type-selector');
    let drawSlatCargoHandleMode = drawModeSelector.value;

    if(drawSlatCargoHandleMode == 0){
        activeLayer = getActiveLayer(layerList).fullLayer[1]
    } else if(drawSlatCargoHandleMode == 1){
        
        let topCargoButton = document.getElementById('top-layer-selector')
        let bottomCargoButton = document.getElementById('bottom-layer-selector')
        
        if(topCargoButton.classList.contains('h25-toggle-selected')){
            activeLayer = getActiveLayer(layerList).fullLayer[3]
        }
        else if(bottomCargoButton.classList.contains('h25-toggle-selected')){
            activeLayer = getActiveLayer(layerList).fullLayer[2]
        }
        
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


/** End drag and leave element in its final (snapped) position
 * 
 */
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

