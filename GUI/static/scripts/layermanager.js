var defaultColor = '#ff0000'

const hexColors = ['#ff0000', '#0000ff', '#ffff00', '#ff69b4', '#008000', '#ffa500'];


document.addEventListener('DOMContentLoaded', () => {
    const layerList = document.getElementById('layer-list');
    const addLayerButton = document.getElementById('add-layer');

    addLayerButton.addEventListener('click', () => {
        addLayer();
    });

    // TODO: move this to its own global function in this file and add a docstring
    function addLayer() {
        const layerItem = document.createElement('div');
        layerItem.className = 'layer-item';

        const layerId = layerList.children.length   // `layer-${layerList.children.length + 1}`;
        layerItem.dataset.layerId = layerId;  // Add a data attribute to identify the layer

        const layerCheckbox = document.createElement('input');
        layerCheckbox.type = 'checkbox';
        layerCheckbox.checked = true;
        layerCheckbox.addEventListener('change', toggleLayer);

        const layerName = document.createElement('span');
        layerName.textContent = `Layer ${layerId }`;//`Layer ${layerList.children.length + 1}`;

        const layerRadio = document.createElement('input');
        layerRadio.type = 'radio';
        layerRadio.name = 'active-layer';
        layerRadio.dataset.layerId = layerId;
        layerRadio.addEventListener('change', setActiveLayer);

        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.value = hexColors[layerId % 6]//defaultColor; // Set default color value
        colorPicker.addEventListener('input', setColor);

        const removeButton = document.createElement('button');
        removeButton.textContent = "\u2715"; //X symbol for removing layer!
        removeButton.classList.add("layer-remove-button");
        removeButton.addEventListener('click', () => {
            layerList.removeChild(layerItem);
            dispatchCustomEvent('layerRemoved', layerItem);
        });

        layerItem.appendChild(layerCheckbox);
        layerItem.appendChild(layerRadio);
        layerItem.appendChild(layerName);
        layerItem.appendChild(colorPicker);
        layerItem.appendChild(removeButton);
        layerList.appendChild(layerItem);

        dispatchCustomEvent('layerAdded', layerItem);

        // Set the first added layer as active by default
        if (layerList.children.length === 1) {
            layerRadio.checked = true;
            setActiveLayer({ target: layerRadio });
        }
    }

    function toggleLayer(event) {
        const layerItem = event.target.parentElement;
        if (event.target.checked) {
            layerItem.classList.remove('disabled');
            dispatchCustomEvent('layerShown', layerItem);
        } else {
            layerItem.classList.add('disabled');
            dispatchCustomEvent('layerHidden', layerItem);
        }
    }

    // TODO: move this to its own global function in this file and add a docstring
    function setActiveLayer(event) {
        const allLayers = document.querySelectorAll('.layer-item');
        allLayers.forEach(layer => layer.classList.remove('active'));

        const activeLayer = event.target.parentElement;
        activeLayer.classList.add('active');
        dispatchCustomEvent('layerMarkedActive', activeLayer);
    }

    // TODO: move this to its own global function in this file and add a docstring
    function setColor(event) {
        const layerItem = event.target.parentElement;
        const color = event.target.value;
        layerItem.dataset.layerColor = color || hexColors[layerItem.dataset.layerId % 6]//defaultColor; // Set the color as a data attribute
        dispatchCustomEvent('layerColorChanged', layerItem);
    }

    // TODO: move this to its own global function in this file and add a docstring
    // Function to dispatch custom events
    function dispatchCustomEvent(eventName, layerItem) {
        const event = new CustomEvent(eventName, {
            detail: {
                layerId: layerItem.dataset.layerId,
                layerElement: layerItem,
                layerColor: layerItem.dataset.layerColor || hexColors[layerItem.dataset.layerId % 6]//defaultColor // Include color in event details
            }
        });
        document.dispatchEvent(event);
    }

    // Add initial layers
    addLayer();
    addLayer();

});
