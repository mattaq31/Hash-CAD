export function updateHandleLayers(layerList){
    const handleLayerViewer = document.getElementById('handle-layers')

    handleLayerViewer.innerHTML = ''

    layerList.forEach((layer, layerIndex) => {

        console.log(layer)

        let layerColor = layer[3]

        const handleLayerItem = document.createElement('div')
        handleLayerItem.className = 'handle-layer-item'
        

        const h25TopDropdown = document.createElement('select')
        h25TopDropdown.options.add( new Option("H2", 2, true, true))
        h25TopDropdown.options.add( new Option("H5", 5))
        h25TopDropdown.style.margin = '5px'

        const h25BottomDropdown = document.createElement('select')
        h25BottomDropdown.options.add( new Option("H2", 2))
        h25BottomDropdown.options.add( new Option("H5", 5, true, true))
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
            
            let index = children.indexOf(clickedChild);

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
            
            let index = children.indexOf(clickedChild) + 1;

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

        handleLayerViewer.appendChild(handleLayerItem);

    });




}



export function getHandleLayerDict(layerList){
    const handleLayerViewer = document.getElementById('handle-layers')
    const layerChildren = handleLayerViewer.children
    const childrenArray = Array.from(layerChildren);


    let handleLayerDict = {}

    layerList.forEach((layer, layerIndex) => {
        var layerElement = childrenArray[layerIndex]
        var topDiv = layerElement.firstChild
        var bottomDiv = layerElement.lastChild

        var topSelector = topDiv.firstChild
        var bottomSelector = bottomDiv.firstChild

        var topH2H5 = topSelector.value
        var bottomH2H5 = bottomSelector.value

        handleLayerDict[layerIndex] = [topH2H5, bottomH2H5]
    })

    console.log(handleLayerDict)

    return handleLayerDict
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
