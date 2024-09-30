import { populateHandleMatchPalette, copyMatchers } from "./functions_handle_matching.js";
import { getVariable, writeVariable } from "./variables.js";

import { getLayerList } from './functions_layers.js'
import { minorGridSize } from "./constants.js";


// Set cargo type from inventory
const handleMatchOptions = document.getElementById('handle-match-options');
handleMatchOptions.addEventListener('click', function(event) {
    if (event.target.classList.contains('handle-match-option')) {
        if(event.target.dataset.source === 'true'){
            console.log("Selected handle match group: Source", event.target.dataset.id)
            writeVariable("handleMatchMode", 'source')
            writeVariable("handleMatchGroup", event.target.dataset.id)
        }
        else{
            console.log("Selected handle match group: Target", event.target.dataset.id)
            writeVariable("handleMatchMode", 'target')
            writeVariable("handleMatchGroup", event.target.dataset.id)

            let sourceMatchDict = copyMatchers(event.target.dataset.id, getLayerList(), getVariable("activeLayerId"), minorGridSize)
            writeVariable("matcherDict", sourceMatchDict)
            writeVariable("placeMatchers", true)
            console.log(sourceMatchDict)
        }
    }
    else if(event.target.dataset.id === "add-handle-match-group"){
        writeVariable("matchGroupNumber", 1 + getVariable("matchGroupNumber"))
        populateHandleMatchPalette(getVariable("matchGroupNumber"))
    }
});
