import { placeHandleMatcher } from "./functions_drawing.js";

export function populateHandleMatchPalette(numberOfMatchGroups) {

    const handleMatchOptions = document.getElementById('handle-match-options');
    handleMatchOptions.innerHTML = ''; // Clear existing options
 
    // Calculate 1/5th of the parent's width
    const paletteWidth = handleMatchOptions.offsetWidth;
    const optionWidth = paletteWidth / 2.3;
    const optionHeight = paletteWidth / 7
    console.log("Palette width is measured as: ", paletteWidth)

    for (let i = 0; i < numberOfMatchGroups; i++) {
        const optionSource = document.createElement('div');
        optionSource.className = 'handle-match-option';
        optionSource.style.width = `${optionWidth}px`;
        optionSource.style.height = `${optionHeight}px`;
        optionSource.style.backgroundColor = 'lightgrey';
        optionSource.style.borderRadius = '5px'
        optionSource.dataset.id = i;
        optionSource.dataset.source = true;
        optionSource.title = "source: " + i;

        const optionTarget = document.createElement('div');
        optionTarget.className = 'handle-match-option';
        optionTarget.style.width = `${optionWidth}px`;
        optionTarget.style.height = `${optionHeight}px`;
        optionTarget.style.backgroundColor = 'lightgrey';
        optionTarget.style.borderRadius = '5px'
        optionTarget.dataset.id = i;
        optionTarget.dataset.source = false;
        optionTarget.title = "target: " + i;

        const drawSource = SVG().addTo(optionSource).size(optionWidth, optionHeight);
        const drawTarget = SVG().addTo(optionTarget).size(optionWidth, optionHeight);

        drawSource.attr('pointer-events', 'none')
        let radius = optionHeight * 0.33
        drawSource.circle(radius * 2).attr({
            cx: optionWidth * 0.75,
            cy: optionHeight * 0.5,
            fill: 'grey',
            stroke: 'black'
        });

        drawTarget.attr('pointer-events', 'none')
        let width = optionHeight * 0.66
        drawTarget.rect(width, width)
                  .move(optionWidth * 0.75 - width * 0.5, optionHeight * 0.5 - width * 0.5)
                  .fill('grey') 
                  .stroke('black') 

        let textSourceNumber = drawSource.text("" + i)
                             .attr({x: optionWidth * 0.75, y: optionHeight * 0.55, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
                             .font({size: optionHeight * 0.4, family: 'Arial', weight: 'bold'})
                             .fill('#000000')
                             .attr('pointer-events', 'none');

        let textTargetNumber = drawTarget.text("" + i)
                             .attr({x: optionWidth * 0.75, y: optionHeight * 0.55, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
                             .font({size: optionHeight * 0.4, family: 'Arial', weight: 'bold'})
                             .fill('#000000')
                             .attr('pointer-events', 'none');

        let textSource = drawSource.text("Source: ")
                             .attr({x: optionWidth * 0.33, y: optionHeight * 0.55, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
                             .font({size: optionHeight * 0.4, family: 'Arial', weight: 'bold'})
                             .fill('#000000')
                             .attr('pointer-events', 'none');

        let textTarget = drawTarget.text("Target: ")
                             .attr({x: optionWidth * 0.3, y: optionHeight * 0.55, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
                             .font({size: optionHeight * 0.4, family: 'Arial', weight: 'bold'})
                             .fill('#000000')
                             .attr('pointer-events', 'none');

        handleMatchOptions.appendChild(optionSource);
        handleMatchOptions.appendChild(optionTarget);
    }

    const addMatchOption = document.createElement('div');
    addMatchOption.style.width = `${paletteWidth * 2 / 2.3 + 10}px`;
    addMatchOption.style.height = `${optionHeight * 0.8}px`;
    addMatchOption.style.backgroundColor = 'lightgrey';
    addMatchOption.style.borderRadius = '5px'
    addMatchOption.dataset.id = "add-handle-match-group";
    addMatchOption.title = "Add handle match group";
    addMatchOption.textContent = "Add New"
    addMatchOption.style.fontWeight = "Bold"
    addMatchOption.style.display = 'flex'
    addMatchOption.style.justifyContent = "center"
    addMatchOption.style.alignItems = "center"

    handleMatchOptions.appendChild(addMatchOption);


}

export function copyMatchers(groupNumber, layerList, activeLayerId, minorGridSize){
    const fullLayer = layerList.get(activeLayerId)

    //Get handle layer
    let layerToCopyFrom = fullLayer[0]
    
    //Collect selected match markers into a dictionary
    let selectedMatchMarkerDict = {}
    let minX = Infinity
    let minY = Infinity
    layerToCopyFrom.children().forEach(child => {
        if(child.attr("class") == "handle-matcher-source"){
            if(child.attr('type') == groupNumber){
                let matchMarkerId = child.attr('id')
                let bbox = child.bbox()

                let centerX = Math.round((bbox.x + bbox.width / 2) / minorGridSize);
                let centerY = Math.round((bbox.y + bbox.height/ 2) / minorGridSize);

                if(centerX < minX){ minX = centerX }
                if(centerY < minY){ minY = centerY }

                // Populate the grid dictionary with the cargo ID for the occupied positions
                let key = [centerX, centerY]; 
                selectedMatchMarkerDict[key] = matchMarkerId
            }
        }
    });

    //Shift keys so that top LH cargo has coordinates (0, 0)
    let shiftedMatchMarkerDict = {}
    for (const [key, matchId] of Object.entries(selectedMatchMarkerDict)) {
        let keyArray = key.split(',')
        let shiftedX = Number(keyArray[0]) - minX
        let shiftedY = Number(keyArray[1]) - minY
        let shiftedKey = [shiftedX, shiftedY]
        shiftedMatchMarkerDict[shiftedKey] = matchId
    }

    return shiftedMatchMarkerDict
}

export function showCopiedMatchers(matcherDict, roundedX, roundedY, fullDrawing, minorGridSize){
    let radius = minorGridSize * 0.2
    let defaultColor = '#808080'; //Grey

    // Remove any existing shadow cargo with the id 'shadow-copied-cargo'
    let oldShadowMatchers = document.getElementById('shadow-copied-matchers')
    if(oldShadowMatchers){
        oldShadowMatchers.remove()
    }

    // Create new group to hold shadow coppied cargo
    let group = fullDrawing.group()

    for (const [key, matcherId] of Object.entries(matcherDict)) {
        let keyArray = key.split(',')
        let shiftedX = Number(keyArray[0]) * minorGridSize + roundedX
        let shiftedY = Number(keyArray[1]) * minorGridSize + roundedY

        let tmpShape = fullDrawing.circle(2 * radius) // SVG.js uses diameter, not radius
                                  .attr({ cx: shiftedX, cy: shiftedY })
                                  .fill(defaultColor) 
                                  .stroke(defaultColor) 
                                  .opacity(0.33);
        group.add(tmpShape)   
    }

    group.attr('id','shadow-copied-matchers')
    group.attr({ 'pointer-events': 'none' })
}

export function pasteMatchers(matcherDict, matchGroupNumber, startingX, startingY, activeHandleLayer, activeLayerId, minorGridSize, activeLayerColor, shownHandleOpacity, layerList){
    
    // Remove any existing shadow cargo with the id 'shadow-copied-cargo'
    let oldShadowMatchers = document.getElementById('shadow-copied-matchers')
    if(oldShadowMatchers){
        oldShadowMatchers.remove()
    }

    //Remove existing target markers
    activeHandleLayer.children().forEach(child => {
        if(child.attr("class") == "handle-matcher-target"){
            if(child.attr('type') == matchGroupNumber){
                child.remove()
            }
        }
    })

    //iterate through cargo, placing them!
    for (const [key, matchId] of Object.entries(matcherDict)) {
        let keyArray = key.split(',')
        let shiftedX = Number(keyArray[0]) * minorGridSize + startingX
        let shiftedY = Number(keyArray[1]) * minorGridSize + startingY

        placeHandleMatcher(shiftedX, 
                           shiftedY, 
                           activeHandleLayer, 
                           activeLayerId, 
                           minorGridSize, 
                           activeLayerColor, 
                           shownHandleOpacity, 
                           matchId, 
                           matchGroupNumber, 
                           layerList,
                           false) 
    }
}