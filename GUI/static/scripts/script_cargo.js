import {updateInventoryItems, populateCargoPalette, renderInventoryTable } from './functions_inventory.js'
import { changeCursorEvents } from './functions_misc.js'

import { getVariable, writeVariable } from './variables.js'

updateInventoryItems()
renderInventoryTable() 

// Choose which sublayer to draw cargo on
const topLayerButton = document.getElementById('top-layer-selector')
const bottomLayerButton = document.getElementById('bottom-layer-selector')
const seedButton = document.getElementById('seed-mode-selector')

topLayerButton.addEventListener('click', (event)=>{
    topLayerButton.classList.add('h25-toggle-selected')
    bottomLayerButton.classList.remove('h25-toggle-selected')
    seedButton.classList.remove('h25-toggle-selected')

    changeCursorEvents(getVariable("activeTopCargoLayer"), 'bounding-box')
    changeCursorEvents(getVariable("activeBottomCargoLayer"), 'none')
    let activeCargoLayer = getVariable("activeTopCargoLayer")
    writeVariable("activeCargoLayer", activeCargoLayer)
})

bottomLayerButton.addEventListener('click', (event)=>{
    bottomLayerButton.classList.add('h25-toggle-selected')
    topLayerButton.classList.remove('h25-toggle-selected')
    seedButton.classList.remove('h25-toggle-selected')

    changeCursorEvents(getVariable("activeTopCargoLayer"), 'none')
    changeCursorEvents(getVariable("activeBottomCargoLayer"), 'bounding-box')
    let activeCargoLayer = getVariable("activeBottomCargoLayer")
    writeVariable("activeCargoLayer", activeCargoLayer)
})

seedButton.addEventListener('click', (event)=>{
    seedButton.classList.add('h25-toggle-selected')
    bottomLayerButton.classList.add('h25-toggle-selected')
    topLayerButton.classList.remove('h25-toggle-selected')

    changeCursorEvents(getVariable("activeTopCargoLayer"), 'none')
    changeCursorEvents(getVariable("activeBottomCargoLayer"), 'bounding-box')
    let activeCargoLayer = getVariable("activeBottomCargoLayer")
    writeVariable("activeCargoLayer", activeCargoLayer)
})

// Set cargo type from inventory
const cargoOptions = document.getElementById('cargo-options')
cargoOptions.addEventListener('click', function(event) {
    if (event.target.classList.contains('cargo-option')) {
        writeVariable("selectedCargoId", event.target.dataset.id);
        console.log("Selected cargo ID: " + getVariable("selectedCargoId"));
    }
    else if(event.target.id == 'cargo-editor'){
        let modal = document.getElementById('cargoInventoryModal')
        modal.style.display = "block";
        renderInventoryTable();
    }
});

// Close inventory popup table
const modalCloseButton = document.getElementById('inventory-modal-close')
modalCloseButton.addEventListener('click',function(event){
    let modal = document.getElementById('cargoInventoryModal')
    modal.style.display = "none";
})

// Add inventory item via popup table
document.getElementById('add-inventory-cargo-element').addEventListener('click',function(event){
    addInventoryItem('Cargo Name', 'ABC', '#000000',"", "")
    renderInventoryTable();
})

// Update inventory to reflect internally stored inventory dictionary
document.getElementById('update-inventory-from-import').addEventListener('click', function(){
    populateCargoPalette();
    renderInventoryTable();
})

