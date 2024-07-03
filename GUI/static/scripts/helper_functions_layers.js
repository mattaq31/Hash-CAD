export function updateHandleLayers(layerList){
    const handleLayerViewer = document.getElementById('handle-layers')

    handleLayerViewer.innerHTML = ''

    layerList.forEach((layer, layerIndex) => {

        console.log(layer)

        let layerColor = layer[3]

        const handleLayerItem = document.createElement('div')
        handleLayerItem.className = 'handle-layer-item'

        const h2Text = document.createElement('p')
        h2Text.className = 'handle-layer-label'
        h2Text.textContent = "h2";

        h2Text.addEventListener('click', function(event){

            let clickedChild = event.target.parentElement;
            let parent = clickedChild.parentElement
            let children = Array.from(parent.children); // Convert HTMLCollection to an array
            
            let index = children.indexOf(clickedChild);

            document.querySelectorAll('.arrow').forEach(e => e.remove());
            let arrow = document.createElement('p')
            arrow.className = 'arrow'
            arrow.textContent = '\u2194'
            clickedChild.prepend(arrow)

            console.log("Handle layer selected: ",index)

        })

        const layerDivider = document.createElement('hr')
        layerDivider.className = 'handle-layer-divider'
        layerDivider.style.backgroundColor = layerColor; 

        const h5Text = document.createElement('p')
        h5Text.className = 'handle-layer-label'
        h5Text.textContent = "h5";

        h5Text.addEventListener('click', function(event){

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

        })

        handleLayerItem.appendChild(h2Text)
        handleLayerItem.appendChild(layerDivider)
        handleLayerItem.appendChild(h5Text)

        handleLayerViewer.appendChild(handleLayerItem);

    });




}