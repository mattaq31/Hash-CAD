/** Check if a point on the SVG canvas (in a specific layer) is on any existing lines 
 *
 * @param Layer The selected layer on the SVG canvas
 * @param x The X-coordinate to check
 * @param y The Y-coordinate to check
 * @param selectedLine If moving a line, the selected line. Prevents self-overlaps from being counted.
 * @returns {boolean}
 */
export function isPointOnLine(Layer, x, y, selectedLine = false) {
    //First chedk if on seed:
    let seed = Layer.find('.seed')

    let onSeed = false;
    if(seed.length != 0){
        console.log("Seed: ", seed)
        const seedBbox = seed.bbox()[0];
        onSeed = (x >= seedBbox.x && x <= seedBbox.x2 && y >= seedBbox.y && y <= seedBbox.y2)
    }

    const lines = Layer.find('.line');
    return lines.some(line => {
      
      //Check if overlapping with any lines in general
        const bbox = line.bbox();
        let onOther = (x >= bbox.x && x <= bbox.x2 && y >= bbox.y && y <= bbox.y2)
      
      //Check if overlapping with self (but only if a self is given!)
        let selfBbox = null;
        let onItself = false
        if(selectedLine){
            selfBbox = selectedLine.bbox();
            onItself = (x >= selfBbox.x && x <= selfBbox.x2 && y >= selfBbox.y && y <= selfBbox.y2)
        }
      
      return (
        onOther && (!onItself) || onSeed
      );
    });
  }

/** Check if a line on the SVG canvas (in a specific layer) would overlap with any existing lines (for dragging)
 *
 * @param startX The starting X-coordinate to test a line from
 * @param startY The starting Y-coordinate to test a line from
 * @param layer The selected layer on the SVG canvas
 * @param GridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param selectedLine The selected line element
 * @returns {boolean}
 */
export function isLineOnLine(startX, startY, layer, GridSize, selectedLine) {
    const x1 = selectedLine.attr('x1');
    const y1 = selectedLine.attr('y1');
    const x2 = selectedLine.attr('x2');
    const y2 = selectedLine.attr('y2');

    let dX = x2-x1;
    let dY = y2-y1

    const lineLength = Math.sqrt(dX * dX + dY * dY)
    const numPoints = Math.floor(lineLength/GridSize)

    let overlap = false

    for (let i = 0; i<= numPoints; i++) {
        const ratio = i / numPoints;
        let x = startX + ratio * dX
        let y = startY + ratio * dY
        overlap = overlap || isPointOnLine(layer, x, y, selectedLine)
    }

    return overlap


}

/** Check if a vertically drawn line would overlap with any existing lines
 * 
 * @param startX The starting (top left) X-coordinate from which to draw the line
 * @param startY The starting (top left) Y-coordinate from which to draw the line
 * @param layer The selected layer on the SVG canvas
 * @param gridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param length The length of one slat, as number of handles. ie 32 handles
 * @returns {boolean}
 */
export function willVertBeOnLine(startX, startY, layer, gridSize, length=32){
    let overlap = false
    for (let i = 0; i<= length; i++) {
        let x = startX 
        let y = startY + i*gridSize
        overlap = overlap || isPointOnLine(layer, x, y)
    }
    return overlap
}

/** Check if a vertically drawn line would overlap with any existing lines
 * 
 * @param startX The starting (top left) X-coordinate from which to draw the line
 * @param startY The starting (top left) Y-coordinate from which to draw the line
 * @param layer The selected layer on the SVG canvas
 * @param gridSize The snapping grid size. Corresponds to the distance between two handles. 
 * @param length The length of one slat, as number of handles. ie 32 handles
 * @returns {boolean}
 */
export function willHorzBeOnLine(startX, startY, layer, gridSize, length=32){
    let overlap = false
    for (let i = 0; i<= length; i++) {
        let x = startX + i*gridSize
        let y = startY 
        overlap = overlap || isPointOnLine(layer, x, y)
    }
    return overlap
}


/** Check if a new cargo would overlap with any existing cargo
 * 
 *
 * @param x The X-coordinate of the cargo
 * @param y The Y-coordinate of the cargo
 * @param layer The selected layer on the SVG canvas
 * @param selectedPoint If moving a cargo, the initial point. Prevents self-overlaps from being counted.
 * @returns {*}
 */
export function isCargoOnCargo(x, y, layer, selectedPoint = false){
    const cargos = layer.find('.cargo');
    return cargos.some(cargo => {
      
        //Check if overlapping with any lines in general
        const bbox = cargo.bbox();
        let onOther = (x >= bbox.x && x <= bbox.x2 && y >= bbox.y && y <= bbox.y2)

        //Check if overlapping with itself
        let onItself = false
        if(selectedPoint){
            const selfBbox = selectedPoint.bbox();
            onItself = (x >= selfBbox.x && x <= selfBbox.x2 && y >= selfBbox.y && y <= selfBbox.y2)
        }

        let cargoOnSeed = isCargoOnSeed(x, y, layer)
      
        return (
            (onOther && (!onItself) || cargoOnSeed)
        );
    });
}




export function isCargoOnSeed(x, y, layer){
    const seed = layer.find('.seed');
    if(seed.length != 0){
        const bbox = seed.bbox()[0];
        let overlapping = (x >= bbox.x && x <= bbox.x2 && y >= bbox.y && y <= bbox.y2)

        return overlapping
    }
    else{
        return false
    }
    
}

export function wasSeedOnCargo(layer){
    const cargos = layer.find('.cargo');
    return cargos.some(cargo => {
      
        //Check if overlapping with any cargo in general
        const bbox = cargo.bbox();
        const xPos = (bbox.x + bbox.x2)/2
        const yPos = (bbox.y + bbox.y2)/2
        let onOther = isCargoOnSeed(xPos, yPos, layer)

        return onOther
    });
}