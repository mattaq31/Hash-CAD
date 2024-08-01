// Sample inventory data
let inventoryData = [
    {id: "default_GFP", name: "Green Fluorescent Protein", tag: "GFP", color: "#00FF00", plate: "", details: [[],[]]},
    {id: "default_RFP", name: "Red Fluorescent Protein", tag: "RFP", color: "#FF0000", plate: "", details: [[],[]]},
    {id: "default_AB1", name: "Antibody 1", tag: "Ab1", color: "#0000FF", plate: "", details: [[],[]]},
    {id: "default_AB2", name: "Antibody 2", tag: "Ab2", color: "#FFFF00", plate: "", details: [[],[]]},
    {id: "default_DH", name: "Dummy Handle", tag: "DH", color: "#FF00FF", plate: "", details: [[],[]]}
];

/**
 * Function to update cargo plates from python backend
 */
function updatePlates() {
    var socket = io();
    socket.emit('list_plates')
    socket.on('list_plates_response', function(files) {

        var fileList = document.getElementById('file-list');
        fileList.innerHTML = ''; // Clear any existing content
    
        files.forEach(function(file) {

            var fileContainer = document.createElement('div');
            fileContainer.classList.add('file-container');
            fileContainer.textContent = file;
            fileList.appendChild(fileContainer);
        });
    });
}

/**
 * Function to update internal inventory dictionary from cargo plates
 */
export function updateInventoryItems() {
    //var filepath = "C:\\Users\\cmbec\\OneDrive\\Cloud_Documents\\Shih_Lab_2024\\Crisscross-Design\\GUI\\used-cargo-plates"
    var socket = io();
    socket.emit('get_inventory')
    socket.on('inventory_sent', function(inventory) {
        console.log("Imported inventory!", inventory)
        inventoryData = inventory
        updatePlates()
    });
}

/**
 * Function to get inventory item with a particular ID
 * @param {String} id ID corresponding to particular type of cargo
 * @returns {{id: string, name: string, tag: string, color: string, plate: string, details: array}} Inventory item
 */
export function getInventoryItemById(id) {
    return inventoryData.find(item => item.id === id);
}

/**
 * Function to adjust SVG.text element size to fit within radius size
 * @param {SVG.text} text Text to scale
 * @param {Number} radius Radius to scale to
 */
function adjustTextSize(text, radius) {
    let fontSize = radius;
    text.font({size: fontSize});

    while (text.bbox().width > 1.8 * radius ) {
        fontSize *= 0.9;
        text.font({size: fontSize});
    }
}

/**
 * Function to populate the cargo palette from internal inventory dictionary
 */
export function populateCargoPalette() {

    const cargoOptions = document.getElementById('cargo-options');
    cargoOptions.innerHTML = ''; // Clear existing options
 
    // Calculate 1/5th of the parent's width
    const paletteWidth = cargoOptions.offsetWidth;
    const optionSize = paletteWidth / 5;

    inventoryData.forEach(item => {
        const option = document.createElement('div');
        option.className = 'cargo-option';

        option.style.width = `${optionSize}px`;
        option.style.height = `${optionSize}px`;
        option.style.backgroundColor = 'lightgrey';
        option.style.borderRadius = '5px'

        option.dataset.id = item.id;
        option.title = item.name;

        const draw = SVG().addTo(option).size(optionSize, optionSize);
        draw.attr('pointer-events', 'none')
        let radius = optionSize * 0.33
        draw.circle(radius * 2).attr({
            cx: optionSize / 2,
            cy: optionSize / 2,
            fill: item.color,
            stroke: 'black'
        });

        let text = draw.text(item.tag)
            .attr({x: optionSize / 2, y: optionSize / 2, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
            .attr({'stroke-width': radius / 20})
            .font({size: radius * 0.4, family: 'Arial', weight: 'bold', stroke: '#000000'})
            .fill('#FFFFFF');
        text.attr('pointer-events', 'none');

        adjustTextSize(text, radius);

        cargoOptions.appendChild(option);
    });

    const editCargo = document.createElement('div');
    editCargo.id = 'cargo-editor';

    editCargo.style.width = `${optionSize}px`;
    editCargo.style.height = `${optionSize}px`;
    editCargo.style.backgroundColor = 'lightgrey';
    editCargo.style.borderRadius = '5px'

    editCargo.title = 'Edit cargo options';
    editCargo.textContent = 'Edit'
    editCargo.style.fontSize = `${optionSize * 0.33}px`
    editCargo.style.display = 'flex'
    editCargo.style.justifyContent = "center"
    editCargo.style.alignItems = "center"
    cargoOptions.appendChild(editCargo)
}

/**
 * Function to add a new inventory item manually
 * @param {String} name Name for cargo item
 * @param {String} tag Short abbreviation for cargo item
 * @param {String} color Color to display cargo
 * @param {String} plate Filename of plate with cargo item
 * @param {Array} details Array [H2compatibility, H5Compatibility]
 * @returns {{id: string, name: string, tag: string, color: string, plate: string, details: array}} Inventory item
 */
export function addInventoryItem(name, tag, color, plate, details) {
    const newId = inventoryData.length + 1;
    const newItem = {
        id: newId,
        name: name,
        tag: tag,
        color: color,
        plate: plate,
        details: details
    };
    inventoryData.push(newItem);
    populateCargoPalette();
    renderInventoryTable();
    return newItem;
}

/**
 * Function to remove inventory item manually
 * @param {String} id ID corresponding to particular type of cargo
 */
function removeItem(id) {
    inventoryData = inventoryData.filter(item => item.id !== id);
    populateCargoPalette();
    renderInventoryTable();
}

/**
 * Function to add an inventory item to the popup table for inventory configuration
 * @param {HTML tbody} tableBody Body of popup table - HTML element
 * @param {{id: string, name: string, tag: string, color: string, plate: string, details: array}} item Inventory item
 * @param {HTML div} compatibilityDiv Div containing the H2/H5 compatibility indicators for the cargo item
 */
function addToInventoryPopup(tableBody, item, compatibilityDiv){
    const row = tableBody.insertRow();
    row.innerHTML = `
        <td ><nobr style="display: block; width: 150px; overflow-x: scroll; ">${item.id}</nobr></td>
        <td><input type="text" value="${item.name}" name="name" style="width: 100px;"></td>
        <td><input type="text" value="${item.tag}" name="tag" style="width: 75px;"></td>
        <td><input type="color" value="${item.color}" name="color"></td>
        <td ><nobr style="display: block; width: 150px; overflow-x: scroll; ">${item.plate}</nobr></td>
        <td class="rowDetails"></td>
        <td>
            <button id="inventory-remove-item">Remove</button>
        </td>
    `;

    row.querySelector(".rowDetails").appendChild(compatibilityDiv)

    // Add event listeners to inputs
    const nameInput = row.querySelector('input[name="name"]');
    const tagInput = row.querySelector('input[name="tag"]');
    const colorInput = row.querySelector('input[name="color"]');
    const removeButton = row.querySelector('#inventory-remove-item');

    nameInput.addEventListener('input', (event) => {
        console.log(`Name changed to: ${event.target.value}`);
        item.name = event.target.value
        populateCargoPalette()
    });

    tagInput.addEventListener('input', (event) => {
        console.log(`Tag changed to: ${event.target.value}`);
        item.tag = event.target.value
        populateCargoPalette()

        const elementsWithSpecificCargoId = document.querySelectorAll(`[data-cargo-Id="${item.id}"]`);

        // Loop through the selected elements
        elementsWithSpecificCargoId.forEach(element => {
            const circle = element.querySelectorAll(`[data-cargo-component="shape"]`)[0]
            const text = element.querySelectorAll(`[data-cargo-component="text"]`)[0]
            console.log(text)
            text.firstChild.textContent = item.tag; //We need to do child bc there is a tspan in the <text> element...
        });
    });

    colorInput.addEventListener('input', (event) => {
        console.log(`Color changed to: ${event.target.value}`);
        item.color = event.target.value
        populateCargoPalette()

        const elementsWithSpecificCargoId = document.querySelectorAll(`[data-cargo-Id="${item.id}"]`);

        // Loop through the selected elements
        elementsWithSpecificCargoId.forEach(element => {
            const circle = element.querySelectorAll(`[data-cargo-component="shape"]`)[0]
            const text = element.querySelectorAll(`[data-cargo-component="text"]`)[0]
            circle.setAttribute('fill', item.color);
        });
    });

    removeButton.addEventListener('click', (event) => {
        const elementsWithSpecificCargoId = document.querySelectorAll(`[data-cargo-Id="${item.id}"]`);

        // Loop through the selected elements
        elementsWithSpecificCargoId.forEach(element => {
            element.remove()
        });

        removeItem(item.id)
        console.log(`Item to remove: ${item.id}`);
    });
}

/**
 * Function to render the inventory palette from the internal inventory dictionary
 */
export function renderInventoryTable() {
    
    const tableBody = document.getElementById('inventoryTableBody');
    tableBody.innerHTML = '';

    inventoryData.forEach(item => {
        
        console.log("Item.details: ", item.details)
        
        const h2CompatibilityDiv = document.createElement('div')
        h2CompatibilityDiv.style.display = "flex";
        h2CompatibilityDiv.style.flexDirection = "row";
        let arrH2Compatibility = item.details[0]

        const h2Label = document.createElement('p')
        h2Label.textContent = "h2 "
        h2Label.style.fontSize = "6px"
        h2Label.style.margin = "0px"
        h2Label.style.whiteSpaceCollapse = "preserve"

        h2CompatibilityDiv.appendChild(h2Label)

        const h5CompatibilityDiv = document.createElement('div')
        h5CompatibilityDiv.style.display = "flex";
        h5CompatibilityDiv.style.flexDirection = "row";
        let arrH5Compatibility = item.details[1]

        const h5Label = document.createElement('p')
        h5Label.textContent = "h5 "
        h5Label.style.fontSize = "6px"
        h5Label.style.margin = "0px"
        h5Label.style.whiteSpaceCollapse = "preserve"

        h5CompatibilityDiv.appendChild(h5Label)

        for(let i=1; i!= 33; i++){
            const childDivH2 = document.createElement('div')
            if(arrH2Compatibility.includes(i)){
                childDivH2.style.backgroundColor = "#00FF00";
            }
            else{
                childDivH2.style.backgroundColor = "#808080"
            }

            const childDivH5 = document.createElement('div')
            if(arrH5Compatibility.includes(i)){
                childDivH5.style.backgroundColor = "#00FF00";
            }
            else{
                childDivH5.style.backgroundColor = "#808080"
            }

            childDivH2.style.width = "2px"
            childDivH2.style.height = "8px"
            childDivH5.style.width = "2px"
            childDivH5.style.height = "8px"
            
            h2CompatibilityDiv.appendChild(childDivH2)
            h5CompatibilityDiv.appendChild(childDivH5)
        }

        const compatibilityDiv = document.createElement('div')
        compatibilityDiv.style.display = "flex";
        compatibilityDiv.style.flexDirection = "column";
        compatibilityDiv.style.gap = "2px";
        compatibilityDiv.style.alignItems = "center"
        compatibilityDiv.appendChild(h2CompatibilityDiv)
        compatibilityDiv.appendChild(h5CompatibilityDiv)

        addToInventoryPopup(tableBody, item, compatibilityDiv)

        
    });
}