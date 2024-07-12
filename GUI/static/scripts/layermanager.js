import {addLayer} from './helper_functions_layers.js'


document.addEventListener('DOMContentLoaded', () => {
    
    const addLayerButton = document.getElementById('add-layer');

    addLayerButton.addEventListener('click', () => {
        addLayer();
    });

    // Add initial layers
    addLayer();
    addLayer();

});
