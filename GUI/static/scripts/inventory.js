// inventory.js

// Sample inventory data
const inventoryData = [
    { id: 1, name: "Green Fluorescent Protein", acronym: "GFP", color: "#00FF00" },
    { id: 2, name: "Red Fluorescent Protein",   acronym: "RFP", color: "#FF0000" },
    { id: 3, name: "Antibody 1",                acronym: "Ab1", color: "#0000FF" },
    { id: 4, name: "Antibody 2",                acronym: "Ab2", color: "#FFFF00" },
    { id: 5, name: "Photonic Crystal 1",        acronym: "PC1", color: "#FF00FF" }
];

// Function to get all inventory items
export function getInventoryItems() {
    return inventoryData;
}

// Function to get a specific inventory item by ID
export function getInventoryItemById(id) {
    return inventoryData.find(item => item.id === id);
}

// Function to populate the cargo palette
export function populateCargoPalette() {
    const cargoOptions = document.getElementById('cargo-options');
    cargoOptions.innerHTML = ''; // Clear existing options

    inventoryData.forEach(item => {
        const option = document.createElement('div');
        option.className = 'cargo-option';
        option.style.backgroundColor = item.color;
        option.textContent = item.acronym;
        option.dataset.id = item.id;
        option.title = item.name;
        cargoOptions.appendChild(option);
    });
}