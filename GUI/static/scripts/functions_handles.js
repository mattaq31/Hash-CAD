let handleConfigDict = {}

/**
 * Function to handle functionality when handle layer selector is clicked. Shows which layer was clicked, adjusts opacity as necessary
 * @param {Event} event Event associated with clicking handle layer selector
 * @param {Map} layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Boolean} top True if above handle layer line. False if below handle layer line.
 * @returns 
 */
function handleDivClicked(event, layerList, top=true){
    //Only execute if div clicked directly, NOT if child dropdown was clicked
    if(event.currentTarget !== event.target){
        return
    }

    let clickedChild = event.target.parentElement;
    let parent = clickedChild.parentElement
    let children = Array.from(parent.children); // Convert HTMLCollection to an array
        
    let index = children.length - (children.indexOf(clickedChild));
    if(top){
        index += 1
    }

    document.querySelectorAll('.arrow').forEach(e => e.remove());
    let arrow = document.createElement('p')
    arrow.className = 'arrow'
    arrow.textContent = '\u2194'

    if(top){
        clickedChild.prepend(arrow)
    }
    else{
        clickedChild.append(arrow)
    }
    
    console.log("Handle layer selected: ", index)

    layerList.forEach((layer, layerIndex) => {
        layer[0].attr('opacity', 0)
        if(layerIndex == index - 1){
            layer[0].attr('opacity', 1)
        }
    })
}

/**
 * Function to draw the proper handle layer interface in the palette
 * @param {Map} layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 */
export function updateHandleLayers(layerList){
    const handleLayerViewer = document.getElementById('handle-layers')
    handleLayerViewer.innerHTML = ''

    layerList.forEach((layer, layerIndex) => {

        let toggleTopH2 = true
        let toggleBottomH2 = false
        if(layerIndex in handleConfigDict){
            let configuration = handleConfigDict[layerIndex]
        
            if(configuration[0] == 2){
                toggleTopH2 = true
            }
            else{
                toggleTopH2 = false
            }

            if(configuration[1] == 2){
                toggleBottomH2 = true
            }
            else{
                toggleBottomH2 = false
            }
        }
        else{
            handleConfigDict[layerIndex] = [2,5]
        }

        console.log(layer)

        let layerColor = layer[4]

        const handleLayerItem = document.createElement('div')
        handleLayerItem.className = 'handle-layer-item'
        
        const h25TopDropdown = document.createElement('select')
        h25TopDropdown.options.add( new Option("H2", 2, toggleTopH2, toggleTopH2))
        h25TopDropdown.options.add( new Option("H5", 5, !toggleTopH2, !toggleTopH2))
        h25TopDropdown.style.margin = '5px'

        const h25BottomDropdown = document.createElement('select')
        h25BottomDropdown.options.add( new Option("H2", 2, toggleBottomH2, toggleBottomH2))
        h25BottomDropdown.options.add( new Option("H5", 5, !toggleBottomH2, !toggleBottomH2))
        h25BottomDropdown.style.margin = '5px'

        const h25TopDiv = document.createElement('div')
        h25TopDiv.appendChild(h25TopDropdown)

        const h25BottomDiv = document.createElement('div')
        h25BottomDiv.appendChild(h25BottomDropdown)

        h25TopDiv.addEventListener('click', function(event){
            handleDivClicked(event, layerList, true)
        })

        h25BottomDiv.addEventListener('click', function(event){
            handleDivClicked(event, layerList, false)
        })

        const layerDivider = document.createElement('hr')
        layerDivider.className = 'handle-layer-divider'
        layerDivider.style.backgroundColor = layerColor; 

        handleLayerItem.appendChild(h25TopDiv)
        handleLayerItem.appendChild(layerDivider)
        handleLayerItem.appendChild(h25BottomDiv)

        if (handleLayerViewer.firstChild){
            handleLayerViewer.insertBefore(handleLayerItem, handleLayerViewer.firstChild)
        }
        else{
            handleLayerViewer.appendChild(handleLayerItem)
        }
    });
}


/**
 * Function to find first non-<p> element that is the child of a particular element
 * @param {Element} parent Element whose children should be searched
 * @returns {Element | null} First non-<p> child of parent
 */
function findFirstNonPElement(parent) {
    for (let child of parent.children) {
        if (child.tagName.toLowerCase() !== 'p') {
            return child;
        }
    }
    return null; // Return null if no non-<p> element is found
}

/**
 * Function to find last non-<p> element that is the child of a particular element
 * @param {Element} parent Element whose children should be searched
 * @returns {Element | null} Last non-<p> child of parent
 */
function findLastNonPElement(parent) {
    for (let i = parent.children.length - 1; i >= 0; i--) {
        let child = parent.children[i];
        if (child.tagName.toLowerCase() !== 'p') {
            console.log("FOUND NON-P ELEMENT")
            return child;
        }
    }
    console.log("NO NON-P ELEMENTS FOUND")
    return null; // Return null if no non-<p> element is found
}

/**
 * Generates a dictionary for the handle configurations by layer
 * @param {Map} layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @returns {Map} Handle configuration dictionary -- {layerID: [top, bottom]}
 */
export function getHandleLayerDict(layerList){
    const handleLayerViewer = document.getElementById('handle-layers')
    const layerChildren = handleLayerViewer.children
    const childrenArray = Array.from(layerChildren);

    handleConfigDict = {}

    let layerIndex = 0

    layerList.forEach((layer, layerId) => {
        var layerElement = childrenArray[layerIndex]
        var topSelector = findFirstNonPElement(layerElement).firstChild
        var bottomSelector = findLastNonPElement(layerElement).firstChild

        if (topSelector && bottomSelector) {
            var topH2H5 = topSelector.value;
            var bottomH2H5 = bottomSelector.value;
            handleConfigDict[layerId] = [topH2H5, bottomH2H5];
        } 
        else {
            console.log(`Could not find suitable elements for layer ${layerId}.`);
        }
        layerIndex += 1
    })
    console.log(handleConfigDict)
    return handleConfigDict
}

// TODO: look into whether this function (and the one above) can be streamlined
export function setHandleLayerInterfacesFromDict(handleConfigDict, layerList){
    const handleLayerViewer = document.getElementById('handle-layers')
    const layerChildren = handleLayerViewer.children
    const childrenArray = Array.from(layerChildren);

    let layerIndex = 0

    layerList.forEach((layer, layerId) => {
        var layerElement = childrenArray[layerIndex]
        var topSelector = findFirstNonPElement(layerElement).firstChild
        var bottomSelector = findLastNonPElement(layerElement).firstChild

        if (topSelector && bottomSelector) {
            var topH2H5 = handleConfigDict[layerId][0];
            var bottomH2H5 = handleConfigDict[layerId][1];
            topSelector.value = topH2H5;
            bottomSelector.value = bottomH2H5;
        }
        else {
            console.log(`Could not find suitable elements for layer ${layerId}.`);
        }
        layerIndex += 1
    })
}


/**
 * Function to update the cargo layer selectors with proper H2/H5 labels
 * @param {Map} layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 * @param {Number} activeLayerId ID of the selected layer
 */
export function updateHandleLayerButtons(layerList, activeLayerId){
    const topLayerButton = document.getElementById('top-layer-selector')
    const bottomLayerButton = document.getElementById('bottom-layer-selector')

    let handleLayerDict = getHandleLayerDict(layerList)
    let handles = handleLayerDict[activeLayerId]

    let topLayerButtonText = topLayerButton.textContent
    let bottomLayerButtonText = bottomLayerButton.textContent

    let newTopButtonText = topLayerButtonText.slice(0, -1) + handles[0]; 
    let newBottomButtonText = bottomLayerButtonText.slice(0, -1) + handles[1]; 

    topLayerButton.textContent = newTopButtonText
    bottomLayerButton.textContent = newBottomButtonText
}

/**
 * Function to clear old handles
 * @param {Map} layerList List/Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 */
export function clearHandles(layerList){
    //First, clear old handles!
    layerList.forEach((layer, layerIndex) => {
        const layerElement = layer[0]; 
        layerElement.children().forEach(child => {
            child.remove();
        });
    })
}
