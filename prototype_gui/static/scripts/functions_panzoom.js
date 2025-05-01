let disablePanStatus = true; 

/**
 * Checks whether pan is currently enabled or disabled
 * @returns {Boolean} True if pan is disabled. False otherwise
 */
export function getPanStatus(){
    return disablePanStatus
}

/**
 * Configured pan and zoom capabilities for the target element
 * @param {div} target Container upon which to apply panzoom capabilities
 * @returns {Panzoom} Created panzoom object
 */
export function configurePanzoom(target){
    let width = target.getBoundingClientRect().width
    let height = target.getBoundingClientRect().height

    //Create panzoom object
    const panzoom = Panzoom(target, {
        maxScale: 5,
        minScale: 0.25,
        contain: "outside",
        cursor: "crosshair"
      })
    
    //Initial setup: Zoom & Pan
    setTimeout(() => {
        panzoom.pan(-width/4,-height/4);
        panzoom.setOptions({ disablePan: disablePanStatus });
        panzoom.zoom(2)
    });
    
    //Allow zoom with touchpad
    target.parentElement.addEventListener('wheel', panzoom.zoomWithWheel)

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

    return panzoom
}