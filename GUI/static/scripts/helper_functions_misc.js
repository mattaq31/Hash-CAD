///////////////////////////////
//       Grid Drawing        //
///////////////////////////////

/** Draw background grid on canvas (in the bottom-most layer)
 * 
 * @param gridGroup Layer of SVG.js canvas corresponding to the grid -- bottom layer.
 * @param width Width of SVG.js canvas
 * @param height Height of SVG.js canvas
 * @param style Integer: 0 corresponding to no grid, 1 corresponding to line grid, and 2 corresponding to dot grid
 * @param majorSize The major grid size. Make sure an integer multiple of minorSize
 * @param minorSize The snapping grid size. Corresponds to the distance between two handles. 
 * @returns {*}
 */
export function drawGrid(gridGroup, width, height, style, majorSize, minorSize) {
    
    //First reset grid:
    gridGroup.clear()

    //Now draw the grid itself:
    if(style != 0){
        // Draw vertical lines
        //Minor
        for (var x = 0; x < width; x += minorSize) {
            let tmpLine = gridGroup.line(x, 0, x, height).stroke({ width: 0.5, color:'#000'})
            if(style==2){
                tmpLine.stroke({dasharray:`${minorSize*0.1},${minorSize*0.9}`, dashoffset:`${minorSize*0.05}`})
            }
        }

        //Major
        for (var x = 0; x < width; x += majorSize) {
            let tmpLine = gridGroup.line(x, 0, x, height).stroke({ width: 1, color:'#000' })
            if(style==2){
                tmpLine.stroke({dasharray:`${majorSize*0.05},${majorSize*0.95}`, dashoffset:`${majorSize*0.025}`})
            }
        }

        // Draw horizontal lines
        //Minor
        for (var y = 0; y < height; y += minorSize) {
            let tmpLine = gridGroup.line(0, y, width, y).stroke({ width: 0.5, color:'#000'})
            if(style==2){
                tmpLine.stroke({dasharray:`${minorSize*0.1},${minorSize*0.9}`, dashoffset:`${minorSize*0.05}`})
            }
        }

        //Major
        for (var y = 0; y < height; y += majorSize) {
            let tmpLine = gridGroup.line(0, y, width, y).stroke({ width: 1, color:'#000' })
            if(style==2){
                tmpLine.stroke({dasharray:`${majorSize*0.05},${majorSize*0.95}`, dashoffset:`${majorSize*0.025}`})
            }
        }
    }
    
    
    return gridGroup;
  }







///////////////////////////////
//  Custom Events for Server //
///////////////////////////////

// Function to dispatch custom events
// TODO: seems like this is not used - can it be removed?
function dispatchServerEvent(eventName, eventItem) {
    const event = new CustomEvent(eventName, {detail: eventItem});
    document.dispatchEvent(event);
}




function updateHandleLayers(layerList){

    const handleLayers = document.getElementById('handle-layers')

    layers.forEach((layer, layerIndex) => {
        layer[2].children().forEach(child => {
            let cargoId = child.attr('type');
            let bbox = child.bbox();
            
            let centerX = Math.round((bbox.x + bbox.width / 2) / minorGridSize);
            let centerY = Math.round((bbox.y + bbox.height/ 2) / minorGridSize);

            // Populate the grid dictionary with the cargo ID for the occupied positions
            let key = gridKey(centerX, centerY, layerIndex);
            gridDict[key] = cargoId;
        });
    });

}