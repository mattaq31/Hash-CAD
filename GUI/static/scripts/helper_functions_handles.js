let handleConfigDict = {}




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

            //Only execute if div clicked directly, NOT if child dropdown was clicked
            if(event.currentTarget !== event.target){
                return
            }

            let clickedChild = event.target.parentElement;
            let parent = clickedChild.parentElement
            let children = Array.from(parent.children); // Convert HTMLCollection to an array
            
            let index = children.length - (children.indexOf(clickedChild)) + 1;

            document.querySelectorAll('.arrow').forEach(e => e.remove());
            let arrow = document.createElement('p')
            arrow.className = 'arrow'
            arrow.textContent = '\u2194'
            clickedChild.prepend(arrow)

            console.log("Handle layer selected: ", index)

            layerList.forEach((layer, layerIndex) => {
                layer[0].attr('opacity', 0)
                if(layerIndex == index - 1){
                    layer[0].attr('opacity', 1)
                }
            })

        })

        

        h25BottomDiv.addEventListener('click', function(event){

            //Only execute if div clicked directly, NOT if child dropdown was clicked
            if(event.currentTarget !== event.target){
                return
            }

            let clickedChild = event.target.parentElement;
            let parent = clickedChild.parentElement
            let children = Array.from(parent.children); // Convert HTMLCollection to an array
            
            let index = children.length - (children.indexOf(clickedChild));

            document.querySelectorAll('.arrow').forEach(e => e.remove());
            let arrow = document.createElement('p')
            arrow.className = 'arrow'
            arrow.textContent = '\u2194'
            clickedChild.appendChild(arrow)

            console.log("Handle layer selected: ",index)
            layerList.forEach((layer, layerIndex) => {

                layer[0].attr('opacity', 0)

                if(layerIndex == index - 1){
                    layer[0].attr('opacity', 1)
                }
            })

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


// Function to find the first non-<p> element
function findFirstNonPElement(parent) {
    for (let child of parent.children) {
        if (child.tagName.toLowerCase() !== 'p') {
            return child;
        }
    }
    return null; // Return null if no non-<p> element is found
}


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



export function getHandleLayerDict(layerList){
    const handleLayerViewer = document.getElementById('handle-layers')
    const layerChildren = handleLayerViewer.children
    const childrenArray = Array.from(layerChildren);


    handleConfigDict = {}


    let layerIndex = 0

    layerList.forEach((layer, layerId) => {
        var layerElement = childrenArray[layerIndex]
        var topDiv = layerElement.firstChild
        var bottomDiv = layerElement.lastChild

        var topSelector = findFirstNonPElement(layerElement).firstChild//topDiv)//.firstChild
        var bottomSelector = findLastNonPElement(layerElement).firstChild//bottomDiv)//.firstChild

        if (topSelector && bottomSelector) {
            var topH2H5 = topSelector.value;
            var bottomH2H5 = bottomSelector.value;
    
            handleConfigDict[layerId] = [topH2H5, bottomH2H5];
        } else {
            console.log(`Could not find suitable elements for layer ${layerId}.`);
        }

        //var topH2H5 = topSelector.value
        //var bottomH2H5 = bottomSelector.value

        //handleConfigDict[layerId] = [topH2H5, bottomH2H5]
        layerIndex += 1
    })

    console.log(handleConfigDict)

    return handleConfigDict
}



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

export function clearHandles(layerList){
    //First, clear old handles!
    layerList.forEach((layer, layerIndex) => {
        const layerElement = layer[0]; 
        layerElement.children().forEach(child => {
            child.remove();
        });

    })
}