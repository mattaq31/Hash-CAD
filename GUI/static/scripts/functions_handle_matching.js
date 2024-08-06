import { getVariable, writeVariable } from "./variables.js";

export function populateHandleMatchPalette(numberOfMatchGroups) {

    const handleMatchOptions = document.getElementById('handle-match-options');
    handleMatchOptions.innerHTML = ''; // Clear existing options
 
    // Calculate 1/5th of the parent's width
    const paletteWidth = handleMatchOptions.offsetWidth;
    const optionWidth = paletteWidth / 2.3;
    const optionHeight = paletteWidth / 7
    console.log("Palette width is measured as: ", paletteWidth)

    for (let i = 0; i < numberOfMatchGroups; i++) {
        const optionSource = document.createElement('div');
        optionSource.className = 'handle-match-option';
        optionSource.style.width = `${optionWidth}px`;
        optionSource.style.height = `${optionHeight}px`;
        optionSource.style.backgroundColor = 'lightgrey';
        optionSource.style.borderRadius = '5px'
        optionSource.dataset.id = i;
        optionSource.dataset.source = true;
        optionSource.title = "source: " + i;

        const optionTarget = document.createElement('div');
        optionTarget.className = 'handle-match-option';
        optionTarget.style.width = `${optionWidth}px`;
        optionTarget.style.height = `${optionHeight}px`;
        optionTarget.style.backgroundColor = 'lightgrey';
        optionTarget.style.borderRadius = '5px'
        optionTarget.dataset.id = i;
        optionTarget.dataset.source = false;
        optionTarget.title = "target: " + i;

        const drawSource = SVG().addTo(optionSource).size(optionWidth, optionHeight);
        const drawTarget = SVG().addTo(optionTarget).size(optionWidth, optionHeight);

        drawSource.attr('pointer-events', 'none')
        let radius = optionHeight * 0.33
        drawSource.circle(radius * 2).attr({
            cx: optionWidth * 0.75,
            cy: optionHeight * 0.5,
            fill: 'grey',
            stroke: 'black'
        });

        drawTarget.attr('pointer-events', 'none')
        let width = optionHeight * 0.66
        drawTarget.rect(width, width)
                  .move(optionWidth * 0.75 - width * 0.5, optionHeight * 0.5 - width * 0.5)
                  .fill('grey') 
                  .stroke('black') 

        let textSourceNumber = drawSource.text("" + i)
                             .attr({x: optionWidth * 0.75, y: optionHeight * 0.55, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
                             .font({size: optionHeight * 0.4, family: 'Arial', weight: 'bold'})
                             .fill('#000000')
                             .attr('pointer-events', 'none');

        let textTargetNumber = drawTarget.text("" + i)
                             .attr({x: optionWidth * 0.75, y: optionHeight * 0.55, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
                             .font({size: optionHeight * 0.4, family: 'Arial', weight: 'bold'})
                             .fill('#000000')
                             .attr('pointer-events', 'none');

        let textSource = drawSource.text("Source: ")
                             .attr({x: optionWidth * 0.33, y: optionHeight * 0.55, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
                             .font({size: optionHeight * 0.4, family: 'Arial', weight: 'bold'})
                             .fill('#000000')
                             .attr('pointer-events', 'none');

        let textTarget = drawTarget.text("Target: ")
                             .attr({x: optionWidth * 0.3, y: optionHeight * 0.55, 'dominant-baseline': 'middle', 'text-anchor': 'middle'})
                             .font({size: optionHeight * 0.4, family: 'Arial', weight: 'bold'})
                             .fill('#000000')
                             .attr('pointer-events', 'none');

        handleMatchOptions.appendChild(optionSource);
        handleMatchOptions.appendChild(optionTarget);
    }

    const addMatchOption = document.createElement('div');
    addMatchOption.style.width = `${paletteWidth * 2 / 2.3 + 10}px`;
    addMatchOption.style.height = `${optionHeight * 0.8}px`;
    addMatchOption.style.backgroundColor = 'lightgrey';
    addMatchOption.style.borderRadius = '5px'
    addMatchOption.dataset.id = "add-handle-match-group";
    addMatchOption.title = "Add handle match group";
    addMatchOption.textContent = "Add New"
    addMatchOption.style.fontWeight = "Bold"
    addMatchOption.style.display = 'flex'
    addMatchOption.style.justifyContent = "center"
    addMatchOption.style.alignItems = "center"

    handleMatchOptions.appendChild(addMatchOption);


}