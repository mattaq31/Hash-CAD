import { populateHandleMatchPalette } from "./functions_handle_matching.js";
import { getVariable, writeVariable } from "./variables.js";

// Set cargo type from inventory
const handleMatchOptions = document.getElementById('handle-match-options');
handleMatchOptions.addEventListener('click', function(event) {
    if (event.target.classList.contains('handle-match-option')) {
        if(event.target.dataset.source == 'true'){
            console.log("Selected handle match group: Source", event.target.dataset.id)
            writeVariable("handleMatchMode", 'source')
            writeVariable("handleMatchGroup", event.target.dataset.id)
        }
        else{
            console.log("Selected handle match group: Target", event.target.dataset.id)
            writeVariable("handleMatchMode", 'target')
            writeVariable("handleMatchGroup", event.target.dataset.id)
        }
    }
    else if(event.target.dataset.id == "add-handle-match-group"){
        writeVariable("matchGroupNumber", 1 + getVariable("matchGroupNumber"))
        populateHandleMatchPalette(getVariable("matchGroupNumber"))
    }
});