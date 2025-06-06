const hexColors = ['#a8327d', '#a83632', '#cf7725', '#a8a632', '#57a832', '#327da8', '#5f32a8']//['#ff0000', '#0000ff', '#ffff00', '#ff69b4', '#008000', '#ffa500'];
let layerList = new Map();

/**
 * Function to return a reference to the layerList map
 * @returns {Map} Dictionary of layers, indexed by layerIds, and containing the SVG.js layer group items
 */
export function getLayerList(){
    return layerList
}

/**
 * Function to create a new layer in the project
 */
export function addLayer() {
    const layerList = document.getElementById('layer-list');

    const layerItem = document.createElement('div');
    layerItem.className = 'layer-item';

    let layerId = null 

    console.log("Layerlist: ", layerList)

    if(layerList.children.length === 0){
        layerId = 1
    }
    else{
        let lastLayerId = layerList.children[0].dataset.layerId
        layerId = parseInt(lastLayerId) + 1
    }

    layerItem.dataset.layerId = layerId;  // Add a data attribute to identify the layer

    const layerCheckbox = document.createElement('input');
    layerCheckbox.type = 'checkbox';
    layerCheckbox.checked = true;
    layerCheckbox.addEventListener('change', toggleLayer);

    const layerName = document.createElement('span');
    layerName.textContent = `Layer ${layerId }`;

    const layerRadio = document.createElement('input');
    layerRadio.type = 'radio';
    layerRadio.name = 'active-layer';
    layerRadio.dataset.layerId = layerId;
    layerRadio.addEventListener('change', setActiveLayer);

    const colorPicker = document.createElement('input');
    colorPicker.type = 'color';
    colorPicker.value = hexColors[layerId % 6]
    colorPicker.addEventListener('input', setColor);

    const removeButton = document.createElement('button');
    removeButton.textContent = "\u2715"; //X symbol for removing layer!
    removeButton.classList.add("layer-remove-button");
    removeButton.addEventListener('click', () => {
        layerList.removeChild(layerItem);
        dispatchCustomLayerEvent('layerRemoved', layerItem);
    });

    layerItem.appendChild(layerCheckbox);
    layerItem.appendChild(layerRadio);
    layerItem.appendChild(layerName);
    layerItem.appendChild(colorPicker);
    layerItem.appendChild(removeButton);

    if (layerList.firstChild){
        layerList.insertBefore(layerItem, layerList.firstChild)
    }
    else{
        layerList.appendChild(layerItem)
    }

    dispatchCustomLayerEvent('layerAdded', layerItem);

    // Set the first added layer as active by default
    if (layerList.children.length === 1) {
        layerRadio.checked = true;
        setActiveLayer({ target: layerRadio });
    }
}

/** 
 * Function to dispatch custom layer-related events
 * @param {string} eventName Event name to be dispatched
 * @param {div} layerItem Layer item associated with this event
 */
export function dispatchCustomLayerEvent(eventName, layerItem) {
    const event = new CustomEvent(eventName, {
        detail: {
            layerId: layerItem.dataset.layerId,
            layerElement: layerItem,
            layerColor: layerItem.dataset.layerColor || hexColors[layerItem.dataset.layerId % 6]
        }
    });
    document.dispatchEvent(event);
}

/** 
 * Function to set active layer when appropriate radio button is pressed. 
 * Note: changes active layer in the layer manager, but doesn't change layer in actual design --> calls an event for that instead
 * @param {event} event Event associated with depression of radio button in layer manager
 */
export function setActiveLayer(event) {
    const allLayers = document.querySelectorAll('.layer-item');
    allLayers.forEach(layer => layer.classList.remove('active'));

    const activeLayer = event.target.parentElement;
    activeLayer.classList.add('active');
    dispatchCustomLayerEvent('layerMarkedActive', activeLayer);
}

/**
 * Function to change the layer color when appropriate color-selector is changed. 
 * Note: Doesn't change layer color in actual design --> calls an event for that instead
 * @param {event} event Event associated with changing of color-picker in layer manager
 */
export function setColor(event) {
    const layerItem = event.target.parentElement;
    const color = event.target.value;
    layerItem.dataset.layerColor = color || hexColors[layerItem.dataset.layerId % 6]
    dispatchCustomLayerEvent('layerColorChanged', layerItem);
}

/**
 * Function to make layers high or low opacity depending on whether the layer toggle is on or off
 * Note: doesn't change the layer opacity in the actual design --> calls an event for that instead.
 * @param {event} event Event associated with the toggling of layers in layer manager
 */
export function toggleLayer(event) {
    const layerItem = event.target.parentElement;
    if (event.target.checked) {
        layerItem.classList.remove('disabled');
        dispatchCustomLayerEvent('layerShown', layerItem);
    } else {
        layerItem.classList.add('disabled');
        dispatchCustomLayerEvent('layerHidden', layerItem);
    }
}
