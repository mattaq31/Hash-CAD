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

        const layerDivider = document.createElement('hr')
        layerDivider.className = 'handle-layer-divider'
        layerDivider.style.backgroundColor = layerColor; 

        const h5Text = document.createElement('p')
        h5Text.className = 'handle-layer-label'
        h5Text.textContent = "h5";

        handleLayerItem.appendChild(h2Text)
        handleLayerItem.appendChild(layerDivider)
        handleLayerItem.appendChild(h5Text)

        handleLayerViewer.appendChild(handleLayerItem);

    });




}